# 修改验证清单 ✅

使用此清单验证全局质量筛选功能是否正确实现。

## 📋 文件清单

### ✅ 核心代码文件

- [x] `main_final_new.py` - 主程序（已修改）
- [x] `utils.py` - 工具函数（已修改）
- [x] `requirements.txt` - 依赖项（已创建）

### ✅ 文档文件

- [x] `README.md` - 主文档（已更新）
- [x] `README_QUALITY_FILTER.md` - 质量筛选功能详细说明
- [x] `CHANGES.md` - 修改说明
- [x] `COMPARISON.md` - 修改前后对比
- [x] `SUMMARY.md` - 修改总结
- [x] `CHECKLIST.md` - 本清单

### ✅ 脚本和测试

- [x] `run_example.sh` - 示例运行脚本（已添加可执行权限）
- [x] `test_quality_filter.py` - 测试脚本

---

## 🔍 功能验证

### 1. 检查命令行参数

```bash
python main_final_new.py --help | grep -E "quality_filter|max_attempts|output_format|generate_report"
```

**预期输出**：应该看到这些参数的说明

---

### 2. 测试质量评估函数

```bash
python test_quality_filter.py
```

**预期输出**：
```
测试 1: 高质量QA（3跳，答案长）
  期望质量: high
  实际质量: high
  ✅ 通过

...

✅ 所有测试通过！
```

---

### 3. 快速生成测试（5个QA）

```bash
python main_final_new.py \
    --input <your_input_file> \
    --output ./test_output \
    --model_path <your_model> \
    --target_count 5 \
    --quality_filter all \
    --batch_size 2 \
    --debug
```

**检查**：
- [ ] 程序正常运行
- [ ] 显示实时进度
- [ ] 生成 `qualified_results.jsonl`
- [ ] 生成 `all_results.jsonl`
- [ ] 文件中恰好有5个QA

---

### 4. 验证质量筛选（high模式）

```bash
python main_final_new.py \
    --input <your_input_file> \
    --output ./test_high \
    --model_path <your_model> \
    --target_count 3 \
    --quality_filter high \
    --batch_size 2 \
    --debug
```

**检查**：
- [ ] 显示成功率统计
- [ ] `qualified_results.jsonl` 恰好有3个QA
- [ ] 所有QA都是high质量（可用 `test_quality_filter.py` 验证）

**验证质量**：
```bash
python3 << EOF
import json
from utils import evaluate_overall_quality

with open('./test_high/qualified_results.jsonl') as f:
    for line in f:
        result = json.loads(line)
        quality = evaluate_overall_quality(result)
        print(f"UID: {result['uid']}, 质量: {quality}, 跳数: {result['final_qa_count']}")
EOF
```

**预期**：所有QA的质量都是 `high`

---

### 5. 验证输出格式

```bash
# 测试JSONL格式
python main_final_new.py \
    --target_count 2 \
    --quality_filter all \
    --output_format jsonl \
    --output ./test_jsonl \
    ...

# 检查文件
ls -la ./test_jsonl/
# 预期：有 qualified_results.jsonl 和 all_results.jsonl

# 测试JSON格式
python main_final_new.py \
    --target_count 2 \
    --quality_filter all \
    --output_format json \
    --output ./test_json \
    ...

# 检查文件
ls -la ./test_json/
# 预期：有 *.json 文件（每个QA一个文件）

# 测试both格式
python main_final_new.py \
    --target_count 2 \
    --quality_filter all \
    --output_format both \
    --output ./test_both \
    ...

# 检查文件
ls -la ./test_both/
# 预期：既有 .jsonl 文件，也有 *.json 文件
```

---

### 6. 验证质量报告

```bash
python main_final_new.py \
    --target_count 5 \
    --quality_filter all \
    --generate_report \
    --output ./test_report \
    ...

# 检查报告
cat ./test_report/quality_report.json
```

**预期**：报告包含以下字段：
- `summary` - 总结
- `quality_distribution` - 质量分布
- `hop_distribution` - 多跳分布
- `length_statistics` - 长度统计

---

### 7. 验证成功率统计

运行任意命令，观察输出中是否有：

```
[PROGRESS] 合格: X/Y, 尝试: Z/W, 成功率: P%
```

**检查**：
- [ ] 显示合格数量
- [ ] 显示尝试次数
- [ ] 显示成功率

---

### 8. 验证质量分布统计

运行命令后，检查输出：

