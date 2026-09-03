import json, math

with open('china_full.json', encoding='utf-8') as f:
    main = json.load(f)
with open('china_boundary.json', encoding='utf-8') as f:
    boundary = json.load(f)

# 省级简称映射
SHORT = {
    '新疆维吾尔自治区':'新疆','西藏自治区':'西藏','内蒙古自治区':'内蒙古','广西壮族自治区':'广西',
    '宁夏回族自治区':'宁夏','黑龙江省':'黑龙江','吉林省':'吉林','辽宁省':'辽宁','河北省':'河北',
    '北京市':'北京','天津市':'天津','山西省':'山西','山东省':'山东','河南省':'河南','江苏省':'江苏',
    '安徽省':'安徽','上海市':'上海','浙江省':'浙江','福建省':'福建','江西省':'江西','湖南省':'湖南',
    '湖北省':'湖北','广东省':'广东','海南省':'海南','台湾省':'台湾','香港特别行政区':'香港',
    '澳门特别行政区':'澳门','甘肃省':'甘肃','青海省':'青海','陕西省':'陕西','四川省':'四川',
    '重庆市':'重庆','云南省':'云南','贵州省':'贵州',
}

LEVELS_2026 = {
    '新疆':4,'黑龙江':2,'吉林':1,'辽宁':1,'内蒙古':2,'北京':0,'天津':1,'河北':1,'山东':0,
    '江苏':3,'青海':3,'甘肃':2,'宁夏':0,'山西':0,'河南':4,'安徽':1,'上海':2,'浙江':1,
    '西藏':0,'四川':3,'陕西':2,'重庆':1,'湖北':2,'江西':3,'福建':3,'台湾':3,'云南':3,
    '贵州':1,'湖南':2,'广西':3,'广东':2,'香港':0,'澳门':0,'海南':1,
}
LEVELS_CENTURY = {
    '新疆':3,'黑龙江':3,'吉林':2,'辽宁':2,'内蒙古':2,'北京':1,'天津':1,'河北':4,'山东':2,
    '江苏':3,'青海':2,'甘肃':4,'宁夏':1,'山西':2,'河南':4,'安徽':3,'上海':1,'浙江':2,
    '西藏':3,'四川':4,'陕西':4,'重庆':2,'湖北':3,'江西':3,'福建':3,'台湾':2,'云南':3,
    '贵州':2,'湖南':3,'广西':2,'广东':2,'香港':0,'澳门':0,'海南':1,
}

FILL = {0:'#1E242C',1:'#2E4757',2:'#7A5A32',3:'#A8552F',4:'#C4513A'}

W, H = 720, 430
LON0, LON1, LAT0, LAT1 = 73.0, 135.5, 17.8, 53.8

def proj(lon, lat):
    x = (lon - LON0) / (LON1 - LON0) * W
    y = (LAT1 - lat) / (LAT1 - LAT0) * H
    return x, y

def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    dmax, idx = 0, 0
    x1, y1 = pts[0]; x2, y2 = pts[-1]
    dx, dy = x2-x1, y2-y1
    norm = math.hypot(dx, dy) or 1
    for i in range(1, len(pts)-1):
        x0, y0 = pts[i]
        dist = abs(dy*x0 - dx*y0 + x2*y1 - y2*x1) / norm
        if dist > dmax:
            dmax, idx = dist, i
    if dmax > eps:
        return rdp(pts[:idx+1], eps) + rdp(pts[idx:], eps)[1:]
    return [pts[0], pts[-1]]

def ring_to_path(ring):
    raw = [tuple(int(round(v)) for v in proj(lon, lat)) for lon, lat in ring]
    if raw and raw[0] == raw[-1]:
        raw = raw[:-1]
    pts = rdp(raw, 0.55)
    if len(pts) < 3:
        pts = raw
    if len(pts) < 3:
        return ''
    d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts) + 'Z'
    return d

def centroid(ring):
    xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
    return (sum(xs)/len(xs), sum(ys)/len(ys))

def build(levels):
    paths = []
    labels = []
    for feat in main['features']:
        name = feat['properties'].get('name', '')
        short = SHORT.get(name)
        if short is None:
            continue
        lvl = levels.get(short, 0)
        fill = FILL[lvl]
        geom = feat['geometry']
        if geom is None:
            continue
        gtype = geom['type']
        coords = geom['coordinates']
        polys = coords if gtype == 'MultiPolygon' else [coords]
        dparts = []
        best_c = None; best_area = -1
        for poly in polys:
            for ring in poly:
                d = ring_to_path(ring)
                if d:
                    dparts.append(d)
                # area proxy for label placement (largest ring)
                a = abs(sum((ring[i][0]*ring[(i+1)%len(ring)][1]-ring[(i+1)%len(ring)][0]*ring[i][1]) for i in range(len(ring))))
                if a > best_area:
                    best_area = a; best_c = centroid(ring)
        if dparts:
            paths.append(f'<path d="{"".join(dparts)}" fill="{fill}" stroke="#0E1218" stroke-width="1" stroke-linejoin="round"/>')
        if best_c:
            cx, cy = proj(*best_c)
            tfill = '#FFFFFF' if lvl >= 2 else '#9AA6B2'
            fs = 13 if short not in ('北京','天津','上海','香港','澳门','宁夏','海南') else 11
            labels.append(f'<text x="{cx:.0f}" y="{cy+4:.0f}" font-size="{fs}" font-family="Noto Sans SC, sans-serif" font-weight="600" fill="{tfill}" text-anchor="middle">{short}</text>')
    # 南海诸岛 inset（使用国界文件中的真实断续线/岛礁几何）
    ix0, iy0, iw, ih = 515, 300, 195, 118
    inset = [f'<rect x="{ix0}" y="{iy0}" width="{iw}" height="{ih}" rx="6" fill="#141A22" stroke="#2A323C" stroke-width="1"/>']
    def insetXY(lon, lat):
        x = ix0 + (lon-106)/(125-106)*iw
        y = iy0 + (22-lat)/(22-3)*ih
        return x, y
    bpolys = boundary['features'][0]['geometry']['coordinates']
    for poly in bpolys:
        for ring in poly:
            lats = [p[1] for p in ring]
            if not lats or min(lats) >= 17:
                continue
            rdp_ring = rdp([tuple(int(round(v)) for v in insetXY(lon, lat)) for lon, lat in ring], 0.8)
            if len(rdp_ring) < 3:
                rdp_ring = [tuple(int(round(v)) for v in insetXY(lon, lat)) for lon, lat in ring]
            dd = 'M' + ' L'.join(f'{x} {y}' for x, y in rdp_ring) + 'Z'
            inset.append(f'<path d="{dd}" fill="#7E8A98" fill-opacity="0.25" stroke="#7E8A98" stroke-width="1.3" stroke-linejoin="round"/>')
    inset.append(f'<text x="{ix0+iw/2:.0f}" y="{iy0+ih-8:.0f}" font-size="11" font-family="Noto Sans SC, sans-serif" fill="#9AA6B2" text-anchor="middle">南海诸岛</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           + ''.join(paths) + ''.join(labels) + ''.join(inset) + '</svg>')
    return svg

for tag, lv in (('map_2026', LEVELS_2026), ('map_century', LEVELS_CENTURY)):
    svg = build(lv)
    with open(tag + '.svg', 'w', encoding='utf-8') as f:
        f.write(svg)
    print(tag, 'chars=', len(svg))
