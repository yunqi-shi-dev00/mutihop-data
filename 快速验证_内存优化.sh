#!/bin/bash

echo "=================================================="
echo "    🔍 验证内存优化和相关QA修复"
echo "=================================================="
echo ""

# 检查1：相关QA保底机制
echo "【检查1】knowledge_base_new.py - 是否有相关QA保底机制？"
if grep -q "保底机制：如果结果太少，补充随机QA" knowledge_base_new.py; then
    echo "✅ 找到：相关QA保底机制"
    echo "   行号："
    grep -n "保底机制" knowledge_base_new.py | head -1
else
    echo "❌ 未找到保底机制"
fi
echo ""

# 检查2：支持自定义batch_size
echo "【检查2】knowledge_base_new.py - __init__是否接受embedding_batch_size参数？"
if grep -q "embedding_batch_size: int = 4" knowledge_base_new.py; then
    echo "✅ 找到：embedding_batch_size参数（默认4）"
    echo "   行号："
    grep -n "embedding_batch_size: int = 4" knowledge_base_new.py | head -1
else
    echo "❌ 未找到embedding_batch_size参数"
fi
echo ""

# 检查3：及时清理显存
echo "【检查3】knowledge_base_new.py - 是否及时清理显存？"
if grep -q "torch.cuda.empty_cache()" knowledge_base_new.py; then
    echo "✅ 找到：显存清理逻辑"
    echo "   行号："
    grep -n "torch.cuda.empty_cache()" knowledge_base_new.py | head -1
else
    echo "❌ 未找到显存清理"
fi
echo ""

# 检查4：main_final_new.py命令行参数
echo "【检查4】main_final_new.py - 是否有--embedding-batch-size参数？"
if grep -q "'--embedding-batch-size'" main_final_new.py; then
    echo "✅ 找到：命令行参数"
    echo "   行号："
    grep -n "'--embedding-batch-size'" main_final_new.py | head -1
else
    echo "❌ 未找到命令行参数"
fi
echo ""

# 检查5：KB初始化传递参数
echo "【检查5】main_final_new.py - 是否传递embedding_batch_size给KB？"
if grep -q "embedding_batch_size=args.embedding_batch_size" main_final_new.py; then
    echo "✅ 找到：参数传递"
    echo "   行号："
    grep -n "embedding_batch_size=args.embedding_batch_size" main_final_new.py | head -1
else
    echo "❌ 未找到参数传递"
fi
echo ""

echo "=================================================="
echo "    ✅ 验证完成！"
echo "=================================================="
echo ""
echo "📝 **测试命令**："
echo ""
echo "# 默认batch_size=4（适用4GB显存）"
echo "python main_final_new.py --input /path/to/QA.jsonl --output ./test --use-embedding --target_count 10"
echo ""
echo "# batch_size=2（适用3GB显存）"
echo "python main_final_new.py --input /path/to/QA.jsonl --output ./test --use-embedding --embedding-batch-size 2 --target_count 10"
echo ""
echo "# batch_size=1（适用2.5GB显存）"
echo "python main_final_new.py --input /path/to/QA.jsonl --output ./test --use-embedding --embedding-batch-size 1 --target_count 10"
echo ""
