# 半导体QA生成系统 - 优化版（真正的融合）

## 🎯 核心思想

**在原版SELECT action内部融合筛选和答案重生成，而不是创建新模式**

---

## ✅ 优化逻辑

### 原版流程（完全保留）
```
迭代循环 {
    选择Action (SELECT/FUZZ/EXIT)
    ↓
    执行Action:
        SELECT: 找QA → 组合 → 得到新QA对
        FUZZ: 模糊化
        EXIT: 退出
    ↓
    验证 → 测试 → 判断
}
```

### 优化版流程（在SELECT内部融合）
```
迭代循环 {
    选择Action (SELECT/FUZZ/EXIT)  ← 不变
    ↓
    执行Action:
        SELECT:  ← 这里是优化点！
            (1) 找相关QA           ← 原版
            (2) 构建link_qa        ← 原版
            (3) 组合QA             ← 原版
                得到参考答案
            (4) 🔧 筛选问题        ← 新增
                不通过 → 跳过此轮
            (5) 🔧 重生成答案      ← 新增
                参考答案 → 最终答案
                (强调：基于子QA，不发散)
            (6) 更新memory         ← 原版
                (用最终答案)
        
        FUZZ: 模糊化           ← 不变
        EXIT: 退出             ← 不变
    ↓
    验证 → 测试 → 判断        ← 不变
}
```

---

## 🔑 关键改进点

### 1. **不是新模式，是真正的融合**
- ❌ 错误理解：迭代后单独做"多跳生成"
- ✅ 正确理解：在SELECT执行时就完成优化

### 2. **多跳自然形成**
- SELECT执行1次 = 2跳QA
- SELECT执行2次 = 3跳QA
- SELECT执行N次 = (N+1)跳QA
- 不需要单独的"多跳生成"逻辑

### 3. **答案准确率提升**
```
原版：
  组合QA → 答案可能不完整 → 直接使用

优化版：
  组合QA → 参考答案 → 基于子QA重生成 → 最终答案
                       ↑
                    强调不发散
                    基于子问答对
                    减少错误
```

### 4. **问题质量提升**
```
原版：
  组合QA → 直接使用

优化版：
  组合QA → 立即筛选（6大标准） → 通过才继续
           不通过 → 跳过此轮
```

---

## 📁 文件结构

### 优化版文件（推荐使用）
- `prompts_optimized.py` - 优化的Prompt模板
  - 组合QA生成参考答案
  - 问题评估（6大标准）
  - 答案重生成（强调基于子QA，不发散）

- `agent_optimized.py` - 优化的Agent
  - 在SELECT内部融合筛选和答案重生成
  - 保持原版核心完全不变

- `main_optimized.py` - 优化的主程序

### 原有文件（保留）
- `prompts.py`, `agent.py`, `main.py` - 之前的版本
- `knowledge_base.py`, `llm_client.py`, `utils.py` - 共用

---

## 🚀 快速使用

### 基础使用

```bash
python main_optimized.py \
    --input /path/to/QA.jsonl \
    --output ./generated_qa \
    --model_path /path/to/model \
    --tokenizer_path /path/to/tokenizer \
    --batch_size 4 \
    --target_count 10
```

### 完整优化模式

```bash
python main_optimized.py \
    --input /path/to/QA.jsonl \
    --output ./generated_qa \
    --model_path /path/to/model \
    --tokenizer_path /path/to/tokenizer \
    --batch_size 4 \
    --target_count 100 \
    --max_turns 10 \
    --enable_dynamic_planning \
    --enable_qa_filtering \
    --enable_answer_regeneration \
    --debug
```

### 仅原版功能（不优化）

```bash
python main_optimized.py \
    --input /path/to/QA.jsonl \
    --output ./generated_qa \
    --model_path /path/to/model \
    --batch_size 4 \
    --target_count 10 \
    --disable_qa_filtering \
    --disable_answer_regeneration
```

---

## 📊 优化效果

### 答案准确率提升

**原版问题：**
- 组合QA时生成的答案可能不完整
- 没有基于完整的推理链
- 容易遗漏关键信息

**优化后：**
- 组合QA生成"参考答案"
- 基于所有子QA和推理链重新生成"最终答案"
- 强调基于子QA，不发散
- 垂域模型不会引入外部错误

### 问题质量提升

**原版问题：**
- 组合后的问题可能不符合标准
- 浪费后续验证和测试时间

**优化后：**
- 每次SELECT后立即筛选
- 6大评估标准（因果性、周密性、可追溯性、通用性、完整性、单一性）
- 不通过直接跳过，不浪费时间

---

## 🔧 核心代码解析

### SELECT action的优化（agent_optimized.py 第485-620行）

