# vLLM 本地大模型使用说明 🚀

## 第一步：启动 vLLM 服务

### 基本启动命令

```bash
python -m vllm.entrypoints.openai.api_server \
    --model /path/to/your/model \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name your-model-name
```

### 推荐启动命令（带常用参数）

```bash
python -m vllm.entrypoints.openai.api_server \
    --model /path/to/your/model \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name your-model-name \
    --dtype auto \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9 \
    --tensor-parallel-size 1
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--model` | **本地模型路径** | `/home/models/qwen2-7b` |
| `--host` | 服务监听地址 | `0.0.0.0`（所有网卡） |
| `--port` | 服务端口 | `8000` |
| `--served-model-name` | 模型服务名称 | `qwen2-7b` |
| `--dtype` | 数据类型 | `auto` / `float16` / `bfloat16` |
| `--max-model-len` | 最大上下文长度 | `8192` / `16384` / `32768` |
| `--gpu-memory-utilization` | GPU显存使用率 | `0.9`（90%） |
| `--tensor-parallel-size` | 张量并行GPU数量 | `1`（单卡） / `2`（双卡） |

---

## 第二步：验证 vLLM 服务

### 检查服务是否启动

```bash
# 查看模型列表
curl http://localhost:8000/v1/models

# 应该返回类似：
# {
#   "object": "list",
#   "data": [
#     {
#       "id": "your-model-name",
#       "object": "model",
#       ...
#     }
#   ]
# }
```

### 测试生成

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model-name",
    "prompt": "你好，请介绍一下半导体",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

---

## 第三步：运行代码连接 vLLM

### 方式1：使用默认配置（推荐）

如果vLLM在本地8000端口，直接运行：

```bash
python main_final.py \
    --input 你的数据.jsonl \
    --output ./生成结果 \
    --model_path /path/to/your/model \
    --tokenizer_path /path/to/your/model
```

**注意**：
- `--model_path` 和 `--tokenizer_path` 可以是同一个路径
- 代码默认连接 `http://localhost:8000/v1`

### 方式2：指定 API 地址

如果vLLM在其他地址或端口：

```bash
python main_final.py \
    --input 你的数据.jsonl \
    --output ./生成结果 \
    --model_path /path/to/your/model \
    --tokenizer_path /path/to/your/model \
    --api_base http://your-server:8000/v1
```

### 方式3：调整并发数

如果GPU显存有限，降低并发：

```bash
python main_final.py \
    --input 你的数据.jsonl \
    --output ./生成结果 \
    --model_path /path/to/your/model \
    --tokenizer_path /path/to/your/model \
    --batch_size 2 \
    --max_concurrent 2
```

---

## 常见配置示例

### 示例1：Qwen2-7B（单卡）

**启动vLLM**：
```bash
python -m vllm.entrypoints.openai.api_server \
    --model /data/models/Qwen2-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name qwen2-7b \
    --dtype auto \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9
```

**运行代码**：
```bash
python main_final.py \
    --input ./data/QA.jsonl \
    --output ./generated_qa \
    --model_path /data/models/Qwen2-7B-Instruct \
    --tokenizer_path /data/models/Qwen2-7B-Instruct \
    --batch_size 4 \
    --target_count 100 \
    --max_hops 3 \
    --debug
```

### 示例2：Qwen2-72B（多卡）

**启动vLLM**（4卡张量并行）：
```bash
python -m vllm.entrypoints.openai.api_server \
    --model /data/models/Qwen2-72B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name qwen2-72b \
    --dtype bfloat16 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.95 \
    --tensor-parallel-size 4
```

**运行代码**：
```bash
python main_final.py \
    --input ./data/QA.jsonl \
    --output ./generated_qa \
    --model_path /data/models/Qwen2-72B-Instruct \
    --tokenizer_path /data/models/Qwen2-72B-Instruct \
    --batch_size 8 \
    --target_count 100 \
    --max_concurrent 8 \
    --max_hops 3 \
    --debug
```

### 示例3：Llama3-8B（单卡）

**启动vLLM**：
```bash
python -m vllm.entrypoints.openai.api_server \
    --model /data/models/Llama-3-8B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name llama3-8b \
    --dtype auto \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9
```

**运行代码**：
```bash
python main_final.py \
    --input ./data/QA.jsonl \
    --output ./generated_qa \
    --model_path /data/models/Llama-3-8B-Instruct \
    --tokenizer_path /data/models/Llama-3-8B-Instruct \
    --batch_size 4 \
    --target_count 100 \
    --max_hops 3 \
    --debug
```

---

## 参数调优建议

### GPU 显存有限（<24GB）

