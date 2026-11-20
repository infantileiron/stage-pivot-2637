import hashlib,json
from datetime import datetime,date
def median(xs):
 xs=sorted(xs);n=len(xs)
 if n==0:return None
 m=n//2
 return xs[m] if n%2 else (xs[m-1]+xs[m])/2
def _parse_day(v):
 if isinstance(v,date) and not isinstance(v,datetime):return v
 if isinstance(v,datetime):return v.date()
 return date.fromisoformat(str(v)[:10])
def _parse_dt(v):
 if isinstance(v,datetime):return v
 if isinstance(v,date):return datetime(v.year,v.month,v.day)
 return datetime.fromisoformat(str(v))
def rate_at(reports,target_day):
 r=next((r for r in reports if r['report_day']==target_day),None)
 if not r:return None,'missing'
 if r['available_seats']<=0:return None,'soldout'
 if r['sold_total']<0:return None,'missing'
 return r['sold_total']/(r['sold_total']+r['available_seats']),None
def build_warnings(sessions,reports,cutoff_at):
 """只读入参，按截止时间重算一版预警。sessions/reports 均为截止前到达的冻结快照。"""
 cutoff=_parse_dt(cutoff_at);cutoff_day=cutoff.date()
 sessions=[dict(s,show_day=_parse_day(s['show_day'])) for s in sessions]
 reports=[dict(r,report_day=_parse_day(r['report_day']),received_at=_parse_dt(r['received_at'])) for r in reports]
 reports=[r for r in reports if r['received_at']<=cutoff]
 by_session={}
 for r in reports:by_session.setdefault(r['session_id'],[]).append(r)
 warnings=[];exclusions=[];targets=0
 for sess in sorted(sessions,key=lambda x:(x['show_day'],x['code'])):
  if sess['show_day']<=cutoff_day:
   exclusions.append({'session_id':sess['id'],'code':sess['code'],'play':sess['play'],'venue':sess['venue'],'show_day':sess['show_day'].isoformat(),'reason':'already_performed','detail':'场次已开演或已结束，不参与未演预警'})
   continue
  targets+=1
  days_to=(sess['show_day']-cutoff_day).days
  target_day=cutoff_day
  mine=by_session.get(sess['id'],[])
  my_rate,my_skip=rate_at(mine,target_day)
  if my_skip=='missing':
   exclusions.append({'session_id':sess['id'],'code':sess['code'],'play':sess['play'],'venue':sess['venue'],'show_day':sess['show_day'].isoformat(),'days_to_show':days_to,'reason':'target_missing','detail':f'截止日（距开演{days_to_show(days_to)}）累计售票上报缺失，漏报留空，无法比较'})
   continue
  if my_skip=='soldout':
   exclusions.append({'session_id':sess['id'],'code':sess['code'],'play':sess['play'],'venue':sess['venue'],'show_day':sess['show_day'].isoformat(),'days_to_show':days_to,'reason':'target_soldout','detail':f'距开演{days_to_show(days_to)}时可售座位为0，已售罄，不参与比较'})
   continue
  peers=[h for h in sessions if h['id']!=sess['id'] and h['play']==sess['play'] and h['venue']==sess['venue'] and h['show_day']<cutoff_day]
  samples=[]
  for h in sorted(peers,key=lambda x:x['show_day']):
   hist_day=h['show_day'].toordinal()-days_to
   if hist_day<1:continue
   hist_day=date.fromordinal(hist_day)
   hr,skip=rate_at(by_session.get(h['id'],[]),hist_day)
   if skip:continue
   rep=next(r for r in by_session[h['id']] if r['report_day']==hist_day)
   samples.append({'session_id':h['id'],'code':h['code'],'show_day':h['show_day'].isoformat(),'report_day':hist_day.isoformat(),'days_to_show':days_to,'sold_total':rep['sold_total'],'available_seats':rep['available_seats'],'rate':hr})
  hist_median=median([x['rate'] for x in samples])
  if hist_median is None or len(samples)<2:
   exclusions.append({'session_id':sess['id'],'code':sess['code'],'play':sess['play'],'venue':sess['venue'],'show_day':sess['show_day'].isoformat(),'days_to_show':days_to,'reason':'insufficient_history','detail':f'同演出同场馆已演场次中，距开演{days_to_show(days_to)}有效样本不足2条（缺数或售罄不参与），无法形成历史中位数'})
   continue
  item={'session_id':sess['id'],'code':sess['code'],'play':sess['play'],'venue':sess['venue'],'show_day':sess['show_day'].isoformat(),'days_to_show':days_to,'report_day':target_day.isoformat(),'current_rate':my_rate,'historical_median_rate':hist_median,'gap':my_rate-hist_median,'samples':samples}
  if my_rate<hist_median:warnings.append(item)
  else:exclusions.append({'session_id':sess['id'],'code':sess['code'],'play':sess['play'],'venue':sess['venue'],'show_day':sess['show_day'].isoformat(),'days_to_show':days_to,'reason':'above_median','detail':f'售票率{my_rate:.4f}不低于历史中位数{hist_median:.4f}，无需预警'})
 digest=hashlib.sha256(json.dumps({'cutoff':cutoff.isoformat(),'sessions':sorted(sessions,key=lambda x:x['id']),'reports':sorted(reports,key=lambda x:x['id'])},sort_keys=True,default=str,ensure_ascii=False).encode()).hexdigest()
 return {'cutoff_at':cutoff.isoformat(),'warnings':warnings,'exclusions':exclusions,'target_count':targets,'warning_count':len(warnings),'exclusion_count':len(exclusions),'snapshot_checksum':digest,'method':'仅使用截止时间前到达的上报；目标为未演场次，按距开演同样天数对齐同演出同场馆已演场次。售票率=累计售票数/(累计售票数+可售座位)，取历史场次同日售票率的中位数；当前售票率严格低于中位数才预警。漏报留空、可售座位为0（售罄）的记录不参与，历史有效样本不足2条不出预警。迟到上报与更正只进入新版本；重跑沿用同一截止点与冻结快照，不向已发布版本追加预警。'}
def days_to_show(n):return f'{n}天'
