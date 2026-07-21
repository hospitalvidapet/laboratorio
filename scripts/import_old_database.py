import os, json
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.exc import NoSuchTableError
from app import create_app, db
from app.models import User, Clinic, Species, ExamGroup, Exam, ExamProfile, SampleType
url=os.getenv("OLD_DATABASE_URL")
if not url: raise SystemExit("Defina OLD_DATABASE_URL com a conexão do banco antigo.")
if url.startswith("postgres://"): url=url.replace("postgres://","postgresql+psycopg://",1)
elif url.startswith("postgresql://"): url=url.replace("postgresql://","postgresql+psycopg://",1)
eng=create_engine(url); meta=MetaData(); app=create_app()
def rows(name):
 try: tbl=Table(name,meta,autoload_with=eng)
 except NoSuchTableError: print(f"Tabela ausente: {name}"); return []
 with eng.connect() as c: return [dict(r._mapping) for r in c.execute(select(tbl))]
with app.app_context():
 counts={k:0 for k in ['users','clinics','species','exam_groups','exams','exam_profiles','sample_types']}
 for r in rows('users'):
  email=(r.get('email') or '').strip().lower()
  if not email or User.query.filter_by(email=email).first(): continue
  u=User(name=r.get('name') or 'Usuário importado',email=email,role=r.get('role') or r.get('profile') or 'requisitante',active=bool(r.get('active',True)))
  u.password_hash=r.get('password_hash') or '';
  if not u.password_hash: u.set_password('alterar123')
  db.session.add(u); counts['users']+=1
 for r in rows('clinics'):
  n=(r.get('name') or '').strip();
  if not n or Clinic.query.filter_by(name=n).first(): continue
  db.session.add(Clinic(name=n,cnpj=r.get('cnpj'),phone=r.get('phone'),email=r.get('email'),active=bool(r.get('active',True)))); counts['clinics']+=1
 for r in rows('species'):
  n=(r.get('name') or '').strip();
  if not n or Species.query.filter_by(name=n).first(): continue
  db.session.add(Species(name=n,display_order=r.get('display_order') or 999,active=bool(r.get('active',True)))); counts['species']+=1
 gmap={}
 for r in rows('exam_groups'):
  n=(r.get('name') or '').strip();
  if not n: continue
  g=ExamGroup.query.filter_by(name=n).first() or ExamGroup(name=n,display_order=r.get('display_order') or 999)
  if not g.id: db.session.add(g); db.session.flush(); counts['exam_groups']+=1
  gmap[r.get('id')]=g.id
 for r in rows('exams'):
  n=(r.get('name') or '').strip();
  if not n or Exam.query.filter_by(name=n).first(): continue
  db.session.add(Exam(name=n,material=r.get('material'),deadline_hours=r.get('deadline_hours') or 24,active=bool(r.get('active',True)),group_id=gmap.get(r.get('group_id')))); counts['exams']+=1
 for r in rows('exam_profiles'):
  n=(r.get('name') or '').strip();
  if not n or ExamProfile.query.filter_by(name=n).first(): continue
  ej=r.get('exams_json') or '[]';
  try: json.loads(ej)
  except: ej='[]'
  db.session.add(ExamProfile(name=n,exams_json=ej,active=bool(r.get('active',True)))); counts['exam_profiles']+=1
 for r in rows('sample_types'):
  n=(r.get('name') or '').strip();
  if not n or SampleType.query.filter_by(name=n).first(): continue
  db.session.add(SampleType(name=n,display_order=r.get('display_order') or 999,active=bool(r.get('active',True)))); counts['sample_types']+=1
 db.session.commit(); print('Importação concluída:',counts)
