from fastapi import HTTPException
from src.models.entities import WarningBatch
def ensure_batch(s,i):
 r=s.get(WarningBatch,i)
 if not r:raise HTTPException(404,'预警版本不存在')
 return r
