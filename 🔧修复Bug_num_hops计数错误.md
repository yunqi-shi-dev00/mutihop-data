# 🔧 修复Bug：num_hops计数错误

**Bug编号**：Bug 8  
**发现时间**：2025-11-19  
**严重程度**：🟡 中等（不影响功能，但误导性强）  
**修复状态**：✅ 已修复

---

## 🐛 **Bug现象**

用户发现生成的JSON中：

```json
{
  "num_hops": 5,           // ← 显示5跳
  "source_qa_ids": [5967], // ← 只有1个源QA
  "action_stats": {
    "SELECT": 15           // 执行了15次SELECT
  }
}
```

**矛盾**：
- `num_hops = 5` 应该意味着5个源QA组合
- 但 `source_qa_ids` 只有1个
- **严重不一致！**

---

## 🔍 **根本原因**

### 错误的计数逻辑

**代码**：`agent_final_new.py` 第746行 + 第990行 + 第1049行

```python
# 初始化
num_hops = 1
memory.relevant = [root_entity]  # 1个实体

# 迭代循环
for turn in range(max_turns):
    if action['action'] == 'SELECT':
        # ... 多跳生成、筛选、答案重生成 ...
        
        num_hops += 1  # ← Bug：无条件累加
        
        # 测试
        if correct_count >= 2:
            memory = memory_new  # ← 只有测试通过才更新memory
        else:
            # ← Bug：测试未通过，memory不更新，但num_hops已经+1了！
            print("[INFO] 测试未通过")

# 输出
output = {
    'num_hops': num_hops,  # ← 5（累积值）
    'source_qa_ids': [e.id for e in memory.relevant],  # ← [5967]（只有1个）
}
```

### 问题分析

| 变量 | 含义 | 值 |
|------|------|-----|
| `num_hops` | **SELECT执行成功的累积次数** | 5 |
| `len(memory.relevant)` | **最终通过测试的实体数量** | 1 |
| `source_qa_ids` | **最终的源QA列表** | [5967] |

**根本矛盾**：
- `num_hops`记录的是**尝试**的跳数
- `source_qa_ids`记录的是**成功**的实体
- **两者不一致！**

---

## 📊 **用户情况复现**

### 执行流程

| 轮次 | Action | num_hops | memory.relevant | 测试结果 | memory更新 |
|------|--------|----------|-----------------|----------|------------|
| 1 | none | 1 | [5967] | - | - |
| 2 | SELECT | 2 | [5967, ???] | ❌ 1/4 | ❌ 不更新 |
| 3 | SELECT | 3 | [5967, ???] | ❌ 0/4 | ❌ 不更新 |
| 4 | SELECT | 4 | [5967, ???] | ❌ 1/4 | ❌ 不更新 |
| 5 | SELECT | 5 | [5967, ???] | ❌ 0/4 | ❌ 不更新 |
| ... | ... | ... | ... | ... | ... |
| 16 | - | 5 | [5967] | - | - |

**结论**：
- SELECT执行了4次，`num_hops`从1增加到5
- 但这4次的**测试都未通过**（正确率<2/4）
- 所以`memory`从未更新，还是初始的`[5967]`
- **num_hops=5，但source_qa_ids只有1个！**

---

## ✅ **修复方案**

### 修改1：使用最终实体数量

**文件**：`agent_final_new.py` 第1039-1060行

```python
# Step 4: 保存
# ========================================
# 🔧 修复Bug：num_hops计数错误
# 修复时间：2025-11-19
# 问题：num_hops是累积值，但source_qa_ids是最终的实体列表，两者不一致
# 解决：num_hops应该等于最终memory.relevant的长度
# ========================================
final_num_hops = len(memory.relevant)  # ⭐ 使用最终的实体数量
# ========================================

output = {
    'uid': memory.uid,
    'question': memory.qa['question'],
    'answer': memory.qa['answer'],
    'source_qa_ids': [e.id for e in memory.relevant],
    'num_hops': final_num_hops,  # ⭐ 修复：使用最终数量，不是累积值
    'num_hops_attempted': num_hops,  # 🆕 新增：记录尝试的跳数
    ...
}
```

**效果**：
```json
{
  "num_hops": 1,              // ⭐ 最终的实体数量
  "num_hops_attempted": 5,    // 🆕 尝试的跳数
  "source_qa_ids": [5967]     // ✅ 一致！
}
```

---

### 修改2：更新打印输出

**文件**：`agent_final_new.py` 第1075行

```python
print(f"\n[DONE] 已保存: {output_file}")
print(f"       问题: {memory.qa['question'][:80]}...")
print(f"       跳数: {final_num_hops} (尝试: {num_hops})")  # ⭐ 显示最终和尝试
print(f"       答案长度: {len(memory.qa['answer'])} 字符")
```

