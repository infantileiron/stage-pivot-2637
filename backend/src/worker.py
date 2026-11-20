import os,time,json,logging
from pathlib import Path
import redis
from src.config.database import Session
from src.models.entities import Pivot,WarningBatch
from src.services.analysis import pivot
from src.services.sales import compute
q=redis.Redis.from_url(os.environ['REDIS_URL'])
with Session() as s:
 for r in s.query(Pivot).filter(Pivot.state.in_(['queued','running'])).all():r.state='queued';q.rpush('stage:pivots',r.id)
 for r in s.query(WarningBatch).filter(WarningBatch.state.in_(['queued','running'])).all():r.state='queued';q.rpush('stage:warnings',r.id)
 s.commit()
def _artifact(name,payload):
 try:Path('/artifacts/'+name).write_text(json.dumps(payload,ensure_ascii=False,default=str))
 except OSError:logging.warning('artifact dir unwritable: %s',name)
def run_pivot(item):
 with Session() as s:
  r=s.get(Pivot,int(item[1]))
  if not r or r.state!='queued':return
  snapshot=r.result['snapshot'];r.state='running';s.commit()
  try:
   r.result={**pivot(snapshot,r.row_dim,r.col_dim),'snapshot':snapshot};r.state='done';_artifact('pivot-'+str(r.id)+'.json',r.result)
  except Exception as e:r.state='failed';r.error=str(e)
  s.commit()
def run_warning(item):
 with Session() as s:
  r=s.get(WarningBatch,int(item[1]))
  if not r or r.state not in ('queued','running'):return
  # 已发布版本永不重算；中断恢复时 running 沿用冻结快照按原截止点继续
  if r.state=='done':return
  r.state='running';s.commit()
  try:
   r.result=compute(s,r);r.state='done';r.error='';_artifact('warning-'+str(r.id)+'.json',r.result)
  except Exception as e:r.state='failed';r.error=str(e)
  s.commit()
while True:
 Path('/tmp/heartbeat').touch()
 try:
  item=q.blpop(['stage:warnings','stage:pivots'],timeout=3)
  if not item:continue
  run_warning(item) if item[0]==b'stage:warnings' else run_pivot(item)
 except Exception:logging.exception('worker');time.sleep(2)
