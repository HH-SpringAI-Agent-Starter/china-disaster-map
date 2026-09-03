# -*- coding: utf-8 -*-
"""生成独立的「一线城市 / 新一线 安全排名」页面 tier1_ranking.html。
数据来自 city_data.json，自包含（数据内嵌），支持 一线/新一线/全部 切换、
搜索、分页、导出 CSV。与 disaster_map_city.html 的排名口径一致。"""
import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
cdata = json.load(open(os.path.join(BASE, 'city_data.json'), encoding='utf-8'))
top = cdata['top']; allc = cdata['cities']

def tier(s):
    if s >= 90: return 'S'
    if s >= 80: return 'A'
    if s >= 70: return 'B'
    if s >= 60: return 'C'
    return 'D'
TIER_NAME = {'S':'≥90 极安全','A':'80–89 安全','B':'70–79 较安全','C':'60–69 中等','D':'<60 高风险'}
TIER_COLOR = {'S':'#7FE0A0','A':'#3FA66A','B':'#C9A227','C':'#A8552F','D':'#C4513A'}

FIRST_TIER = {'北京','上海','广州','深圳'}
NEW_TIER = {'成都','重庆','杭州','武汉','西安','苏州','南京','天津','长沙','郑州','东莞','青岛','沈阳','宁波','昆明'}

# 汇集全部城市/市辖区（与主页面一致）
_nat = list(allc)
_seen = {c['name'] for c in _nat}
for t in top:
    if t['name'] not in _seen:
        _nat.append(t); _seen.add(t['name'])
_nat.sort(key=lambda c: (-c['safety'], c['prov'], c['name']))

NAT_DATA = [{'name': c['name'], 'prov': c['prov'], 'safety': c['safety'],
             'tierLabel': TIER_NAME[tier(c['safety'])], 'tierColor': TIER_COLOR[tier(c['safety'])],
             'note': (c.get('note') or ''),
             't1': c['name'] in FIRST_TIER or c['prov'] in FIRST_TIER,
             'new': c['name'] in NEW_TIER or c['prov'] in NEW_TIER}
            for c in _nat]
nat_json = json.dumps(NAT_DATA, ensure_ascii=False).replace('</', '<\\/')

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>一线城市 / 新一线 · 自然灾害安全排名</title>
<style>
* { box-sizing:border-box;margin:0;padding:0 }
body { background:#0F1319;color:#E6EBF0;font-family:"Noto Sans SC","PingFang SC",sans-serif;
  padding:28px 32px 40px;line-height:1.5 }
