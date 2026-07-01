
import os,json
from pathlib import Path
from datetime import datetime,timedelta
from functools import wraps
from flask import Flask,render_template,request,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import create_engine,text

APP_NAME="LABORATÓRIO VIDAPET"
BASE=Path(__file__).resolve().parent
DBURL=os.environ.get("DATABASE_URL")
if DBURL:
    DBURL = DBURL.replace("postgres://", "postgresql+psycopg://", 1)
    DBURL = DBURL.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DBURL = f"sqlite:///{BASE/'laboratorio_vidapet.db'}"
engine=create_engine(DBURL,future=True)
app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY","troque-esta-chave")
STATUS_LIST=["Requisição enviada","Aguardando amostra","Amostra recebida","Em análise","Resultado liberado","Exame cancelado"]
PRIORITIES=["Rotina","Urgente","Emergência"]

def pg(): return engine.dialect.name=="postgresql"
def compat(sql): return sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT","SERIAL PRIMARY KEY") if pg() else sql
def rows(res): return [dict(r._mapping) for r in res]
def one(res):
    r=res.fetchone(); return dict(r._mapping) if r else None

def init_db():
    with engine.begin() as db:
        for sql in [
        "CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY,value TEXT)",
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,profile TEXT NOT NULL,active INTEGER DEFAULT 1,created_at TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS clinics (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,cnpj TEXT,phone TEXT,email TEXT,created_at TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS exam_groups (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,display_order INTEGER DEFAULT 999)",
        "CREATE TABLE IF NOT EXISTS exams (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,material TEXT,deadline_hours INTEGER DEFAULT 24,group_id INTEGER,active INTEGER DEFAULT 1,display_order INTEGER DEFAULT 999)",
        "CREATE TABLE IF NOT EXISTS exam_profiles (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,exams_json TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS sample_types (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,active INTEGER DEFAULT 1,display_order INTEGER DEFAULT 999)",
        "CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT,number TEXT UNIQUE NOT NULL,clinic_name TEXT NOT NULL,veterinarian TEXT NOT NULL,crmv TEXT,tutor TEXT NOT NULL,tutor_phone TEXT,patient TEXT NOT NULL,species TEXT,breed TEXT,sex TEXT,age TEXT,weight TEXT,samples_json TEXT NOT NULL,collection_datetime TEXT,priority TEXT NOT NULL,exams_json TEXT NOT NULL,history_clinical TEXT,suspicion TEXT,medications TEXT,observations TEXT,status TEXT NOT NULL,due_at TEXT,created_by INTEGER,created_at TEXT NOT NULL,lab_internal_obs TEXT)",
        "CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,user_name TEXT,action TEXT NOT NULL,created_at TEXT NOT NULL)"
        ]: db.execute(text(compat(sql)))
        seeded=db.execute(text("SELECT value FROM app_settings WHERE key='seeded_defaults'")).scalar()
        if seeded=="1": return
        existing_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        if existing_users and int(existing_users) > 0:
            db.execute(text("INSERT INTO app_settings (key,value) VALUES ('seeded_defaults','1')"))
            return
        now=datetime.now().isoformat(timespec="seconds")
        for n,e,p,prof in [("Administrador","admin@vidapet.com.br","admin123","admin"),("Laboratório","laboratorio@vidapet.com.br","123456","laboratorio"),("Requisitante","requisitante@vidapet.com.br","123456","requisitante")]:
            db.execute(text("INSERT INTO users (name,email,password_hash,profile,active,created_at) VALUES (:n,:e,:h,:p,1,:c)"),dict(n=n,e=e,h=generate_password_hash(p),p=prof,c=now))
        for n,c,p in [("VIDAPET JD DAS AMÉRICAS","54.689.572/001-21",""),("VIDAPET STA CÂNDIDA","54.689.572/001-21","(41) 3209-3950")]:
            db.execute(text("INSERT INTO clinics (name,cnpj,phone,email,created_at) VALUES (:n,:c,:p,'',:dt)"),dict(n=n,c=c,p=p,dt=now))
        gids={}
        for n,o in [("Hematologia",20),("Bioquímica",30),("Urinálise",40),("Microbiologia",50),("Endocrinologia",60),("Testes rápidos",70),("Outros",999)]:
            if pg():
                gid=db.execute(text("INSERT INTO exam_groups (name,display_order) VALUES (:n,:o) RETURNING id"),dict(n=n,o=o)).scalar()
            else:
                db.execute(text("INSERT INTO exam_groups (name,display_order) VALUES (:n,:o)"),dict(n=n,o=o)); gid=db.execute(text("SELECT last_insert_rowid()")).scalar()
            gids[n]=gid
        for n,m,d,g in [("Hemograma","Sangue total EDTA",24,"Hematologia"),("Bioquímico completo","Soro",24,"Bioquímica"),("Ureia e Creatinina","Soro",24,"Bioquímica"),("ALT, FA e GGT","Soro",24,"Bioquímica"),("Urina tipo I","Urina",24,"Urinálise"),("Urocultura + Antibiograma","Urina estéril",72,"Microbiologia"),("Perfil pancreático","Soro",48,"Bioquímica"),("Eletrólitos","Soro/Plasma",24,"Bioquímica"),("T4 Total","Soro",48,"Endocrinologia"),("Teste rápido","Conforme kit",4,"Testes rápidos")]:
            db.execute(text("INSERT INTO exams (name,material,deadline_hours,group_id,active,display_order) VALUES (:n,:m,:d,:g,1,999)"),dict(n=n,m=m,d=d,g=gids[g]))
        for n,exs in [("Perfil pré-operatório",["Hemograma","Bioquímico completo"]),("Perfil renal",["Ureia e Creatinina","Urina tipo I","Eletrólitos"]),("Perfil hepático",["ALT, FA e GGT","Bioquímico completo"])]:
            db.execute(text("INSERT INTO exam_profiles (name,exams_json) VALUES (:n,:e)"),dict(n=n,e=json.dumps(exs,ensure_ascii=False)))
        for n,o in [("Sangue total EDTA",10),("Soro",20),("Plasma",30),("Urina",40),("Fezes",50),("Swab",60),("Líquido cavitário",70),("Outro",999)]:
            db.execute(text("INSERT INTO sample_types (name,active,display_order) VALUES (:n,1,:o)"),dict(n=n,o=o))
        db.execute(text("INSERT INTO app_settings (key,value) VALUES ('seeded_defaults','1')"))

def cur_user():
    if "uid" not in session: return None
    with engine.begin() as db: return one(db.execute(text("SELECT * FROM users WHERE id=:id AND active=1"),dict(id=session["uid"])))
def login_required(f):
    @wraps(f)
    def w(*a,**k):
        if not cur_user(): return redirect(url_for("login"))
        return f(*a,**k)
    return w
def role(*profiles):
    def dec(f):
        @wraps(f)
        def w(*a,**k):
            u=cur_user()
            if not u or u["profile"] not in profiles:
                flash("Acesso não autorizado.","error"); return redirect(url_for("dashboard"))
            return f(*a,**k)
        return w
    return dec
def audit(act):
    u=cur_user()
    with engine.begin() as db: db.execute(text("INSERT INTO audit (user_id,user_name,action,created_at) VALUES (:i,:n,:a,:d)"),dict(i=u["id"] if u else None,n=u["name"] if u else "Sistema",a=act,d=datetime.now().isoformat(timespec="seconds")))
def refs(active=True):
    with engine.begin() as db:
        clinics=rows(db.execute(text("SELECT * FROM clinics ORDER BY name")))
        where="WHERE e.active=1" if active else ""
        exams=rows(db.execute(text(f"SELECT e.*,g.name group_name FROM exams e LEFT JOIN exam_groups g ON g.id=e.group_id {where} ORDER BY COALESCE(g.display_order,999),g.name,COALESCE(e.display_order,999),e.name")))
        groups=rows(db.execute(text("SELECT * FROM exam_groups ORDER BY COALESCE(display_order,999),name")))
        profiles=rows(db.execute(text("SELECT * FROM exam_profiles ORDER BY name")))
        samples=rows(db.execute(text(("SELECT * FROM sample_types WHERE active=1 " if active else "SELECT * FROM sample_types ")+"ORDER BY COALESCE(display_order,999),name")))
        users=rows(db.execute(text("SELECT * FROM users ORDER BY name")))
        return clinics,exams,groups,profiles,samples,users

@app.context_processor
def inj(): return dict(APP_NAME=APP_NAME,user=cur_user(),STATUS_LIST=STATUS_LIST,PRIORITIES=PRIORITIES)
@app.template_filter("json_list")
def jl(v):
    try: return ", ".join(json.loads(v))
    except Exception: return v or "-"
@app.template_filter("json_to_list")
def jtl(v):
    try: return json.loads(v)
    except Exception: return []
@app.template_filter("datebr")
def db(v):
    if not v: return "-"
    try: return datetime.fromisoformat(v).strftime("%d/%m/%Y %H:%M")
    except Exception: return v

@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); pwd=request.form.get("password","")
        with engine.begin() as db: u=one(db.execute(text("SELECT * FROM users WHERE email=:e AND active=1"),dict(e=email)))
        if u and check_password_hash(u["password_hash"],pwd):
            session["uid"]=u["id"]; audit("Acessou o sistema"); return redirect(url_for("dashboard"))
        flash("Usuário ou senha inválidos.","error")
    return render_template("login.html")
