import json
from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_login import login_required,current_user
from app import db
from app.models import User,Clinic,Species,ExamGroup,Exam,ExamProfile,SampleType,LabRequest,LabResult,LabReport,Patient
admin_bp=Blueprint('admin',__name__)
def ok(): return current_user.is_authenticated and current_user.role=='admin'
def deny(): return ('Acesso negado',403)
@admin_bp.route('/')
@login_required
def index():
 if not ok(): return deny()
 return render_template('admin/index.html')
@admin_bp.route('/users',methods=['GET','POST'])
@login_required
def users():
 if not ok(): return deny()
 if request.method=='POST':
  u=User(name=request.form['name'],email=request.form['email'].strip().lower(),role=request.form['role'],active=True); u.set_password(request.form['password']); db.session.add(u); db.session.commit(); flash('Usuário criado.','success'); return redirect(url_for('admin.users'))
 return render_template('admin/users.html',rows=User.query.order_by(User.name).all())
@admin_bp.route('/users/<int:id>/edit',methods=['POST'])
@login_required
def edit_user(id):
 if not ok(): return deny()
 u=User.query.get_or_404(id); u.name=request.form['name']; u.email=request.form['email'].strip().lower(); u.role=request.form['role']; u.active=request.form.get('active')=='1'
 if request.form.get('password'): u.set_password(request.form['password'])
 db.session.commit(); flash('Usuário atualizado.','success'); return redirect(url_for('admin.users'))
@admin_bp.route('/users/<int:id>/delete',methods=['POST'])
@login_required
def delete_user(id):
 if not ok(): return deny()
 u=User.query.get_or_404(id)
 if u.id==current_user.id: flash('Não é possível excluir o próprio usuário.','error')
 else: u.active=False; db.session.commit(); flash('Usuário inativado.','success')
 return redirect(url_for('admin.users'))
@admin_bp.route('/clinics',methods=['GET','POST'])
@login_required
def clinics():
 if not ok(): return deny()
 if request.method=='POST': db.session.add(Clinic(name=request.form['name'],cnpj=request.form.get('cnpj'),phone=request.form.get('phone'),email=request.form.get('email'))); db.session.commit(); flash('Clínica cadastrada.','success'); return redirect(url_for('admin.clinics'))
 return render_template('admin/clinics.html',rows=Clinic.query.order_by(Clinic.name).all())
@admin_bp.route('/clinics/<int:id>/edit',methods=['POST'])
@login_required
def edit_clinic(id):
 if not ok(): return deny()
 c=Clinic.query.get_or_404(id); c.name=request.form['name']; c.cnpj=request.form.get('cnpj'); c.phone=request.form.get('phone'); c.email=request.form.get('email'); c.active=request.form.get('active')=='1'; db.session.commit(); flash('Clínica atualizada.','success'); return redirect(url_for('admin.clinics'))
@admin_bp.route('/clinics/<int:id>/delete',methods=['POST'])
@login_required
def delete_clinic(id):
 if not ok(): return deny()
 c=Clinic.query.get_or_404(id)
 if LabRequest.query.filter_by(clinic_id=id).first(): c.active=False; flash('Clínica inativada para preservar histórico.','success')
 else: db.session.delete(c); flash('Clínica excluída.','success')
 db.session.commit(); return redirect(url_for('admin.clinics'))
@admin_bp.route('/catalog',methods=['GET','POST'])
@login_required
def catalog():
 if not ok(): return deny()
 if request.method=='POST':
  a=request.form['action']
  if a=='species': db.session.add(Species(name=request.form['name'],display_order=int(request.form.get('display_order') or 999)))
  elif a=='group': db.session.add(ExamGroup(name=request.form['name'],display_order=int(request.form.get('display_order') or 999)))
  elif a=='sample': db.session.add(SampleType(name=request.form['name'],display_order=int(request.form.get('display_order') or 999)))
  elif a=='exam': db.session.add(Exam(name=request.form['name'],material=request.form.get('material'),deadline_hours=int(request.form.get('deadline_hours') or 24),group_id=int(request.form['group_id'])))
  elif a=='profile': db.session.add(ExamProfile(name=request.form['name'],exams_json=json.dumps(request.form.getlist('exams'),ensure_ascii=False)))
  db.session.commit(); flash('Cadastro salvo.','success'); return redirect(url_for('admin.catalog'))
 return render_template('admin/catalog.html',species=Species.query.order_by(Species.display_order).all(),groups=ExamGroup.query.order_by(ExamGroup.display_order).all(),samples=SampleType.query.order_by(SampleType.display_order).all(),exams=Exam.query.order_by(Exam.name).all(),profiles=ExamProfile.query.order_by(ExamProfile.name).all())
