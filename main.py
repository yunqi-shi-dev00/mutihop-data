"""
半导体QA生成系统 - 主程序
完整版：原版功能 + 新增流程（多跳生成→问题筛选→答案重生成→迭代优化）

使用示例:
    python main.py \
        --input /path/to/QA.jsonl \
        --output ./generated_qa \
        --model_path /path/to/model \
        --tokenizer_path /path/to/tokenizer \
        --server_type vllm \
        --host localhost \
        --port 8000 \
        --batch_size 4 \
        --target_count 100 \
        --max_turns 10 \
        --enable_dynamic_planning \
        --enable_qa_filtering \
        --enable_answer_regeneration \
        --debug
"""

import argparse
import asyncio
import sys

from knowledge_base import EnhancedSemiconductorKB
from llm_client import LLMAPIClient
from agent import EnhancedSemiconductorQAAgent
from utils import (
    load_qa_data,
    validate_qa_data,
    generate_batch_with_monitoring,
    merge_generated_qa,
    print_usage_distribution,
    filter_by_quality
)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='半导体QA生成系统 - 增强版',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 输入输出参数
    parser.add_argument('--input', type=str, required=True,
                        help='输入QA数据文件路径 (.json或.jsonl)')
    parser.add_argument('--output', type=str, required=True,
                        help='输出目录路径')
    
    # 模型参数
    parser.add_argument('--model_path', type=str, required=True,
                        help='LLM模型路径')
    parser.add_argument('--tokenizer_path', type=str, default=None,
                        help='Tokenizer路径（默认与model_path相同）')
    parser.add_argument('--server_type', type=str, default='vllm',
                        choices=['vllm', 'sglang'],
                        help='推理服务器类型')
    parser.add_argument('--host', type=str, default='localhost',
                        help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8000,
                        help='服务器端口')
    
    # 生成参数
    parser.add_argument('--batch_size', type=int, default=4,
                        help='并发批次大小')
    parser.add_argument('--target_count', type=int, default=50,
                        help='目标生成数量')
    parser.add_argument('--max_turns', type=int, default=16,
                        help='最大迭代轮数')
    
    # 🆕 新增功能开关
    parser.add_argument('--enable_dynamic_planning', action='store_true',
                        help='启用动态规划策略')
    parser.add_argument('--disable_dynamic_planning', dest='enable_dynamic_planning',
                        action='store_false',
                        help='禁用动态规划策略')
    parser.set_defaults(enable_dynamic_planning=True)
    
    parser.add_argument('--enable_qa_filtering', action='store_true',
                        help='启用问题筛选流程')
    parser.add_argument('--disable_qa_filtering', dest='enable_qa_filtering',
                        action='store_false',
                        help='禁用问题筛选流程')
    parser.set_defaults(enable_qa_filtering=True)
    
    parser.add_argument('--enable_answer_regeneration', action='store_true',
                        help='启用答案重生成流程')
    parser.add_argument('--disable_answer_regeneration', dest='enable_answer_regeneration',
                        action='store_false',
                        help='禁用答案重生成流程')
    parser.set_defaults(enable_answer_regeneration=True)
    
    # 调试参数
    parser.add_argument('--debug', action='store_true',
                        help='启用调试模式（输出详细信息）')
    parser.add_argument('--merge_output', action='store_true',
                        help='生成后合并所有QA到单个文件')
    parser.add_argument('--filter_quality', action='store_true',
                        help='生成后筛选高质量QA')
    
    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_args()
    
    # 如果未指定tokenizer路径，使用model路径
    if args.tokenizer_path is None:
        args.tokenizer_path = args.model_path
    
    print(f"\n{'='*80}")
    print(f"半导体QA生成系统 - 增强版")
    print(f"{'='*80}")
    print(f"输入文件: {args.input}")
    print(f"输出目录: {args.output}")
    print(f"模型路径: {args.model_path}")
    print(f"服务器: {args.host}:{args.port} ({args.server_type})")
    print(f"目标数量: {args.target_count}")
    print(f"批次大小: {args.batch_size}")
    print(f"最大轮数: {args.max_turns}")
    print(f"\n功能配置:")
    print(f"  动态规划: {'✓ 启用' if args.enable_dynamic_planning else '✗ 禁用'}")
    print(f"  问题筛选: {'✓ 启用' if args.enable_qa_filtering else '✗ 禁用'}")
    print(f"  答案重生成: {'✓ 启用' if args.enable_answer_regeneration else '✗ 禁用'}")
    print(f"  调试模式: {'✓ 启用' if args.debug else '✗ 禁用'}")
    print(f"{'='*80}\n")
    
    # Step 1: 加载和验证数据
    try:
        qa_data = load_qa_data(args.input)
        qa_data = validate_qa_data(qa_data)
        
        if len(qa_data) == 0:
            print("[ERROR] 没有有效的QA数据")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 数据加载失败: {e}")
        sys.exit(1)
    
    # Step 2: 初始化知识库
    try:
        kb = EnhancedSemiconductorKB(qa_data)
    except Exception as e:
        print(f"[ERROR] 知识库初始化失败: {e}")
        sys.exit(1)
    
    # Step 3: 初始化LLM客户端
    try:
        llm_client = LLMAPIClient(
            model_path=args.model_path,
            server_type=args.server_type,
            host=args.host,
            port=args.port
        )
        
        if not llm_client.is_connected:
            print(f"[WARNING] LLM服务器未连接，继续运行可能失败")
            print(f"[WARNING] 请确保已启动 {args.server_type} 服务")
    except Exception as e:
        print(f"[ERROR] LLM客户端初始化失败: {e}")
        sys.exit(1)
    
    # Step 4: 初始化Agent
    try:
        async with llm_client:
            agent = EnhancedSemiconductorQAAgent(
                knowledge_base=kb,
                llm_client=llm_client,
                tokenizer_path=args.tokenizer_path,
                max_turns=args.max_turns,
                use_dynamic_planning=args.enable_dynamic_planning,
                enable_qa_filtering=args.enable_qa_filtering,
                enable_answer_regeneration=args.enable_answer_regeneration,
                debug_mode=args.debug
            )
            
            # Step 5: 批量生成QA
            print(f"\n{'='*80}")
            print(f"开始生成QA")
            print(f"{'='*80}\n")
            
            stats = await generate_batch_with_monitoring(
                agent=agent,
                save_path=args.output,
                batch_size=args.batch_size,
                target_count=args.target_count
            )
            
            # Step 6: 打印知识库使用分布
            kb_stats = kb.get_usage_stats()
            print_usage_distribution(kb_stats)
            
            # Step 7: 可选 - 合并输出
            if args.merge_output:
                merge_generated_qa(args.output)
            
            # Step 8: 可选 - 筛选高质量QA
            if args.filter_quality:
                high_quality_files = filter_by_quality(args.output)
                print(f"\n[QUALITY] 高质量QA文件列表已保存")
            
            print(f"\n{'='*80}")
            print(f"生成完成！")
            print(f"{'='*80}")
            print(f"成功生成: {stats['successful']} 个QA")
            print(f"多跳QA: {stats['multihop_count']} 个")
            print(f"通过筛选: {stats['passed_filtering']} 个")
            print(f"答案重生成: {stats['answer_regenerated']} 个")
            print(f"输出目录: {args.output}")
            print(f"{'='*80}\n")
            
    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] 用户中断，正在保存当前进度...")
        print("[INFO] 已保存的QA文件在: " + args.output)
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    # 运行主函数
    asyncio.run(main())