.wrap { max-width:1100px;margin:0 auto }
header { border-bottom:1px solid #232B35;padding-bottom:16px;margin-bottom:16px }
h1 { font-size:30px;font-weight:800;letter-spacing:.5px }
.sub { color:#94A0AE;font-size:14px;margin-top:6px }
.controls { display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:16px 0 }
.btn { background:#1B232E;color:#CBD2DA;border:1px solid #2E3A47;border-radius:8px;
  padding:7px 14px;font-size:13px;cursor:pointer;font-family:inherit }
.btn.on { background:#2E4757;color:#fff;border-color:#3C5A70 }
.pfilter { background:#1B232E;color:#E6EBF0;border:1px solid #2E3A47;border-radius:6px;padding:7px 10px;font-size:13px;font-family:inherit;min-width:200px }
.psel { background:#1B232E;color:#E6EBF0;border:1px solid #2E3A47;border-radius:6px;padding:7px 8px;font-size:13px;font-family:inherit }
.lead { font-size:13.5px;color:#A9B4BF;margin:8px 0 14px }
.row { display:grid;grid-template-columns:120px 1fr;gap:8px 12px;align-items:center;padding:6px 0;border-bottom:1px solid #1B232E }
.rname { font-size:14px;font-weight:600;color:#E6EBF0 }
.rprov { font-size:11px;color:#7E8A98;margin-left:6px;font-weight:400 }
.rbadge { font-size:10px;color:#0F1319;background:#3FA66A;border-radius:4px;padding:1px 5px;margin-left:6px;font-weight:700 }
.rtrack { position:relative;background:#0C1016;border-radius:6px;height:18px;overflow:hidden }
.rfill { height:100%;border-radius:6px } .rval { position:absolute;right:6px;top:0;font-size:11px;line-height:18px;color:#fff;font-weight:700 }
.rnote { grid-column:1 / -1;font-size:11.5px;color:#8E99A6;margin-top:-4px }
.list { max-height:620px;overflow:auto;padding:4px 8px;border:1px solid #1B232E;border-radius:8px }
.pager { display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px;font-size:13px;color:#A9B4BF }
.pgbtn { background:#1B232E;color:#CBD2DA;border:1px solid #2E3A47;border-radius:6px;padding:5px 12px;font-size:13px;cursor:pointer;font-family:inherit }
.pgbtn:disabled { opacity:.4;cursor:default }
.pginfo { font-size:13px;color:#A9B4BF }
.pgjump { display:flex;align-items:center;gap:4px }
.pgin { width:66px;background:#1B232E;color:#E6EBF0;border:1px solid #2E3A47;border-radius:6px;padding:5px 8px;font-size:13px }
.foot { margin-top:24px;font-size:11.5px;color:#6E7A88;line-height:1.7;border-top:1px solid #232B35;padding-top:14px }
a { color:#7FB4D6 }
</style></head>
<body><div class="wrap">
<header>
  <h1>一线城市 / 新一线 · 自然灾害安全排名</h1>
  <div class="sub">基于百年灾害等级（lc）与 2026 态势（l2）推导的自然灾害暴露安全指数 · 与主页口径一致</div>
</header>
<div class="lead">指数 = 100 −（百年灾害权重×0.6 ＋ 2026 态势×0.4 ＋ 灾害带暴露惩罚）。仅衡量自然灾害暴露度，不含经济、人口、基础设施与防灾能力。<b>安全≠无灾</b>，仅表示相对暴露较低。</div>
<div class="controls">
  <button class="btn on" id="bT1">一线城市</button>
  <button class="btn" id="bNew">新一线</button>
  <button class="btn" id="bAll">全部城市</button>
  <input class="pfilter" id="kw" placeholder="按城市 / 省筛选…" />
  <select class="psel" id="size"><option>50</option><option>100</option><option>200</option></select>
  <button class="pgbtn" id="export" data-file="城市安全排名.csv">导出 CSV</button>
</div>
<div class="list" id="list"></div>
<div class="pager" id="pager"></div>
<div class="foot">
  底图与城市数据依据自然资源部标准地图（DataV GeoAtlas）与公开灾害年鉴。台湾省为中国领土不可分割的一部分。
  本排名为自然灾害暴露度科普示意，非城市综合安全评价，不作选址 / 投资 / 防灾规划决策依据。
  完整交互地图见 <a href="disaster_map_city.html">disaster_map_city.html</a>。
</div>
</div>
<script>
const NAT_DATA = __NATDATA__;
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function csvCell(v){ v = String(v==null?'':v); if(/[",\n\r]/.test(v)) v = '"'+v.replace(/"/g,'""')+'"'; return v; }
function item(d){
  return `<div class="row">
    <div class="rname">${esc(d.name)}<span class="rprov">${esc(d.prov)}</span><span class="rbadge" style="background:${d.tierColor}">${esc(d.tierLabel)}</span></div>
    <div class="rtrack"><div class="rfill" style="width:${d.safety}%;background:${d.tierColor}"></div><span class="rval">${d.safety}</span></div>
    ${d.note?`<div class="rnote">${esc(d.note)}</div>`:''}
  </div>`;
}
const list = document.getElementById('list'), pager = document.getElementById('pager');
const kw = document.getElementById('kw'), size = document.getElementById('size');
let mode = 't1', per = 50, page = 1;
function base(){
  if(mode==='t1') return NAT_DATA.filter(d=>d.t1);
  if(mode==='new') return NAT_DATA.filter(d=>d.new);
  return NAT_DATA;
}
function filtered(){
  const q = kw.value.trim().toLowerCase();
  const arr = base();
  return q ? arr.filter(d => (d.name+' '+d.prov+' '+d.tierLabel+' '+(d.note||'')).toLowerCase().indexOf(q) >= 0) : arr;
}
function render(){
  const flt = filtered();
  const total = flt.length;
  const pages = Math.max(1, Math.ceil(total / per));
  if(page>pages) page=pages; if(page<1) page=1;
  const a=(page-1)*per, b=Math.min(a+per,total);
  list.innerHTML = flt.slice(a,b).map(item).join('') || '<div class="rnote">没有匹配的结果。</div>';
  pager.innerHTML='';
  const mk=(t,dis,fn)=>{const x=document.createElement('button');x.className='pgbtn';x.textContent=t;x.disabled=dis;x.onclick=fn;return x;};
  pager.appendChild(mk('上一页', page<=1, ()=>{page--;render();}));
  const info=document.createElement('span'); info.className='pginfo';
  info.textContent='第 '+page+' / '+pages+' 页 · 共 '+total+' 条';
  pager.appendChild(info);
  pager.appendChild(mk('下一页', page>=pages, ()=>{page++;render();}));
  const jump=document.createElement('span'); jump.className='pgjump';
  const inp=document.createElement('input'); inp.type='number'; inp.min=1; inp.max=pages; inp.value=page; inp.className='pgin';
  inp.onchange=()=>{let v=parseInt(inp.value)||1;v=Math.max(1,Math.min(pages,v));page=v;render();};
  const go=document.createElement('button'); go.className='pgbtn'; go.textContent='跳转'; go.onclick=()=>inp.onchange();
  jump.appendChild(document.createTextNode(' 跳至 ')); jump.appendChild(inp); jump.appendChild(document.createTextNode(' 页 ')); jump.appendChild(go);
  pager.appendChild(jump);
}
function setMode(m, btn){
  mode=m; page=1;
  [['t1',document.getElementById('bT1')],['new',document.getElementById('bNew')],['all',document.getElementById('bAll')]].forEach(([k,el])=>el.classList.toggle('on', k===m));
  render();
}
document.getElementById('bT1').onclick=()=>setMode('t1');
document.getElementById('bNew').onclick=()=>setMode('new');
document.getElementById('bAll').onclick=()=>setMode('all');
kw.addEventListener('input', ()=>{page=1;render();});
size.addEventListener('change', ()=>{per=parseInt(size.value)||50;page=1;render();});
document.getElementById('export').addEventListener('click', ()=>{
  const flt = filtered();
  const cols=[{k:'name',l:'城市'},{k:'prov',l:'省份'},{k:'safety',l:'安全指数'},{k:'tierLabel',l:'风险档'},{k:'note',l:'备注'}];
  const lines=[cols.map(c=>c.l).join(',')];
  flt.forEach(d=>lines.push(cols.map(c=>csvCell(d[c.k])).join(',')));
  const blob=new Blob(['﻿'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob); const a=document.createElement('a');
  a.href=url; a.download=document.getElementById('export').dataset.file||'export.csv';
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
});
render();
</script>
</body></html>'''

HTML = HTML.replace('__NATDATA__', nat_json)
open(os.path.join(BASE, 'tier1_ranking.html'), 'w', encoding='utf-8').write(HTML)
print('tier1_ranking.html', len(HTML))
