# Hunt.py 改进总结

## 📊 评分机制优化

### 旧系统 (3-component)
- 语义相似度: 60%
- 关键词匹配: 30% (每个技能 +20 分，阈值 80%)
- 标题加分: 10% (仅 Junior/New Grad/2025)
- **平均分**: ~23, **最高分**: 37

### 新系统 (4-component，改进版)

| 组件 | 旧权重 | 新权重 | 变化 | 说明 |
|------|--------|--------|------|------|
| 语义相似度 | 60% | 40% | ↓ 20% | 减少权重：简历与JD措辞差异大 |
| 关键词匹配 | 30% | 35% | ↑ 5% | 增加权重：关键技能是核心信号 |
| 标题加分 | 10% | 15% | ↑ 5% | 增加权重：Junior/Entry信号很重要 |
| **位置加分** | — | **10%** | ✨ **新增** | Toronto/Mississauga +10, Ontario +5 |

## 🎯 具体改进

### 1. 关键词匹配改进
```python
# 旧: 20 分/匹配 + 80% 阈值 → 太严格
KEYWORD_FUZZ_THRESHOLD = 80
KEYWORD_MATCH_POINTS = 20

# 新: 25 分/匹配 + 75% 阈值 → 更容易触发
KEYWORD_FUZZ_THRESHOLD = 75
KEYWORD_MATCH_POINTS = 25
```

**影响**：即使技能名称不完全匹配（如"Java"在"Java Developer"中），也有75%的概率被识别

### 2. 标题关键词扩展
```python
# 旧: r"\b(Junior|New\s+Grad|2025)\b"
# 新: r"\b(Junior|New\s+Grad|2025|Entry.?Level|Early.?Career|Graduate)\b"
```

**包含**: Junior, New Grad, 2025, Entry-Level, Early-Career, Graduate role

### 3. 位置加分 (新功能)
```python
def _location_bonus(location: str) -> int:
    if "toronto" in loc or "mississauga" in loc:
        return 10  # 最优地点
    if "ontario" in loc:
        return 5   # 次优地点
    return 0
```

### 4. 配置文件支持 (新功能)
创建 `job_positions.yaml` - 快速切换职位配置

```yaml
positions:
  backend:
    skills: ["Java", "Python", "SQL", "Spring", "Docker"]
    weights:
      semantic: 0.40
      keyword: 0.35
      title_bonus: 0.15
      location_bonus: 0.10
  
  frontend:
    skills: ["JavaScript", "React", "TypeScript", "CSS"]
    weights: {...}
  
  data:
    skills: ["Python", "Statistics", "SQL", "Machine Learning"]
    weights: {...}
```

## 💻 使用方法

### 基础用法（使用默认配置）
```bash
python hunt.py --search "Junior Software Engineer" --location "Canada" --results 30
```

### 使用自定义职位配置
```bash
# Backend 职位
python hunt.py --search "Backend Engineer" \
  --config job_positions.yaml --position backend

# Frontend 职位
python hunt.py --search "Frontend Developer" \
  --config job_positions.yaml --position frontend

# Data Science 职位
python hunt.py --search "Data Scientist" \
  --config job_positions.yaml --position data
```

### 其他选项
```bash
# 指定输出路径
python hunt.py --out "results_feb.xlsx"

# 输出 CSV (已删除)
# python hunt.py --csv

# 自定义简历路径
python hunt.py --resume-pdf "/path/to/resume.pdf"
```

## 📈 预期效果

### 分数改进预期
- **更多职位达到 50+ 分**: 位置和扩展的关键词匹配
- **更高的平均分**: 4-component 系统更全面
- **更准确的排序**: 优先级清晰 (关键词 > 语义 > 标题 > 位置)

### 假设场景
对于"Java Software Engineer - Toronto"的职位：
- **旧系统**: 可能 25-30 分 (语义不高，少数关键词)
- **新系统**: 可能 40-50 分 (Java +25, 位置 +10, 标题 +15, 语义 +15-25)

## 🔧 如何自定义配置

编辑 `job_positions.yaml`：

1. **添加新职位**
```yaml
  devops:
    skills: ["Docker", "Kubernetes", "AWS", "Python", "Bash"]
    weights:
      semantic: 0.35
      keyword: 0.40
      title_bonus: 0.15
      location_bonus: 0.10
```

2. **调整权重**
```yaml
  weights:
    semantic: 0.50  # 如果重视 JD 相似度
    keyword: 0.25   # 如果重视广泛匹配
```

3. **修改技能列表**
```yaml
  skills:
    - "Go"
    - "Rust"
    - "PostgreSQL"
```

## 📝 文件清单

- `hunt.py` - 主脚本 (已更新)
- `job_positions.yaml` - 新增：职位配置文件
- `Grace_cs3.pdf` - 简历 (保持不变)
- `requirements.txt` - 依赖 (添加 pyyaml)

## ⚠️ 依赖更新

如果要支持 YAML 配置，需要安装：
```bash
pip install pyyaml
# 或
pip install -r requirements.txt
```

如果未安装 PyYAML，脚本会自动降级为 JSON 配置或默认设置。

---

**总结**: 通过增加关键词权重、降低匹配阈值、添加位置bonus、支持配置文件，系统现在更适合快速迭代和个性化职位搜索。