# generic edit/delete routes
@admin_bp.route('/species/<int:id>/edit',methods=['POST'])
@login_required
def edit_species(id):
 s=Species.query.get_or_404(id); s.name=request.form['name']; s.display_order=int(request.form.get('display_order') or 999); s.active=request.form.get('active')=='1'; db.session.commit(); flash('Espécie atualizada.','success'); return redirect(url_for('admin.catalog'))
@admin_bp.route('/species/<int:id>/delete',methods=['POST'])
@login_required
def delete_species(id):
 s=Species.query.get_or_404(id); s.active=False; db.session.commit(); flash('Espécie inativada.','success'); return redirect(url_for('admin.catalog'))
@admin_bp.route('/samples/<int:id>/edit',methods=['POST'])
@login_required
def edit_sample(id):
 s=SampleType.query.get_or_404(id); s.name=request.form['name']; s.display_order=int(request.form.get('display_order') or 999); s.active=request.form.get('active')=='1'; db.session.commit(); flash('Amostra atualizada.','success'); return redirect(url_for('admin.catalog'))
@admin_bp.route('/samples/<int:id>/delete',methods=['POST'])
@login_required
def delete_sample(id):
 s=SampleType.query.get_or_404(id); s.active=False; db.session.commit(); flash('Amostra inativada.','success'); return redirect(url_for('admin.catalog'))
@admin_bp.route('/groups/<int:id>/edit',methods=['POST'])
@login_required
def edit_group(id):
 g=ExamGroup.query.get_or_404(id); g.name=request.form['name']; g.display_order=int(request.form.get('display_order') or 999); db.session.commit(); flash('Grupo atualizado.','success'); return redirect(url_for('admin.catalog'))
@admin_bp.route('/groups/<int:id>/delete',methods=['POST'])
@login_required
def delete_group(id):
 g=ExamGroup.query.get_or_404(id)
 if g.exams: flash('Grupo possui exames vinculados.','error')
 else: db.session.delete(g); db.session.commit(); flash('Grupo excluído.','success')
 return redirect(url_for('admin.catalog'))
@admin_bp.route('/exams/<int:id>/edit',methods=['POST'])
@login_required
def edit_exam(id):
 e=Exam.query.get_or_404(id); e.name=request.form['name']; e.material=request.form.get('material'); e.deadline_hours=int(request.form.get('deadline_hours') or 24); e.group_id=int(request.form['group_id']); e.active=request.form.get('active')=='1'; db.session.commit(); flash('Exame atualizado.','success'); return redirect(url_for('admin.catalog'))
@admin_bp.route('/exams/<int:id>/delete',methods=['POST'])
@login_required
def delete_exam(id):
 e=Exam.query.get_or_404(id); e.active=False; db.session.commit(); flash('Exame inativado para preservar histórico.','success'); return redirect(url_for('admin.catalog'))
@admin_bp.route('/profiles/<int:id>/edit',methods=['POST'])
@login_required
def edit_profile(id):
 p=ExamProfile.query.get_or_404(id); p.name=request.form['name']; p.exams_json=json.dumps(request.form.getlist('exams'),ensure_ascii=False); p.active=request.form.get('active')=='1'; db.session.commit(); flash('Perfil atualizado.','success'); return redirect(url_for('admin.catalog'))
@admin_bp.route('/profiles/<int:id>/delete',methods=['POST'])
@login_required
def delete_profile(id):
 p=ExamProfile.query.get_or_404(id); p.active=False; db.session.commit(); flash('Perfil inativado para preservar histórico.','success'); return redirect(url_for('admin.catalog'))

