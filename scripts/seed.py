import json
from app import create_app, db
from app.models import User, Clinic, Species, ExamGroup, Exam, ExamProfile, SampleType

app=create_app()
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="admin@vidapet.com.br").first():
        u=User(name="Administrador",email="admin@vidapet.com.br",role="admin",active=True); u.set_password("admin123"); db.session.add(u)
    if not Clinic.query.first():
        db.session.add_all([Clinic(name="VIDAPET JD DAS AMÉRICAS"),Clinic(name="VIDAPET STA CÂNDIDA",phone="(41) 3209-3950")])
    if not ExamGroup.query.first():
        h=ExamGroup(name="Hematologia",display_order=20); b=ExamGroup(name="Bioquímica",display_order=30); db.session.add_all([h,b]); db.session.flush()
        db.session.add_all([Exam(name="Hemograma",material="Sangue total EDTA",group=h),Exam(name="Bioquímico completo",material="Soro",group=b)])
    if not ExamProfile.query.first():
        db.session.add(ExamProfile(name="Perfil pré-operatório",exams_json=json.dumps(["Hemograma","Bioquímico completo"],ensure_ascii=False)))
    if not Species.query.first():
        db.session.add_all([Species(name='Canino',display_order=10),Species(name='Felino',display_order=20)])
    if not SampleType.query.first():
        db.session.add_all([SampleType(name="Sangue total EDTA",display_order=10),SampleType(name="Soro",display_order=20),SampleType(name="Urina",display_order=30)])
    db.session.commit()
    print("Banco inicializado com sucesso.")
