# 半导体QA生成系统 - 全局质量筛选功能说明

## 🎯 核心功能

新增**全局质量筛选**机制，确保生成的QA数量和质量都符合要求。

## 📊 工作原理

### 原来的逻辑（无质量筛选）
```bash
# 生成100个QA
python main.py --target_count 100

# 结果：生成约100个QA，但质量不保证
```

### 现在的逻辑（带质量筛选）
```bash
# 生成100个high质量QA
python main_final_new.py --target_count 100 --quality_filter high

# 结果：恰好100个high质量QA（可能尝试了300次）
```

## 🔧 使用方法

### 1. 基础用法（推荐）

```bash
python main_final_new.py \
    --input /path/to/QA.jsonl \
    --output ./generated_qa \
    --model_path /path/to/model \
    --target_count 100 \
    --quality_filter high \
    --batch_size 4 \
    --debug
```

**参数说明**：
- `--target_count 100`：目标生成**100个符合质量标准**的QA
- `--quality_filter high`：只保留high质量的QA
- `--batch_size 4`：并发生成4个QA

**预期结果**：
- 输出恰好100个high质量QA
- 可能尝试200-300次（成功率约30-50%）
- 实时显示成功率

---

### 2. 不同质量级别

#### 严格模式（只要high质量）
```bash
python main_final_new.py \
    --input data.jsonl \
    --output results_high \
    --model_path model \
    --target_count 100 \
    --quality_filter high
```

- ✅ 输出：100个high质量QA
- ⏱️ 速度：较慢（成功率约30%）
- 📊 质量：最高

#### 平衡模式（high + medium）（推荐）
```bash
python main_final_new.py \
    --input data.jsonl \
    --output results_medium \
    --model_path model \
    --target_count 100 \
    --quality_filter medium+
```

- ✅ 输出：100个high或medium质量QA
- ⏱️ 速度：适中（成功率约60%）
- 📊 质量：良好

#### 快速模式（所有质量）
```bash
python main_final_new.py \
    --input data.jsonl \
    --output results_all \
    --model_path model \
    --target_count 100 \
    --quality_filter all
```

- ✅ 输出：100个QA（任意质量）
- ⏱️ 速度：最快（成功率近100%）
- 📊 质量：不保证

---

### 3. 高级配置

#### 控制最大尝试次数
```bash
python main_final_new.py \
    --target_count 100 \
    --quality_filter high \
    --max_attempts 500  # 最多尝试500次
```

**说明**：
- 默认 `max_attempts = target_count * 3`（即300次）
- 如果成功率低，可以增加此值

#### 输出格式控制
```bash
# JSONL格式（推荐，所有QA在一个文件中）
python main_final_new.py \
    --output_format jsonl \
    --target_count 100 \
    --quality_filter high

# JSON格式（每个QA单独文件）
python main_final_new.py \
    --output_format json \
    --target_count 100 \
    --quality_filter high

# 两种格式都输出
python main_final_new.py \
    --output_format both \
    --target_count 100 \
    --quality_filter high
```

#### 生成详细质量报告
```bash
python main_final_new.py \
    --target_count 100 \
    --quality_filter high \
    --generate_report  # 生成quality_report.json
```

---

## 📁 输出文件说明

生成的文件位于 `--output` 指定的目录：

```
output_directory/
├── qualified_results.jsonl    # ⭐ 合格的QA（符合quality_filter）
├── all_results.jsonl          # 所有尝试的QA（包括不合格的）
├── quality_report.json        # 详细质量报告（如果启用）
└── *.json                     # 单独的QA文件（如果output_format=json）
```

### 文件详解

#### 1. `qualified_results.jsonl`（⭐ 最重要）
包含**恰好 target_count 个**符合质量标准的QA。

**示例**：
```bash
--target_count 100 --quality_filter high
# → qualified_results.jsonl 包含100个high质量QA
```

#### 2. `all_results.jsonl`
包含所有尝试生成的QA（包括不合格的），用于：
- 分析失败原因
- 调试
- 统计

