# 半导体QA生成系统 - 带全局质量筛选 🚀

一个强大的半导体领域问答（QA）生成系统，支持**全局质量筛选**，确保生成的QA数量和质量都符合要求。

## ✨ 核心特性

- 🎯 **数量保证**：恰好生成 `target_count` 个符合质量标准的QA
- 📊 **质量保证**：支持3种质量级别（high/medium+/all）
- 🔗 **多跳推理**：自动生成2-4跳的复杂推理问题
- 📈 **实时监控**：显示成功率、进度、耗时
- 📁 **灵活输出**：支持多种输出格式（JSONL/JSON）
- 📝 **详细报告**：生成质量分布、多跳分布等统计报告

## 🎯 核心功能：全局质量筛选

### 问题

原来的代码生成 `target_count` 个QA，但**质量不保证**：

```bash
python main.py --target_count 100
# 结果：生成约100个QA，但可能70个是1跳低质量QA
```

### 解决

新代码生成 `target_count` 个**符合质量标准**的QA：

```bash
python main_final_new.py --target_count 100 --quality_filter high
# 结果：恰好100个high质量QA（可能尝试了300次）
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install torch transformers aiohttp requests tqdm numpy
```

### 2. 启动LLM服务

```bash
# 使用vLLM启动模型服务
vllm serve /path/to/Qwen2.5-14B-Instruct --port 8000
```

### 3. 运行生成

```bash
python main_final_new.py \
    --input ./data/semiconductor_qa.jsonl \
    --output ./results \
    --model_path Qwen2.5-14B-Instruct \
    --target_count 100 \
    --quality_filter high
```

### 4. 查看结果

```bash
# 查看合格的QA
cat results/qualified_results.jsonl

# 查看质量报告
cat results/quality_report.json
```

## 📊 质量级别说明

### high - 严格模式

```bash
--quality_filter high
```

- **标准**：3-4跳、答案≥200字符、推理完整
- **成功率**：30-40%
- **适用**：训练数据生成
- **示例**：生成100个需尝试约300次

### medium+ - 平衡模式（推荐）

```bash
--quality_filter medium+
```

- **标准**：2-4跳、答案≥100字符、推理较完整
- **成功率**：60-70%
- **适用**：大部分场景
- **示例**：生成100个需尝试约150次

### all - 快速模式

```bash
--quality_filter all
```

- **标准**：任意质量
- **成功率**：90-95%
- **适用**：快速测试、兼容原版
- **示例**：生成100个需尝试约110次

## 📝 使用示例

### 示例1：生成1000个高质量训练数据

```bash
python main_final_new.py \
    --input semiconductor_qa.jsonl \
    --output training_data_1000 \
    --model_path Qwen2.5-14B-Instruct \
    --target_count 1000 \
    --quality_filter high \
    --batch_size 8 \
    --max_attempts 3000 \
    --output_format jsonl \
    --generate_report \
    --debug
```

**预期结果**：
- 输出：恰好1000个high质量QA
- 耗时：约6-8小时
- 成功率：约35%

### 示例2：快速测试（10个QA）

```bash
python main_final_new.py \
    --input semiconductor_qa.jsonl \
    --output test_results \
    --model_path Qwen2.5-14B-Instruct \
    --target_count 10 \
    --quality_filter medium+ \
    --batch_size 4 \
    --debug
```

**预期结果**：
- 输出：10个medium+质量QA
- 耗时：约10-15分钟
- 成功率：约65%

### 示例3：使用脚本运行

```bash
# 编辑配置
vim run_example.sh

# 运行
bash run_example.sh
```

## 📁 输出文件说明

```
output_directory/
├── qualified_results.jsonl    # ⭐ 符合质量标准的QA（恰好target_count个）
├── all_results.jsonl          # 所有尝试的QA（包括不合格的）
├── quality_report.json        # 详细质量报告（如果启用）
└── *.json                     # 单独的QA文件（如果output_format=json）
```

### 关键文件

- **`qualified_results.jsonl`**：最重要，包含恰好 `target_count` 个符合 `quality_filter` 的QA
- **`all_results.jsonl`**：用于分析失败原因、统计成功率
- **`quality_report.json`**：详细统计（质量分布、多跳分布、长度统计等）

## 📊 质量评估标准

系统基于以下6个维度自动评估QA质量（总分10分）：

| 维度 | 权重 | high标准 | medium标准 |
|------|------|---------|-----------|
| **多跳数量** | 40% | ≥3跳（4分） | ≥2跳（3分） |
| **答案长度** | 20% | ≥200字符（2分） | ≥100字符（1分） |
| **问题长度** | 10% | ≥50字符（1分） | ≥30字符（1分） |
| **轮数合理性** | 10% | 3-15轮（1分） | 2-16轮（1分） |
| **陈述数量** | 10% | ≥2条（1分） | ≥1条（1分） |
| **编辑历史** | 10% | ≥3条（1分） | ≥2条（1分） |

**质量等级**：
- `score ≥ 7分` → **high**
- `4分 ≤ score < 7分` → **medium**
- `score < 4分` → **low**

## 🔧 命令行参数

### 核心参数