```bash
# vLLM启动
--max-model-len 4096 \              # 降低上下文长度
--gpu-memory-utilization 0.85       # 降低显存使用率

# 代码运行
--batch_size 2 \                    # 降低并发
--max_concurrent 2
```

### GPU 显存充足（≥40GB）

```bash
# vLLM启动
--max-model-len 16384 \             # 增加上下文长度
--gpu-memory-utilization 0.95       # 提高显存使用率

# 代码运行
--batch_size 8 \                    # 增加并发
--max_concurrent 8
```

### 追求速度

```bash
# vLLM启动
--gpu-memory-utilization 0.95 \
--max-num-batched-tokens 8192 \
--max-num-seqs 256

# 代码运行
--batch_size 8 \
--max_concurrent 8 \
--disable_qa_filtering \            # 禁用筛选
--disable_answer_regeneration       # 禁用重生成
```

### 追求质量

```bash
# 代码运行
--batch_size 2 \                    # 降低并发（减少OOM风险）
--max_concurrent 2 \
--enable_dynamic_planning \         # 启用动态规划
--enable_qa_filtering \             # 启用筛选
--enable_answer_regeneration \      # 启用重生成
--max_hops 3 \                      # 最多3跳
--debug                             # 查看过程
```

---

## 完整工作流程

### 1. 启动 vLLM（后台运行）

```bash
# 使用 nohup 后台运行
nohup python -m vllm.entrypoints.openai.api_server \
    --model /path/to/your/model \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name your-model \
    --dtype auto \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9 \
    > vllm.log 2>&1 &

# 查看日志
tail -f vllm.log
```

### 2. 等待模型加载完成

```bash
# 等待出现类似日志：
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000

# 或者测试连接
curl http://localhost:8000/v1/models
```

### 3. 运行生成代码

```bash
python main_final.py \
    --input ./data/QA.jsonl \
    --output ./generated_qa \
    --model_path /path/to/your/model \
    --tokenizer_path /path/to/your/model \
    --batch_size 4 \
    --target_count 100 \
    --max_hops 3 \
    --enable_dynamic_planning \
    --enable_qa_filtering \
    --enable_answer_regeneration \
    --debug
```

### 4. 监控生成进度

代码会实时输出进度：
```
[Agent] 最大迭代轮数: 16, 最多组合问题数: 3
[Agent] ✓ 启用动态规划策略
[Agent] ✓ 启用问题筛选（在SELECT后执行）
[Agent] ✓ 启用答案重生成（在SELECT后执行，强调围绕子QA）
[Agent] ✓ 启用调试模式

开始生成QA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
进度: 10/100 (10.0%)
...
```

---

## 常见问题

### Q1: vLLM启动失败，报错 CUDA out of memory？

**A**: 降低显存使用率或减少上下文长度
```bash
--gpu-memory-utilization 0.8 \
--max-model-len 4096
```

### Q2: 代码连接不上vLLM？

**A**: 检查以下几点
1. vLLM服务是否启动：`curl http://localhost:8000/v1/models`
2. 端口是否正确：检查 `--port` 和 `--api_base`
3. 防火墙是否阻挡

### Q3: 生成速度很慢？

**A**: 尝试以下优化
1. 增加并发：`--batch_size 8 --max_concurrent 8`
2. 禁用筛选和重生成（如果不需要最高质量）
3. 使用更小的模型或更多GPU

### Q4: `model_path` 和 `tokenizer_path` 有什么区别？

**A**: 
- `model_path`：用于代码内部的一些工具函数（如分词）
- `tokenizer_path`：用于加载tokenizer
- **大多数情况下，两者设置为同一个模型目录即可**

### Q5: 支持哪些模型？

**A**: vLLM支持的所有模型都可以用，常见的有：
- Qwen / Qwen2 系列
- Llama / Llama2 / Llama3 系列
- ChatGLM 系列
- Baichuan 系列
- InternLM 系列
- 等等...

---

## 快速开始（一条命令）

### 适用于大多数情况

```bash
# 1. 启动vLLM（替换模型路径）
python -m vllm.entrypoints.openai.api_server \
    --model /你的模型路径 \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype auto

# 2. 运行代码（替换数据和模型路径）
python main_final.py \
    --input 你的数据.jsonl \
    --output ./生成结果 \
    --model_path /你的模型路径 \
    --tokenizer_path /你的模型路径
```

**就这么简单！** 🎉

---

## 总结

1. **启动vLLM**：`python -m vllm.entrypoints.openai.api_server --model 你的模型路径`
2. **运行代码**：`python main_final.py --input 数据 --output 结果 --model_path 模型路径 --tokenizer_path 模型路径`
3. **model_path 和 tokenizer_path 通常设置为同一个路径（你的本地模型目录）**
4. **代码会自动连接本地8000端口的vLLM服务**
