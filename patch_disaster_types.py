# -*- coding: utf-8 -*-
"""补录偏少灾害类型（泥石流 / 雪灾）的真实历史重大事件。
所有事件均经公开权威来源核实（中国政府网、人民网、央视网、中国新闻网、中国气象局等），
仅补年份/月份/城市齐全、能落到具体地点的条目；月份为事件峰值月。
去重键：(year, month, type, region, city)，避免重复追加。"""
import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(BASE, 'disaster_data.json')
d = json.load(open(P, encoding='utf-8'))
evs = d['events']

# 去重：已存在的 (year, month, type, region, city)
seen = set((e['year'], e['month'], e['type'], e.get('region'), e.get('city')) for e in evs)

NEW = [
    # ---------------- 泥石流 ----------------
    {"year":2013,"month":7,"type":"泥石流","region":"四川","city":"都江堰",
     "detail":"7月10日都江堰中兴镇三溪村特大型高位滑坡泥石流，最终26人遇难、123人失踪",
     "level":4,"source":"中国政府网、人民网"},
    {"year":2019,"month":8,"type":"泥石流","region":"四川","city":"汶川",
     "detail":"8·20 强降雨特大山洪泥石流，汶川、理县、茂县等多地受灾，最终12人遇难、26人失联",
     "level":4,"source":"央视网"},
    {"year":2010,"month":8,"type":"泥石流","region":"四川","city":"绵竹",
     "detail":"8·13 绵竹清平乡特大山洪泥石流（冲出量约600万方，规模超舟曲3倍），因预警及时仅数人遇难；映秀红椿沟泥石流堵断岷江、213国道中断",
     "level":3,"source":"中国水利报、央视网"},
    {"year":2012,"month":6,"type":"泥石流","region":"四川","city":"宁南",
     "detail":"6·28 白鹤滩矮子沟特大山洪泥石流，水电站施工区38人失踪、3人遇难",
     "level":4,"source":"央视网、中国新闻网"},
    {"year":2014,"month":7,"type":"泥石流","region":"云南","city":"福贡",
     "detail":"7月9日福贡县匹河乡沙瓦村泥石流冲毁硅矿厂，17人失踪、1人受伤",
     "level":3,"source":"中国新闻网"},
    {"year":2017,"month":6,"type":"泥石流","region":"四川","city":"茂县",
     "detail":"6·24 茂县叠溪镇新磨村高位山体垮塌（高位滑坡），村庄被掩埋，10人遇难、93人失联",
     "level":4,"source":"央视网"},
    # ---------------- 雪灾 ----------------
    {"year":2021,"month":11,"type":"雪灾","region":"内蒙古","city":"通辽",
     "detail":"11月5日起通辽遭遇有气象记录以来最强暴风雪，最大积雪68厘米，直接经济损失超3.5亿元",
     "level":3,"source":"人民网、中国新闻网"},
    {"year":2019,"month":1,"type":"雪灾","region":"青海","city":"玉树",
     "detail":"1月以来玉树州特重雪灾，5.8万人受灾、2.1万头（只）牲畜死亡",
     "level":3,"source":"央视网、中国新闻网"},
    {"year":2018,"month":1,"type":"雪灾","region":"湖南","city":"长沙",
     "detail":"1月24–29日中东部三轮低温雨雪冰冻，湘鄂皖等10省受灾、341.9万人受灾，湖南为主要重灾区之一",
     "level":3,"source":"中国气象局、民政部"},
    {"year":2023,"month":12,"type":"雪灾","region":"河南","city":"郑州",
     "detail":"12月华北黄淮强降雪，郑州发布暴雪红色预警、山东文登积雪破纪录，多地气温创1961年以来同期最低",
     "level":3,"source":"中国气象局"},
    {"year":2009,"month":11,"type":"雪灾","region":"河北","city":"石家庄",
     "detail":"11月9–12日北方罕见暴雪，石家庄积雪55厘米破1955年以来纪录，华北多省达60年一遇",
     "level":3,"source":"中国新闻网、中国气象局"},
]

added = 0
for e in NEW:
    k = (e['year'], e['month'], e['type'], e['region'], e['city'])
    if k in seen:
        print("SKIP dup:", e['year'], e['type'], e['city'])
        continue
    evs.append(e); seen.add(k); added += 1
    print("ADD:", e['year'], e['type'], e['region'], e['city'])

d['events'] = evs
open(P, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2))
print("\nadded:", added, "| total events:", len(evs))

from collections import Counter
print("type counts:", dict(Counter(e['type'] for e in evs).most_common()))
print("month:null:", sum(1 for e in evs if e.get('month') in (None, '')))
