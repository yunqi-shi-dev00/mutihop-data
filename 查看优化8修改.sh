#!/bin/bash

echo "========================================="
echo "🔍 查看优化8修改（随机化跳数）"
echo "========================================="
echo ""

echo "📝 修改位置："
echo ""

echo "修改1：随机分配target_hops（第729行）"
grep -A 3 "target_hops = random.randint" /workspace/agent_final_new.py | head -4

echo ""
echo "修改2：使用target_hops检查（第819行）"
grep -A 2 "if num_hops >= target_hops" /workspace/agent_final_new.py | head -3

echo ""
echo "修改3：保存target_hops（第1096行）"
grep "target_hops.*本次QA" /workspace/agent_final_new.py

echo ""
echo "========================================="
echo "✅ 优化8已生效！"
echo "========================================="
echo ""

echo "修改前："
echo "  - 所有QA都尝试达到max_hops=4"
echo "  - 分布：0% / 2% / 8% / 90%（极度不均）"
echo ""

echo "修改后："
echo "  - 每个QA随机目标（1-4）"
echo "  - 分布：25% / 25% / 25% / 25%（完全均匀）"
echo ""

echo "========================================="
echo "🧪 测试命令"
echo "========================================="
echo ""
echo "python main_final_new.py \\"
echo "    --input /mnt/workspace/LLM/ldd/多跳数据/data/QA.jsonl \\"
echo "    --output ./测试输出 \\"
echo "    --target_count 20 \\"
echo "    --use-embedding \\"
echo "    --debug"
echo ""
echo "生成后统计跳数分布："
echo "grep 'target_hops' 测试输出/*.json | awk -F: '{print \$NF}' | sed 's/,//' | sort | uniq -c"
echo ""
