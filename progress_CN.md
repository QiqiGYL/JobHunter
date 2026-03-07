# JobHunter 项目进度

记录从项目开始到现在的功能与改动，便于回顾「哪天做了什么」。

PS: 更早记录的IMPROVEMENTS.md，CHANGELOG.md跟KEYWORD_ANALYSIS_GUIDE.md都放在JobHunter_old文件夹里了

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

- **2026-03-07**（续）
  - UI：简历上传区域改进——选择文件后在 `Choose PDF` 旁显示文件名标签（含 × 取消按钮），可随时清除选择；上传成功/失败/错误提示均随界面语言切换（中英文）。
  - 修复：英文界面下"未选择文件"等错误提示之前仍显示中文，现已全部翻译。
  - 清理仓库：删除 `CHANGELOG.md`、`IMPROVEMENTS.md`、`.github/copilot-instructions.md`；`.gitignore` 补充 `data/` 生成文件。
  - 全部 Python 源码注释和 docstring 改为英文（`src/`、`api/app.py`、`hunt.py`）。
  - UI：新增中英文切换按钮（右上角固定，`[EN|CN]` 分段样式）；DeepSeek key 未设置时 Analysis 按钮显示友好提示而非原始报错。
  - 新增 `progress_en.md`（英文版进度日志）；`README.md` 改写为英文，新增 `README_CN.md`。

- **2026-03-07**  
  - 抓取：LinkedIn 现在抓取完整职位描述（`linkedin_fetch_description=True`）；通过 `RESULTS_PER_SITE` 控制各站点数量（indeed=100, linkedin=30）；`--results` 默认值降为 30。 
  - 打分：`tech_keywords.yaml` 从 77 个关键词扩展到 160+ 个（前端、后端、云/DevOps、AI/ML、工具）；修复 `resume.py` 中含 `.` 或 `/` 的关键词（如 React.js、CI/CD）匹配问题。
  - 过滤：`Associate` 加入 `ENTRY_LEVEL`（修复 TD Associate SWE 被误筛的问题）；`Mechanical Engineer` 和 `Electrical Engineer` 加入 `NON_SOFTWARE_TITLE`；扩展非软件岗排除范围（环境、医疗、会计、体力劳动等）。 
  - 配置：简历自动优先选择上传的 PDF（`data/uploads/current_resume.pdf`），没有则用 `Grace_cs3.pdf`。
  - 前端：header 改为绿色渐变设计并加入简历上传栏；删除标题和按钮中的 emoji；Match Score 圆圈固定在右侧且垂直对齐；每个职位卡片新增来源徽章（indeed/linkedin）和 Remote 徽章。

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
  - 不记得做的时间了
  - 抓取：`run_scrape` 增加 `country_indeed='Canada'` 传给 jobspy，便于 Indeed 返回加拿大职位；抓取后在 hunt 中打印各站点数量 `df["site"].value_counts()` 便于排查 Indeed 是否被去重掉。

- **2026-02-26**  
  - 当前进度存入 git。  
  - 明日计划：处理 (1) LinkedIn 无 description — 在 `src/scrape.py` 中为 jobspy 增加 `linkedin_fetch_description=True`；(2) Indeed 在 xlsx 中不显示 — 排查去重逻辑（company+title 只保留一条）及是否需传 `country_indeed`。

- **2026-02-26**  
  - 新增 ATS 分析结果持久化：缓存写入 `data/ats_analysis_cache.json`，缓存键优先用 `job_url`，否则用 title+company+description 哈希；分析接口先查缓存，命中则直接返回并带 `cached: true`。  
  - 新增 `progress.md`：记录每次功能改进与日期，便于回顾开发历程。

- **2026-02-09**  
  - 评分系统升级：3-component → 4-component，具体权重对比如下：

    | 组件 | 旧权重（3-component） | 新权重（4-component） | 变化 |
    |------|----------------------|----------------------|------|
    | 语义相似度 | 60% | 40% | ↓ 20% |
    | 关键词匹配 | 30% | 35% | ↑ 5% |
    | 标题加分 | 10% | 15% | ↑ 5% |
    | 位置加分 | — | 10% | ✨ 新增 |

  - 关键词匹配：阈值从 80% 降到 75%，分值从 20 → 25，更容易命中。  
  - 标题关键词扩展：新增 "Entry-Level"、"Early-Career"、"Graduate"。  
  - 新增位置加分：Toronto/Mississauga +10，Ontario +5。  
  - 新增 `job_positions.yaml` 配置文件，支持 `--config` / `--position` 切换 backend / frontend / data 等预设。  
  - 新函数：`_load_config_file()`、`_location_bonus()`、`load_skill_config()`。  
  - 新增文档：`IMPROVEMENTS.md`（改进说明）、`QUICK_REFERENCE.sh`（常用命令参考）。  
  - 版本标记：v2（四路评分 + 配置支持）。

- **（更早 · 项目初始化）**  
  - 用 `jobspy` 抓取 Indeed / LinkedIn 职位，输出 `job_hunt_results.xlsx`。  
  - 用 `sentence-transformers`（all-MiniLM-L6-v2）做语义相似度打分，`rapidfuzz` 做关键词模糊匹配。  
  - 用 `pdfplumber` 解析简历 PDF，提取技能关键词（`analyze_resume.py`）。  
  - `deepseek_ats_analyzer.py`：调用 DeepSeek API 对单职位做 ATS 深度分析，输出结构化报告。  
  - `api/app.py`（Flask）：`/api/jobs`、`/api/resume`、`/api/jobs/analyze`、简历 PDF 预览接口。  
  - `ui/`（React + Vite + Ant Design）：职位列表、分页、简历上传与预览、单职位 Analysis 抽屉。