@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))
@app.route("/dashboard")
@login_required
def dashboard():
    with engine.begin() as db:
        total=db.execute(text("SELECT COUNT(*) FROM requests")).scalar()
        pending=db.execute(text("SELECT COUNT(*) FROM requests WHERE status NOT IN ('Resultado liberado','Exame cancelado')")).scalar()
        analysis=db.execute(text("SELECT COUNT(*) FROM requests WHERE status='Em análise'")).scalar()
        released=db.execute(text("SELECT COUNT(*) FROM requests WHERE status='Resultado liberado'")).scalar()
        latest=rows(db.execute(text("SELECT * FROM requests ORDER BY id DESC LIMIT 5")))
    return render_template("dashboard.html",total=total,pending=pending,analysis=analysis,released=released,latest=latest)
@app.route("/requests")
@login_required
def requests_list():
    with engine.begin() as db: reqs=rows(db.execute(text("SELECT * FROM requests ORDER BY id DESC")))
    return render_template("requests.html",rows=reqs)
@app.route("/request/new",methods=["GET","POST"])
@login_required
@role("requisitante","admin")
def new_request():
    clinics,exams,groups,profiles,samples,users=refs(True)
    if request.method=="POST":
        clinic=request.form.get("clinic_other","").strip()
        if request.form.get("clinic")!="outro":
            with engine.begin() as db:
                c=one(db.execute(text("SELECT name FROM clinics WHERE id=:id"),dict(id=int(request.form.get("clinic")))))
                clinic=c["name"] if c else clinic
        ex=request.form.getlist("exams"); sm=request.form.getlist("samples")
        if not clinic or not ex or not sm:
            flash("Preencha clínica, amostras e exames.","error"); return redirect(url_for("new_request"))
        num="LV-"+datetime.now().strftime("%Y%m%d-%H%M%S")
        vals=dict(number=num,clinic_name=clinic,veterinarian=request.form.get("veterinarian"),crmv=request.form.get("crmv"),tutor=request.form.get("tutor"),tutor_phone=request.form.get("tutor_phone"),patient=request.form.get("patient"),species=request.form.get("species"),breed=request.form.get("breed"),sex=request.form.get("sex"),age=request.form.get("age"),weight=request.form.get("weight"),samples_json=json.dumps(sm,ensure_ascii=False),collection_datetime=request.form.get("collection_datetime"),priority=request.form.get("priority"),exams_json=json.dumps(ex,ensure_ascii=False),history_clinical=request.form.get("history_clinical"),suspicion=request.form.get("suspicion"),medications=request.form.get("medications"),observations=request.form.get("observations"),status="Requisição enviada",due_at=(datetime.now()+timedelta(hours=24)).isoformat(timespec="seconds"),created_by=cur_user()["id"],created_at=datetime.now().isoformat(timespec="seconds"))
        with engine.begin() as db:
            db.execute(text("""INSERT INTO requests (number,clinic_name,veterinarian,crmv,tutor,tutor_phone,patient,species,breed,sex,age,weight,samples_json,collection_datetime,priority,exams_json,history_clinical,suspicion,medications,observations,status,due_at,created_by,created_at) VALUES (:number,:clinic_name,:veterinarian,:crmv,:tutor,:tutor_phone,:patient,:species,:breed,:sex,:age,:weight,:samples_json,:collection_datetime,:priority,:exams_json,:history_clinical,:suspicion,:medications,:observations,:status,:due_at,:created_by,:created_at)"""),vals)
        audit(f"Criou requisição {num}"); flash("Requisição enviada.","success"); return redirect(url_for("requests_list"))
    grouped=[{"group":g,"exams":[e for e in exams if e["group_id"]==g["id"]]} for g in groups]
    grouped=[b for b in grouped if b["exams"]]
    return render_template("new_request.html",clinics=clinics,profiles=profiles,grouped_exams=grouped,samples=samples)
