# JobHunter 项目进度

记录从项目开始到现在的功能与改动，便于回顾「哪天做了什么」。

---

## 一、进度总览（按模块）

| 模块 | 状态 | 说明 |
|------|------|------|
| 职位抓取与打分 (hunt.py) | ✅ 完成 | jobspy 抓取、四路评分、过滤、输出 xlsx |
| 职位配置 (job_positions.yaml) | ✅ 完成 | 多职位技能与权重，--config / --position |
| 简历解析与关键词 (analyze_resume, src/resume) | ✅ 完成 | PDF 提取、关键词分析、tech_keywords.yaml |
| ATS 深度分析 (src/ats, deepseek_ats_analyzer) | ✅ 完成 | DeepSeek 单职位分析、结构化输出、CLI 批量报告 |
| 后端 API (api/app.py) | ✅ 完成 | /api/jobs、/api/resume、/api/jobs/analyze、简历预览 |
| 前端 (ui) | ✅ 完成 | 职位列表、分页、简历上传与预览、单职位 Analysis 抽屉 |
| ATS 结果持久化 | ✅ 完成 | data/ats_analysis_cache.json，按 job 缓存，先读缓存再调 API |

---

## 二、按时间记录（新在上）

> **维护说明**：每次做功能改进或重要修改时，在本节**顶部**新增一条，格式：`日期 | 简短描述`，下面可跟 1～3 行补充。

- **2026-03-04**（续）  
  - 前端：JobCard 新增来源徽章（indeed / linkedin 等绿色小标签）和 Remote 蓝色小标签；`hunt.py` 的 OUTPUT_COLUMNS 加入 `site` 字段，下次抓取后 xlsx 里会有来源列。

- **2026-03-04**  
  - 抓取：按站点打印进度（正在抓取 indeed/linkedin…、→ 完成 N 条）；country_indeed 已在 run_scrape 中传递。  
  - 过滤：Intern/Co-op 仅看标题（避免 "Preferred: co-op experience" 误杀 Junior Engineer）；排除非软件岗（Construction Estimator、CAD Technician 等）；排除 Level 2+ / III/IV；排除 XXX Lead（Test Lead、QA Lead 等）；标题含 Junior/Entry 时不因 description 里的 Senior/Lead 排除。  
  - hunt：ATS 批量分析默认 0（--analyze-top 0），抓取完成打印 ATS 开始提示。  
  - 明日计划：将 filter 规则做成可配置（profile：毕业年份、经验范围、是否排除 Lead/Level 2+/非软件岗、banned 关键词等）。

- **2026-03-01**  
  - 抓取容错：`run_scrape` 改为按站点逐个调用 jobspy 再合并；某站（如 Indeed）出现 `RemoteDisconnected`/ConnectionError 时只打 WARNING 并跳过该站，其余站点结果照常返回，避免整次抓取崩溃。

- **2026-02-2?**  
  - 抓取：`run_scrape` 增加 `country_indeed='Canada'` 传给 jobspy，便于 Indeed 返回加拿大职位；抓取后在 hunt 中打印各站点数量 `df["site"].value_counts()` 便于排查 Indeed 是否被去重掉。

- **2026-02-26**  
  - 当前进度存入 git。  
  - 明日计划：处理 (1) LinkedIn 无 description — 在 `src/scrape.py` 中为 jobspy 增加 `linkedin_fetch_description=True`；(2) Indeed 在 xlsx 中不显示 — 排查去重逻辑（company+title 只保留一条）及是否需传 `country_indeed`。

- **2026-02-26**  
  - 新增 ATS 分析结果持久化：缓存写入 `data/ats_analysis_cache.json`，缓存键优先用 `job_url`，否则用 title+company+description 哈希；分析接口先查缓存，命中则直接返回并带 `cached: true`。  
  - 新增 `progress.md`：记录每次功能改进与日期，便于回顾开发历程。

- **2026-02-09**  
  - hunt.py：四路评分（语义 + 关键词 + 标题 + 位置）、job_positions.yaml 与 --config/--position、关键词阈值与分数调整、标题关键词扩展（Entry-Level / Early-Career / Graduate）。  
  - 见 CHANGELOG.md、IMPROVEMENTS.md。

- **（更早）**  
  - 项目初始化：职位抓取与打分、简历解析、ATS 分析脚本、Flask API、React 前端、简历上传与单职位 Analysis 抽屉等。
