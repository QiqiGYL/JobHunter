# JobHunter

职位抓取、筛选与展示工具。从 Indeed / LinkedIn 等抓取职位，按简历匹配度打分并过滤，输出 Excel；可选通过 DeepSeek 对高分职位做 ATS 分析。提供 React Web 界面查看结果并上传简历。

---

## 项目结构

```
JobHunter/
├── hunt.py                     # 入口：抓取、打分、过滤、写 xlsx
├── analyze_resume.py           # 入口：简历关键词分析
├── deepseek_ats_analyzer.py    # 入口：DeepSeek ATS 深度分析
│
├── src/                        # 核心逻辑（与入口/UI/API 解耦）
│   ├── __init__.py
│   ├── config.py               # 全局配置、路径、技能列表、YAML/JSON 加载
│   ├── resume.py               # 简历 PDF 提取、文本清洗、关键词提取与对比
│   ├── scoring.py              # 语义模型、关键词硬分、标题/位置加分、综合打分
│   ├── filters.py              # 过滤规则（经验年限、Intern/Co-op、2026 grad）
│   ├── salary.py               # 从 JD 文本中提取薪资（CA$/yr、$XXk、时薪等）
│   ├── scrape.py               # 调用 jobspy 抓取职位
│   └── ats.py                  # DeepSeek ATS 分析逻辑
│
├── api/                        # Flask 后端
│   └── app.py                  # GET /api/jobs、POST /api/resume
│
├── ui/                         # React 前端（Vite）
│   ├── src/
│   │   ├── App.jsx             # 主页面
│   │   ├── JobList.jsx         # 职位列表
│   │   ├── JobCard.jsx         # 职位卡片（含 Match Score 圆环）
│   │   └── ResumeUpload.jsx    # 简历上传
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── config/                     # 配置文件
│   ├── tech_keywords.yaml      # 技术关键词库（简历技能提取用）
│   └── job_positions.yaml      # 职位与权重配置（可选）
│
├── data/                       # 数据与输出
│   ├── uploads/                # 上传的简历（current_resume.pdf）
│   ├── job_hunt_results.xlsx   # 抓取结果（Jobs + Filtered_Out）
│   └── ats_analysis_report.md  # ATS 分析报告（若启用）
│
└── requirements.txt
```

---

## 环境与依赖

### Python（后端与脚本）

```bash
pip install -r requirements.txt
```

需要 Python 3.10+。主要依赖：pandas, openpyxl, jobspy, sentence-transformers, pdfplumber, flask 等。

### Node（前端）

```bash
cd ui
npm install
```

---

## 使用方式

### 1. 生成职位数据

```bash
python hunt.py --search "Software Engineer" --location "Canada" --results 100
```

- 默认读取根目录下 `Grace_cs3.pdf` 作为简历（可通过 `--resume-pdf` 指定）。
- 结果写入 `data/job_hunt_results.xlsx`。
- 可选：`--analyze-top 20` 对前 20 名调用 DeepSeek（需设置 `DEEPSEEK_API_KEY`）。

```bash
python hunt.py --help    # 查看所有参数
```

### 2. 启动 API

```bash
python api/app.py
```

默认 `http://localhost:5000`，提供：

| 端点                 | 方法 | 说明                                    |
|----------------------|------|-----------------------------------------|
| `/api/jobs`          | GET  | 返回 Jobs + Filtered_Out，按 score 降序 |
| `/api/resume`        | POST | 上传 PDF 简历到 data/uploads/           |
| `/api/resume/status` | GET  | 查询是否已有上传的简历                  |

### 3. 启动前端

```bash
cd ui
npm run dev
```

浏览器打开 `http://localhost:5173`。Vite 会代理 `/api` 到后端。

### 4. 使用上传的简历

```bash
python hunt.py --resume-pdf data/uploads/current_resume.pdf --results 100
```

或设置环境变量：

```bash
export RESUME_PDF=data/uploads/current_resume.pdf   # Linux/macOS
set RESUME_PDF=data\uploads\current_resume.pdf       # Windows
python hunt.py
```

### 5. 简历关键词分析（单独运行）

```bash
python analyze_resume.py --resume Grace_cs3.pdf
```

### 6. ATS 分析（单独运行）

```bash
export DEEPSEEK_API_KEY="your-key"
python deepseek_ats_analyzer.py --excel data/job_hunt_results.xlsx --resume Grace_cs3.pdf
```

---

## 配置说明

| 文件                          | 用途                                                         |
|-------------------------------|--------------------------------------------------------------|
| `config/tech_keywords.yaml`   | 技术关键词库，用于从简历中自动提取技能                       |
| `config/job_positions.yaml`   | 可选；配合 `--config`、`--position` 切换不同职位的技能与权重 |

---

## 技术栈

| 部分       | 技术                                                    |
|------------|---------------------------------------------------------|
| 抓取与打分 | Python, jobspy, pandas, sentence-transformers, rapidfuzz |
| 简历解析   | pdfplumber                                              |
| ATS 分析   | DeepSeek API (requests)                                 |
| 后端 API   | Flask                                                   |
| 前端       | React 18, Vite 5                                        |
