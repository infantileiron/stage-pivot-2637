import {state} from '../stores/session.js';import {esc} from '../utils/html.js';import {badge} from '../components/common/status.js';import {table} from '../components/common/table.js';import {field,select} from '../components/common/fields.js';import {VENUES,WARNING_REASONS} from '../constants/enums.js';import {pct} from '../utils/format.js';
function rateOf(r){const d=r.sold_total+r.available_seats;return d?r.sold_total/d:null}
function batchView(){
 const b=state.selectedWarning;if(!b)return '<p class="notice">在右侧指定截止时间发布预警版本；回看只使用截止前已到达的数据。</p>';
 if(b.state!=='done')return `<p class="notice">版本 #${b.id} 状态：${esc(b.state)}${b.error?' · '+esc(b.error):'，后台计算中，请刷新。'}</p>`;
 const r=b.result;
 return `<h3>#${b.id} ${esc(b.name)} ${badge(b.state)}</h3><p class="notice">截止时间 ${esc(r.cutoff_at)} · 未演场次 ${r.target_count} · 预警 ${r.warning_count} · 排除 ${r.exclusion_count}<br>${esc(r.method)}</p>
 <div class="metrics"><div><strong>${r.warning_count}</strong>预警场次</div><div><strong>${r.target_count}</strong>未演场次</div><div><strong>${r.exclusion_count}</strong>排除场次</div></div>
 <h3>预警名单（当前售票率严格低于历史中位数）</h3>
 ${r.warnings.length?r.warnings.map(w=>`<article class="rec"><h3>${esc(w.code)} · ${esc(w.play)} / ${esc(w.venue)} ${badge('预警')}</h3><p>开演 ${esc(w.show_day)}（距开演${w.days_to_show}天） · 上报日 ${esc(w.report_day)} · 当前售票率 <b>${pct(w.current_rate)}</b> · 历史中位数 ${pct(w.historical_median_rate)} · 差值 ${pct(w.gap)}</p>${table(['历史场次','开演日','对齐上报日','累计售票','可售座位','售票率'],w.samples.map(x=>[x.code,x.show_day,x.report_day,x.sold_total,x.available_seats,pct(x.rate)]))}</article>`).join(''):'<p>本版本没有触发预警的场次。</p>'}
 <h3>排除场次与原因（缺数、售罄不参与比较）</h3>
 ${table(['场次','演出/场馆','开演日','距开演','排除原因','说明'],r.exclusions.map(e=>[e.code,e.play+' / '+e.venue,e.show_day,e.days_to_show??'—',WARNING_REASONS[e.reason]||e.reason,e.detail]))}`;
}
export function render(){
 const b=state.selectedWarning;
 return `<div class="split"><section class="panel"><div class="result-head"><h2>临演售票预警 ${b?badge(b.state):''}</h2><button id="refresh">刷新数据</button></div>${batchView()}
 <h3>历史预警版本</h3>${state.warningBatches.map(x=>`<button class="study" data-batch="${x.id}">#${x.id} ${esc(x.name)} · 截止 ${esc(x.cutoff_at)} · ${esc(x.state)}</button>`).join('')||'<p>暂无版本。</p>'}
 ${b&&b.state!=='done'&&state.user.role!=='viewer'?`<button data-rerun="${b.id}">按原截止点补跑该版本</button>`:''}${b&&b.state==='done'?`<button id="download-warning">下载版本 JSON（名单/样本/排除）</button>`:''}
 <h3>演出场次档案</h3>${table(['场次编号','演出','场馆','开演日','容量'],state.sessions.map(x=>[x.code,x.play,x.venue,x.show_day,x.capacity]))}
 <h3>每日累计售票上报（漏报留空，可补报更正）</h3>${table(['场次','上报日','累计售票','可售座位','售票率','到达时间'],state.reports.map(x=>[state.sessions.find(s=>s.id===x.session_id)?.code||x.session_id,x.report_day,x.sold_total,x.available_seats,pct(rateOf(x)),x.received_at]))}</section>
 <aside class="side"><h2>新建演出场次</h2><form id="session">${field('场次编号','code','text','required placeholder="XS-073"')}${field('演出名称','play','text','required')}${select('场馆','venue',VENUES.map(x=>[x,x]))}${field('开演日期','show_day','date','required')}${field('可售总容量','capacity','number','required min=1')}<button class="primary">保存场次</button></form>
 <h2>补报 / 更正每日售票</h2><form id="report">${field('场次编号','code','text','required placeholder="XS-073"')}${field('上报日期','report_day','date','required')}${field('累计售票数','sold_total','number','required min=0')}${field('可售座位','available_seats','number','required min=0')}${field('到达时间（UTC，留空取当前）','received_at','datetime-local')}<p>同一上报日重复提交即更正；迟到记录只进入之后发布的新版本。时间统一按 UTC 比较。</p><button class="primary">提交补报</button></form>
 <h2>发布预警版本</h2><form id="warning">${field('版本名称','name','text','required value="11月下旬临演预警"')}${field('截止时间（UTC）','cutoff_at','datetime-local','required')}<p>仅统计未演场次；按距开演同样天数对齐同演出同场馆已演场次的售票率中位数。仅纳入到达时间不晚于截止点的上报。</p><button class="primary">按截止点发布</button></form></aside></div>`;
}
