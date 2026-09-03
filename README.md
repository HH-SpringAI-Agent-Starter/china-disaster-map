# 中国自然灾害分布图 · 城市级（可按年月检索）

基于自然资源部标准地图（DataV GeoAtlas）绘制的中国地级市自然灾害分级填色图，
覆盖 **1926–2026 百年** 时空分布，并支持 **按年份 / 月份 / 灾害类型 / 关键词检索**，
可在地图上联动高亮命中城市。

> ⚠️ 底图含台湾省、南海诸岛及断续线，依国家标准示意呈现；色阶为相对灾害强度示意，**非精确统计**。

## 在线查看

- GitHub Pages（实时更新）：https://hh-springai-agent-starter.github.io/china-disaster-map/
- 或直接打开仓库根目录的 `disaster_map_city.html`（双击即可，离线使用内置数据）

## 功能

- **双栏地图**：左为 2026 年当前态势，右为 1926–2026 百年累计（频次＋伤亡）分级填色
- **年月检索**：顶部下拉框选年份 / 月份 / 灾害类型，输入关键词，下方时间轴即时过滤
- **地图联动**：筛选后自动高亮命中的地级市，其余置灰
- **安全指数面板**：给出“最安全 / 最适合发展”城市梯队（仅衡量自然灾害暴露度）
- **数据自动更新**：页面加载时拉取 `disaster_data.json` 最新版；离线则回退内置数据

## 每年如何更新

本图的数据与代码分离，**每年只需追加一页数据，无需改代码**：

1. 编辑 `disaster_data.json` 的 `events` 数组，按现有格式追加该年灾害事件：

   ```json
   { "year": 2027, "month": 7, "type": "洪涝", "region": "广东", "city": "广州",
     "detail": "……", "level": 3, "source": "……" }
   ```

   - `city` 用**地级市短名**（如“广州”“柳州”），须与地图图名一致才能联动高亮；
     流域/省级层面的事件 `city` 留空 `""` 即可。
   - `month` 未知填 `null`。
2. 提交并推送到 `main` 分支：

   ```bash
   git add disaster_data.json
   git commit -m "add 2027 disaster events"
   git push
   ```

3. GitHub Pages 会在数分钟内自动 rebuild，公开页面即反映最新数据。

## 文件结构

| 文件 | 说明 |
|------|------|
| `disaster_map_city.html` | 成品页面（自包含，含双地图 + 搜索 + 安全面板） |
| `disaster_data.json` | **唯一数据源**：灾害事件（年月可检索）+ 元数据 |
| `city_data.json` | 各城市分级与安全指数（由 `gen_city_map.py` 生成） |
| `gen_map.py` | 省级地图 SVG 生成（早期版本） |
| `gen_city_map.py` | 地级市地图 SVG 生成（合并边界 + 安全指数） |
| `gen_html_city.py` | 由 SVG + 数据生成成品 HTML |

## 重新生成地图（可选）

如需重绘底图，先下载标准边界（见 `.gitignore` 中排除的 `china_cities/`），再运行生成脚本：

```bash
python gen_city_map.py     # 生成 city_2026.svg / city_century.svg / city_data.json
python gen_html_city.py    # 生成 disaster_map_city.html
```

## 合规与免责

- 底图依据自然资源部标准地图（DataV GeoAtlas）绘制，台湾省为中国领土不可分割的一部分，
  南海诸岛及断续线依国家标准示意呈现。
- 城市级安全指数仅衡量自然灾害暴露度（地震带 / 七大流域中下游 / 台风沿海），
  **不含经济、人口、基础设施与防灾能力**，不作选址或投资决策依据。
- 数据来自公开灾害年鉴、年度灾情通报及用户整理的年表，属科普示意。
