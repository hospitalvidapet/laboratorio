import json
import os
import threading
import time
from datetime import datetime
from typing import Any

from flask import current_app
from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.exc import NoSuchTableError, SQLAlchemyError

from app import db
from app.models import Exam, ExamGroup, ExamProfile, SampleType, Species, SyncRun

_sync_lock = threading.Lock()
_scheduler_started = False


def normalize_database_url(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def source_url() -> str:
    return normalize_database_url(os.getenv("ONLINE_DATABASE_URL", ""))


def is_configured() -> bool:
    return bool(source_url())


def _rows(engine, table_name: str) -> list[dict[str, Any]]:
    metadata = MetaData()
    try:
        table = Table(table_name, metadata, autoload_with=engine)
    except NoSuchTableError:
        return []
    with engine.connect() as connection:
        return [dict(row._mapping) for row in connection.execute(select(table))]


def test_connection() -> dict[str, Any]:
    url = source_url()
    if not url:
        return {"ok": False, "message": "ONLINE_DATABASE_URL não está configurada."}
    engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10} if url.startswith("postgresql") else {})
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        available = []
        for name in ("species", "exam_groups", "exams", "exam_profiles", "sample_types"):
            if _rows(engine, name) or _table_exists(engine, name):
                available.append(name)
        return {"ok": True, "message": "Conexão realizada com sucesso.", "tables": available}
    except SQLAlchemyError as exc:
        current_app.logger.exception("Falha ao testar conexão de sincronização")
        return {"ok": False, "message": f"Falha na conexão: {type(exc).__name__}"}
    finally:
        engine.dispose()


def _table_exists(engine, table_name: str) -> bool:
    from sqlalchemy import inspect
    return inspect(engine).has_table(table_name)


def _clean_name(value: Any) -> str:
    return str(value or "").strip()


def _as_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "não", "nao", "off", "inactive"}
    return bool(value)


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalized_exam_list(value: Any) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        try:
            raw = json.loads(value or "[]")
        except (TypeError, json.JSONDecodeError):
            raw = []
    result = []
    for item in raw:
        if isinstance(item, dict):
            name = _clean_name(item.get("name"))
        else:
            name = _clean_name(item)
        if name and name not in result:
            result.append(name)
    return result