@app.route("/request/<int:req_id>")
@login_required
def request_detail(req_id):
    with engine.begin() as db: r=one(db.execute(text("SELECT * FROM requests WHERE id=:id"),dict(id=req_id)))
    return render_template("request_detail.html",row=r)
@app.route("/request/<int:req_id>/status",methods=["POST"])
@login_required
@role("laboratorio","admin")
def update_status(req_id):
    with engine.begin() as db: db.execute(text("UPDATE requests SET status=:s, lab_internal_obs=:o WHERE id=:id"),dict(s=request.form.get("status"),o=request.form.get("lab_internal_obs"),id=req_id))
    flash("Status atualizado.","success"); return redirect(url_for("request_detail",req_id=req_id))
@app.route("/catalog",methods=["GET","POST"])
@login_required
@role("admin")
def catalog():
    if request.method=="POST":
        a=request.form.get("action")
        with engine.begin() as db:
            if a=="group": db.execute(text("INSERT INTO exam_groups (name,display_order) VALUES (:n,:o)"),dict(n=request.form.get("group_name"),o=request.form.get("group_order") or 999))
            elif a=="exam": db.execute(text("INSERT INTO exams (name,material,deadline_hours,group_id,active,display_order) VALUES (:n,:m,:d,:g,1,999)"),dict(n=request.form.get("exam_name"),m=request.form.get("material"),d=request.form.get("deadline_hours") or 24,g=request.form.get("group_id") or None))
            elif a=="profile": db.execute(text("INSERT INTO exam_profiles (name,exams_json) VALUES (:n,:e)"),dict(n=request.form.get("profile_name"),e=json.dumps(request.form.getlist("profile_exams"),ensure_ascii=False)))
            elif a=="sample": db.execute(text("INSERT INTO sample_types (name,active,display_order) VALUES (:n,1,:o)"),dict(n=request.form.get("sample_name"),o=request.form.get("sample_order") or 999))
        flash("Cadastro salvo.","success"); return redirect(url_for("catalog"))
    clinics,exams,groups,profiles,samples,users=refs(False)
    return render_template("catalog.html",exams=exams,groups=groups,profiles=profiles,sample_types=samples)
