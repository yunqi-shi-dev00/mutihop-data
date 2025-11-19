bash# 基础依赖
pip install asyncio aiohttp requests numpy transformers tqdm

# 选择一个推理框架（二选一）
pip install vllm            # 推荐：更成熟稳定
# 或
pip install "sglang[all]"   # 更快，但文档较少
步骤2: 启动模型服务
方案A: 使用vLLM（推荐）
bash# 在阿里云服务器上启动vLLM服务
CUDA_VISIBLE_DEVICES=2,3
python -m vllm.entrypoints.openai.api_server \
    --model /mnt/storage/models/Qwen/Qwen/Qwen3-235B-A22B-Instruct-2507 \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 32768 \
    --max-num-batched-tokens 16384 \
    --gpu-memory-utilization 0.9 \
    --tensor-parallel-size 2

/mnt/data/LLM/lhy/models/Qwen/Qwen2.5-0.5B-Instruct
/mnt/storage/models/Qwen/Qwen/Qwen3-235B-A22B-Instruct-2507
参数说明:

--model: 本地模型路径（例如 /home/models/Qwen2.5-32B-Instruct）
--host 0.0.0.0: 允许外部访问
--port 8000: 端口号
--gpu-memory-utilization 0.9: GPU显存使用率
--tensor-parallel-size: GPU数量（单卡=1，双卡=2）

方案B: 使用SGLang
bashpython -m sglang.launch_server \
    --model-path /path/to/your/Qwen2.5-32B-Instruct \
    --host 0.0.0.0 \
    --port 30000 \
    --tp 1
步骤3: 测试服务是否启动成功
bash# 测试vLLM
curl http://localhost:8000/v1/models

# 测试SGLang
curl http://localhost:30000/get_model_info



步骤4: 运行QA生成脚本
使用vLLM:
python semiconductor_qa_agent.py \
    --input /mnt/workspace/LLM/ldd/多跳数据/data/QA.jsonl \
    --output ./generated_qa \
    --model_path /mnt/data/LLM/lhy/models/Qwen/Qwen2.5-14B-Instruct \
    --server_type vllm \
    --host localhost \
    --port 8000 \
    --batch_size 4 \
    --total 10 \
    --max_turns 10
使用SGLang:
bashpython semiconductor_qa_agent.py \
    --input semiconductor_qa.jsonl \
    --output ./generated_qa \
    --model_path Qwen2.5-32B-Instruct \
    --server_type sglang \
    --host localhost \
    --port 30000 \
    --batch_size 16 \
    --total 50



python semiconductor_qa_agent.py \
    --input /mnt/workspace/LLM/ldd/多跳数据/data/QA.jsonl \
    --output test/ \
    --model_path /mnt/storage/models/Qwen/Qwen/Qwen3-235B-A22B-Instruct-2507 \
    --target_count 10 \
    --quality_filter high \
    --output_format json \
    --batch_size 4 \
    --max_turns 10 \
    --generate_report