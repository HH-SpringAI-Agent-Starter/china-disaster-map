# -*- coding: utf-8 -*-
"""
县级「农村粮食减产」估算生成器
================================
输入：
  - area_code.csv       五级行政区划（省/市/县/乡/村），用于取全部县级单元及其归属
  - city_data.json      每市/区灾害等级：lc=百年累计(0-4), l2=2026态势(0-4), safety=安全指数(0-96)
  - disaster_data.json  百年灾害事件（用于标注各县主要受灾类型）
输出：
  - crop_yield_county.csv   全部 2975 个县级单元的减产估算
  - yield_summary.json      省份汇总 + 全部县级单元（供页面板块嵌入）

减产率口径（科普估算，与页面安全指数同源）：
    减产率(%) = round( (0.6*lc + 0.4*l2) / 4 * 40 , 1 )
  lc/l2 取值 0–4；重灾区(4/4)封顶 40%。仅衡量自然灾害暴露导致的减产风险，
  不含真实产量、作物品种、防灾工程与田间管理。
"""
import json, csv, os, collections

BASE = os.path.dirname(os.path.abspath(__file__))
AREA = r'C:/Users/Administrator/Desktop/ai数据库/area_code.csv'

cdata = json.load(open(os.path.join(BASE, 'city_data.json'), encoding='utf-8'))
ddata = json.load(open(os.path.join(BASE, 'disaster_data.json'), encoding='utf-8'))
top = cdata['top']; allc = cdata['cities']

# ---------- 1. 行政区划层级（code -> row, 并向上找省/市） ----------
rows = {}
with open(AREA, encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        rows[r['code']] = r

def ancestors(code):
    """返回 (省名, 市名) 通过 pcode 链向上爬。"""
    prov = city = None
    cur = rows.get(code)
    seen = 0
    while cur and seen < 6:
        lvl = cur['level']
        if lvl == '1':
            prov = cur['name']
        elif lvl == '2':
            city = cur['name']
        p = cur['pcode']
        if not p or p == '0' or p == cur['code']:
            break
        cur = rows.get(p)
        seen += 1
    return prov, city

def strip(n):
    """去掉行政后缀，便于跨源匹配：郑州市->郑州, 市辖区->市辖区。"""
    return n.rstrip('市州区县省自治州地区盟')

# ---------- 2. city_data 查找表 ----------
city_by_strip = {}
for c in allc:
    city_by_strip.setdefault(strip(c['name']), c)
prov_agg = collections.defaultdict(list)
for c in allc:
    prov_agg[strip(c['prov'])].append(c)

MUNI = {'北京', '上海', '天津', '重庆'}

def profile(prov, cityname):
    """返回 (lc, l2, safety, note) 用于某县。优先匹配所属市，否则用全省均值。"""
    ps = strip(prov)
    if ps in MUNI:
        cs = prov_agg.get(ps, [])
        if cs:
            return (round(sum(x['lc'] for x in cs)/len(cs), 1),
                    round(sum(x['l2'] for x in cs)/len(cs), 1),
                    round(sum(x['safety'] for x in cs)/len(cs), 1), '')
    base = strip(cityname) if cityname else ''
    if base and base in city_by_strip:
        c = city_by_strip[base]
        return (c['lc'], c['l2'], c['safety'], c.get('note', '') or '')
    cs = prov_agg.get(ps, [])
    if cs:
        return (round(sum(x['lc'] for x in cs)/len(cs), 1),
                round(sum(x['l2'] for x in cs)/len(cs), 1),
                round(sum(x['safety'] for x in cs)/len(cs), 1), '')
    return (0, 0, 96, '')  # 无数据省份，按基本无灾害处理

# ---------- 3. 主要受灾类型（按省/市聚合灾害事件计数） ----------
prov_events = collections.defaultdict(collections.Counter)
city_events = collections.defaultdict(collections.Counter)
for e in ddata['events']:
    prov_events[strip(e['region'])][e['type']] += 1
    if e.get('city'):
        city_events[strip(e['city'])][e['type']] += 1

def main_disaster(prov, cityname):
    base = strip(cityname) if cityname else ''
    if base and city_events.get(base):
        return city_events[base].most_common(1)[0][0]
    if prov_events.get(strip(prov)):
        return prov_events[strip(prov)].most_common(1)[0][0]
    return '无显著记录'

# ---------- 4. 减产率模型 ----------
def reduction_pct(lc, l2):
    return round((0.6 * lc + 0.4 * l2) / 4 * 40, 1)

def risk_tier(r):
    if r >= 25: return '高风险'
    if r >= 15: return '中风险'
    if r >= 5:  return '较低风险'
    return '基本无影响'

# ---------- 5. 遍历县级单元 ----------
out = []
for code, r in rows.items():
    if r['level'] != '3':
        continue
    prov, city = ancestors(code)
    if not prov:
        continue
    lc, l2, safety, note = profile(prov, city)
    red = reduction_pct(lc, l2)
    out.append({
        'code': code,
        'name': r['name'],
        'prov': prov,
        'city': city or '',
        'lc': lc,
        'l2': l2,
        'safety': safety,
        'yield_reduction_pct': red,
        'risk_tier': risk_tier(red),
        'main_disaster': main_disaster(prov, city),
        'note': note,
    })

out.sort(key=lambda x: (-x['yield_reduction_pct'], x['prov'], x['name']))

# ---------- 6. 写 CSV ----------
csv_path = os.path.join(BASE, 'crop_yield_county.csv')
fields = ['code', 'name', 'prov', 'city', 'lc', 'l2', 'safety',
          'yield_reduction_pct', 'risk_tier', 'main_disaster', 'note']
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(out)
print('crop_yield_county.csv', len(out), 'rows ->', csv_path)

# ---------- 7. 汇总（供页面板块） ----------
prov_stat = collections.defaultdict(lambda: {'n': 0, 'sum': 0.0, 'high': 0, 'mid': 0})
for o in out:
    p = prov_stat[o['prov']]
    p['n'] += 1
    p['sum'] += o['yield_reduction_pct']
    if o['yield_reduction_pct'] >= 25: p['high'] += 1
    elif o['yield_reduction_pct'] >= 15: p['mid'] += 1
provinces = []
for prov, p in prov_stat.items():
    provinces.append({'prov': prov, 'counties': p['n'],
                      'avg': round(p['sum'] / p['n'], 1),
                      'high': p['high'], 'mid': p['mid']})
provinces.sort(key=lambda x: -x['avg'])

top_n = out[:20]
summary = {
    'updated': ddata.get('meta', {}).get('updated', '2026-09'),
    'method': '减产率(%) = (0.6×百年等级lc + 0.4×2026态势l2) / 4 × 40，封顶 40%；lc/l2 取自 city_data.json（0–4）。属自然灾害暴露科普估算，非真实产量。',
    'counties_total': len(out),
    'provinces': provinces,
    'top': top_n,
    'counties': out,
}
json.dump(summary, open(os.path.join(BASE, 'yield_summary.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('yield_summary.json provinces:', len(provinces), '| top high-risk prov:',
      provinces[0]['prov'], provinces[0]['avg'])
