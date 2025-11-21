#!/bin/bash

echo "=================================================="
echo "    🔍 验证Bug修复：未找到目标实体"
echo "=================================================="
echo ""

# 检查prompts_final.py中的SELECT prompt修复
echo "【检查1】prompts_final.py - SELECT prompt是否包含'可选ID列表'？"
if grep -q "{available_ids}" prompts_final.py; then
    echo "✅ 找到：{available_ids}"
    echo "   行号："
    grep -n "{available_ids}" prompts_final.py | head -1
else
    echo "❌ 未找到：{available_ids}"
fi
echo ""

echo "【检查2】prompts_final.py - 是否包含'禁止编造不存在的ID'？"
if grep -q "禁止编造不存在的ID" prompts_final.py; then
    echo "✅ 找到：禁止编造不存在的ID"
else
    echo "❌ 未找到警告语句"
fi
echo ""

# 检查agent_final_new.py中的choose_action修复
echo "【检查3】agent_final_new.py - choose_action是否接受memory参数？"
if grep -q "memory: AgentMemory = None" agent_final_new.py; then
    echo "✅ 找到：memory: AgentMemory = None"
    echo "   行号："
    grep -n "memory: AgentMemory = None" agent_final_new.py | head -1
else
    echo "❌ 未找到memory参数"
fi
echo ""

echo "【检查4】agent_final_new.py - 是否提取available_ids并转为字符串？"
if grep -q "str(e.id) for e in memory.relevant" agent_final_new.py; then
    echo "✅ 找到：available_ids 提取逻辑（已转字符串）"
    echo "   行号："
    grep -n "str(e.id) for e in memory.relevant" agent_final_new.py | head -1
else
    echo "❌ 未找到available_ids提取或未转字符串"
fi
echo ""

echo "【检查5】agent_final_new.py - 是否传递memory给choose_action？"
if grep -q "memory=memory" agent_final_new.py; then
    echo "✅ 找到：调用时传递memory"
    echo "   行号："
    grep -n "action = await self.choose_action.*memory=memory" agent_final_new.py
else
    echo "❌ 未找到memory参数传递"
fi
echo ""

echo "【检查6】agent_final_new.py - 是否增加容错（随机选择）？"
if grep -q "随机选择" agent_final_new.py; then
    echo "✅ 找到：容错逻辑（随机选择）"
    echo "   行号："
    grep -n "随机选择" agent_final_new.py | head -1
else
    echo "❌ 未找到容错逻辑"
fi
echo ""

# 检查FUZZ去重（之前的修复）
echo "【检查7】agent_final_new.py - 是否修复类型匹配（str(e.id)）？"
if grep -q "str(e.id) == str(action\['target'\])" agent_final_new.py; then
    echo "✅ 找到：类型匹配修复（统一转字符串）"
    echo "   行号："
    grep -n "str(e.id) == str(action\['target'\])" agent_final_new.py | head -1
else
    echo "❌ 未找到类型匹配修复"
fi
echo ""

echo "=================================================="
echo "    ✅ 验证完成！"
echo "=================================================="
echo ""
echo "📝 **下一步**："
echo "   1. 如果所有检查都通过，立即运行测试"
echo "   2. 如果有❌，请检查对应文件"
echo ""
echo "🧪 **测试命令**："
echo "   python main_final_new.py --input /path/to/QA.jsonl --output ./fix_test --target_count 10 --use-embedding --debug"
echo ""
