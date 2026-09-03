# -*- coding: utf-8 -*-
"""生成城市级（地级市）中国自然灾害分布图：双栏 choropleth + 安全指数排名。
底图 = DataV GeoAtlas（自然资源部标准边界）。含台湾省、南海诸岛断续线。
"""
import json, os, math

BASE = os.path.dirname(os.path.abspath(__file__))
W, H = 760, 500
LON0, LON1, LAT0, LAT1 = 73.0, 135.5, 17.5, 54.0

def proj(lon, lat):
    x = (lon - LON0) / (LON1 - LON0) * W
    y = (LAT1 - lat) / (LAT1 - LAT0) * H
    return x, y

# ---------- RDP 简化 ----------
def rdp(points, eps):
    if len(points) < 3:
        return points
    def pld(p, a, b):
        dx, dy = b[0]-a[0], b[1]-a[1]
        L = math.hypot(dx, dy)
        if L == 0:
            return math.hypot(p[0]-a[0], p[1]-a[1])
        return abs(dy*p[0]-dx*p[1]+b[0]*a[1]-b[1]*a[0]) / L
    dmax, idx = 0, 0
    for i in range(1, len(points)-1):
        d = pld(points[i], points[0], points[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        l = rdp(points[:idx+1], eps); r = rdp(points[idx:], eps)
        return l[:-1] + r
    return [points[0], points[-1]]

def ring_to_path(ring, eps=0.5):
    raw = []
    for i, (lon, lat) in enumerate(ring):
        x, y = proj(lon, lat)
        raw.append((round(x, 1), round(y, 1)))
        if i > 0 and i == len(ring)-1:
            break
    # 去重首尾重合
    if raw and raw[0] == raw[-1]:
        raw = raw[:-1]
    # 保留足够点保证小图斑可见
    if len(raw) < 4:
        pts = raw
    else:
        pts = rdp(raw, eps)
        if len(pts) < 3:
            pts = raw
    if len(pts) < 3:
        return ''
    d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts) + 'Z'
    return d

def poly_paths(geom, eps=0.5):
    out = []
    if geom is None:
        return out
    t = geom.get('type'); c = geom.get('coordinates')
    if t == 'Polygon':
        for ring in c:
            p = ring_to_path(ring, eps)
            if p: out.append(p)
    elif t == 'MultiPolygon':
        for poly in c:
            for ring in poly:
                p = ring_to_path(ring, eps)
                if p: out.append(p)
    return out

# ---------- 省 → 级别 ----------
# 2026 当前态势（L0-L4）
LVL_2026 = {
 '新疆':4,'黑龙江':2,'吉林':1,'辽宁':1,'内蒙古':2,'北京':0,'天津':1,'河北':1,'山东':0,
 '江苏':3,'青海':3,'甘肃':2,'宁夏':0,'山西':0,'河南':4,'安徽':1,'上海':2,'浙江':1,
 '西藏':0,'四川':3,'陕西':2,'重庆':1,'湖北':2,'江西':3,'福建':3,'台湾':3,'云南':3,
 '贵州':1,'湖南':2,'广西':3,'广东':2,'海南':1,'香港':0,'澳门':0,
}
# 1926-2026 百年累计（L0-L4）
LVL_CEN = {
 '新疆':3,'黑龙江':1,'吉林':1,'辽宁':1,'内蒙古':1,'北京':0,'天津':2,'河北':4,'山东':1,
 '江苏':3,'青海':3,'甘肃':4,'宁夏':3,'山西':2,'河南':4,'安徽':2,'上海':1,'浙江':1,
 '西藏':3,'四川':4,'陕西':2,'重庆':2,'湖北':3,'江西':2,'福建':2,'台湾':4,'云南':4,
 '贵州':1,'湖南':3,'广西':2,'广东':2,'海南':1,'香港':0,'澳门':0,
}
PROV_NAME = {  # adcode -> 省名
 '110000':'北京','120000':'天津','130000':'河北','140000':'山西','150000':'内蒙古',
 '210000':'辽宁','220000':'吉林','230000':'黑龙江','310000':'上海','320000':'江苏',
 '330000':'浙江','340000':'安徽','350000':'福建','360000':'江西','370000':'山东',
 '410000':'河南','420000':'湖北','430000':'湖南','440000':'广东','450000':'广西',
 '460000':'海南','500000':'重庆','510000':'四川','520000':'贵州','530000':'云南',
 '540000':'西藏','610000':'陕西','620000':'甘肃','630000':'青海','640000':'宁夏',
 '650000':'新疆','710000':'台湾','810000':'香港','820000':'澳门',
}
# 地震带核心 / 流域中下游 / 台风沿海 省集合
BELT_EQ = {'新疆','青海','甘肃','宁夏','四川','云南','西藏','河北','山西','台湾','内蒙古','北京','天津'}
BELT_FLOOD = {'河南','山东','安徽','江苏','湖北','湖南','江西','浙江','上海','四川','重庆','广东','广西','黑龙江','天津','辽宁','贵州'}
BELT_TYPHOON = {'广东','福建','浙江','海南','台湾','上海','江苏','广西','香港','澳门'}

# 具体地级市覆盖（来自用户原文 2026 + 百年年表）
def norm(n):
    for s in ['维吾尔自治区','壮族自治区','回族自治区','自治区','自治州','地区','盟',
              '特别行政区','省','市','县','区']:
        n = n.replace(s, '')
    return n.strip()

# (城市短名, 省, 2026级, 百年级, 备注)
CITY_OVR = [
 # 2026 地震重点
 ('喀什','新疆',4,3,'2026 地震频次全国最高'),
 ('巴音郭楞','新疆',4,3,'2026 地震多发'),
 ('吐鲁番','新疆',4,3,'2026 地震'),
 ('和田','新疆',3,3,'南疆地震带'),
 ('阿克苏','新疆',3,3,'南疆地震带'),
 ('花莲','台湾',4,4,'2026 海域地震多发'),
 ('台东','台湾',4,4,'2026 海域地震'),
 ('昭通','云南',4,4,'2026 5级地震'),
 ('宜宾','四川',4,4,'2026 5级地震；历史震区'),
 ('甘南','甘肃',4,4,'2026 震感；邻近叠溪'),
 ('海西','青海',4,3,'2026 6.3级地震'),
 ('玉树','青海',3,4,'2010 7.1级地震'),
 ('柳州','广西',4,2,'2026 一天两次5.2级'),
 # 2026 洪涝
 ('周口','河南',4,4,'贾鲁河溃口严重内涝'),
 ('无锡','江苏',4,3,'太湖流域超标洪水'),
 ('苏州','江苏',4,3,'太湖流域；苏南内涝'),
 ('常州','江苏',4,3,'苏南洪涝'),
 ('南通','江苏',3,3,'沿江/沿海'),
 ('嘉兴','浙江',3,2,'太湖流域'),
 ('湖州','浙江',3,2,'太湖流域'),
 ('岳阳','湖南',3,3,'洞庭湖水系'),
 ('九江','江西',3,2,'鄱阳湖水系'),
 ('上饶','江西',3,2,'鄱阳湖水系'),
 ('成都','四川',3,4,'双流居民区火灾；震区'),
 ('上海','上海',3,1,'松江电动车火灾'),
 # 2026 火灾（森林草原+城市）
 ('福州','福建',3,2,'南部森林火险+沿海'),
 ('厦门','福建',3,2,'东南沿海火险'),
 ('龙岩','福建',3,2,'西部森林火险'),
 ('赣州','江西',4,2,'东南部高度火险'),
 ('南昌','江西',3,2,'大部火险'),
 ('广州','广东',3,2,'东部/南部火险'),
 ('深圳','广东',3,2,'南部火险'),
 ('汕头','广东',3,2,'东部火险+台风'),
 ('湛江','广东',3,2,'南部火险+台风'),
 ('南宁','广西',3,2,'东南部火险'),
 ('桂林','广西',3,2,'东南部火险'),
 ('呼伦贝尔','内蒙古',3,1,'东部草原火险'),
 ('兴安','内蒙古',3,1,'东部火险'),
 ('通辽','内蒙古',3,1,'东部火险'),
 ('赤峰','内蒙古',3,1,'东部火险'),
 ('大兴安岭','黑龙江',3,1,'北部森林火险'),
 ('黑河','黑龙江',3,1,'北部火险'),
 ('伊春','黑龙江',3,1,'北部火险'),
 # 百年重大灾难城市
 ('唐山','河北',1,4,'1976 7.8级 24万人遇难'),
 ('邢台','河北',1,4,'1966 6.8级地震'),
 ('汶川','四川',3,4,'2008 8.0级地震'),
 ('茂县','四川',3,4,'1933 叠溪7.5级'),
 ('北川','四川',3,4,'2008 重灾'),
 ('雅安','四川',3,4,'2013 芦山7.0级'),
 ('泸定','四川',3,4,'2022 6.8级'),
 ('舟曲','甘肃',2,4,'2010 特大泥石流'),
 ('古浪','甘肃',2,4,'1927 8.0级地震'),
 ('通海','云南',3,4,'1970 7.7级地震'),
 ('大理','云南',3,3,'地震带'),
 ('察隅','西藏',0,4,'1950 8.5级（墨脱）'),
 ('驻马店','河南',4,4,'1975 板桥溃坝 2.6万人'),
 ('天津','天津',1,3,'1939 海河大水'),
 ('哈尔滨','黑龙江',1,3,'1932 松花江大水'),
 ('武汉','湖北',2,3,'1931/1998 长江洪水'),
 ('长沙','湖南',2,3,'1931 四水洪灾'),
 ('广州','广东',3,2,'1994 西江大水+台风'),
 ('香港','香港',0,0,'无重大记录'),
 ('澳门','澳门',0,0,'无重大记录'),
]
OVR = {}
for nm, prov, l2, lc, note in CITY_OVR:
    OVR[nm] = (prov, l2, lc, note)

# ---------- 合并边界 ----------
cities = []  # {name, prov, paths, cx, cy}
for fn in sorted(os.listdir(os.path.join(BASE, 'china_cities'))):
    if not fn.endswith('.json'):
        continue
    adcode = fn.replace('.json', '')
    prov = PROV_NAME.get(adcode)
    if not prov:
        continue
    try:
        d = json.load(open(os.path.join(BASE, 'china_cities', fn), encoding='utf-8'))
    except Exception as e:
        print('  skip bad file', fn, e)
        continue
    for f in d.get('features', []):
        p = f.get('properties', {})
        nm = p.get('name', '')
        geom = f.get('geometry')
        paths = poly_paths(geom, 0.5)
        if not paths:
            continue
        c = p.get('center') or p.get('centroid')
        if c:
            cx, cy = proj(c[0], c[1])
        else:
            cx = cy = None
        cities.append({'name': nm, 'prov': prov, 'paths': paths,
                       'cx': cx, 'cy': cy, 'adcode': p.get('adcode')})

# 台湾省（从省级文件取轮廓，无县市分层）
cf = json.load(open(os.path.join(BASE, 'china_full.json'), encoding='utf-8'))
for f in cf['features']:
    if f.get('properties', {}).get('name') == '台湾省':
        paths = poly_paths(f.get('geometry'), 0.5)
        if paths:
            cities.append({'name': '台湾省', 'prov': '台湾', 'paths': paths,
                           'cx': proj(120.9, 23.7)[0], 'cy': proj(120.9, 23.7)[1],
                           'adcode': '710000', 'prov_level': True})

print('合并城市数:', len(cities))

# ---------- 计算每市级别与安全指数 ----------
def compute(c):
    nm = norm(c['name']); prov = c['prov']
    if nm in OVR:
        _p, l2, lc, note = OVR[nm]
        c['note'] = note
    else:
        l2 = LVL_2026.get(prov, 1)
        lc = LVL_CEN.get(prov, 1)
        c['note'] = ''
    c['l2'] = l2; c['l4'] = lc
    # 灾害带暴露惩罚
    pen = 0
    if prov in BELT_EQ: pen += 6
    if prov in BELT_FLOOD: pen += 5
    if prov in BELT_TYPHOON: pen += 4
    risk = 0.6 * lc * 25 + 0.4 * l2 * 25 + pen
    c['safety'] = max(0, min(100, round(100 - risk)))
    return c

for c in cities:
    compute(c)

# ---------- 调色 ----------
COL = {0:'#1E242C', 1:'#2E4757', 2:'#7A5A32', 3:'#A8552F', 4:'#C4513A'}
def svg_map(field, title):
    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
             f'font-family="Noto Sans SC, sans-serif" class="map">']
    # 背景
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#11161D"/>')
    for c in cities:
        lv = c[field]
        col = COL[lv]
        nm = norm(c['name'])
        attrs = (f'data-name="{nm}" data-prov="{c["prov"]}" data-l2="{c["l2"]}" '
                 f'data-lc="{c["l4"]}" data-safety="{c["safety"]}" data-note="{c["note"]}"')
        parts.append(f'<g class="city" {attrs}>')
        for p in c['paths']:
            parts.append(f'<path d="{p}" fill="{col}" stroke="#0C0F14" stroke-width="0.4"/>')
        parts.append('</g>')
    # 标注：L4 高危城市（避免重叠：仅标字号短的）
    labeled = [c for c in cities if c[field] == 4 and c['cx'] is not None]
    grid_seen = {}
    for c in labeled:
        gx, gy = int(c['cx'] // 22), int(c['cy'] // 14)
        if grid_seen.get((gx, gy)):
            continue
        grid_seen[(gx, gy)] = 1
        short = norm(c['name'])
        if len(short) > 4:
            short = short[:3]
        parts.append(f'<text x="{c["cx"]:.0f}" y="{c["cy"]:.0f}" font-size="9" '
                     f'fill="#FFE8E0" text-anchor="middle" pointer-events="none">{short}</text>')
    # 台湾标注花莲/台东
    parts.append(f'<text x="{(proj(121.0,23.8)[0]):.0f}" y="{(proj(121.0,23.8)[1]):.0f}" '
                 f'font-size="9" fill="#FFE8E0" text-anchor="middle" pointer-events="none">花莲·台东</text>')
    parts.append('</svg>')
    return ''.join(parts)

svg_2026 = svg_map('l2', '2026')
svg_cen = svg_map('l4', 'century')

open(os.path.join(BASE, 'city_2026.svg'), 'w', encoding='utf-8').write(svg_2026)
open(os.path.join(BASE, 'city_century.svg'), 'w', encoding='utf-8').write(svg_cen)
print('SVG 生成完成 2026:', len(svg_2026), 'century:', len(svg_cen))

# ---------- 安全城市排名（直辖市/港澳按整市聚合，不拆区）----------
MUNI = {'北京','天津','上海','重庆','香港','澳门'}
safe = [c for c in cities if (not c.get('prov_level')) and (c['prov'] not in MUNI)]
# 合成直辖市/港澳整市条目
for m in MUNI:
    lv2 = LVL_2026.get(m, 1); lvc = LVL_CEN.get(m, 1)
    pen = 0
    if m in BELT_EQ: pen += 6
    if m in BELT_FLOOD: pen += 5
    if m in BELT_TYPHOON: pen += 4
    sf = max(0, min(100, round(100 - (0.6*lvc*25 + 0.4*lv2*25 + pen))))
    safe.append({'name': m, 'prov': m, 'l2': lv2, 'l4': lvc, 'safety': sf, 'note': ''})
safe.sort(key=lambda c: (-c['safety'], c['prov']))
TOP = safe[:24]
print('\n最安全地级市/直辖市 Top:')
for c in TOP:
    print(f"  {c['name']:>6}（{c['prov']}） 安全指数 {c['safety']}  2026:L{c['l2']} 百年:L{c['l4']}")

# 保存数据供 HTML 用
data = {
 'cities': [{'name': norm(c['name']), 'prov': c['prov'], 'l2': c['l2'],
             'lc': c['l4'], 'safety': c['safety'], 'note': c['note']} for c in cities],
 'top': [{'name': c['name'], 'prov': c['prov'], 'safety': c['safety'],
          'l2': c['l2'], 'lc': c['l4'], 'note': c['note']} for c in TOP],
}
json.dump(data, open(os.path.join(BASE, 'city_data.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('city_data.json 已保存')
