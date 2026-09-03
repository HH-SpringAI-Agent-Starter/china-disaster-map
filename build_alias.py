# -*- coding: utf-8 -*-
"""构建"事件城市 → 地图节点"的回退别名表 city_alias.json。

背景：灾害事件里的 city 可能是 县级市/县/自治州/直辖市整市，
而地图 SVG 的节点是 地级行政区（自治州用民族全称，如「甘孜藏族」）+ 直辖市的市辖区。
直接按名匹配会漏掉这些事件，导致地图上不亮。

本脚本产出三种映射，供页面高亮时逐级回退：
  1) 县 / 县级市 / 区 / 旗  ->  所属地级节点（来自 area_code.csv 五级区划）
  2) 自治州 / 地级市短名    ->  地图上的全称节点（前缀匹配，如「玉树」->「玉树藏族」）
  3) 直辖市整名            ->  该市全部市辖区节点（北京/上海/天津/重庆）
"""
import json, re, csv, os

BASE = os.path.dirname(os.path.abspath(__file__))
AREA = r"C:\Users\Administrator\Desktop\ai数据库\area_code.csv"

# ---------- 1. 读地图节点 ----------
svg = open(os.path.join(BASE, 'city_2026.svg'), encoding='utf-8').read()
pairs = re.findall(r'data-name="([^"]+)"[^>]*data-prov="([^"]+)"', svg)
NODES = [n for n, _ in pairs]
NODESET = set(NODES)
PROV_OF = {n: p for n, p in pairs}
print("地图节点数:", len(NODES))

# 直辖市：地图按市辖区拆分，整市名需要展开
MUNI = {'北京', '上海', '天津', '重庆'}
MUNI_NODES = {m: [n for n, p in pairs if p == m] for m in MUNI}
for m in MUNI:
    print(f"  {m} 展开为 {len(MUNI_NODES[m])} 个区节点")

# 短名 -> 全称节点（前缀匹配，用于自治州）
PREFIX = {}
for n in NODES:
    for k in (2, 3, 4):
        if len(n) > k:
            PREFIX.setdefault(n[:k], set()).add(n)


def resolve(name):
    """把一个地名解析成地图节点列表（已存在则原样返回）。"""
    if name in NODESET:
        return [name]
    if name in MUNI_NODES:
        return MUNI_NODES[name]
    # 自治州 / 地级市短名 -> 全称节点（如 玉树 -> 玉树藏族）
    cand = PREFIX.get(name)
    if cand:
        return sorted(cand)
    return None