@app.route("/catalog/exam/<int:id>/update",methods=["POST"])
@login_required
@role("admin")
def update_exam(id):
    with engine.begin() as db: db.execute(text("UPDATE exams SET name=:n,material=:m,deadline_hours=:d,group_id=:g,active=:a WHERE id=:id"),dict(n=request.form.get("name"),m=request.form.get("material"),d=request.form.get("deadline_hours") or 24,g=request.form.get("group_id") or None,a=1 if request.form.get("active")=="1" else 0,id=id))
    flash("Exame atualizado.","success"); return redirect(url_for("catalog"))
@app.route("/catalog/exam/<int:id>/delete",methods=["POST"])
@login_required
@role("admin")
def delete_exam(id):
    with engine.begin() as db: db.execute(text("DELETE FROM exams WHERE id=:id"),dict(id=id))
    flash("Exame excluído.","success"); return redirect(url_for("catalog"))
@app.route("/catalog/profile/<int:id>/update",methods=["POST"])
@login_required
@role("admin")
def update_profile(id):
    with engine.begin() as db: db.execute(text("UPDATE exam_profiles SET name=:n,exams_json=:e WHERE id=:id"),dict(n=request.form.get("name"),e=json.dumps(request.form.getlist("profile_exams"),ensure_ascii=False),id=id))
    flash("Perfil atualizado.","success"); return redirect(url_for("catalog"))
