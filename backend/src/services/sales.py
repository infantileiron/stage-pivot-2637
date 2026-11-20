from datetime import datetime,timezone,date
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from src.models.entities import ShowSession,SalesReport,WarningBatch
from src.services.business import dump
from src.services.warnings import build_warnings
import os,redis
QUEUE='stage:warnings'
def now():return datetime.now(timezone.utc).replace(tzinfo=None)
def _jsonable(row):
 out={}
 for k,v in dump(row).items():
  if isinstance(v,(date,datetime)):out[k]=v.isoformat()
  else:out[k]=v
 return out
def save_session(s,data):
 r=s.query(ShowSession).filter_by(code=data.code).first()
 if r:raise HTTPException(409,'场次编号已存在，一场次仅一条演出档案')
 r=ShowSession(code=data.code,play=data.play,venue=data.venue,show_day=data.show_day,capacity=data.capacity)
 s.add(r)
 try:s.commit()
 except IntegrityError:s.rollback();raise HTTPException(409,'场次编号重复')
 return dump(r)
def save_report(s,data):
 sess=s.query(ShowSession).filter_by(code=data.code).first()
 if not sess:raise HTTPException(404,'演出场次不存在，请先建档')
 received=data.received_at or now()
 if received.tzinfo is not None:received=received.astimezone(timezone.utc).replace(tzinfo=None)
 if data.sold_total+data.available_seats>sess.capacity:
  raise HTTPException(422,'累计售票数与可售座位之和不得超过场次容量')
 r=s.query(SalesReport).filter_by(session_id=sess.id,report_day=data.report_day).first()
 if r:
  r.sold_total=data.sold_total;r.available_seats=data.available_seats;r.received_at=received;r.updated_at=now()
 else:
  r=SalesReport(session_id=sess.id,report_day=data.report_day,sold_total=data.sold_total,available_seats=data.available_seats,received_at=received,updated_at=now());s.add(r)
 try:s.commit()
 except IntegrityError:s.rollback();raise HTTPException(409,'同一场次同一上报日仅一条记录，请用补报更正')
 return dump(r)
def _naive(v):
 return v.astimezone(timezone.utc).replace(tzinfo=None) if v.tzinfo else v
def _snapshot(s,b):
 cutoff=_naive(b.cutoff_at)
 sessions=[_jsonable(x) for x in s.query(ShowSession).order_by(ShowSession.id).all()]
 reports=[_jsonable(x) for x in s.query(SalesReport).filter(SalesReport.received_at<=cutoff).order_by(SalesReport.id).all()]
 return sessions,reports
def create_batch(s,data):
 b=WarningBatch(name=data.name,cutoff_at=_naive(data.cutoff_at),result={})
 s.add(b);s.commit()
 sessions,reports=_snapshot(s,b)
 b.result={'snapshot':{'sessions':sessions,'reports':reports}}
 try:
  redis.Redis.from_url(os.environ['REDIS_URL']).rpush(QUEUE,b.id)
 except redis.RedisError:
  b.state='failed';b.error='队列暂不可用，请恢复后在预警页补跑';s.commit();raise HTTPException(503,b.error)
 s.commit();return dump(b)
def rerun_batch(s,b):
 if b.state=='done':raise HTTPException(409,'已发布版本不可重跑；迟到上报与更正请新建版本')
 sessions,reports=_snapshot(s,b)
 b.result={'snapshot':{'sessions':sessions,'reports':reports}};b.state='queued';b.error=''
 try:redis.Redis.from_url(os.environ['REDIS_URL']).rpush(QUEUE,b.id)
 except redis.RedisError:b.state='failed';b.error='队列暂不可用，请稍后补跑';s.commit();raise HTTPException(503,b.error)
 s.commit();return dump(b)
def compute(s,b):
 snap=b.result['snapshot']
 out=build_warnings(snap['sessions'],snap['reports'],b.cutoff_at)
 return {**out,'snapshot':snap}