```bash
--input PATH              # 输入QA数据文件路径（必需）
--output PATH             # 输出目录路径（必需）
--model_path PATH         # LLM模型路径（必需）
--target_count N          # ⭐ 目标生成数量（符合quality_filter的数量）
--quality_filter FILTER   # ⭐ 质量过滤器：high, medium+, all（默认：all）
```

### 生成参数

```bash
--batch_size N            # 并发批次大小（默认：4）
--max_attempts N          # 最大尝试次数（默认：target_count * 3）
--max_turns N             # 最大迭代轮数（默认：16）
--max_hops N              # 最多组合的问题数量（默认：3）
```

### 输出参数

```bash
--output_format FORMAT    # 输出格式：jsonl, json, both（默认：jsonl）
--generate_report         # 生成详细质量报告
--merge_output            # 合并输出
```

### 功能开关

```bash
--enable_dynamic_planning     # 启用动态规划（默认：开启）
--enable_qa_filtering         # 启用问题筛选（默认：开启）
--enable_answer_regeneration  # 启用答案重生成（默认：开启）
--enable_bridge_check         # 启用桥联合理性检查（默认：开启）
--use-embedding               # 使用语义embedding查找相关QA
--debug                       # 启用调试模式
```

### 完整示例

```bash
python main_final_new.py \
    --input ./data/qa.jsonl \
    --output ./results \
    --model_path Qwen2.5-14B-Instruct \
    --target_count 100 \
    --quality_filter high \
    --batch_size 8 \
    --max_attempts 300 \
    --output_format jsonl \
    --generate_report \
    --debug
```

## 📈 实际运行示例

```bash
$ python main_final_new.py --target_count 100 --quality_filter high

[BATCH] 批量生成任务（带质量筛选）
  目标数量: 100 个（high质量）
  并发数: 4
  最大尝试: 300

生成high质量QA: 100%|████████████| 100/100 [1:23:45<00:00, 50.3s/it]

[PROGRESS] 合格: 100/100, 尝试: 287/300, 成功率: 34.8%

[BATCH] 完成！
  目标数量: 100
  实际获得: 100
  总尝试数: 287
  成功率: 34.8%
  总耗时: 2.3小时

📊 质量分布:
   high: 100

🔗 多跳分布:
   2跳: 15
   3跳: 60
   4跳: 25
```

## 🧪 测试

运行测试脚本验证功能：

```bash
python test_quality_filter.py
```

预期输出：

```
测试 1: 高质量QA（3跳，答案长）
  期望质量: high
  实际质量: high
  ✅ 通过

测试 2: 中等质量QA（2跳，答案中等）
  期望质量: medium
  实际质量: medium
  ✅ 通过

...

✅ 所有测试通过！
```

## 📚 详细文档

- **[README_QUALITY_FILTER.md](README_QUALITY_FILTER.md)** - 完整使用指南（推荐阅读）
- **[CHANGES.md](CHANGES.md)** - 详细修改说明
- **[COMPARISON.md](COMPARISON.md)** - 修改前后对比
- **[SUMMARY.md](SUMMARY.md)** - 修改总结

## ❓ 常见问题

### Q: 为什么成功率只有30%？

**A**: 这是正常的。`quality_filter=high` 的标准很严格（3-4跳，答案长，推理完整），只有约30-40%的QA能达到。

**解决**：
- 使用 `--quality_filter medium+`（成功率60-70%）
- 增加 `--max_attempts`

### Q: 如何查看不合格的QA？

**A**: 查看 `all_results.jsonl`，它包含所有尝试的QA。

### Q: 能否自定义质量标准？

**A**: 可以！修改 `utils.py` 中的 `evaluate_overall_quality` 函数。

### Q: 如何提升生成速度？

**A**:
- 降低质量标准：`high` → `medium+`
- 增加并发数：`--batch_size 16`
- 使用更快的模型

更多问题请参考 [README_QUALITY_FILTER.md](README_QUALITY_FILTER.md)。

## 🎯 推荐配置

### 训练数据生成

```bash
python main_final_new.py \
    --target_count 1000 \
    --quality_filter high \
    --batch_size 8 \
    --generate_report
```

### 快速原型测试

```bash
python main_final_new.py \
    --target_count 10 \
    --quality_filter medium+ \
    --batch_size 4
```

### 兼容原有流程

```bash
python main_final_new.py \
    --target_count 100 \
    --quality_filter all
```

## 📞 技术支持

如有问题，请：

1. 阅读 [README_QUALITY_FILTER.md](README_QUALITY_FILTER.md)
2. 运行 `python test_quality_filter.py` 测试
3. 查看 `all_results.jsonl` 和 `quality_report.json`
4. 启用 `--debug` 模式

## 📄 许可证

（根据您的项目添加许可证信息）

## 🎉 开始使用

```bash
# 克隆代码
git clone <repository_url>

# 安装依赖
pip install -r requirements.txt

# 启动LLM服务
vllm serve /path/to/model --port 8000

# 运行生成（使用示例脚本）
bash run_example.sh

# 或直接运行
python main_final_new.py \
    --input your_data.jsonl \
    --output results \
    --model_path your_model \
    --target_count 100 \
    --quality_filter high
```

**祝您使用愉快！** 🚀
