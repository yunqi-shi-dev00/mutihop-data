# 文件结构说明

## 📁 项目文件列表

```
/workspace/
├── 🔧 核心代码文件
│   ├── main_final_new.py          ⭐ 主程序（已添加质量筛选）
│   ├── utils.py                   ⭐ 工具函数（已添加质量评估和筛选逻辑）
│   ├── agent_final_new.py         ⚪ Agent逻辑（无需修改）
│   ├── knowledge_base_new.py      ⚪ 知识库（无需修改）
│   ├── llm_client.py              ⚪ LLM客户端（无需修改）
│   ├── prompts_final.py           ⚪ Prompts（无需修改）
│   └── semiconductor_qa_agent.py  ⚪ 原版Agent（已废弃，保留用于参考）
│
├── 📚 文档文件
│   ├── README.md                      ⭐ 主文档（已更新）
│   ├── README_QUALITY_FILTER.md       🆕 质量筛选功能详细说明
│   ├── CHANGES.md                     🆕 修改说明
│   ├── COMPARISON.md                  🆕 修改前后对比
│   ├── SUMMARY.md                     🆕 修改总结
│   ├── CHECKLIST.md                   🆕 验证清单
│   └── FILE_STRUCTURE.md              🆕 本文件
│
├── 🧪 测试和脚本
│   ├── test_quality_filter.py         🆕 质量筛选功能测试脚本
│   ├── run_example.sh                 🆕 示例运行脚本（可执行）
│   └── requirements.txt               🆕 Python依赖项
│
└── 📁 其他文件
    └── readme.md                      ⚪ 原有README（未修改）
```

**图例**：
- ⭐ 已修改的核心文件
- 🆕 新创建的文件
- ⚪ 未修改的文件

---

## 📄 文件说明

### 🔧 核心代码文件

#### ⭐ `main_final_new.py`（已修改）

**主程序**，添加了全局质量筛选功能。

**核心修改**：
- 新增 `--quality_filter` 参数（high/medium+/all）
- 新增 `--max_attempts` 参数（最大尝试次数）
- 新增 `--output_format` 参数（jsonl/json/both）
- 新增 `--generate_report` 参数（生成质量报告）
- 调用新的批量生成函数 `generate_batch_with_quality_filter`
- 显示详细统计信息（成功率、质量分布、多跳分布）

**使用**：
```bash
python main_final_new.py \
    --input data.jsonl \
    --output results \
    --model_path model \
    --target_count 100 \
    --quality_filter high
```

---

#### ⭐ `utils.py`（已修改）

**工具函数模块**，包含质量评估和筛选逻辑。

**核心新增**：
1. **`evaluate_overall_quality(result: Dict) -> str`**
   - 评估单个QA的质量
   - 基于6个维度（多跳数量、答案长度、问题长度等）
   - 返回 'high', 'medium', 'low'

2. **`generate_batch_with_quality_filter(...)`**
   - 带质量筛选的批量生成
   - 持续生成直到获得 `target_count` 个符合质量标准的QA
   - 实时显示成功率和进度
   - 返回详细统计信息

3. **`generate_quality_report(all_results, output_path)`**
   - 生成详细质量报告
   - 统计质量分布、多跳分布、长度统计等

**使用**（通常被 `main_final_new.py` 调用）：
```python
from utils import generate_batch_with_quality_filter

stats = await generate_batch_with_quality_filter(
    agent=agent,
    save_path=output_dir,
    target_count=100,
    quality_filter='high'
)
```

---

#### ⚪ 其他代码文件（未修改）

- `agent_final_new.py` - Agent逻辑
- `knowledge_base_new.py` - 知识库
- `llm_client.py` - LLM客户端
- `prompts_final.py` - Prompts模板

这些文件**无需修改**，质量筛选功能不影响它们。

---

### 📚 文档文件

#### ⭐ `README.md`（主文档）

项目的主要入口文档。

**内容**：
- 项目简介
- 核心特性
- 快速开始
- 使用示例
- 命令行参数
- 常见问题