#### 3. `quality_report.json`（如果启用 `--generate_report`）
详细统计报告：
```json
{
  "summary": {
    "total_count": 300,
    "quality_distribution": {
      "high": 100,
      "medium": 120,
      "low": 80
    },
    "high_quality_rate": 0.33
  },
  "hop_distribution": {
    "1": 50,
    "2": 150,
    "3": 80,
    "4": 20
  },
  "length_statistics": {
    "avg_answer_length": 234.5,
    "avg_question_length": 78.3
  }
}
```

---

## 📊 质量评估标准

质量评估基于以下维度（自动计算）：

| 维度 | 权重 | high标准 | medium标准 |
|------|------|---------|-----------|
| **多跳数量** | 40% | ≥3跳 | ≥2跳 |
| **答案长度** | 20% | ≥200字符 | ≥100字符 |
| **问题长度** | 10% | ≥50字符 | ≥30字符 |
| **轮数合理性** | 10% | 3-15轮 | 2-16轮 |
| **陈述数量** | 10% | ≥2条 | ≥1条 |
| **编辑历史** | 10% | ≥3条 | ≥2条 |

**总分计算**：
- `score ≥ 7分` → high
- `4分 ≤ score < 7分` → medium
- `score < 4分` → low

---

## 🎯 实际案例

### 案例1：生成高质量多跨paper多跳QA

**目标**：生成1000个high质量、2-4跳的多跨paper QA

```bash
python main_final_new.py \
    --input semiconductor_qa.jsonl \
    --output qa_high_1000 \
    --model_path /path/to/Qwen2.5-14B \
    --target_count 1000 \
    --quality_filter high \
    --batch_size 8 \
    --max_attempts 3000 \
    --output_format jsonl \
    --generate_report \
    --debug
```

**预期输出**：
```
[PROGRESS] 合格: 1000/1000, 尝试: 2847/3000, 成功率: 35.1%, 平均耗时: 45.2s/个

[BATCH] 完成！
  目标数量: 1000
  实际获得: 1000
  总尝试数: 2847
  成功率: 35.1%
  总耗时: 12.6小时

📊 质量分布:
   high: 1000

🔗 多跳分布:
   2跳: 250
   3跳: 500
   4跳: 250
```

---

### 案例2：快速测试（10个QA）

```bash
python main_final_new.py \
    --input semiconductor_qa.jsonl \
    --output test_qa \
    --model_path /path/to/Qwen2.5-14B \
    --target_count 10 \
    --quality_filter medium+ \
    --batch_size 4 \
    --debug
```

**预期输出**：
```
[PROGRESS] 合格: 10/10, 尝试: 15/30, 成功率: 66.7%

[BATCH] 完成！
  实际获得: 10
  总尝试数: 15
  总耗时: 7.5分钟
```

---

## 🔍 监控和调试

### 实时进度显示

运行时会实时显示：
```
[PROGRESS] 合格: 50/100, 尝试: 150/300, 成功率: 33.3%, 平均耗时: 42.1s/个
```

### 详细日志（启用 `--debug`）

```bash
python main_final_new.py --debug ...
```

会显示：
- 每个QA的生成过程
- SELECT操作的候选ID
- 筛选结果
- 桥联检查结果
- JSON解析过程

---

## ⚙️ 性能优化建议

### 1. 提升成功率

如果成功率过低（<20%），尝试：

```bash
# 放宽质量标准
--quality_filter medium+  # 而不是 high

# 增加最大尝试次数
--max_attempts 5000

# 关闭某些检查（谨慎）
--disable_bridge_check
```

### 2. 提升速度

```bash
# 增加并发数（需要GPU显存足够）
--batch_size 16

# 使用更快的模型
--model_path /path/to/Qwen2.5-7B

# 减少max_turns
--max_turns 8
```

### 3. 提升质量

```bash
# 使用更大的模型
--model_path /path/to/Qwen2.5-72B

# 启用所有检查
--enable_bridge_check
--enable_qa_filtering
--enable_answer_regeneration

# 使用语义embedding
--use-embedding
```

---

## 📈 成功率参考

基于测试数据（Qwen2.5-14B-Instruct）：

