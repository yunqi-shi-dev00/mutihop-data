# 半导体QA生成系统 - 最终版

## ✅ 当前逻辑说明

### 核心流程

```
迭代循环 {
    选择Action (SELECT/FUZZ/EXIT)  ← 原版不变
    ↓
    if action == 'SELECT':
        (1) 收集新子QA → memory.relevant现在有N个子QA
        (2) 用所有N个子QA调用多跳组合模板
        (3) 生成N跳问题（带推理步骤）← 用户给的模板
        (4) 筛选问题（6大标准）← 用户给的模板  
        (5) 重生成答案（强调围绕子QA）← 用户给的模板
        (6) 更新memory
    
    elif action == 'FUZZ':  ← 原版不变
        ...
    
    elif action == 'EXIT':  ← 原版不变
        ...
    
    验证 → 测试  ← 原版不变
}
```

### 关键改进

**1. 每次SELECT用所有子QA生成问题**

```python
# agent_final.py 第196-234行
async def generate_multihop_question(self, all_sub_qas, statements):
    """基于所有已收集的子QA，生成多跳问题"""
    
    num_hops = len(all_sub_qas)  # 当前有几个子QA
    
    # 格式化所有子QA
    single_hop_str = "\n\n".join([
        f"单跳QA-{i+1}:\n问题: ...\n答案: ..."
        for i, qa in enumerate(all_sub_qas)
    ])
    
    # 调用用户给的多跳组合模板
    prompt = SemiconductorQAPrompts.compose_qa_multihop.format(
        num_hops=num_hops,
        single_hop_qas=single_hop_str,
        statements=statements_str
    )
    
    # 返回包含question, answer, reasoning_steps的结果
    return result
```

**2. 多跳自然形成**

```
第1轮SELECT：
  memory.relevant = [QA1, QA2]
  → 调用generate_multihop_question
  → 生成2跳问题

第2轮SELECT：
  memory.relevant = [QA1, QA2, QA3]
  → 调用generate_multihop_question
  → 生成3跳问题
```

---

## 📋 模板完全按用户给的

### 1. 组合生成问答对模板

**位置**：`prompts_final.py` 第59-156行

**关键内容**：

```python
compose_qa_multihop = '''...

<think>
首先，我需要理解这{num_hops}个单跳问答之间的逻辑关系。

让我分析：
1. 识别每个问答的核心技术点
2. 理解它们之间如何连接
3. 确定组合后的推理逻辑链
...
</think>

## 【核心要求】（严格执行）

### 1. 问题设计准则（借鉴专家模板）：

**(1) 因果链完整性**
- 问题需呈现完整技术逻辑链：机制A → 参数B → 现象C

**(2) 通用性（严格执行）**
- 问题必须具有通用性，不局限于特定论文
- 禁止使用"本文"、"本研究"等

**(3) 单一性（严格执行）**
- 问题只包含一个核心疑问点
- 禁止复合问题

错误示例：
"...如何实现高迁移率？并分析其对器件稳定性的影响？"（包含2个问题）

正确示例：
"...氧分压参数如何通过影响氧空位浓度进而调控载流子迁移率和器件长期稳定性？"

### 2. 答案生成准则：

**(1) 完整性（严格执行）**
- 必须完整回答问题的所有方面
- 必须体现{num_hops}步推理过程

**(2) 准确性（严格执行）**
- 必须基于给定的单跳答案逻辑推导

**(3) 通用性（严格执行）**
- 答案具有通用性，不特指论文

### 3. 推理步骤要求：

- 必须包含{num_hops}个清晰的推理步骤
- 每个步骤对应一个单跳问答的核心内容
- 步骤之间要有明确的逻辑连接词

## 【输出格式】

```json
{
  "question": "组合后的{num_hops}跳问题",
  "answer": "参考答案（80-150字）",
  "reasoning_steps": [
    "第一步：...",
    "第二步：..."
  ],
  "quality_indicators": {
    "has_complete_reasoning_chain": true,
    "is_single_question": true,
    "is_universal": true,
    "is_traceable": true,
    "answer_completeness": "complete"
  },
  "metadata": {
    "difficulty": "medium/hard",
    "naturalness": 1-5
  }
}
```
'''
```

---

### 2. 问题评估模板

**位置**：`prompts_final.py` 第158-237行

**完全按用户给的6大标准**：

```python
question_evaluation = """...

## 【评估标准】（认真思考，严格按以下6个标准判断）：

###1. 因果性：
(1) 问题应展现出完整的技术逻辑链

###2. 周密性：
(1) 思维过程要科学且严谨

###3.可追溯性（严格执行）：
(1) 问题必须源于论文内容
(2) 答案也在论文中有描述，但不能特指论文

###4.问题通用性（严格执行）：
(1) 问题必须具有通用性，不局限于文本中，禁止特指论文

示例：
    错误：Nd掺杂Al合金栅极材料经300℃热处理后的电阻率具体数值是多少？
    原因：特指论文，不同材料数值不一样
    
    正确：如何精确调控氧分压参数与后退火温度条件...

(2) 不能引用论文文献或文章自定义的专有名词

###5.完整性：
(1) 问题全面涵盖相关内容
(2) 问题描述简洁凝练
(3) 问题完全独立，不依赖文章
(4) 能基于内容回答，但没有特指论文

###6.单一性（必须严格执行）
(1) 每个问题只包含一个问题，禁止复合问题

---

评判：以上6个标准全部通过才输出【是】，只要有一个不通过就是【否】。

格式：仅输出【是】或者【否】（严格执行！！）
"""
```