**阅读顺序**：⭐⭐⭐ 第一个阅读

---

#### 🆕 `README_QUALITY_FILTER.md`（详细说明）

质量筛选功能的完整使用指南。

**内容**：
- 工作原理
- 使用方法（基础、高级）
- 输出文件说明
- 质量评估标准
- 实际案例
- 性能优化建议
- 常见问题

**阅读顺序**：⭐⭐⭐ 推荐详细阅读

---

#### 🆕 `CHANGES.md`（修改说明）

详细的修改说明文档。

**内容**：
- 修改文件清单
- 核心修改详解
- 代码对比（修改前后）
- 预期效果
- 向后兼容性说明

**阅读顺序**：⭐⭐ 了解修改细节时阅读

---

#### 🆕 `COMPARISON.md`（前后对比）

修改前后的详细对比。

**内容**：
- 命令行对比
- 实际运行对比
- 代码逻辑对比
- 输出文件对比
- 性能对比

**阅读顺序**：⭐⭐ 想了解差异时阅读

---

#### 🆕 `SUMMARY.md`（修改总结）

修改的总结文档。

**内容**：
- 修改完成清单
- 核心功能说明
- 快速开始
- 输出文件
- 预期效果
- 常见问题

**阅读顺序**：⭐ 快速了解时阅读

---

#### 🆕 `CHECKLIST.md`（验证清单）

用于验证修改是否正确的清单。

**内容**：
- 文件清单
- 功能验证步骤
- 完整验证示例
- 最终清单

**阅读顺序**：🧪 验证功能时使用

---

#### 🆕 `FILE_STRUCTURE.md`（本文件）

项目文件结构说明。

**内容**：
- 文件列表
- 文件说明
- 阅读建议

**阅读顺序**：📁 了解文件结构时阅读

---

### 🧪 测试和脚本

#### 🆕 `test_quality_filter.py`

质量筛选功能的测试脚本。

**功能**：
- 测试 `evaluate_overall_quality` 函数
- 测试质量筛选逻辑
- 验证不同质量级别的QA

**使用**：
```bash
python test_quality_filter.py
```

**预期输出**：
```
测试 1: 高质量QA（3跳，答案长）
  ✅ 通过

...

✅ 所有测试通过！
```

---

#### 🆕 `run_example.sh`

交互式示例运行脚本。

**功能**：
- 交互式配置参数
- 环境检查
- 运行生成
- 结果统计

**使用**：
```bash
# 编辑配置
vim run_example.sh

# 运行
bash run_example.sh
```

---

#### 🆕 `requirements.txt`

Python依赖项列表。

**内容**：
```
torch>=2.0.0
transformers>=4.30.0
aiohttp>=3.8.0
requests>=2.28.0
tqdm>=4.65.0
numpy>=1.24.0
sentence-transformers>=2.2.0  # 可选
```

**使用**：
```bash
pip install -r requirements.txt
```

---

## 📖 推荐阅读顺序

### 🚀 快速上手

1. **`README.md`** - 了解项目和基本使用
2. **`run_example.sh`** - 运行示例（或直接运行 `main_final_new.py`）
3. **`test_quality_filter.py`** - 验证功能

### 📚 深入理解

4. **`README_QUALITY_FILTER.md`** - 详细了解质量筛选功能
5. **`COMPARISON.md`** - 了解修改前后的差异
6. **`CHANGES.md`** - 了解具体修改内容

### 🔧 开发和调试

7. **`SUMMARY.md`** - 快速查阅修改总结
8. **`CHECKLIST.md`** - 验证功能是否正确
9. **`FILE_STRUCTURE.md`** - 了解文件结构

---

## 🎯 不同场景的使用指南

### 场景1：我是新用户，想快速开始

**步骤**：
1. 阅读 `README.md` 的"快速开始"部分
2. 安装依赖：`pip install -r requirements.txt`
3. 编辑 `run_example.sh` 中的配置
4. 运行：`bash run_example.sh`

---

### 场景2：我想了解质量筛选功能