@admin_bp.route("/requests")
@login_required
def requests_admin():
    if not ok(): return deny()
    rows=LabRequest.query.order_by(LabRequest.created_at.desc(),LabRequest.id.desc()).all()
    return render_template("admin/requests.html",rows=rows)

@admin_bp.route("/requests/<int:id>/edit",methods=["GET","POST"])
@login_required
def edit_request(id):
    if not ok(): return deny()
    row=LabRequest.query.get_or_404(id)
    if request.method=="POST":
        row.veterinarian=request.form["veterinarian"]; row.crmv=request.form.get("crmv")
        row.priority=request.form.get("priority","Rotina"); row.status=request.form.get("status",row.status)
        row.clinical_history=request.form.get("clinical_history"); row.diagnostic_suspicion=request.form.get("diagnostic_suspicion")
        row.medications=request.form.get("medications"); row.observations=request.form.get("observations"); row.internal_notes=request.form.get("internal_notes")
        row.patient.name=request.form["patient_name"]; row.patient.tutor_name=request.form["tutor_name"]
        row.patient.tutor_phone=request.form.get("tutor_phone"); row.patient.species=request.form.get("species")
        row.patient.breed=request.form.get("breed"); row.patient.sex=request.form.get("sex")
        row.patient.age=request.form.get("age"); row.patient.weight=request.form.get("weight")
        db.session.commit(); flash("Requisição atualizada.","success")
        return redirect(url_for("admin.requests_admin"))
    return render_template("admin/request_edit.html",row=row)

@admin_bp.route("/requests/<int:id>/delete",methods=["POST"])
@login_required
def delete_request(id):
    if not ok(): return deny()

    row = LabRequest.query.get_or_404(id)
    patient_id = row.patient_id

    # Delete dependents explicitly. This avoids loading an old result schema
    # through the ORM and also makes the operation predictable on PostgreSQL.
    report_filenames = [name for (name,) in db.session.query(LabReport.filename).filter_by(request_id=id).all()]
    LabResult.query.filter_by(request_id=id).delete(synchronize_session=False)
    LabReport.query.filter_by(request_id=id).delete(synchronize_session=False)
    LabRequest.query.filter_by(id=id).delete(synchronize_session=False)

    # A patient created only for this requisition can be removed as well.
    if not LabRequest.query.filter_by(patient_id=patient_id).first():
        Patient.query.filter_by(id=patient_id).delete(synchronize_session=False)

    db.session.commit()

    # PDF cleanup is best-effort and never blocks database deletion.
    try:
        from flask import current_app
        for filename in report_filenames:
            path = current_app.config["UPLOAD_FOLDER"] / filename
            if path.exists():
                path.unlink()
    except Exception:
        current_app.logger.exception("Não foi possível remover um arquivo de laudo")

    flash("Requisição excluída.","success")
    return redirect(url_for("admin.requests_admin"))

@admin_bp.route('/sync')
@login_required
def sync_catalog_page():
 if not ok(): return deny()
 from app.catalog_sync import is_configured
 from app.models import SyncRun
 rows=SyncRun.query.order_by(SyncRun.started_at.desc()).limit(20).all()
 return render_template('admin/sync.html',rows=rows,configured=is_configured())

@admin_bp.route('/sync/test',methods=['POST'])
@login_required
def sync_catalog_test():
 if not ok(): return deny()
 from app.catalog_sync import test_connection
 result=test_connection()
 flash(result['message'],'success' if result['ok'] else 'error')
 return redirect(url_for('admin.sync_catalog_page'))

@admin_bp.route('/sync/run',methods=['POST'])
@login_required
def sync_catalog_run():
 if not ok(): return deny()
 from app.catalog_sync import synchronize_catalog
 result=synchronize_catalog(trigger='manual')
 if result.get('ok'):
  c=result.get('counts',{})
  created=sum(v for k,v in c.items() if k.endswith('_created'))
  updated=sum(v for k,v in c.items() if k.endswith('_updated'))
  flash(f"Sincronização concluída: {created} criados e {updated} atualizados.",'success')
 else:
  flash(result.get('message','Falha na sincronização.'),'error')
 return redirect(url_for('admin.sync_catalog_page'))
