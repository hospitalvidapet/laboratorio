from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import LabRequest

main_bp = Blueprint("main", __name__)

@main_bp.route("/dashboard")
@login_required
def dashboard():
    selected = request.args.get("status", "").strip()

    total = LabRequest.query.count()
    pending = LabRequest.query.filter(
        LabRequest.status.notin_(["Resultado liberado", "Exame cancelado"])
    ).count()
    analysis = LabRequest.query.filter_by(status="Em análise").count()
    released = LabRequest.query.filter_by(status="Resultado liberado").count()

    query = LabRequest.query
    page_title = "Últimas requisições"

    if selected == "pending":
        query = query.filter(
            LabRequest.status.notin_(["Resultado liberado", "Exame cancelado"])
        )
        page_title = "Requisições pendentes"
    elif selected == "analysis":
        query = query.filter_by(status="Em análise")
        page_title = "Requisições em análise"
    elif selected == "released":
        query = query.filter_by(status="Resultado liberado")
        page_title = "Resultados liberados"

    latest = query.order_by(LabRequest.id.desc()).limit(100).all()

    return render_template(
        "main/dashboard.html",
        total=total,
        pending=pending,
        analysis=analysis,
        released=released,
        latest=latest,
        selected=selected,
        page_title=page_title,
    )

@main_bp.route("/health")
def health():
    return {"status": "ok"}, 200
