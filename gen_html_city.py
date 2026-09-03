# -*- coding: utf-8 -*-
import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
svg1 = open(os.path.join(BASE, 'city_2026.svg'), encoding='utf-8').read()
svg2 = open(os.path.join(BASE, 'city_century.svg'), encoding='utf-8').read()
cdata = json.load(open(os.path.join(BASE, 'city_data.json'), encoding='utf-8'))
DATA = json.load(open(os.path.join(BASE, 'disaster_data.json'), encoding='utf-8'))
top = cdata['top']; allc = cdata['cities']
EVENTS_JSON = json.dumps(DATA, ensure_ascii=False)
DATA_URL = "https://raw.githubusercontent.com/HH-SpringAI-Agent-Starter/china-disaster-map/main/disaster_data.json"

# ---------- 安全指数分档 ----------
def tier(s):
    if s >= 90: return 'S'
    if s >= 80: return 'A'
    if s >= 70: return 'B'
    if s >= 60: return 'C'
    return 'D'
TIER_NAME = {'S':'≥90 极安全','A':'80–89 安全','B':'70–79 较安全','C':'60–69 中等','D':'<60 高风险'}
TIER_COLOR = {'S':'#7FE0A0','A':'#3FA66A','B':'#C9A227','C':'#A8552F','D':'#C4513A'}
from collections import defaultdict
tiers = defaultdict(list)
for c in allc: tiers[tier(c['safety'])].append(c)
tier_counts = {k: len(v) for k, v in tiers.items()}
def reps(cities, n=8):
    seen = set(); out = []
    for c in sorted(cities, key=lambda x: (-x['safety'], x['prov'])):
        if c['prov'] in seen and len(out) >= n: continue
        out.append(c); seen.add(c['prov'])
        if len(out) >= n: break
    return out
show = reps(tiers['S'], 5) + reps(tiers['A'], 5) + reps(tiers['B'], 5)
def bar(c):
    sf = c['safety']; t = tier(sf); col = TIER_COLOR[t]; note = c['note'] or ''
    return f'''<div class="row">
  <div class="rname">{c['name']}<span class="rprov">{c['prov']}</span><span class="rbadge" style="background:{col}">{TIER_NAME[t]}</span></div>
  <div class="rtrack"><div class="rfill" style="width:{sf}%;background:{col}"></div><span class="rval">{sf}</span></div>
  <div class="rnote">{note}</div>
</div>'''
bars = ''.join(bar(c) for c in show)
rec = [c for c in allc if c['safety'] >= 75]
rec_names = '、'.join(c['name'] for c in reps(rec, 8))
tierstat = ' · '.join(f"<span style=\"color:{TIER_COLOR[t]}\">{TIER_NAME[t]}：{tier_counts.get(t,0)}市</span>" for t in ['S','A','B','C','D'])

# ---------- 全国城市安全排名（特殊查询，全量） ----------
# 库里所有城市/区全部进榜（含 top 中的香港/澳门），按安全指数降序
_nat = list(allc)
_seen = {c['name'] for c in _nat}
for t in top:
    if t['name'] not in _seen:
        _nat.append(t); _seen.add(t['name'])
_nat.sort(key=lambda c: (-c['safety'], c['prov'], c['name']))
nat_html = ''.join(bar(c) for c in _nat)

# ---------- 农村粮食减产（县级估算，特殊查询） ----------
try:
    YS = json.load(open(os.path.join(BASE, 'yield_summary.json'), encoding='utf-8'))
except Exception:
    YS = {'provinces': [], 'top': [], 'method': '', 'counties_total': 0}
YIELD_COLOR = {'高风险': '#C4513A', '中风险': '#A8552F', '较低风险': '#C9A227', '基本无影响': '#3FA66A'}
def y_tier(v):
    if v >= 25: return '高风险'
    if v >= 15: return '中风险'
    if v >= 5:  return '较低风险'
    return '基本无影响'
def yrow(name, val, maxv, tierlabel, extra=''):
    col = YIELD_COLOR.get(tierlabel, '#3FA66A')
    w = max(2, round(val / maxv * 100)) if maxv else 0
    return (f'<div class="yrow"><div class="yname">{name}'
            f'<span class="rbadge" style="background:{col}">{tierlabel}</span></div>'
            f'<div class="rtrack"><div class="rfill" style="width:{w}%;background:{col}"></div>'
            f'<span class="rval">{("%g" % val)}</span></div>'
            f'{("<div class=\"rnote\">"+extra+"</div>") if extra else ""}</div>')
