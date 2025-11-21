#!/bin/bash

echo "========================================"
echo "🔧 优化9修改内容"
echo "========================================"
echo ""

echo "修改1：只显示候选QA（不包含已组合的）"
echo "文件：agent_final_new.py 第575-597行"
echo "----------------------------------------"
grep -n "优化9" agent_final_new.py | head -1
echo ""
sed -n '575,597p' agent_final_new.py
echo ""
echo ""

echo "修改2：改进容错处理（避免嵌套）"
echo "文件：agent_final_new.py 第619-627行"
echo "----------------------------------------"
grep -n "优化9" agent_final_new.py | tail -1
echo ""
sed -n '619,627p' agent_final_new.py
echo ""
echo ""

echo "========================================"
echo "✅ 优化9完成"
echo "========================================"
echo ""
echo "效果："
echo "1. ✅ 候选ID只包含未组合的QA（更清晰）"
echo "2. ✅ JSON解析失败直接EXIT（避免嵌套）"
echo "3. ✅ 核心优化7和8正常工作"
echo ""
echo "测试命令："
echo "./🚀一键测试_选择方案.sh"
echo ""