def synchronize_catalog(trigger: str = "manual") -> dict[str, Any]:
    """Synchronize catalog data from ONLINE_DATABASE_URL into the current database.

    Matching is case-insensitive by name. Existing destination records are updated;
    missing records are created. Nothing is deleted, protecting local history.
    """
    if not _sync_lock.acquire(blocking=False):
        return {"ok": False, "message": "Já existe uma sincronização em andamento."}

    run = SyncRun(trigger=trigger, status="running", started_at=datetime.utcnow())
    db.session.add(run)
    db.session.commit()

    counts = {
        "species_created": 0, "species_updated": 0,
        "groups_created": 0, "groups_updated": 0,
        "exams_created": 0, "exams_updated": 0,
        "profiles_created": 0, "profiles_updated": 0,
        "samples_created": 0, "samples_updated": 0,
    }

    engine = None
    try:
        url = source_url()
        if not url:
            raise RuntimeError("ONLINE_DATABASE_URL não está configurada.")
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 15} if url.startswith("postgresql") else {})

        species_rows = _rows(engine, "species")
        group_rows = _rows(engine, "exam_groups")
        exam_rows = _rows(engine, "exams")
        profile_rows = _rows(engine, "exam_profiles")
        sample_rows = _rows(engine, "sample_types")

        source_group_names = {row.get("id"): _clean_name(row.get("name")) for row in group_rows}

        for row in species_rows:
            name = _clean_name(row.get("name"))
            if not name:
                continue
            obj = Species.query.filter(db.func.lower(Species.name) == name.lower()).first()
            if obj is None:
                obj = Species(name=name)
                db.session.add(obj)
                counts["species_created"] += 1
            else:
                counts["species_updated"] += 1
            obj.display_order = _as_int(row.get("display_order"), 999)
            obj.active = _as_bool(row.get("active"), True)

        for row in group_rows:
            name = _clean_name(row.get("name"))
            if not name:
                continue
            obj = ExamGroup.query.filter(db.func.lower(ExamGroup.name) == name.lower()).first()
            if obj is None:
                obj = ExamGroup(name=name)
                db.session.add(obj)
                counts["groups_created"] += 1
            else:
                counts["groups_updated"] += 1
            obj.display_order = _as_int(row.get("display_order"), 999)
        db.session.flush()

        destination_groups = {group.name.lower(): group for group in ExamGroup.query.all()}
        for row in exam_rows:
            name = _clean_name(row.get("name"))
            if not name:
                continue
            obj = Exam.query.filter(db.func.lower(Exam.name) == name.lower()).first()
            if obj is None:
                obj = Exam(name=name)
                db.session.add(obj)
                counts["exams_created"] += 1
            else:
                counts["exams_updated"] += 1
            group_name = source_group_names.get(row.get("group_id"), "")
            obj.group = destination_groups.get(group_name.lower()) if group_name else None
            obj.material = row.get("material")
            obj.deadline_hours = _as_int(row.get("deadline_hours"), 24)
            obj.active = _as_bool(row.get("active"), True)

        for row in profile_rows:
            name = _clean_name(row.get("name"))
            if not name:
                continue
            obj = ExamProfile.query.filter(db.func.lower(ExamProfile.name) == name.lower()).first()
            if obj is None:
                obj = ExamProfile(name=name)
                db.session.add(obj)
                counts["profiles_created"] += 1
            else:
                counts["profiles_updated"] += 1
            obj.exams_json = json.dumps(_normalized_exam_list(row.get("exams_json")), ensure_ascii=False)
            obj.active = _as_bool(row.get("active"), True)

        for row in sample_rows:
            name = _clean_name(row.get("name"))
            if not name:
                continue
            obj = SampleType.query.filter(db.func.lower(SampleType.name) == name.lower()).first()
            if obj is None:
                obj = SampleType(name=name)
                db.session.add(obj)
                counts["samples_created"] += 1
            else:
                counts["samples_updated"] += 1
            obj.display_order = _as_int(row.get("display_order"), 999)
            obj.active = _as_bool(row.get("active"), True)

        run.status = "success"
        run.finished_at = datetime.utcnow()
        run.details_json = json.dumps(counts, ensure_ascii=False)
        db.session.commit()
        return {"ok": True, "message": "Sincronização concluída.", "counts": counts}
    except Exception as exc:
        db.session.rollback()
        failed_run = db.session.get(SyncRun, run.id)
        if failed_run:
            failed_run.status = "error"
            failed_run.finished_at = datetime.utcnow()
            failed_run.error_message = str(exc)[:1000]
            db.session.commit()
        current_app.logger.exception("Falha na sincronização automática")
        return {"ok": False, "message": str(exc)}
    finally:
        if engine is not None:
            engine.dispose()
        _sync_lock.release()


def start_scheduler(app) -> None:
    global _scheduler_started
    if _scheduler_started or not app.config.get("AUTO_SYNC_ENABLED") or not is_configured():
        return
    # Avoid duplicate development-reloader threads.
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return
    _scheduler_started = True
    interval = max(5, int(app.config.get("AUTO_SYNC_INTERVAL_MINUTES", 30))) * 60

    def worker() -> None:
        if app.config.get("AUTO_SYNC_ON_STARTUP", True):
            time.sleep(5)
            with app.app_context():
                synchronize_catalog(trigger="startup")
        while True:
            time.sleep(interval)
            with app.app_context():
                synchronize_catalog(trigger="automatic")

    threading.Thread(target=worker, name="catalog-sync", daemon=True).start()
