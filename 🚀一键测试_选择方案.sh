#!/bin/bash

echo "========================================="
echo "🚀 一键测试：修复验证"
echo "========================================="
echo ""
echo "你的GPU内存不足（只剩19 MiB），需要选择一个方案："
echo ""
echo "  1️⃣ 使用CPU运行embedding（推荐，质量高但慢5-10分钟）"
echo "  2️⃣ 不使用embedding（最快，质量中等）"
echo "  3️⃣ 退出（手动释放GPU内存）"
echo ""
read -p "请选择方案 [1/2/3]: " choice

case $choice in
    1)
        echo ""
        echo "========================================="
        echo "✅ 方案1：使用CPU运行embedding"
        echo "========================================="
        echo ""
        echo "⚠️ 注意：CPU运行embedding会比较慢（约5-10分钟）"
        echo "         但只需要运行一次，之后会保存embedding文件"
        echo ""
        read -p "确认继续？[y/n]: " confirm
        if [ "$confirm" = "y" ]; then
            ./测试_CPU_embedding.sh
        else
            echo "已取消"
        fi
        ;;
    2)
        echo ""
        echo "========================================="
        echo "✅ 方案2：不使用embedding"
        echo "========================================="
        echo ""
        echo "⚠️ 注意：不使用embedding会降低相关QA的质量"
        echo "         建议后续用方案1重新生成"
        echo ""
        read -p "确认继续？[y/n]: " confirm
        if [ "$confirm" = "y" ]; then
            ./测试_不用embedding.sh
        else
            echo "已取消"
        fi
        ;;
    3)
        echo ""
        echo "========================================="
        echo "退出"
        echo "========================================="
        echo ""
        echo "手动释放GPU内存的方法："
        echo ""
        echo "1. 查看GPU使用情况："
        echo "   nvidia-smi"
        echo ""
        echo "2. 关闭占用最多的进程（如vLLM）："
        echo "   kill -9 22077  # 66.70 GiB"
        echo "   kill -9 253990  # 12.41 GiB"
        echo ""
        echo "3. 重新运行测试："
        echo "   ./🚀一键测试_选择方案.sh"
        ;;
    *)
        echo ""
        echo "无效选择，退出"
        ;;
esac

echo ""