**效果**：
```
[DONE] 已保存: ./output/xxx.json
       问题: 在熔盐辅助CVD法合成MoS₂/NbS₂范德华异质结...
       跳数: 1 (尝试: 5)  ← ✅ 清晰显示最终和尝试次数
       答案长度: 1234 字符
```

---

## 📊 **修复前后对比**

### 修复前

```json
{
  "num_hops": 5,              // ❌ 误导：以为有5个源QA
  "source_qa_ids": [5967]     // 实际只有1个
}
```

**问题**：用户看到`num_hops=5`，会以为是5跳问题，但实际只有1跳

---

### 修复后

```json
{
  "num_hops": 1,              // ✅ 正确：最终有1个源QA
  "num_hops_attempted": 5,    // 🆕 额外信息：尝试了5次
  "source_qa_ids": [5967]     // ✅ 一致
}
```

**优点**：
- ✅ `num_hops`与`source_qa_ids`长度一致
- ✅ 新增`num_hops_attempted`记录尝试次数
- ✅ 不会误导用户

---

## 🎯 **字段含义（修复后）**

| 字段 | 含义 | 示例 |
|------|------|------|
| `num_hops` | **最终成功的跳数** | 1 |
| `num_hops_attempted` | **尝试的跳数（累积）** | 5 |
| `source_qa_ids` | **最终的源QA列表** | [5967] |
| `len(source_qa_ids)` | **源QA数量** | 1 |

**关系**：
- `num_hops = len(source_qa_ids)` ✅
- `num_hops_attempted >= num_hops` ✅

---

## 💡 **为什么会出现num_hops=5但只有1个QA？**

### 典型原因

1. **测试标准太严**：
   - 需要4次测试中至少2次正确
   - 多跳问题往往更难，正确率低
   - 导致大量SELECT虽然执行了，但测试未通过

2. **问题质量不高**：
   - 桥联不合理
   - 问题筛选通过但答案错误
   - LLM生成的测试答案不正确

3. **答案不够准确**：
   - 答案重生成后偏离了原始信息
   - LLM judge判断不准确

### 改进建议

如果经常出现这种情况，可以：

1. **降低测试标准**：
   ```python
   if correct_count >= 1:  # 从2改为1
       memory = memory_new
   ```

2. **优化问题筛选**：
   - 确保筛选通过的问题质量高
   - 减少激进优化的放宽程度

3. **优化答案生成**：
   - 确保答案严格基于子QA
   - 提高LLM judge的准确性

---

## 🧪 **测试验证**

### 测试用例

**场景**：SELECT执行3次，2次测试通过，1次未通过

```
初始：memory.relevant = [QA-1]，num_hops = 1

轮1：SELECT → memory.relevant = [QA-1, QA-2]，num_hops = 2，测试通过✅ → memory更新
轮2：SELECT → memory.relevant = [QA-1, QA-2, QA-3]，num_hops = 3，测试通过✅ → memory更新
轮3：SELECT → memory.relevant = [QA-1, QA-2, QA-3, QA-4]，num_hops = 4，测试失败❌ → memory不更新

最终：memory.relevant = [QA-1, QA-2, QA-3]（3个）
```

**修复前**：
```json
{
  "num_hops": 4,                     // ❌ 错误
  "source_qa_ids": [1, 2, 3]         // 只有3个
}
```

**修复后**：
```json
{
  "num_hops": 3,                     // ✅ 正确
  "num_hops_attempted": 4,           // 🆕 记录尝试
  "source_qa_ids": [1, 2, 3]         // ✅ 一致
}
```

---

## 📝 **修改位置**

| 修改 | 文件 | 行号 | 内容 |
|------|------|------|------|
| **1** | `agent_final_new.py` | 1039-1060 | 使用`len(memory.relevant)`计算num_hops |
| **2** | `agent_final_new.py` | 1075 | 打印输出显示最终和尝试次数 |

**查看修改**：
```bash
grep -n "num_hops计数错误" agent_final_new.py
# 输出：1040:            # 🔧 修复Bug：num_hops计数错误
```

---

## 🎉 **总结**

### ✅ 修复内容

- **问题**：`num_hops`是累积值，与`source_qa_ids`长度不一致
- **修复**：`num_hops = len(memory.relevant)`，使用最终实体数量
- **新增**：`num_hops_attempted`字段，记录尝试次数
- **效果**：`num_hops`与`source_qa_ids`长度始终一致

### 🎯 修复后的含义

- **`num_hops`**：最终成功的跳数（等于source_qa_ids长度）
- **`num_hops_attempted`**：尝试的跳数（包括测试未通过的）
- **`source_qa_ids`**：最终的源QA列表

---

**Bug已修复！现在`num_hops`准确反映最终的多跳数量！** ✅