```python
elif action['action'] == 'SELECT':
    # (1-4) 原版逻辑：找QA、构建link_qa、检查重复、组合QA
    ...
    combine_qa_result = await self.combine_qa(...)
    q_new = combine_qa_result['question']
    reference_answer = combine_qa_result['answer']  # 参考答案
    
    # (5) 🔧 优化：立即筛选问题
    if self.enable_qa_filtering:
        eval_result = await self.evaluate_question_inline(...)
        if not eval_result['passed']:
            continue  # 不通过就跳过此轮
    
    # (6) 🔧 优化：立即重生成答案
    if self.enable_answer_regeneration:
        regen_result = await self.regenerate_answer_inline(
            q_new,
            reference_answer,  # 传入参考答案
            memory_new.relevant,  # 所有子QA
            memory_new.statements  # 技术陈述
        )
        
        # 检查答案是否基于子QA
        if grounded_check.get('all_info_from_subqa'):
            final_answer = regen_result['final_answer']
        else:
            final_answer = reference_answer  # 回退
    
    # (7) 更新memory（用最终答案）
    memory_new.qa['answer'] = final_answer  # ⭐ 关键
```

### 答案重生成的Prompt（prompts_optimized.py 第121-220行）

**核心要求：**
```
⚠️ 核心要求：严格基于给定的子问答对，不要发散，不要引入外部知识！

1. 基于子QA，不发散（⚠️ 最重要）
   - ✓ 答案的每一句话都必须有子问答对的支撑
   - ✓ 推理过程必须基于子问答对中的信息
   - ✓ 不得引入子问答对中没有提到的概念、数据、结论
   - ✗ 禁止使用子问答对外的专业知识
   - ✗ 禁止发散到相关但未提及的技术点
   - ✗ 禁止过度发散（垂直领域模型容易引入错误）

2. 完整性
   - 体现推理过程（但要自然，不要生硬列举步骤）
   - 答案长度：80-200字

3. 准确性验证
   - 生成答案后，逐句检查：这句话在子QA中有依据吗？
   - 如果没有依据，必须删除
```

---

## 📈 输出格式

每个生成的QA包含：

```json
{
  "uid": "...",
  "question": "最终问题",
  "answer": "最终答案（重生成的）",
  "source_qa_ids": ["qa_001", "qa_045"],
  "num_hops": 2,
  "qa_filtering_enabled": true,
  "answer_regeneration_enabled": true,
  "action_stats": {
    "SELECT": 1,
    "EXIT": 1
  }
}
```

---

## ❓ 常见问题

### Q1: 和之前的版本有什么区别？

**之前的版本（错误理解）：**
```
迭代循环（原版）
    ↓
【迭代结束】
    ↓
重新生成多跳QA  ← 重复劳动！
    ↓
筛选
    ↓
答案重生成
```

**现在的版本（正确融合）：**
```
迭代循环 {
    SELECT:
        组合 → 筛选 → 答案重生成  ← 在内部完成！
    
    FUZZ/EXIT: 原样不变
}
```

### Q2: 多跳是怎么实现的？

不需要单独实现！SELECT本身就是多跳：
- 第1次SELECT：QA1 + QA2 → 2跳问题
- 第2次SELECT：2跳问题 + QA3 → 3跳问题

### Q3: 为什么强调"基于子QA，不发散"？

因为：
1. 这是垂直领域模型
2. 发散可能引入错误的专业知识
3. 答案必须可追溯到给定的子QA
4. 保证答案准确性

### Q4: 筛选标准是什么？

6大标准：
1. **因果性** - 完整技术逻辑链
2. **周密性** - 科学严谨推理
3. **可追溯性** - 基于子QA
4. **通用性** - 不特指论文 ⭐
5. **完整性** - 全面覆盖
6. **单一性** - 禁止复合问题 ⭐

### Q5: 原版功能会丢失吗？

**绝对不会！**
- Action机制完全不变（SELECT/FUZZ/EXIT/BRAINSTORM）
- 迭代循环结构完全不变
- 验证测试逻辑完全不变
- 只是在SELECT执行时**加了两步**：筛选 + 答案重生成

---

## 🎓 设计原则

### 1. 不破坏原版核心
- Action机制不变
- 迭代循环不变
- 只在执行时加优化

### 2. 在合适的地方加东西
- 不是迭代后加
- 是在SELECT执行时加
- 每次SELECT都经过优化

### 3. 强调基于子QA
- 组合生成参考答案
- 重生成时基于子QA
- 不发散，不引入外部知识

### 4. 功能可独立开关
```bash
# 只用原版
--disable_qa_filtering --disable_answer_regeneration

# 只加筛选
--enable_qa_filtering --disable_answer_regeneration

# 全部优化
--enable_qa_filtering --enable_answer_regeneration
```

---

## 📝 总结

这是一个**真正的融合版本**：

✅ **保持原版核心不变**
- Action机制 100% 保留
- 迭代循环 100% 保留

✅ **在SELECT内部优化**
- 组合 → 参考答案
- 筛选 → 过滤低质量
- 重生成 → 最终答案（基于子QA）

✅ **多跳自然形成**
- 不需要单独逻辑
- SELECT执行N次 = (N+1)跳

✅ **答案准确率提升**
- 基于子QA生成
- 不发散，减少错误
- 适合垂直领域模型

✅ **问题质量提升**
- 6大标准筛选
- 每轮都检查
- 不浪费时间

---

**这才是真正的"在原版基础上优化"，而不是"设计新模式"！** 🎉