# ---------- 2. 读五级区划，建 县 -> 地级 映射 ----------
code2 = {}
if os.path.exists(AREA):
    with open(AREA, encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            if row['level'] in ('1', '2', '3'):
                code2[row['code']] = (row['name'], row['level'], row['pcode'])
print("区划索引行数:", len(code2))

SUFFIX = re.compile(r'(自治州|自治县|自治旗|地区|盟|特区|林区|新区|市|县|区|旗)$')


def strip_name(s):
    return SUFFIX.sub('', s)


county2pref = {}   # 县短名 -> 地级原名
for code, (nm, lv, pc) in code2.items():
    if lv != '3':
        continue
    if len(pc) == 12:
        pcode = pc[:4] + '00000000'
        if pcode in code2:
            pname = code2[pcode][0]
            # 直辖市的 level2 是「市辖区」，直接用省名
            if pname in ('市辖区', '县'):
                pcode2 = pc[:2] + '0000000000'
                pname = code2.get(pcode2, (pname,))[0]
            # 原名与去后缀名都注册，避免「茂县」被切成「茂」而失配
            for k in {nm, strip_name(nm)}:
                if len(k) >= 2:
                    county2pref.setdefault(k, set()).add(pname)
print("县->地级 映射条数:", len(county2pref))

# ---------- 3. 生成别名表 ----------
alias = {}


def put(key, targets):
    if not targets:
        return
    for k in {key, strip_name(key)}:
        if len(k) < 2:
            continue
        if k in NODESET and targets == [k]:
            continue    # 已能直接命中，不需要别名
        cur = alias.get(k)
        merged = sorted(set(cur or []) | set(targets))
        if cur is None or merged != cur:
            alias[k] = merged


# 3a. 县 / 县级市 -> 所属地级节点
for county, prefs in county2pref.items():
    tg = []
    for p in prefs:
        r = resolve(strip_name(p))
        if r:
            tg.extend(r)
    if tg:
        put(county, tg)

# 3b. 自治州 / 地级市短名 -> 全称节点
# 地图节点名形如「巴音郭楞蒙古」「阿坝藏族羌族」「西双版纳傣族」，
# 事件里常写短名（巴音郭楞 / 阿坝 / 西双版纳），此处剥离民族后缀建立短名映射。
ETH = (r'(?:藏族|羌族|彝族|回族|蒙古族|蒙古|维吾尔|壮族|苗族|侗族|布依族|朝鲜族|土家族|白族|'
       r'哈尼族|哈萨克|傈僳族|傣族|景颇族|柯尔克孜|塔吉克|裕固族|撒拉族|门巴族|珞巴族|基诺族|'
       r'德昂族|阿昌族|普米族|怒族|独龙族|纳西族|拉祜族|佤族|畲族|瑶族|黎族|水族|仡佬族|京族|'
       r'毛南族|仫佬族|锡伯族|达斡尔族|鄂温克|鄂伦春|赫哲族|俄罗斯族|乌孜别克|满族|各族)')
for n in NODES:
    base = re.sub(ETH + r'.*$', '', n)
    if base and base != n:
        put(base, [n])

# 3c. 直辖市整市及其市辖区 -> 用「@省名」标记，运行时按省展开（避免 86 条重复存区名）
for m, nodes in MUNI_NODES.items():
    if not nodes:
        continue
    alias[m] = '@' + m
    for n in nodes:
        alias[n] = '@' + m
        alias[n + '区'] = '@' + m

# 3d. 台湾各县市 -> 台湾节点（地图为整省一个节点）
if '台湾' in NODESET:
    for c in ('台北', '高雄', '台中', '台南', '台东', '宜兰', '花莲', '彰化', '屏东', '云林',
              '苗栗', '嘉义', '新竹', '南投', '基隆', '桃园', '澎湖', '金门', '连江'):
        alias.setdefault(c, '台湾')

# ---------- 4. 输出（紧凑格式：值为「节点1,节点2」或「@省名」）----------
out = os.path.join(BASE, 'city_alias.json')
compact = {}
for k, v in alias.items():
    compact[k] = v if isinstance(v, str) else ','.join(v)
json.dump(compact, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
raw = json.dumps(compact, ensure_ascii=False, separators=(',', ':'))
print("\n别名表条数:", len(compact), "| 紧凑体积:", len(raw.encode('utf-8')), "字节 ->", out)

# ---------- 5. 自检：现有事件的城市命中率 ----------
evs = json.load(open(os.path.join(BASE, 'disaster_data.json'), encoding='utf-8'))['events']


def resolve_event(city):
    if not city:
        return None
    if city in NODESET:
        return [city]
    a = alias.get(city)
    if a:
        if isinstance(a, list):
            return a
        return MUNI_NODES.get(a[1:]) if a.startswith('@') else a.split(',')
    return resolve(city)


miss = sorted(set(e['city'] for e in evs if e['city'] and not resolve_event(e['city'])))
hit_cities = sorted(set(e['city'] for e in evs if e['city'] and resolve_event(e['city'])))
print(f"可命中城市 {len(hit_cities)} 个 | 仍无法命中 {len(miss)} 个: {miss or '无'}")
for c in ('都江堰', '汶川', '绵竹', '宁南', '茂县', '福贡', '玉树', '舟曲', '漳浦', '通海',
          '兴海', '察隅', '彭水', '古浪', '台东', '宜兰', '花莲', '北京', '上海', '重庆', '甘孜'):
    print(f"  {c:5s} -> {resolve_event(c)}")
