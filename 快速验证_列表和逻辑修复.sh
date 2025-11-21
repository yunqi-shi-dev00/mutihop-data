#!/bin/bash

echo "========================================="
echo "🔍 快速验证：列表只有1个 + 逻辑问题修复"
echo "========================================="
echo ""

echo "📋 检查修改是否已应用..."
echo ""

echo "✅ 修复1：可选ID增加到3-4个（agent_final_new.py 第582行）"
grep -A 2 "candidate_ids = memory.relevant\[0\].related_qas\[:3\]" agent_final_new.py | head -3
echo ""

echo "✅ 修复2：支持选择候选QA（agent_final_new.py 第840行）"
grep -A 2 "从KB中获取候选QA" agent_final_new.py | head -3
echo ""

echo "✅ 修复3：筛选放宽到70%（agent_final_new.py 第474行）"
grep "if random.random() < 0.7" agent_final_new.py
echo ""

echo "========================================="
echo "🧪 开始测试（生成3个QA）"
echo "========================================="
echo ""

python main_final_new.py \
    --input /mnt/workspace/LLM/ldd/多跳数据/data/QA.jsonl \
    --output ./修复后测试 \
    --target_count 3 \
    --use-embedding \
    --debug 2>&1 | tee test_fix.log

echo ""
echo "========================================="
echo "📊 验证结果"
echo "========================================="
echo ""

echo "1️⃣ 检查可选ID列表是否增加（应该有3-4个）："
echo ""
grep "可选ID列表：" test_fix.log | head -5
echo ""

echo "2️⃣ 检查是否能选择候选QA："
echo ""
grep "从候选QA中选择" test_fix.log | head -5
echo ""

echo "3️⃣ 检查筛选通过率（应该有很多'宽松通过'）："
echo ""
echo "筛选通过："
grep "\[筛选\] ✓" test_fix.log | wc -l
echo "筛选未通过："
grep "\[筛选\] ✗" test_fix.log | wc -l
echo "宽松通过："
grep "宽松通过" test_fix.log | wc -l
echo ""

echo "4️⃣ 检查最终跳数分布："
echo ""
grep "跳数:" test_fix.log | awk '{print $2}' | sort | uniq -c
echo ""

echo "========================================="
echo "✅ 验证完成！"
echo "========================================="
echo ""
echo "📝 详细日志：test_fix.log"
echo ""