| quality_filter | 预期成功率 | 建议batch_size | 预期耗时（100个） |
|---------------|----------|---------------|-----------------|
| **high** | 30-40% | 8-16 | 2-3小时 |
| **medium+** | 60-70% | 4-8 | 1-1.5小时 |
| **all** | 90-95% | 4 | 30-45分钟 |

---

## ❓ 常见问题

### Q1: 为什么 `all_results.jsonl` 比 `qualified_results.jsonl` 多很多？

**A**: 这是正常的。`all_results.jsonl` 包含所有尝试（成功+失败），而 `qualified_results.jsonl` 只包含符合质量标准的。

**示例**：
```
--target_count 100 --quality_filter high
# all_results.jsonl: 300条（100个high + 120个medium + 80个low）
# qualified_results.jsonl: 100条（只有high）
```

---

### Q2: 如何只要多跳QA（≥2跳）？

**A**: 使用 `quality_filter=medium+` 或 `high`，因为质量评估会考虑多跳数量。

或者手动过滤：
```bash
# 生成后过滤
jq 'select(.final_qa_count >= 2)' qualified_results.jsonl > multihop_only.jsonl
```

---

### Q3: 成功率太低怎么办？

**A**: 尝试以下方法：
1. 降低质量标准：`high` → `medium+`
2. 增加尝试次数：`--max_attempts 5000`
3. 检查输入数据质量
4. 查看 `all_results.jsonl` 分析失败原因

---

### Q4: 如何查看某个QA为什么被拒绝？

**A**: 查看 `all_results.jsonl`，每个QA都有完整信息：
```json
{
  "uid": "...",
  "question": "...",
  "final_qa_count": 1,  // 只有1跳，可能被判为low
  "num_turns": 16,      // 达到最大轮数，可能质量不高
  "answer": "...",      // 答案长度
  ...
}
```

然后用 `evaluate_overall_quality()` 函数分析。

---

## 🚀 完整示例脚本

```bash
#!/bin/bash

# 配置
INPUT_FILE="/path/to/semiconductor_qa.jsonl"
OUTPUT_DIR="./qa_generation_results"
MODEL_PATH="/path/to/Qwen2.5-14B-Instruct"
TARGET_COUNT=1000
QUALITY_FILTER="high"
BATCH_SIZE=8

# 运行
python main_final_new.py \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_DIR" \
    --model_path "$MODEL_PATH" \
    --target_count "$TARGET_COUNT" \
    --quality_filter "$QUALITY_FILTER" \
    --batch_size "$BATCH_SIZE" \
    --max_attempts $((TARGET_COUNT * 3)) \
    --output_format jsonl \
    --generate_report \
    --enable_dynamic_planning \
    --enable_qa_filtering \
    --enable_answer_regeneration \
    --enable_bridge_check \
    --debug

# 生成后统计
echo "生成完成！"
echo "合格QA数量: $(wc -l < $OUTPUT_DIR/qualified_results.jsonl)"
echo "总尝试数量: $(wc -l < $OUTPUT_DIR/all_results.jsonl)"

# 查看质量分布
if [ -f "$OUTPUT_DIR/quality_report.json" ]; then
    echo "质量报告:"
    jq '.summary.quality_distribution' "$OUTPUT_DIR/quality_report.json"
fi
```

---

## 📞 技术支持

如有问题，请查看：
1. `all_results.jsonl` - 查看所有生成结果
2. `quality_report.json` - 查看详细统计
3. 启用 `--debug` - 查看详细日志
4. 检查LLM服务器连接

---

## 🎉 总结

**核心优势**：
- ✅ **数量保证**：恰好生成 `target_count` 个符合质量标准的QA
- ✅ **质量保证**：通过 `quality_filter` 确保质量
- ✅ **实时监控**：显示成功率、进度、耗时
- ✅ **灵活配置**：支持多种质量级别和输出格式

**推荐配置**：
```bash
python main_final_new.py \
    --target_count 100 \
    --quality_filter medium+ \
    --batch_size 8 \
    --generate_report \
    --debug
```

开始使用吧！🚀
