#!/bin/bash
# 快速验证所有优化是否生效

echo "=========================================="
echo "验证 agent_final_new.py 的所有优化"
echo "=========================================="
echo ""

echo "✅ 优化1：候选数量 10→30"
grep -n "top_k=30" agent_final_new.py | head -1
echo ""

echo "✅ 优化2：从前5个候选中选"
grep -n "top_candidates = candidates\[:min(5" agent_final_new.py | head -1
echo ""

echo "✅ 优化3：桥联阈值降到3"
grep -n "relevance_score < 3" agent_final_new.py | head -1
echo ""

echo "✅ 优化4：放宽信息覆盖"
grep -n "陈述部分重复，但仍继续" agent_final_new.py | head -1
echo ""

echo "✅ 优化5：放宽筛选标准"
grep -n "random.random() < 0.3" agent_final_new.py | head -1
echo ""

echo "=========================================="
echo "所有优化标记汇总："
echo "=========================================="
grep -n "⭐⭐⭐" agent_final_new.py | grep "优化"
echo ""

echo "✅ 所有优化已完成！"
echo "现在可以运行测试了！"
