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

- **2026-02-14**  
  - 当前进度存入 git。  
  - 明日计划：处理 (1) LinkedIn 无 description — 在 `src/scrape.py` 中为 jobspy 增加 `linkedin_fetch_description=True`；(2) Indeed 在 xlsx 中不显示 — 排查去重逻辑（company+title 只保留一条）及是否需传 `country_indeed`。

- **2026-02-26**  
  - 新增 ATS 分析结果持久化：缓存写入 `data/ats_analysis_cache.json`，缓存键优先用 `job_url`，否则用 title+company+description 哈希；分析接口先查缓存，命中则直接返回并带 `cached: true`。  
  - 新增 `progress.md` 与 Cursor 规则：功能改进时自动更新本文件并带日期。

- **2026-02-09**  
  - hunt.py：四路评分（语义 + 关键词 + 标题 + 位置）、job_positions.yaml 与 --config/--position、关键词阈值与分数调整、标题关键词扩展（Entry-Level / Early-Career / Graduate）。  
  - 见 CHANGELOG.md、IMPROVEMENTS.md。

- **（更早）**  
  - 项目初始化：职位抓取与打分、简历解析、ATS 分析脚本、Flask API、React 前端、简历上传与单职位 Analysis 抽屉等。
