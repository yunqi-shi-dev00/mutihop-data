#!/bin/bash

echo "========================================="
echo "🧪 测试：不使用embedding（避免OOM）"
echo "========================================="
echo ""

python main_final_new.py \
    --input /mnt/workspace/LLM/ldd/多跳数据/data/QA.jsonl \
    --output ./修复后测试_无embedding \
    --target_count 3 \
    --debug 2>&1 | tee test_no_emb.log

echo ""
echo "========================================="
echo "📊 验证结果"
echo "========================================="
echo ""

echo "1️⃣ 可选ID列表（应该有3-4个）："
grep "可选ID列表：" test_no_emb.log | head -3

echo ""
echo "2️⃣ 筛选通过率："
echo "  通过: $(grep '\[筛选\] ✓' test_no_emb.log | wc -l)"
echo "  未通过: $(grep '\[筛选\] ✗' test_no_emb.log | wc -l)"
echo "  宽松: $(grep '宽松通过' test_no_emb.log | wc -l)"

echo ""
echo "3️⃣ 最终跳数分布："
grep "跳数:" test_no_emb.log | awk '{print $2}' | sort | uniq -c

echo ""