@app.route("/catalog/profile/<int:id>/delete",methods=["POST"])
@login_required
@role("admin")
def delete_profile(id):
    with engine.begin() as db: db.execute(text("DELETE FROM exam_profiles WHERE id=:id"),dict(id=id))
    flash("Perfil excluído.","success"); return redirect(url_for("catalog"))
@app.route("/catalog/sample/<int:id>/update",methods=["POST"])
@login_required
@role("admin")
def update_sample(id):
    with engine.begin() as db: db.execute(text("UPDATE sample_types SET name=:n,active=:a,display_order=:o WHERE id=:id"),dict(n=request.form.get("name"),a=1 if request.form.get("active")=="1" else 0,o=request.form.get("display_order") or 999,id=id))
    flash("Amostra atualizada.","success"); return redirect(url_for("catalog"))
@app.route("/catalog/sample/<int:id>/delete",methods=["POST"])
@login_required
@role("admin")
def delete_sample(id):
    with engine.begin() as db: db.execute(text("DELETE FROM sample_types WHERE id=:id"),dict(id=id))
    flash("Amostra excluída.","success"); return redirect(url_for("catalog"))
@app.route("/catalog/group-order",methods=["POST"])
@login_required
@role("admin")
def group_order():
    with engine.begin() as db:
        for k,v in request.form.items():
            if k.startswith("order_"): db.execute(text("UPDATE exam_groups SET display_order=:o WHERE id=:id"),dict(o=v or 999,id=int(k.replace("order_",""))))
    flash("Ordem atualizada.","success"); return redirect(url_for("catalog"))
@app.route("/admin",methods=["GET","POST"])
@login_required
@role("admin")
def admin():
    if request.method=="POST":
        with engine.begin() as db: db.execute(text("INSERT INTO users (name,email,password_hash,profile,active,created_at) VALUES (:n,:e,:h,:p,1,:c)"),dict(n=request.form.get("name"),e=request.form.get("email").strip().lower(),h=generate_password_hash(request.form.get("password")),p=request.form.get("profile"),c=datetime.now().isoformat(timespec="seconds")))
        flash("Usuário criado.","success"); return redirect(url_for("admin"))
    clinics,exams,groups,profiles,samples,users=refs(False)
    return render_template("admin.html",users=users)
@app.route("/reports")
@login_required
@role("laboratorio","admin")
def reports():
    with engine.begin() as db: by_status=rows(db.execute(text("SELECT status, COUNT(*) total FROM requests GROUP BY status")))
    return render_template("reports.html",by_status=by_status)
@app.route("/audit")
@login_required
@role("admin")
def audit_page():
    with engine.begin() as db: ar=rows(db.execute(text("SELECT * FROM audit ORDER BY id DESC LIMIT 200")))
    return render_template("audit.html",rows=ar)

with app.app_context(): init_db()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
