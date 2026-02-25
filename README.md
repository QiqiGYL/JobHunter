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

## 如何运行（快速开始）

1. **安装依赖**
   - 项目根目录：`pip install -r requirements.txt`
   - 前端：`cd ui && npm install`

2. **配置 DeepSeek（可选，用于 ATS 分析）**
   - 复制 `.env.example` 为 `.env`，在 `.env` 中填写 `DEEPSEEK_API_KEY=你的key`
   - 不配置也可运行；仅在使用「跑 hunt 时顺带 ATS」或网页上「Analysis」按钮时需要

3. **启动后端**（终端 1）
   ```bash
   python api/app.py
   ```
   看到 `Running on http://127.0.0.1:5000` 即表示成功。

4. **启动前端**（终端 2）
   ```bash
   cd ui
   npm run dev
   ```
   浏览器打开 **http://localhost:5173**。前端会通过 Vite 代理访问后端 `/api`。

5. **（可选）生成职位数据**
   ```bash
   python hunt.py --search "Software Engineer" --location "Canada" --results 100
   ```
   会生成 `data/job_hunt_results.xlsx`，刷新网页即可在「保留的职位 / 已筛除」Tab 中查看；上传简历后可使用「当前简历」预览和每个职位卡片的「Analysis」做 ATS 分析。

---

## 环境与依赖

### Python（后端与脚本）

```bash
pip install -r requirements.txt
```

需要 Python 3.10+。主要依赖：pandas, openpyxl, jobspy, sentence-transformers, pdfplumber, flask, python-dotenv 等。

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
- 可选：`--analyze-top 20` 对前 20 名调用 DeepSeek（需在项目根目录 `.env` 中设置 `DEEPSEEK_API_KEY`，或传 `--deepseek-key`）。

```bash
python hunt.py --help    # 查看所有参数
```

### 2. 启动 API

```bash
python api/app.py
```

默认 `http://localhost:5000`。启动前会从项目根目录 `.env` 加载 `DEEPSEEK_API_KEY`（供 ATS 分析使用）。提供：

| 端点                   | 方法 | 说明                                          |
|------------------------|------|-----------------------------------------------|
| `/api/jobs`            | GET  | 返回 Jobs + Filtered_Out，按 score 降序       |
| `/api/jobs/analyze`    | POST | 单职位 ATS 分析（请求体 `{ "job": {...} }`）  |
| `/api/resume`          | POST | 上传 PDF 简历到 data/uploads/                 |
| `/api/resume/status`   | GET  | 查询是否已有上传的简历                        |
| `/api/resume/file`     | GET  | 返回当前简历 PDF（浏览器内预览）              |

### 3. 启动前端

```bash
cd ui
npm run dev
```

浏览器打开 `http://localhost:5173`。Vite 会代理 `/api` 到后端。页面功能：保留的职位 / 已筛除 两个 Tab、每页 10 条分页、上传简历、点击「当前简历: current_resume.pdf」在新标签页预览 PDF、每个职位卡片上的「Analysis」按钮可对该职位做 DeepSeek ATS 分析并弹抽屉展示结果（需后端已配置 `DEEPSEEK_API_KEY`）。

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

确保 `.env` 中有 `DEEPSEEK_API_KEY`，或：

```bash
export DEEPSEEK_API_KEY="your-key"   # Linux/macOS
set DEEPSEEK_API_KEY=your-key       # Windows CMD
python deepseek_ats_analyzer.py --excel data/job_hunt_results.xlsx --resume data/uploads/current_resume.pdf
```

---

## 配置说明

| 文件                          | 用途                                                         |
|-------------------------------|--------------------------------------------------------------|
| `.env`                        | 本地配置，如 `DEEPSEEK_API_KEY`（参考 `.env.example`，不要提交 .env） |
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
| 前端       | React 18, Vite 5, Ant Design（职位卡片 Analysis 抽屉等）   |
