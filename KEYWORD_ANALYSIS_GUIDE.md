# 简历关键词分析指南

## 已完成的工作

✓ 创建了 3 个新文件来支持简历关键词提取和分析：

### 1️⃣ `_resume_keyword_module.py` (共享模块)
**作用**：提供可复用的 PDF 处理和关键词提取函数
- `extract_text_from_pdf()` — 从 PDF 读取文本
- `clean_resume_text()` — 清洗乱码
- `extract_keywords_from_resume()` — 提取关键词
- `compare_with_resume_skills()` — 对比分析

**使用场景**：被 `hunt.py` 和 `analyze_resume.py` 导入使用

---

### 2️⃣ `tech_keywords.yaml` (关键词库)
**作用**：定义 77 个技术关键词库，分 6 类
```yaml
编程语言:     Python, Java, C++, JavaScript, TypeScript, Go, Rust...
Web框架:      Spring, Springboot, Django, Flask, React, Vue...
数据库:       SQLite, MySQL, PostgreSQL, MongoDB, Redis...
云平台与容器:  Docker, Kubernetes, AWS, Azure, GitHub...
数据与分析:   Statistics, Machine Learning, Pandas, NumPy...
其他技术:     REST API, GraphQL, Git, Linux, XML...
```

**可自定义**：需要添加新关键词时，编辑这个 YAML 文件即可

---

### 3️⃣ `analyze_resume.py` (分析脚本)
**作用**：独立的 CLI 工具，分析简历并生成报告

**功能**：
1. 从 Grace_cs3.pdf 扫描出所有技术关键词
2. 与 RESUME_SKILLS 列表对比
3. 输出两个报告文件：
   - `resume_analysis_report.txt` — 人类可读版本
   - `resume_analysis_report.json` — 机器可读版本

---

### 4️⃣ `hunt.py` (更新)
**修改内容**：
- 将 PDF 处理函数替换为从 `_resume_keyword_module.py` 导入
- 更新了 `RESUME_SKILLS` 列表（添加了 6 个之前遗漏的技能）

**新的 RESUME_SKILLS**：
```python
["C++", "Java", "Springboot", "SQLite", "Statistics", "Python",
 "MySQL", "MongoDB", "MariaDB", "Redis", "GitHub", "R"]
```

---

## 分析结果总结

### 📊 发现的关键词（10 个）

| 类别 | 关键词 | 出现次数 |
|------|--------|--------|
| 编程语言 | Java | 4 |
| 编程语言 | Python | 3 |
| 编程语言 | R | 1 |
| Web框架 | Springboot | 1 |
| 数据库 | MariaDB | 2 |
| 数据库 | MySQL | 1 |
| 数据库 | MongoDB | 1 |
| 数据库 | Redis | 1 |
| 云平台 | GitHub | 1 |
| 数据分析 | Statistics | 1 |

### 🚨 需要添加的技能（之前遗漏，现已在 RESUME_SKILLS 中）
- GitHub
- MariaDB
- MongoDB
- MySQL
- R
- Redis

### ℹ️ 信息：RESUME_SKILLS 中但简历未提及
- C++
- SQLite

**建议**：这两个技能可能不够突出，考虑在简历中更加强调，或者确认它们是否真的是主要技能。

---

## 使用指南

### 运行分析工具
```bash
# 使用默认配置分析简历
python analyze_resume.py

# 自定义简历文件路径
python analyze_resume.py --resume "my_resume.pdf"

# 自定义 RESUME_SKILLS 列表
python analyze_resume.py --skills "Python,Java,Docker,Kubernetes"

# 自定义关键词配置文件
python analyze_resume.py --config "custom_keywords.yaml"

# 自定义输出路径
python analyze_resume.py --output "my_analysis.txt"
```

### 更新 hunt.py 中的 RESUME_SKILLS
当分析完成后，如果发现新的关键词，手动编辑 `hunt.py` 中的 RESUME_SKILLS：

```python
RESUME_SKILLS = ["C++", "Java", "Springboot", "SQLite", "Statistics", "Python",
                 "MySQL", "MongoDB", "MariaDB", "Redis", "GitHub", "R"]
```

### 重新运行职位抓取
更新 RESUME_SKILLS 后，重新运行 hunt.py 会获得更精准的职位匹配：

```bash
python hunt.py --search "Software Engineer" --location "Canada" --results 30
```

---

## 文件清单

| 文件名 | 类型 | 说明 |
|--------|------|------|
| `_resume_keyword_module.py` | 新增 | 共享的 PDF 和关键词处理模块 |
| `tech_keywords.yaml` | 新增 | 77 个技术关键词库（分 6 类） |
| `analyze_resume.py` | 新增 | 简历分析 CLI 工具 |
| `hunt.py` | 修改 | 导入共享模块 + 更新 RESUME_SKILLS |
| `resume_analysis_report.txt` | 生成 | 文本格式的分析报告 |
| `resume_analysis_report.json` | 生成 | JSON 格式的分析数据 |

---

## 工作流程

```
1. 运行 analyze_resume.py
   ↓
2. 查看 resume_analysis_report.txt
   ↓
3. 找出 "在简历中但不在RESUME_SKILLS中" 的技能
   ↓
4. 手动更新 hunt.py 中的 RESUME_SKILLS
   ↓
5. 重新运行 hunt.py 抓取职位
   ↓
6. 获得更精准的职位匹配结果
```

---

## 常见问题

### Q: 如何添加新的关键词？
A: 编辑 `tech_keywords.yaml`，在相应类别下添加新关键词，然后重新运行 `analyze_resume.py`

### Q: 如何排除某些关键词？
A: 编辑 `RESUME_SKILLS` 列表，移除不需要的技能即可

### Q: 如果简历中的某些技能被识别不出来怎么办？
A: 可能是拼写不同（例如 "Spring Boot" vs "Springboot"）或关键词库中没有包含。编辑 `tech_keywords.yaml` 添加变体或修改规则

### Q: JSON 输出文件有什么用？
A: 可以用于程序化处理或导入其他系统。包含了详细的关键词统计和对比数据

---

## 下一步优化建议

1. **定期更新关键词库** — 随着技术更新，定期在 `tech_keywords.yaml` 中添加新技术
2. **自动化更新** — 可以写脚本自动从分析结果更新 hunt.py 中的 RESUME_SKILLS
3. **职位特定配置** — 在 `job_positions.yaml` 中为不同职位配置不同的技能列表
4. **与职位匹配集成** — 考虑在 hunt.py 中添加 `--analyze-keywords` 参数，自动触发分析

---

**最后更新**：2026-02-09  
**分析工具**：`analyze_resume.py` v1.0
