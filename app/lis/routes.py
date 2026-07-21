import json
from datetime import datetime
from flask import Blueprint,render_template,request,redirect,url_for,flash,current_app,send_from_directory
from flask_login import login_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from app import db
from app.models import Clinic,Species,Patient,ExamGroup,Exam,ExamProfile,SampleType,LabRequest,LabResult,LabReport
lis_bp=Blueprint('lis',__name__); STATUSES=['Requisição enviada','Aguardando amostra','Amostra recebida','Em análise','Resultado liberado','Exame cancelado']
@lis_bp.route('/requests')
@login_required
def requests_list():
 q=request.args.get('q','').strip()
 query=LabRequest.query.join(Patient)
 if q:
  like=f'%{q}%'
  query=query.filter(db.or_(Patient.name.ilike(like),Patient.tutor_name.ilike(like),Patient.species.ilike(like)))
 rows=query.order_by(LabRequest.id.desc()).all()
 return render_template('lis/requests.html',rows=rows,query_text=q)
@lis_bp.route('/request/new',methods=['GET','POST'])
@login_required
def new_request():
 clinics=Clinic.query.filter_by(active=True).order_by(Clinic.name).all(); species=Species.query.filter_by(active=True).order_by(Species.display_order).all(); groups=ExamGroup.query.order_by(ExamGroup.display_order).all(); exams=Exam.query.filter_by(active=True).order_by(Exam.name).all(); profiles=ExamProfile.query.filter_by(active=True).order_by(ExamProfile.name).all(); samples=SampleType.query.filter_by(active=True).order_by(SampleType.display_order).all()
 if request.method=='POST':
  y=int(request.form.get('age_years') or 0); m=int(request.form.get('age_months') or 0); parts=[]
  if y: parts.append(f'{y} ano' if y==1 else f'{y} anos')
  if m: parts.append(f'{m} mês' if m==1 else f'{m} meses')
  age=', '.join(parts) or 'Não informado'; selected_profile_names=request.form.getlist('profiles'); selected_individual_exams=request.form.getlist('exams')
  profile_objects=ExamProfile.query.filter(ExamProfile.name.in_(selected_profile_names)).all() if selected_profile_names else []
  profile_details=[{'name':p.name,'exams':list(p.exams)} for p in profile_objects]
  profile_exam_names={n for p in profile_details for n in p.get('exams',[])}
  selected_individual_exams=[n for n in selected_individual_exams if n not in profile_exam_names]
  patient=Patient(name=request.form['patient_name'],tutor_name=request.form['tutor_name'],tutor_phone=request.form.get('tutor_phone'),species=request.form.get('species'),breed=request.form.get('breed'),sex=request.form.get('sex'),age=age,weight=request.form.get('weight')); db.session.add(patient); db.session.flush()
  req=LabRequest(number=str(max([int(r.number) for r in LabRequest.query.with_entities(LabRequest.number).all() if str(r.number).isdigit()] or [-1])+1).zfill(6),clinic_id=int(request.form['clinic_id']),patient_id=patient.id,veterinarian=request.form['veterinarian'],crmv=request.form.get('crmv'),priority=request.form.get('priority','Rotina'),profiles_json=json.dumps(profile_details,ensure_ascii=False),exams_json=json.dumps(selected_individual_exams,ensure_ascii=False),samples_json=json.dumps(request.form.getlist('samples'),ensure_ascii=False),clinical_history=request.form.get('clinical_history'),diagnostic_suspicion=request.form.get('diagnostic_suspicion'),medications=request.form.get('medications'),observations=request.form.get('observations')); db.session.add(req); db.session.commit(); flash('Requisição criada.','success'); return redirect(url_for('lis.request_detail',request_id=req.id))
 grouped=[(g,[e for e in exams if e.group_id==g.id]) for g in groups]
 return render_template('lis/new_request.html',clinics=clinics,species=species,profiles=profiles,samples=samples,grouped=grouped)
@lis_bp.route('/request/<int:request_id>')
@login_required
def request_detail(request_id): return render_template('lis/request_detail.html',row=LabRequest.query.get_or_404(request_id),statuses=STATUSES)
@lis_bp.route('/request/<int:request_id>/status',methods=['POST'])
@login_required
def update_status(request_id):
 row=LabRequest.query.get_or_404(request_id); row.status=request.form['status']; row.internal_notes=request.form.get('internal_notes'); db.session.commit(); flash('Status atualizado.','success'); return redirect(url_for('lis.request_detail',request_id=row.id))
@lis_bp.route('/request/<int:request_id>/results',methods=['GET','POST'])
@login_required
def results(request_id):
 row=LabRequest.query.get_or_404(request_id)
 if request.method=='POST': db.session.add(LabResult(request_id=row.id,exam_name=request.form['exam_name'],parameter=request.form['parameter'],result_value=request.form.get('result_value'),unit=request.form.get('unit'),reference_value=request.form.get('reference_value'),flag=request.form.get('flag'),method=request.form.get('method'),observations=request.form.get('observations'))); db.session.commit(); flash('Resultado salvo.','success'); return redirect(url_for('lis.results',request_id=row.id))
 return render_template('lis/results.html',row=row)
@lis_bp.route('/request/<int:request_id>/generate-pdf',methods=['POST'])
@login_required
def generate_pdf(request_id):
 row=LabRequest.query.get_or_404(request_id); filename=f'laudo_{row.number}.pdf'; folder=current_app.config['UPLOAD_FOLDER']; folder.mkdir(exist_ok=True); c=canvas.Canvas(str(folder/filename),pagesize=A4); y=800; c.setFont('Helvetica-Bold',18); c.drawString(50,y,'LABORATÓRIO VIDAPET'); y-=35; c.setFont('Helvetica',10)
 for line in [f'Requisição: {row.number}',f'Paciente: {row.patient.name}',f'Tutor: {row.patient.tutor_name}',f'Espécie: {row.patient.species or "-"}',f'Idade: {row.patient.age or "-"}',f'Clínica: {row.clinic.name}',f'Perfis: {", ".join(row.profiles) or "-"}',f'Exames: {", ".join(row.exams) or "-"}',f'Histórico: {row.clinical_history or "-"}',f'Suspeita: {row.diagnostic_suspicion or "-"}',f'Medicações: {row.medications or "-"}']:
  c.drawString(50,y,line[:115]); y-=18
 for r in row.results:
  c.drawString(50,y,f'{r.exam_name} - {r.parameter}: {r.result_value or "-"} {r.unit or ""} | Ref.: {r.reference_value or "-"}'); y-=18
  if y<60: c.showPage(); y=800
 c.save(); db.session.add(LabReport(request_id=row.id,filename=filename)); row.status='Resultado liberado'; db.session.commit(); flash('PDF gerado.','success'); return redirect(url_for('lis.request_detail',request_id=row.id))
@lis_bp.route('/files/<filename>')
@login_required
def files(filename): return send_from_directory(str(current_app.config['UPLOAD_FOLDER']),filename)