---

### 3. 答案重新生成模板

**位置**：`prompts_final.py` 第239-354行

**强调围绕子QA，不发散**：

```python
answer_regeneration = """...

⚠️ **核心要求：严格基于给定的子问答对，不要发散，不要引入外部知识！
尽量让模型围绕子QA写，不要过于发散，因为是垂域通域模型发散可能会引入错误**

# 问题
{question}

# 参考答案（仅作参考，可能不完整）
{reference_answer}

# 子问答对（作为参考文本）
{sub_qa_pairs}

# 推理步骤
{reasoning_steps}

---

<think>
我需要：
1. **仔细阅读所有子问答对的内容**
2. **识别问题需要的推理链条**
3. **逐步构建推理过程**，确保每一步都有子QA支撑
4. **生成完整答案**
5. **检查答案**：是否脱离了子QA的内容？
6. **围绕子QA写**，不要过于发散
</think>

## 【答案生成准则】（严格执行）

### 1. 基于子QA，不发散（⚠️ 最重要）
- ✓ 答案的每一句话都必须有子问答对的支撑
- ✓ 推理过程必须基于子问答对中的信息
- ✓ 不得引入子问答对中没有提到的概念、数据、结论
- ✓ 尽量让模型围绕子QA写，不要过于发散
- ✗ 禁止使用子问答对外的专业知识
- ✗ 禁止发散到相关但未提及的技术点
- ✗ 禁止过度发散（垂域模型容易引入错误）

### 2. 完整性
- ✓ 答案必须完整回答问题的所有方面
- ✓ 答案长度：80-200字

### 3. 推理链体现
- ✓ 答案应自然地体现：通过理解A → 推导到B
- ✓ 使用逻辑连接词

### 4. 通用性
- ✓ 答案具有通用性，不特指论文
- ✗ 禁止使用"本文"、"本研究"等

### 5. 准确性验证
- ✓ 生成答案后，逐句检查：这句话在子QA中有依据吗？
- ✓ 如果没有依据，必须删除

---

输出JSON格式：
```json
{
    "final_answer": "最终答案（80-200字，严格基于子QA）",
    "reasoning_trace": "推理轨迹（30-50字）",
    "confidence": 0.0-1.0,
    "grounded_check": {
        "all_info_from_subqa": true/false,
        "no_external_knowledge": true/false,
        "complete_reasoning": true/false
    }
}
```
"""
```

---

## 🚀 使用方法

### 启动vLLM

```bash
CUDA_VISIBLE_DEVICES=0,1 python -m vllm.entrypoints.openai.api_server \
    --model /path/to/model \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 2
```

### 运行生成

```bash
python main_final.py \
    --input /path/to/QA.jsonl \
    --output ./generated_qa \
    --model_path /path/to/model \
    --tokenizer_path /path/to/tokenizer \
    --batch_size 4 \
    --target_count 100 \
    --max_turns 10 \
    --enable_qa_filtering \
    --enable_answer_regeneration \
    --debug
```

---

## 📊 完整示例

### 第1轮SELECT

```
memory.relevant = [QA1, QA2]  # 收集了2个子QA
↓
调用 generate_multihop_question([QA1, QA2])
↓
使用 compose_qa_multihop 模板（num_hops=2）
↓
生成：
{
  "question": "2跳问题...",
  "answer": "参考答案...",
  "reasoning_steps": ["第一步...", "第二步..."]
}
↓
筛选问题（6大标准）
↓
重生成答案（围绕子QA）
↓
更新memory
```

### 第2轮SELECT

```
memory.relevant = [QA1, QA2, QA3]  # 收集了3个子QA
↓
调用 generate_multihop_question([QA1, QA2, QA3])
↓
使用 compose_qa_multihop 模板（num_hops=3）
↓
生成3跳问题...
```

---

## ✅ 总结

### 核心特点

1. **完全按用户给的模板**
   - 组合模板：{num_hops}个单跳QA → 多跳问题（带推理步骤）
   - 评估模板：6大标准（因果性、周密性、可追溯性、通用性、完整性、单一性）
   - 答案模板：强调围绕子QA，不发散

2. **每次SELECT用所有子QA**
   - 不是只组合2个QA
   - 是用所有已收集的子QA重新生成问题
   - 多跳自然形成

3. **保持原版核心不变**
   - Action机制不变（SELECT/FUZZ/EXIT/BRAINSTORM）
   - 迭代循环不变
   - 只在SELECT执行时用新逻辑

4. **强调不发散**
   - 答案必须基于子QA
   - 垂域模型，不引入外部知识
   - 逐句检查：有依据吗？

---

## 📁 文件列表

**最终版文件（推荐使用）**：
- `prompts_final.py` - 完全按用户给的模板
- `agent_final.py` - 每次SELECT用所有子QA生成多跳问题
- `main_final.py` - 主程序

**共用文件**：
- `knowledge_base.py` - 知识库
- `llm_client.py` - LLM客户端
- `utils.py` - 工具函数
- `requirements.txt` - 依赖

**其他文件（保留）**：
- `semiconductor_qa_agent.py` - 原版代码（未修改）
- 其他版本...

---

**这个版本完全按您的要求实现！** ✅
