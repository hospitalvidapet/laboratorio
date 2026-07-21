import json
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
@login_manager.user_loader
def load_user(user_id): return db.session.get(User,int(user_id))
class User(UserMixin,db.Model):
 __tablename__='users'; id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),nullable=False); email=db.Column(db.String(160),unique=True,nullable=False); password_hash=db.Column(db.String(255),nullable=False); role=db.Column(db.String(30),nullable=False,default='requisitante'); active=db.Column(db.Boolean,nullable=False,default=True)
 def set_password(self,p): self.password_hash=generate_password_hash(p)
 def check_password(self,p): return check_password_hash(self.password_hash,p)
 @property
 def is_active(self): return self.active
class Clinic(db.Model):
 __tablename__='clinics'; id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(180),nullable=False); cnpj=db.Column(db.String(30)); phone=db.Column(db.String(40)); email=db.Column(db.String(160)); active=db.Column(db.Boolean,default=True)
class Species(db.Model):
 __tablename__='species'; id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(80),unique=True,nullable=False); active=db.Column(db.Boolean,default=True); display_order=db.Column(db.Integer,default=999)
class ExamGroup(db.Model):
 __tablename__='exam_groups'; id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),unique=True,nullable=False); display_order=db.Column(db.Integer,default=999)
class Exam(db.Model):
 __tablename__='exams'; id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(180),nullable=False); material=db.Column(db.String(180)); deadline_hours=db.Column(db.Integer,default=24); active=db.Column(db.Boolean,default=True); group_id=db.Column(db.Integer,db.ForeignKey('exam_groups.id')); group=db.relationship('ExamGroup',backref='exams')
class ExamProfile(db.Model):
 __tablename__='exam_profiles'; id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(180),unique=True,nullable=False); exams_json=db.Column(db.Text,nullable=False,default='[]'); active=db.Column(db.Boolean,default=True)
 @property
 def exams(self):
  try:return json.loads(self.exams_json)
  except:return []
class SampleType(db.Model):
 __tablename__='sample_types'; id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),unique=True,nullable=False); display_order=db.Column(db.Integer,default=999); active=db.Column(db.Boolean,default=True)
class Patient(db.Model):
 __tablename__='patients'; id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),nullable=False); tutor_name=db.Column(db.String(160),nullable=False); tutor_phone=db.Column(db.String(40)); species=db.Column(db.String(50)); breed=db.Column(db.String(100)); sex=db.Column(db.String(20)); age=db.Column(db.String(50)); weight=db.Column(db.String(30))
class LabRequest(db.Model):
 __tablename__='lab_requests'; id=db.Column(db.Integer,primary_key=True); number=db.Column(db.String(60),unique=True,nullable=False); clinic_id=db.Column(db.Integer,db.ForeignKey('clinics.id'),nullable=False); patient_id=db.Column(db.Integer,db.ForeignKey('patients.id'),nullable=False); veterinarian=db.Column(db.String(160),nullable=False); crmv=db.Column(db.String(50)); priority=db.Column(db.String(30),default='Rotina'); status=db.Column(db.String(50),default='Requisição enviada'); profiles_json=db.Column(db.Text,nullable=False,default='[]'); exams_json=db.Column(db.Text,nullable=False,default='[]'); samples_json=db.Column(db.Text,nullable=False,default='[]'); clinical_history=db.Column(db.Text); diagnostic_suspicion=db.Column(db.Text); medications=db.Column(db.Text); observations=db.Column(db.Text); internal_notes=db.Column(db.Text); created_at=db.Column(db.DateTime,default=datetime.utcnow)
 clinic=db.relationship('Clinic'); patient=db.relationship('Patient'); results=db.relationship('LabResult',backref='request',cascade='all, delete-orphan'); reports=db.relationship('LabReport',backref='request',cascade='all, delete-orphan')
 @property
 def profile_details(self):
  try:data=json.loads(self.profiles_json or '[]')
  except:return []
  out=[]
  for item in data:
   if isinstance(item,dict):out.append({'name':item.get('name','Perfil'),'exams':item.get('exams',[]) or []})
   else:out.append({'name':str(item),'exams':[]})
  return out
 @property
 def profiles(self):return [item['name'] for item in self.profile_details]
 @property
 def exams(self):
  try:return json.loads(self.exams_json or '[]')
  except:return []
 @property
 def profile_exam_names(self):
  out=[]
  for p in self.profile_details:
   for n in p.get('exams',[]):
    if n not in out:out.append(n)
  return out
 @property
 def all_exams(self):
  out=list(self.profile_exam_names)
  for n in self.exams:
   if n not in out:out.append(n)
  return out
 @property
 def samples(self):
  try:return json.loads(self.samples_json or '[]')
  except:return []
class LabResult(db.Model):
 __tablename__='lab_results'; id=db.Column(db.Integer,primary_key=True); request_id=db.Column(db.Integer,db.ForeignKey('lab_requests.id'),nullable=False); exam_name=db.Column(db.String(180),nullable=False); parameter=db.Column(db.String(180),nullable=False); result_value=db.Column(db.String(120)); unit=db.Column(db.String(80)); reference_value=db.Column(db.String(120)); flag=db.Column(db.String(40)); method=db.Column(db.String(180)); observations=db.Column(db.Text)
class LabReport(db.Model):
 __tablename__='lab_reports'; id=db.Column(db.Integer,primary_key=True); request_id=db.Column(db.Integer,db.ForeignKey('lab_requests.id'),nullable=False); filename=db.Column(db.String(255),nullable=False); created_at=db.Column(db.DateTime,default=datetime.utcnow)

class SyncRun(db.Model):
 __tablename__='sync_runs'; id=db.Column(db.Integer,primary_key=True); trigger=db.Column(db.String(30),nullable=False,default='manual'); status=db.Column(db.String(30),nullable=False,default='running'); started_at=db.Column(db.DateTime,nullable=False,default=datetime.utcnow); finished_at=db.Column(db.DateTime); details_json=db.Column(db.Text); error_message=db.Column(db.Text)
 @property
 def details(self):
  try:return json.loads(self.details_json or '{}')
  except:return {}
