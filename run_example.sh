#!/bin/bash
# 半导体QA生成系统 - 示例运行脚本（带质量筛选）

# ============ 配置区域 ============

# 输入输出
INPUT_FILE="./data/semiconductor_qa.jsonl"
OUTPUT_DIR="./generated_qa_results"
MODEL_PATH="/path/to/Qwen2.5-14B-Instruct"

# 生成参数
TARGET_COUNT=100          # 目标生成数量
QUALITY_FILTER="high"     # 质量过滤器: high, medium+, all
BATCH_SIZE=4              # 并发数
MAX_ATTEMPTS=300          # 最大尝试次数

# 功能开关
USE_EMBEDDING=false       # 是否使用语义embedding
GENERATE_REPORT=true      # 是否生成质量报告
DEBUG_MODE=true           # 是否启用调试模式

# ============ 检查环境 ============

echo "================================"
echo "半导体QA生成系统 - 带质量筛选"
echo "================================"
echo ""

# 检查输入文件
if [ ! -f "$INPUT_FILE" ]; then
    echo "[ERROR] 输入文件不存在: $INPUT_FILE"
    echo "请修改 INPUT_FILE 变量指向正确的路径"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "[ERROR] Python未安装"
    exit 1
fi

echo "[✓] 环境检查通过"
echo ""

# ============ 构建命令 ============

CMD="python main_final_new.py \
    --input \"$INPUT_FILE\" \
    --output \"$OUTPUT_DIR\" \
    --model_path \"$MODEL_PATH\" \
    --target_count $TARGET_COUNT \
    --quality_filter $QUALITY_FILTER \
    --batch_size $BATCH_SIZE \
    --max_attempts $MAX_ATTEMPTS \
    --output_format jsonl"

# 添加可选参数
if [ "$USE_EMBEDDING" = true ]; then
    CMD="$CMD --use-embedding"
fi

if [ "$GENERATE_REPORT" = true ]; then
    CMD="$CMD --generate_report"
fi

if [ "$DEBUG_MODE" = true ]; then
    CMD="$CMD --debug"
fi

# ============ 显示配置 ============

echo "运行配置："
echo "  输入文件: $INPUT_FILE"
echo "  输出目录: $OUTPUT_DIR"
echo "  模型路径: $MODEL_PATH"
echo ""
echo "生成参数："
echo "  目标数量: $TARGET_COUNT 个（$QUALITY_FILTER 质量）"
echo "  并发数: $BATCH_SIZE"
echo "  最大尝试: $MAX_ATTEMPTS"
echo ""
echo "功能配置："
echo "  语义embedding: $([ "$USE_EMBEDDING" = true ] && echo "✓" || echo "✗")"
echo "  质量报告: $([ "$GENERATE_REPORT" = true ] && echo "✓" || echo "✗")"
echo "  调试模式: $([ "$DEBUG_MODE" = true ] && echo "✓" || echo "✗")"
echo ""

# ============ 确认运行 ============

read -p "是否开始生成？(y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# ============ 运行 ============

echo ""
echo "================================"
echo "开始生成..."
echo "================================"
echo ""

START_TIME=$(date +%s)

eval $CMD

EXIT_CODE=$?

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# ============ 结果统计 ============

echo ""
echo "================================"
echo "生成完成"
echo "================================"
echo ""
echo "总耗时: $((ELAPSED / 60)) 分钟 $((ELAPSED % 60)) 秒"

if [ -f "$OUTPUT_DIR/qualified_results.jsonl" ]; then
    QUALIFIED_COUNT=$(wc -l < "$OUTPUT_DIR/qualified_results.jsonl")
    echo "合格QA: $QUALIFIED_COUNT 个"
fi

if [ -f "$OUTPUT_DIR/all_results.jsonl" ]; then
    TOTAL_ATTEMPTS=$(wc -l < "$OUTPUT_DIR/all_results.jsonl")
    echo "总尝试: $TOTAL_ATTEMPTS 次"
    
    if [ -f "$OUTPUT_DIR/qualified_results.jsonl" ]; then
        SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($QUALIFIED_COUNT/$TOTAL_ATTEMPTS)*100}")
        echo "成功率: ${SUCCESS_RATE}%"
    fi
fi

if [ -f "$OUTPUT_DIR/quality_report.json" ]; then
    echo ""
    echo "质量分布:"
    python3 -c "
import json
with open('$OUTPUT_DIR/quality_report.json') as f:
    report = json.load(f)
    for quality, count in report['summary']['quality_distribution'].items():
        print(f'  {quality}: {count}')
" 2>/dev/null || echo "  (需要Python查看详细报告)"
fi

echo ""
echo "输出目录: $OUTPUT_DIR"
echo ""

# ============ 快速查看 ============

if [ $EXIT_CODE -eq 0 ]; then
    read -p "是否查看第一个生成的QA？(y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "$OUTPUT_DIR/qualified_results.jsonl" ]; then
            echo ""
            echo "================================"
            echo "第一个生成的QA："
            echo "================================"
            head -n 1 "$OUTPUT_DIR/qualified_results.jsonl" | python3 -m json.tool 2>/dev/null || cat
        fi
    fi
fi

exit $EXIT_CODE
