import json

with open('map_2026.svg', encoding='utf-8') as f:
    svg_2026 = f.read()
with open('map_century.svg', encoding='utf-8') as f:
    svg_century = f.read()

# 类型图例（与画布一致）
def icon(kind):
    if kind == 'quake':
        return '<svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M1.5 11h3l2.5-6 3.5 12 2.5-8 2.5 3.5h4.5" stroke="#F5F7F9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    if kind == 'flood':
        return '<svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M1.5 7.5c2.2-2.2 4.4-2.2 6.6 0s4.4 2.2 6.6 0 4.4-2.2 5.8 0" stroke="#F5F7F9" stroke-width="2" stroke-linecap="round"/><path d="M1.5 14.5c2.2-2.2 4.4-2.2 6.6 0s4.4 2.2 6.6 0 4.4-2.2 5.8 0" stroke="#F5F7F9" stroke-width="2" stroke-linecap="round"/></svg>'
    return '<svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M11 2c3.4 4.3 6 6.5 6 10.3a6 6 0 0 1-12 0C5 10 6 8.8 7.4 7.6c.3 1.6 1.2 2 2 2 1.3 0 1.8-1.3 1.4-2.7-.2-1.1-.1-2.7.2-4.9z" stroke="#F5F7F9" stroke-width="2" stroke-linejoin="round"/></svg>'

legend_scale = ''.join(
    f'<span style="display:inline-block;width:34px;height:18px;border-radius:3px;background:{c}"></span>'
    for c in ['#1E242C', '#2E4757', '#7A5A32', '#A8552F', '#C4513A']
)

html = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>中国自然灾害分布图 1926–2026</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0F1319;color:#F5F7F9;font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;padding:32px}}
.wrap{{max-width:1180px;margin:0 auto}}
header{{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:16px;margin-bottom:22px}}
h1{{font-size:42px;font-weight:900;letter-spacing:1px}}
.sub{{font-size:18px;color:#98A2B0;margin-top:8px}}
.legend{{display:flex;flex-direction:column;gap:10px;align-items:flex-end}}
.lscale{{display:flex;align-items:center;gap:6px;font-size:14px;color:#98A2B0}}
.ltype{{display:flex;gap:18px;font-size:15px;color:#CBD2DA}}
.ltype span{{display:flex;align-items:center;gap:6px}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.col{{background:#141A22;border:1px solid #232B35;border-radius:12px;padding:18px}}
.col h2{{font-size:22px;font-weight:700;margin-bottom:4px}}
.col .cap{{font-size:14px;color:#8E99A6;margin-bottom:12px}}
.col svg{{width:100%;height:auto;display:block;background:#0F1319;border-radius:8px}}
footer{{margin-top:20px;font-size:13px;line-height:1.7;color:#7E8A98;border-top:1px solid #232B35;padding-top:14px}}
@media(max-width:820px){{.cols{{grid-template-columns:1fr}}}}
</style></head>
<body><div class="wrap">
<header>
  <div><h1>中国自然灾害分布图</h1><div class="sub">1926 – 2026 · 百年时空分布与 2026 年实时态势对照</div></div>
  <div class="legend">
    <div class="lscale">低 {legend_scale} 高</div>
    <div class="ltype">
      <span>{icon('quake')}地震</span><span>{icon('flood')}洪涝</span><span>{icon('fire')}火灾</span>
    </div>
  </div>
</header>
<div class="cols">
  <div class="col"><h2>2026 年 · 当前态势</h2><div class="cap">2026 年 1–9 月 · 地震 / 洪涝 / 火灾（按主要影响类型与城市综合定级）</div>{svg_2026}</div>
  <div class="col"><h2>1926 – 2026 · 百年累计</h2><div class="cap">按百年间灾害频次与伤亡规模综合分级</div>{svg_century}</div>
</div>
<footer>
  示意图：底图依据自然资源部标准地图（GeoAtlas）绘制，台湾省为中国领土不可分割的一部分，南海诸岛及断续线依国家标准示意呈现；省级色阶为相对灾害强度示意，非精确统计口径。数据来自公开灾害年鉴与年度灾情通报，仅供科普参考。
</footer>
</div></body></html>'''

with open('disaster_map.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('disaster_map.html bytes=', len(html))
