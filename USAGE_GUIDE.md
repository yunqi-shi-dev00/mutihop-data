# 快速使用指南

## 📋 文件说明

### 新建的模块化文件（推荐使用）
- `prompts.py` - 所有Prompt模板
- `knowledge_base.py` - 知识库和实体类
- `llm_client.py` - LLM客户端
- `agent.py` - 增强Agent（核心逻辑）
- `utils.py` - 工具函数
- `main.py` - 主程序入口
- `requirements.txt` - 依赖列表
- `README_NEW.md` - 完整文档

### 原有文件（保留）
- `semiconductor_qa_agent.py` - 原版完整代码（未修改）

---

## 🚀 快速开始

### 1. 启动vLLM服务

```bash
# 示例：使用2张GPU启动vLLM
CUDA_VISIBLE_DEVICES=0,1 python -m vllm.entrypoints.openai.api_server \
    --model /mnt/storage/models/Qwen/Qwen2.5-32B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 2
```

### 2. 运行生成（基础模式）

```bash
python main.py \
    --input /path/to/QA.jsonl \
    --output ./generated_qa \
    --model_path /mnt/storage/models/Qwen/Qwen2.5-32B-Instruct \
    --tokenizer_path /mnt/data/LLM/lhy/models/Qwen/Qwen2.5-14B-Instruct \
    --batch_size 4 \
    --target_count 10
```

### 3. 运行生成（完整增强模式）

```bash
python main.py \
    --input /path/to/QA.jsonl \
    --output ./generated_qa \
    --model_path /mnt/storage/models/Qwen/Qwen2.5-32B-Instruct \
    --tokenizer_path /mnt/data/LLM/lhy/models/Qwen/Qwen2.5-14B-Instruct \
    --batch_size 4 \
    --target_count 100 \
    --max_turns 10 \
    --enable_dynamic_planning \
    --enable_qa_filtering \
    --enable_answer_regeneration \
    --debug \
    --merge_output
```

---

## ✨ 核心改进

### 1. 保留所有原版功能 ✅
- SELECT/FUZZ/EXIT/BRAINSTORM Action机制
- 迭代式QA构建
- 质量验证和测试
- 动态规划策略

### 2. 新增多跳QA生成 🆕
- 支持2-3跳问答组合
- 完整推理步骤记录
- 使用增强版Prompt模板

### 3. 问题筛选流程 🆕
- 6大评估标准（因果性、周密性、可追溯性、通用性、完整性、单一性）
- 自动筛选高质量问题
- 详细评估报告

### 4. 答案重新生成 🆕
- 基于子问答对重新生成
- 参考推理步骤
- 置信度评估

### 5. Debug模式 🆕
- 详细阶段标注
- 实时进度显示
- 错误诊断信息

---

## 🎯 生成流程

```
原版流程:
选择根QA → 构建基础QA → 迭代优化(Action) → 验证 → 保存

增强流程:
选择根QA → 构建基础QA → 迭代优化(Action) → 多跳生成 → 问题筛选 → 答案重生成 → 保存
         ↑                    ↓                    ↓           ↓              ↓
      动态规划          SELECT/FUZZ/EXIT      2-3跳组合    评估标准      推理链答案
```

---

## 📊 输出示例

每个生成的QA包含：
- `question`: 最终问题
- `answer`: 最终答案
- `source_qa_ids`: 来源QA ID列表
- `source_papers`: 来源论文列表
- `has_multihop`: 是否多跳QA
- `passed_filtering`: 是否通过筛选
- `answer_regenerated`: 答案是否重新生成
- `multihop_metadata`: 多跳元数据（推理步骤、质量指标等）

---

## 🔧 功能开关

所有新功能都可以独立开关：

```bash
# 仅原版功能
python main.py ... --disable_dynamic_planning --disable_qa_filtering --disable_answer_regeneration

# 仅动态规划
python main.py ... --enable_dynamic_planning --disable_qa_filtering --disable_answer_regeneration

# 仅问题筛选
python main.py ... --disable_dynamic_planning --enable_qa_filtering --disable_answer_regeneration

# 完整增强（默认）
python main.py ... --enable_dynamic_planning --enable_qa_filtering --enable_answer_regeneration
```

---

## 📝 注意事项

1. **tokenizer路径**: 如果与model路径不同，需要明确指定
2. **批次大小**: 建议从小开始测试（2-4），确保稳定后再增加
3. **调试模式**: 首次运行建议开启`--debug`，观察生成过程
4. **筛选率**: 问题筛选标准严格，通过率约75%，属正常现象
5. **原版代码**: `semiconductor_qa_agent.py`文件未修改，可随时回退

---

## 🎓 更多信息

详细文档请参考 `README_NEW.md`
