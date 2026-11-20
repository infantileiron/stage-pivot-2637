import random
from datetime import date,timedelta,datetime,timezone
from src.config.database import Base,engine,Session
from src.models.entities import User,Settlement,ShowSession,SalesReport
from src.utils.security import hash_password
from src.constants.enums import VENUES,CHANNELS
PLAYS=['渡口来信','星河漫游','一间书房','冬日序曲']
def seed():
 Base.metadata.create_all(engine);rng=random.Random(3112)
 with Session() as s:
  for role in ('admin','analyst','viewer'):
   email=role+'@demo.local'
   if not s.query(User).filter_by(email=email).first():s.add(User(email=email,role=role,password=hash_password('Demo123!')))
  for i in range(180):
   code=f'YM-{i+1:03}';seats=[800,240,120][i%3];checked=rng.randint(seats//2,seats);gross=checked*rng.choice([8000,12000,18000]);refund=rng.randint(0,checked//10)*8000;fee=int((gross-refund)*[0,.07,.03][i%3])
   if not s.query(Settlement).filter_by(code=code).first():s.add(Settlement(code=code,day=(date(2026,9,1)+timedelta(days=i//3)).isoformat(),venue=VENUES[i%3],play=PLAYS[i%4],channel=CHANNELS[(i//3)%3],gross_cents=gross,refund_cents=refund,fee_cents=fee,seats=seats,checked=checked))
  _seed_sales(s)
  s.commit();print({'users':s.query(User).count(),'settlements':s.query(Settlement).count(),'sessions':s.query(ShowSession).count(),'reports':s.query(SalesReport).count()})
def _seed_sales(s):
 rng=random.Random(8701);today=date(2026,11,20)
 if s.query(ShowSession).count():return
 def add_session(idx,show_day):
  code=f'XS-{idx+1:03}';play=PLAYS[idx%4];venue=VENUES[idx%3];capacity=[800,240,120][idx%3]
  sess=ShowSession(code=code,play=play,venue=venue,show_day=show_day,capacity=capacity);s.add(sess);s.flush()
  pace=rng.uniform(.05,.11);sold=0
  for d in range(7,0,-1):
   report_day=show_day-timedelta(days=d)
   if report_day>today:continue
   rate=max(0.0,min(.98,pace*(7-d)+rng.uniform(-.02,.03)))
   sold=int(capacity*rate)
   # 演示漏报：第4个历史场次缺距开演3天的数据；演示售罄：第7个场次开演前一天售罄
   if idx==3 and d==3:continue
   # 演示迟到：XS-061 的11月18日数据不在常规循环生成，改由下方迟到逻辑补入
   if code=='XS-061' and report_day==today-timedelta(days=2):continue
   available=0 if (idx==6 and d==1) else capacity-sold
   if available<0:available=0
   received=datetime.combine(report_day,datetime.min.time()).replace(hour=9,tzinfo=timezone.utc).replace(tzinfo=None)
   s.add(SalesReport(session_id=sess.id,report_day=report_day,sold_total=sold,available_seats=available,received_at=received,updated_at=received))
 for i in range(60):add_session(i,today-timedelta(days=60-i))
 for i in range(12):add_session(60+i,today+timedelta(days=1+i))
 # 演示迟到上报：11月18日的数据11月20日才到，截止11月19日的版本看不到它
 late=s.query(ShowSession).filter_by(code='XS-061').first()
 if late:
  report_day=today-timedelta(days=2);received=datetime.combine(today,datetime.min.time()).replace(hour=8,tzinfo=timezone.utc).replace(tzinfo=None)
  if not s.query(SalesReport).filter_by(session_id=late.id,report_day=report_day).first():
   s.add(SalesReport(session_id=late.id,report_day=report_day,sold_total=int(late.capacity*.31),available_seats=int(late.capacity*.69),received_at=received,updated_at=received))
if __name__=='__main__':seed()
