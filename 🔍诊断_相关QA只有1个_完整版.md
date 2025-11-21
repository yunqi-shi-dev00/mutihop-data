# 🔍 诊断：相关QA实体列表只有1个（完整版）

**问题**：用户看到`相关QA实体列表`只有1个QA  
**诊断时间**：2025-11-19  
**已完成**：✅ 添加debug输出 + 进一步优化

---

## 💡 **关键理解**

### `相关QA实体列表`是什么？

```
相关QA实体列表：
- [QA-8691] (ID: 8691)  ← 这是什么？
```

**不是**：
- ❌ "可以选择的候选QA"（SELECT时会找30个候选）
- ❌ "知识库中所有相关的QA"

**而是**：
- ✅ **"当前多跳问题已经组合进去的源QA"**
- ✅ 等于最终JSON中的`source_qa_ids`

**初始值**：
- 初始化后只有1个root_entity是**正常的**！
- SELECT成功后会增加到2个、3个...

---

## 📊 **执行流程**

### 初始化（只有1个是正常的）

```python
# Step 1: 提取根实体
root_id = 8691
memory.relevant = [QA-8691]  # ← 初始只有1个

# 显示
相关QA实体列表：
- [QA-8691] (ID: 8691)  ← ✅ 正常！
```

---

### SELECT尝试（会找30个候选）

```python
# Step 2: SELECT
target = memory.relevant[0]  # QA-8691

# ⭐⭐ 关键：SELECT会找30个候选，不是1个！
candidates = find_related_qas(QA-8691, top_k=30)  # [QA-2048, QA-3072, ...]

print("找到 30 个候选邻居")  # ← ✅ 候选充足
print("排除已存在的，剩余 29 个候选")

neighbor = random.choice(candidates[:5])  # 从前5个中选
# neighbor = QA-2048

# 桥联、多跳生成、筛选、测试...
```

**关键**：SELECT时会找30个候选邻居，但用户看到的`memory.relevant`还是1个！

---

### SELECT成功（增加到2个）

```python
# 如果桥联、筛选、测试都通过
memory.relevant = [QA-8691, QA-2048]  # ← 增加到2个

# 显示
相关QA实体列表：
- [QA-8691] (ID: 8691)
- [QA-2048] (ID: 2048)  ← ✅ 新增
```

---

### SELECT失败（还是1个）

```python
# 如果桥联失败、筛选失败或测试未通过
memory.relevant = [QA-8691]  # ← 还是1个

# 显示
相关QA实体列表：
- [QA-8691] (ID: 8691)  ← 还是1个
```

---

## 🔍 **诊断步骤**

### 步骤1：运行带debug的测试

```bash
python main_final_new.py \
    --input /mnt/workspace/LLM/ldd/多跳数据/data/QA.jsonl \
    --output ./诊断测试 \
    --target_count 5 \
    --use-embedding \
    --debug | tee 诊断.log
```

---

### 步骤2：检查日志，找到原因

#### 检查1：KB大小

```bash
grep "加载.*个QA" 诊断.log

# 应该看到：
# 加载了 1000 个QA  ← ✅ KB充足
# 加载了 5 个QA     ← ❌ KB太小
```

---

#### 检查2：候选数量

```bash
grep "找到.*个候选邻居" 诊断.log | head -10

# 应该看到：
# [SELECT] 找到 30 个候选邻居  ← ✅ 候选充足
# [SELECT] 找到 1 个候选邻居   ← ❌ 候选太少
```

---

#### 检查3：保底机制

```bash
grep "保底补充" 诊断.log | head -10

# 应该看到：
# [KB] 保底补充：embedding找到5个，补充25个，总计30个  ← ✅ 保底生效
# [KB] ⚠️ 无可补充的QA（KB总数: 2）  ← ❌ KB太小
```

---

#### 检查4：失败原因

```bash
# 桥联失败
grep -c "桥联分数过低" 诊断.log

# 筛选失败
grep -c "未通过筛选" 诊断.log

# 测试失败
grep -c "测试未通过" 诊断.log

# 看看哪个最多
```

---

## 🔧 **根据诊断结果，采取行动**

### 情况1：KB太小

**日志**：
```
加载了 5 个QA
[KB] ⚠️ 无可补充的QA（KB总数: 5）
```

**解决**：
```bash
# 添加更多QA到知识库
# 或者降低target_count
```

---

### 情况2：候选充足，但桥联失败多

**日志**：
```
[SELECT] 找到 30 个候选邻居  ← ✅ 候选充足
[SELECT] ✗ 桥联分数过低 (1 < 2)  ← ❌ 桥联失败（出现10+次）
```

**解决**：已自动放宽阈值（3→2）

如果还是失败多，可以进一步放宽：

<function_calls>
<invoke name="StrReplace">
<parameter name="file_path">/workspace/agent_final_new.py