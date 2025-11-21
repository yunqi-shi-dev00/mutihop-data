#!/bin/bash

echo "========================================="
echo "🧪 测试：使用CPU运行embedding（避免GPU OOM）"
echo "========================================="
echo ""

echo "⚠️ 注意：CPU运行embedding会比较慢（但只需要一次）"
echo ""

python main_final_new.py \
    --input /mnt/workspace/LLM/ldd/多跳数据/data/QA.jsonl \
    --output ./修复后测试_CPU_embedding \
    --target_count 3 \
    --use-embedding \
    --embedding-batch-size 2 \
    --debug 2>&1 | tee test_cpu_emb.log

echo ""
echo "========================================="
echo "📊 验证结果"
echo "========================================="
echo ""

echo "1️⃣ 检查是否用CPU运行embedding："
grep "使用设备:" test_cpu_emb.log | head -1

echo ""
echo "2️⃣ 可选ID列表（应该有3-4个）："
grep "可选ID列表：" test_cpu_emb.log | head -3

echo ""
echo "3️⃣ 筛选通过率："
echo "  通过: $(grep '\[筛选\] ✓' test_cpu_emb.log | wc -l)"
echo "  未通过: $(grep '\[筛选\] ✗' test_cpu_emb.log | wc -l)"
echo "  宽松: $(grep '宽松通过' test_cpu_emb.log | wc -l)"

echo ""
echo "4️⃣ 最终跳数分布："
grep "跳数:" test_cpu_emb.log | awk '{print $2}' | sort | uniq -c

echo ""