**步骤**：
1. 阅读 `README_QUALITY_FILTER.md`
2. 运行测试：`python test_quality_filter.py`
3. 阅读 `COMPARISON.md` 了解前后差异

---

### 场景3：我想验证修改是否正确

**步骤**：
1. 阅读 `CHECKLIST.md`
2. 按照清单逐项验证
3. 运行测试：`python test_quality_filter.py`

---

### 场景4：我想了解代码修改细节

**步骤**：
1. 阅读 `CHANGES.md` 了解修改概览
2. 查看 `main_final_new.py` 和 `utils.py` 的具体修改
3. 阅读 `COMPARISON.md` 的代码对比部分

---

### 场景5：我想自定义质量标准

**步骤**：
1. 阅读 `README_QUALITY_FILTER.md` 的"质量评估标准"部分
2. 修改 `utils.py` 中的 `evaluate_overall_quality` 函数
3. 运行测试：`python test_quality_filter.py`

---

## 📊 文件关系图

```
用户
 │
 ├─→ README.md ────────────────────→ 快速开始
 │                                    │
 │                                    ↓
 ├─→ run_example.sh ──────────────→ 运行示例
 │                                    │
 │                                    ↓
 └─→ main_final_new.py ────────────→ 主程序
      │
      ├─→ utils.py ────────────────→ 工具函数
      │    │
      │    ├─→ evaluate_overall_quality()     质量评估
      │    ├─→ generate_batch_with_quality_filter()  批量生成
      │    └─→ generate_quality_report()      质量报告
      │
      ├─→ agent_final_new.py ──────→ Agent逻辑
      ├─→ knowledge_base_new.py ───→ 知识库
      ├─→ llm_client.py ───────────→ LLM客户端
      └─→ prompts_final.py ────────→ Prompts

输出
 │
 ├─→ qualified_results.jsonl ─────→ 符合质量标准的QA
 ├─→ all_results.jsonl ───────────→ 所有尝试的QA
 └─→ quality_report.json ─────────→ 质量报告

文档
 │
 ├─→ README_QUALITY_FILTER.md ───→ 详细说明
 ├─→ CHANGES.md ──────────────────→ 修改说明
 ├─→ COMPARISON.md ───────────────→ 前后对比
 ├─→ SUMMARY.md ──────────────────→ 修改总结
 └─→ CHECKLIST.md ────────────────→ 验证清单

测试
 │
 └─→ test_quality_filter.py ──────→ 功能测试
```

---

## ✅ 快速检查

确认所有文件都存在：

```bash
cd /workspace

# 核心代码文件
ls -l main_final_new.py utils.py

# 文档文件
ls -l README.md README_QUALITY_FILTER.md CHANGES.md COMPARISON.md SUMMARY.md CHECKLIST.md

# 脚本和测试
ls -l run_example.sh test_quality_filter.py requirements.txt

# 检查脚本可执行权限
ls -l run_example.sh | grep -q 'x' && echo "✓ run_example.sh 可执行" || echo "✗ run_example.sh 不可执行"
```

---

## 🎉 总结

### 核心修改文件（2个）

1. **`main_final_new.py`** - 新增质量筛选参数和统计显示
2. **`utils.py`** - 新增质量评估和筛选逻辑

### 新增文档（6个）

3. **`README_QUALITY_FILTER.md`** - 详细使用指南
4. **`CHANGES.md`** - 修改说明
5. **`COMPARISON.md`** - 前后对比
6. **`SUMMARY.md`** - 修改总结
7. **`CHECKLIST.md`** - 验证清单
8. **`FILE_STRUCTURE.md`** - 本文件

### 新增脚本和配置（3个）

9. **`test_quality_filter.py`** - 测试脚本
10. **`run_example.sh`** - 示例脚本
11. **`requirements.txt`** - 依赖配置

### 更新文档（1个）

12. **`README.md`** - 主文档更新

---

**开始使用吧！** 🚀

推荐从 `README.md` 开始阅读，然后运行 `bash run_example.sh` 尝试生成。