```
📊 质量分布:
   high: X
   medium: Y
   low: Z

🔗 多跳分布:
   1跳: A
   2跳: B
   3跳: C
   4跳: D
```

**检查**：
- [ ] 显示质量分布
- [ ] 显示多跳分布
- [ ] 数字合理

---

### 9. 验证向后兼容

确认原有代码仍然可以工作（如果有）：

```python
from utils import generate_batch_with_monitoring

# 原有代码应该仍然可以运行
stats = await generate_batch_with_monitoring(...)
```

---

## 📊 完整验证示例

运行完整的端到端测试：

```bash
#!/bin/bash
# 完整验证脚本

echo "开始验证..."

# 1. 测试质量评估函数
echo "1. 测试质量评估函数..."
python test_quality_filter.py
if [ $? -ne 0 ]; then
    echo "✗ 质量评估函数测试失败"
    exit 1
fi
echo "✓ 质量评估函数测试通过"

# 2. 测试all模式（快速）
echo "2. 测试all模式..."
python main_final_new.py \
    --input your_data.jsonl \
    --output ./verify_all \
    --model_path your_model \
    --target_count 3 \
    --quality_filter all \
    --batch_size 2
if [ $? -ne 0 ]; then
    echo "✗ all模式测试失败"
    exit 1
fi
COUNT=$(wc -l < ./verify_all/qualified_results.jsonl)
if [ "$COUNT" -ne 3 ]; then
    echo "✗ all模式数量错误: 期望3, 实际$COUNT"
    exit 1
fi
echo "✓ all模式测试通过"

# 3. 测试medium+模式
echo "3. 测试medium+模式..."
python main_final_new.py \
    --input your_data.jsonl \
    --output ./verify_medium \
    --model_path your_model \
    --target_count 2 \
    --quality_filter medium+ \
    --batch_size 2
if [ $? -ne 0 ]; then
    echo "✗ medium+模式测试失败"
    exit 1
fi
COUNT=$(wc -l < ./verify_medium/qualified_results.jsonl)
if [ "$COUNT" -ne 2 ]; then
    echo "✗ medium+模式数量错误: 期望2, 实际$COUNT"
    exit 1
fi
echo "✓ medium+模式测试通过"

# 4. 测试质量报告
echo "4. 测试质量报告..."
python main_final_new.py \
    --input your_data.jsonl \
    --output ./verify_report \
    --model_path your_model \
    --target_count 2 \
    --quality_filter all \
    --batch_size 2 \
    --generate_report
if [ ! -f ./verify_report/quality_report.json ]; then
    echo "✗ 质量报告未生成"
    exit 1
fi
echo "✓ 质量报告测试通过"

echo ""
echo "✅ 所有验证通过！"
echo ""
echo "功能正常："
echo "  ✓ 质量评估"
echo "  ✓ 全局筛选"
echo "  ✓ 数量保证"
echo "  ✓ 质量报告"
```

---

## ✅ 最终清单

### 核心功能

- [ ] `--quality_filter` 参数可用
- [ ] `--max_attempts` 参数可用
- [ ] `--output_format` 参数可用
- [ ] `--generate_report` 参数可用
- [ ] 质量评估函数工作正常
- [ ] 全局筛选逻辑正确
- [ ] 数量保证（恰好 `target_count` 个）
- [ ] 实时进度显示
- [ ] 成功率统计
- [ ] 质量分布统计
- [ ] 多跳分布统计

### 输出文件

- [ ] `qualified_results.jsonl` 正确生成
- [ ] `all_results.jsonl` 正确生成
- [ ] `quality_report.json` 正确生成（如果启用）
- [ ] 单独的JSON文件正确生成（如果output_format=json）

### 文档

- [ ] `README.md` 完整
- [ ] `README_QUALITY_FILTER.md` 完整
- [ ] `CHANGES.md` 完整
- [ ] `COMPARISON.md` 完整
- [ ] `SUMMARY.md` 完整

### 测试

- [ ] `test_quality_filter.py` 通过
- [ ] 端到端测试通过
- [ ] 向后兼容性验证

---

## 🎉 完成

如果所有检查都通过，恭喜！全局质量筛选功能已经成功实现！

**下一步**：
1. 阅读 `README_QUALITY_FILTER.md` 了解详细使用方法
2. 运行 `bash run_example.sh` 尝试生成
3. 根据需要调整质量标准（修改 `evaluate_overall_quality` 函数）

**开始使用吧！** 🚀