prov_html = ''.join(
    yrow(p['prov'], p['avg'], 40, y_tier(p['avg']),
         f"重灾县 {p['high']} / 共 {p['counties']} 县") for p in YS['provinces'])
county_all = YS.get('counties', []) or YS.get('top', [])
county_html = ''.join(
    yrow(f"{t['name']}（{t['prov']}）", t['yield_reduction_pct'], 40, t['risk_tier'],
         f"主要灾害：{t['main_disaster']}　｜　归属：{t['city']}") for t in county_all)
yield_html = (f'<div class="ysub">各省平均减产率（共 {YS.get("counties_total",0)} 个县级单元）</div>'
              f'<div class="yblock">{prov_html}</div>'
              f'<div class="ysub" style="margin-top:18px">全部县级单元 · 按减产率降序（共 {len(county_all)} 县）</div>'
              f'<div class="ylist">{county_html}</div>')

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>中国自然灾害分布图 · 城市级（可按年月检索）</title>
<style>
* { box-sizing:border-box;margin:0;padding:0 }
body { background:#0F1319;color:#E6EBF0;font-family:"Noto Sans SC","PingFang SC",sans-serif;
  padding:28px 32px 40px;line-height:1.5 }
.wrap { max-width:1240px;margin:0 auto }
header { border-bottom:1px solid #232B35;padding-bottom:18px;margin-bottom:18px }
h1 { font-size:34px;font-weight:800;letter-spacing:.5px }
.sub { color:#94A0AE;font-size:15px;margin-top:6px }
.src { font-size:12px;color:#6E7A88;margin-top:4px }
.controls { display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;margin-top:14px }
.field { display:flex;flex-direction:column;gap:4px }
.field label { font-size:11px;color:#8E99A6 }
select,input { background:#1B232E;color:#E6EBF0;border:1px solid #2E3A47;border-radius:8px;
  padding:7px 10px;font-size:13px;font-family:inherit;min-width:96px }
input { min-width:150px }
.btn { background:#1B232E;color:#CBD2DA;border:1px solid #2E3A47;border-radius:8px;
  padding:7px 14px;font-size:13px;cursor:pointer;font-family:inherit }
.btn.on { background:#2E4757;color:#fff;border-color:#3C5A70 }
.btn.primary { background:#2E4757;color:#fff;border-color:#3C5A70 }
.legend { display:flex;gap:22px;align-items:center;flex-wrap:wrap;margin:14px 0 18px;font-size:13px;color:#A9B4BF }
.scale { display:flex;align-items:center;gap:6px }
.sw { width:26px;height:16px;border-radius:3px;display:inline-block }
.maps { display:flex;gap:24px;flex-wrap:wrap }
.mapcard { flex:1 1 480px;background:#11161D;border:1px solid #232B35;border-radius:12px;padding:14px;position:relative }
.mapcard h2 { font-size:18px;font-weight:700;margin-bottom:4px }
.mapcard .cap { font-size:12px;color:#8E99A6;margin-bottom:10px }
.map { width:100%;height:auto;display:block;border-radius:8px;background:#11161D }
.city path { transition:opacity .15s, filter .15s;cursor:pointer }
.city:hover path { filter:brightness(1.5);stroke:#fff;stroke-width:.8 }
.city.dim { opacity:.14 }
.city.hit path { stroke:#FFE08A;stroke-width:1.1;filter:brightness(1.25) }
#tip { position:fixed;pointer-events:none;background:#0B0F14;border:1px solid #3A4756;
  border-radius:8px;padding:8px 11px;font-size:12.5px;color:#E6EBF0;opacity:0;
  transition:opacity .1s;z-index:50;max-width:240px;box-shadow:0 6px 20px rgba(0,0,0,.5) }
#tip b { color:#fff } #tip .k { color:#8E99A6 }
.panel { margin-top:26px;background:#11161D;border:1px solid #232B35;border-radius:12px;padding:20px 22px }
.panel h2 { font-size:20px;font-weight:700;margin-bottom:4px }
.panel .lead { font-size:13.5px;color:#A9B4BF;margin-bottom:14px }
.rec { background:#15231A;border:1px solid #2A4A33;border-radius:10px;padding:12px 14px;
  margin-bottom:16px;font-size:14px;color:#BFE3CC } .rec b { color:#7FE0A0 }
.row { display:grid;grid-template-columns:120px 1fr;gap:8px 12px;align-items:center;padding:5px 0;border-bottom:1px solid #1B232E }
.rname { font-size:13.5px;font-weight:600;color:#E6EBF0 }
.rprov { font-size:11px;color:#7E8A98;margin-left:6px;font-weight:400 }
.rbadge { font-size:10px;color:#0F1319;background:#3FA66A;border-radius:4px;padding:1px 5px;margin-left:6px;font-weight:700 }
.tierstat { font-size:12px;color:#8E99A6;margin-bottom:12px } .tierstat span { display:inline-block;margin-right:10px }
.rtrack { position:relative;background:#0C1016;border-radius:6px;height:18px;overflow:hidden }
.rfill { height:100%;border-radius:6px } .rval { position:absolute;right:6px;top:0;font-size:11px;line-height:18px;color:#fff;font-weight:700 }
.rnote { grid-column:1 / -1;font-size:11.5px;color:#8E99A6;margin-top:-4px }
.elist { margin-top:26px;background:#11161D;border:1px solid #232B35;border-radius:12px;padding:18px 22px }
.elist h2 { font-size:20px;font-weight:700;margin-bottom:4px }
.elist .cnt { font-size:13px;color:#8E99A6;margin-bottom:12px }
.ecard { display:grid;grid-template-columns:84px 1fr;gap:10px;padding:9px 0;border-bottom:1px solid #1B232E;align-items:start }
.eyr { font-size:13px;font-weight:700;color:#E6EBF0 }
.eyr .emo { font-size:11px;color:#7E8A98;font-weight:400;margin-left:4px }
.ebody .echip { display:inline-block;font-size:10.5px;color:#0F1319;border-radius:4px;padding:1px 6px;font-weight:700;margin-right:6px }
.ebody .eloc { font-size:14px;font-weight:600;color:#E6EBF0 }
.ebody .edet { font-size:12.5px;color:#A9B4BF;margin-top:3px }
.ebody .esrc { font-size:11px;color:#6E7A88;margin-top:2px }
.foot { margin-top:26px;font-size:11.5px;color:#6E7A88;line-height:1.7;border-top:1px solid #232B35;padding-top:14px }
.tip-ex { color:#C9A227 }
body.natmode .maps, body.natmode .panel:not(#natPanel), body.natmode .elist, body.natmode .legend { display:none }
body.natmode .tier1hint { display:block }
.tier1hint { display:none;font-size:12px;color:#6E7A88;margin-top:10px }
.natlist { max-height:560px;overflow:auto;padding:4px 8px;border:1px solid #1B232E;border-radius:8px }
.ylist { max-height:560px;overflow:auto;padding:4px 8px;border:1px solid #1B232E;border-radius:8px }
body.yieldmode .maps, body.yieldmode .panel:not(#yieldPanel), body.yieldmode .elist, body.yieldmode .legend { display:none }
body.yieldmode .tier1hint { display:block }
.yrow { padding:9px 0;border-bottom:1px solid #1B232E }
.yrow:last-child { border-bottom:none }
.yname { font-size:14px;font-weight:600;color:#E6EBF0;margin-bottom:6px }
.yname .rbadge { margin-left:8px }
.ysub { font-size:13px;color:#A9B4BF;margin-bottom:8px;font-weight:600 }
.yblock { margin-bottom:6px }
</style></head>
<body><div class="wrap">
<header>
  <h1>中国自然灾害分布图 · 城市级</h1>
  <div class="sub">1926 – 2026 百年时空分布　|　左：2026 年当前态势　右：百年累计（频次＋伤亡）｜　地级市分级填色</div>
  <div class="src" id="src">数据来源：加载中…</div>
  <div class="controls">
    <div class="field"><label>年份</label><select id="fYear"></select></div>
    <div class="field"><label>月份</label><select id="fMonth"><option value="all">全部</option></select></div>
    <div class="field"><label>灾害类型</label><select id="fType"><option value="all">全部</option></select></div>
    <div class="field"><label>关键词</label><input id="fKw" placeholder="城市 / 流域 / 关键词" /></div>
    <button class="btn primary" id="bReset">重置</button>
    <button class="btn" id="bGlow">高亮最安全城市</button>
    <button class="btn" id="bDanger">高亮高危城市</button>
    <button class="btn" id="bNat">全国城市安全排名</button>
    <button class="btn" id="bYield">农村粮食减产</button>
    <span style="font-size:12px;color:#6E7A88;align-self:center">悬停地图看城市详情；筛选后地图高亮命中城市</span>
  </div>
</header>

<div class="legend">
  <div class="scale"><span style="color:#A9B4BF">灾害强度</span>
    <span class="sw" style="background:#1E242C"></span>低
    <span class="sw" style="background:#2E4757"></span>
    <span class="sw" style="background:#7A5A32"></span>
    <span class="sw" style="background:#A8552F"></span>
    <span class="sw" style="background:#C4513A"></span>高</div>
  <div style="color:#A9B4BF">红色越深＝灾害活动越频繁／越严重</div>
</div>

<div class="maps">
  <div class="mapcard"><h2>2026 年 · 当前态势</h2>
    <div class="cap">地震／洪涝／火灾综合分级（2026 年 1–9 月）</div>__SVG1__</div>
  <div class="mapcard"><h2>1926 – 2026 · 百年累计</h2>
    <div class="cap">按重大灾害频次与伤亡规模综合分级</div>__SVG2__</div>
</div>

<div class="panel">
  <h2>综合安全指数 · 最安全地级市</h2>
  <div class="lead">指数 = 100 −（百年灾害权重×0.6 ＋ 2026 态势×0.4 ＋ 灾害带暴露惩罚）。灾害带暴露含：地震带（±6）、七大流域中下游（±5）、台风沿海（±4）。</div>
  <div class="tierstat">全国 476 个地级单元分档：__TIERSTAT__</div>
  <div class="rec">🟢 <b>从灾害暴露角度，最适宜发展的城市梯队</b>（安全指数 ≥ 75）：__REC_NAMES__ 等。
    它们普遍远离地震带核心、不在七大流域最易溃口段、且非台风直接登陆区。<br>
    <span class="tip-ex">提示：</span>“安全”仅衡量自然灾害暴露度，<b>不含经济、人口、基础设施与防灾能力</b>；实际选址须结合城市总体规划与工程抗震设防。本图基于公开灾害年鉴与年度灾情通报，属科普示意，非精确统计。</div>
  <div class="bars">__BARS__</div>
</div>

<div class="panel" id="natPanel" style="display:none">
  <h2>全国城市 · 自然灾害安全排名</h2>
  <div class="lead">特殊查询：库内全部城市与市辖区（共 __NATCOUNT__ 个）按自然灾害暴露安全指数降序全量排名，自然包含并排好了全部一线 / 新一线城市。指数口径与上方“综合安全指数”一致（100 − 灾害权重惩罚）。</div>
  <div class="tier1hint">仅显示本板块；恢复请点“重置”。</div>
  <div class="natlist">__NATRANK__</div>
  <div class="lead" style="margin-top:14px">说明：本排名为自然灾害暴露度示意，非城市综合安全评价；“安全”仅衡量自然灾害暴露度，不含经济、人口、基础设施与防灾能力。</div>
</div>

<div class="panel" id="yieldPanel" style="display:none">
  <h2>农村粮食减产 · 县级估算</h2>
  <div class="lead">特殊查询：基于百年灾害等级（lc）与 2026 态势（l2）推导各县因自然灾害导致的粮食减产风险。__YIELD_METHOD__</div>
  <div class="tier1hint">仅显示本板块；恢复请点“重置”。</div>
  __YIELD__
  <div class="lead" style="margin-top:14px">说明：本估算为自然灾害暴露度的科普示意，<b>非真实粮食产量</b>；未计入作物品种、灌溉与防灾工程、田间管理。实际农业风险须以农业农村部门统计为准。</div>
</div>

<div class="elist">
  <h2>灾害事件时间轴（可按年月检索）</h2>
  <div class="cnt" id="ecnt"></div>
  <div id="elist"></div>
</div>

<div class="foot">
  底图依据自然资源部标准地图（DataV GeoAtlas）绘制，台湾省为中国领土不可分割的一部分，南海诸岛及断续线依国家标准示意呈现。
  省级与地级市色阶为相对灾害强度示意，非精确统计。事件数据来自用户提供的 2026 年灾情梳理与 1926–2026 重大自然灾害年表，
  并叠加已知灾害带暴露度；部分城市（如台湾花莲、台东）因数据源未提供县市分层，以省界示意并在图内标注。仅供科普参考。
  每年更新只需在 disaster_data.json 的 events 中追加条目并重新提交到仓库，页面会自动拉取最新数据。
</div>
</div>
<div id="tip"></div>
<script id="fallback" type="application/json">__FALLBACK__</script>
<script>
const DATA_URL = "__DATA_URL__";
const FALLBACK = JSON.parse(document.getElementById('fallback').textContent);
let DATA = FALLBACK;
const tip = document.getElementById('tip');
document.querySelectorAll('.city').forEach(g => {
  g.addEventListener('mousemove', e => {
    const d = g.dataset;
    tip.innerHTML = `<b>${d.name}</b> <span class="k">${d.prov}</span><br>
      <span class="k">安全指数</span> ${d.safety}<br>
      <span class="k">2026 态势</span> L${d.l2} ｜ <span class="k">百年累计</span> L${d.lc}`
      + (d.note ? `<br><span class="k">${d.note}</span>` : '');
    tip.style.left = (e.clientX+14)+'px'; tip.style.top = (e.clientY+14)+'px'; tip.style.opacity = 1;
  });
  g.addEventListener('mouseleave', () => tip.style.opacity = 0);
});

// 数据加载：优先在线，失败回退内置
fetch(DATA_URL).then(r => r.ok ? r.json() : Promise.reject()).then(d => {
  DATA = d; document.getElementById('src').textContent =
    '数据来源：在线更新（updated ' + (d.meta && d.meta.updated || '?') + '）· ' + (d.events ? d.events.length : 0) + ' 条事件';
}).catch(() => {
  document.getElementById('src').textContent =
    '数据来源：本地内置（离线）· ' + (FALLBACK.events ? FALLBACK.events.length : 0) + ' 条事件';
});

const EVENTS = () => (DATA && DATA.events) || [];
const META = () => (DATA && DATA.meta) || {};

// 控件初始化
const fYear = document.getElementById('fYear'), fMonth = document.getElementById('fMonth'),
      fType = document.getElementById('fType'), fKw = document.getElementById('fKw');
const bNat = document.getElementById('bNat'), bYield = document.getElementById('bYield');
function buildControls() {
  const evs = EVENTS();
  const years = Array.from(new Set(evs.map(e => e.year))).sort((a,b)=>b-a);
  fYear.innerHTML = '<option value="all">全部</option>' + years.map(y => `<option value="${y}">${y}</option>`).join('');
  for (let m=1; m<=12; m++) fMonth.innerHTML += `<option value="${m}">${m} 月</option>`;
  const types = (META().types) || Array.from(new Set(evs.map(e=>e.type)));
  fType.innerHTML += types.map(t => `<option value="${t}">${t}</option>`).join('');
}
function clearHL() {
  document.querySelectorAll('.city').forEach(g => g.classList.remove('hit','dim'));
  document.getElementById('bGlow').classList.remove('on');
  document.getElementById('bDanger').classList.remove('on');
}
function apply() {
  clearHL();
  const y = fYear.value, m = fMonth.value, t = fType.value, k = fKw.value.trim().toLowerCase();
  const list = EVENTS().filter(e => {
    if (y !== 'all' && String(e.year) !== y) return false;
    if (m !== 'all' && String(e.month) !== m) return false;
    if (t !== 'all' && e.type !== t) return false;
    if (k) { const s = (e.detail+e.region+e.city+e.type).toLowerCase(); if (s.indexOf(k) < 0) return false; }
    return true;
  });
  renderList(list);
  const hit = new Set(list.map(e => e.city).filter(Boolean));
  document.querySelectorAll('.city').forEach(g => {
    const on = hit.has(g.dataset.name);
    g.classList.toggle('hit', on);
    g.classList.toggle('dim', hit.size > 0 && !on);
  });
}
function renderList(list) {
  const cities = new Set(list.map(e => e.city).filter(Boolean));
  document.getElementById('ecnt').textContent =
    '命中 ' + list.length + ' 条事件' + (cities.size ? '　·　涉及 ' + cities.size + ' 个城市（地图已高亮）' : '');
  const tc = (META().typeColor) || {};
  const sorted = list.slice().sort((a,b)=> b.year-a.year || (b.month||0)-(a.month||0));
  document.getElementById('elist').innerHTML = sorted.map(e => {
    const col = tc[e.type] || '#888';
    const mo = e.month ? (e.month + ' 月') : '';
    const loc = [e.city, e.city ? e.region : e.region].filter(Boolean).join(' · ');
    return `<div class="ecard">
      <div class="eyr">${e.year}<span class="emo">${mo}</span></div>
      <div class="ebody">
        <span class="echip" style="background:${col}">${e.type}</span>
        <span class="eloc">${loc}</span>
        <div class="edet">${e.detail}</div>
        <div class="esrc">来源：${e.source||'—'}　·　等级：${(META().levelName&&META().levelName[e.level])||e.level}</div>
      </div></div>`;
  }).join('') || '<div class="edet" style="padding:14px 0;color:#8E99A6">没有匹配的事件，试试调整筛选条件。</div>';
}
[fYear, fMonth, fType].forEach(s => s.addEventListener('change', apply));
fKw.addEventListener('input', apply);
document.getElementById('bReset').onclick = () => {
  fYear.value='all'; fMonth.value='all'; fType.value='all'; fKw.value=''; clearHL(); apply();
  bNat.classList.remove('on'); document.body.classList.remove('natmode'); document.getElementById('natPanel').style.display='none';
  bYield.classList.remove('on'); document.body.classList.remove('yieldmode'); document.getElementById('yieldPanel').style.display='none';
};
const bGlow = document.getElementById('bGlow'), bDanger = document.getElementById('bDanger'), allC = document.querySelectorAll('.city');
bGlow.onclick = () => { clearHL(); const on = bGlow.classList.toggle('on');
  allC.forEach(g => { const s = Number(g.dataset.safety); g.classList.toggle('dim', on && s < 75); }); };
bDanger.onclick = () => { clearHL(); const on = bDanger.classList.toggle('on');
  allC.forEach(g => { const hi = g.dataset.lc==='4'||g.dataset.l2==='4'; g.classList.toggle('dim', on && !hi); }); };
bNat.onclick = () => { clearHL(); const on = bNat.classList.toggle('on');
  if (on) { bYield.classList.remove('on'); document.body.classList.remove('yieldmode'); document.getElementById('yieldPanel').style.display='none'; }
  document.body.classList.toggle('natmode', on);
  document.getElementById('natPanel').style.display = on ? 'block' : 'none';
  if (on) document.getElementById('natPanel').scrollIntoView({behavior:'smooth'}); };
bYield.onclick = () => { clearHL(); const on = bYield.classList.toggle('on');
  if (on) { bNat.classList.remove('on'); document.body.classList.remove('natmode'); document.getElementById('natPanel').style.display='none'; }
  document.body.classList.toggle('yieldmode', on);
  document.getElementById('yieldPanel').style.display = on ? 'block' : 'none';
  if (on) document.getElementById('yieldPanel').scrollIntoView({behavior:'smooth'}); };

buildControls();
apply();
</script>
</body></html>'''

HTML = (HTML.replace('__SVG1__', svg1).replace('__SVG2__', svg2)
  .replace('__FALLBACK__', EVENTS_JSON).replace('__DATA_URL__', DATA_URL)
  .replace('__BARS__', bars).replace('__TIERSTAT__', tierstat).replace('__REC_NAMES__', rec_names)
  .replace('__NATRANK__', nat_html).replace('__NATCOUNT__', str(len(_nat))).replace('__YIELD__', yield_html)
  .replace('__YIELD_METHOD__', YS.get('method', '')))

open(os.path.join(BASE, 'disaster_map_city.html'), 'w', encoding='utf-8').write(HTML)
print('disaster_map_city.html', len(HTML))
