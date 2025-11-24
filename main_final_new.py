"""
半导体QA生成系统 - 最终版主程序（优化版 + 质量筛选）
完全按用户要求：每次SELECT用所有子QA生成多跳问题
新增功能：
1. 支持语义embedding模式（--use-embedding）
2. 桥联合理性检查（--enable-bridge-check）
3. 全局JSON容错
4. ⭐ 全局质量筛选（--quality-filter）

使用示例:
    # 生成100个high质量QA（推荐）
    python main_final_new.py \
        --input /path/to/QA.jsonl \
        --output ./generated_qa \
        --model_path /path/to/model \
        --target_count 100 \
        --quality_filter high \
        --debug
    
    # 生成100个medium+质量QA（更快）
    python main_final_new.py \
        --input /path/to/QA.jsonl \
        --output ./generated_qa \
        --model_path /path/to/model \
        --target_count 100 \
        --quality_filter medium+ \
        --batch_size 8
    
    # 启用语义embedding（更准确）
    python main_final_new.py \
        --input /path/to/QA.jsonl \
        --output ./generated_qa \
        --model_path /path/to/model \
        --use-embedding \
        --quality_filter high \
        --debug
"""

import argparse
import asyncio
import sys

from knowledge_base_new import EnhancedSemiconductorKB
from llm_client import LLMAPIClient
from agent_final_new import FinalSemiconductorQAAgent
from utils import (
    load_qa_data,
    validate_qa_data,
    generate_batch_with_quality_filter,  # ⭐ 新的批量生成函数
    merge_generated_qa,
    print_usage_distribution,
    generate_quality_report  # ⭐ 新增质量报告
)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='半导体QA生成系统 - 最终优化版（全局质量筛选）',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 输入输出
    parser.add_argument('--input', type=str, required=True,
                        help='输入QA数据文件路径')
    parser.add_argument('--output', type=str, required=True,
                        help='输出目录路径')
    
    # 模型参数
    parser.add_argument('--model_path', type=str, required=True,
                        help='LLM模型路径')
    parser.add_argument('--tokenizer_path', type=str, default=None,
                        help='Tokenizer路径')
    parser.add_argument('--server_type', type=str, default='vllm',
                        choices=['vllm', 'sglang'],
                        help='推理服务器类型')
    parser.add_argument('--host', type=str, default='localhost',
                        help='服务器主机')
    parser.add_argument('--port', type=int, default=8000,
                        help='服务器端口')
    
    # ===== 🆕 生成参数（新增质量筛选） =====
    parser.add_argument('--batch_size', type=int, default=4,
                        help='并发批次大小')
    parser.add_argument('--target_count', type=int, default=50,
                        help='⭐ 目标生成数量（符合quality_filter的数量）')
    parser.add_argument('--max_attempts', type=int, default=None,
                        help='最大尝试次数（默认为target_count的3倍）')
    
    # ⭐⭐⭐ 核心新增：质量筛选参数 ⭐⭐⭐
    parser.add_argument('--quality_filter', type=str, default='all',
                        choices=['high', 'medium+', 'all'],
                        help='''质量过滤器（默认: all）
  - high: 只保留high质量（严格模式）
  - medium+: 保留high和medium质量（推荐）
  - all: 保留所有（快速模式）''')
    
    parser.add_argument('--max_turns', type=int, default=16,
                        help='最大迭代轮数')
    parser.add_argument('--max_hops', type=int, default=3,
                        help='最多组合的问题数量（默认3）')
    
    # Embedding相关
    parser.add_argument('--use-embedding', action='store_true',
                        help='使用语义embedding查找相关QA（需要安装sentence-transformers）')
    parser.add_argument('--embedding-batch-size', type=int, default=4,
                        help='Embedding生成的批量大小（默认4，减少内存占用）')
    parser.add_argument('--embedding-model-path', type=str, default=None,
                        help='Embedding模型路径（可选，默认使用Qwen3-Embedding-0.6B）')
    
    # 功能开关
    parser.add_argument('--enable_dynamic_planning', action='store_true',
                        help='启用动态规划')
    parser.add_argument('--disable_dynamic_planning', dest='enable_dynamic_planning',
                        action='store_false')
    parser.set_defaults(enable_dynamic_planning=True)
    
    parser.add_argument('--enable_qa_filtering', action='store_true',
                        help='启用问题筛选')
    parser.add_argument('--disable_qa_filtering', dest='enable_qa_filtering',
                        action='store_false')
    parser.set_defaults(enable_qa_filtering=True)
    
    parser.add_argument('--enable_answer_regeneration', action='store_true',
                        help='启用答案重生成')
    parser.add_argument('--disable_answer_regeneration', dest='enable_answer_regeneration',
                        action='store_false')
    parser.set_defaults(enable_answer_regeneration=True)
    
    parser.add_argument('--enable_bridge_check', action='store_true',
                        help='启用桥联合理性检查')
    parser.add_argument('--disable_bridge_check', dest='enable_bridge_check',
                        action='store_false')
    parser.set_defaults(enable_bridge_check=True)
    
    # 输出选项
    parser.add_argument('--debug', action='store_true',
                        help='启用调试模式')
    parser.add_argument('--merge_output', action='store_true',
                        help='合并输出')
    parser.add_argument('--generate_report', action='store_true',
                        help='⭐ 生成详细质量报告')
    
    # ⭐ 输出格式选项
    parser.add_argument('--output_format', type=str, default='jsonl',
                        choices=['jsonl', 'json', 'both'],
                        help='输出格式 (默认: jsonl)\n'
                             '  jsonl: 所有结果在一个.jsonl文件中（推荐）\n'
                             '  json: 每个结果单独.json文件\n'
                             '  both: 同时输出两种格式')
    
    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_args()
    
    if args.tokenizer_path is None:
        args.tokenizer_path = args.model_path
    
    if args.max_attempts is None:
        args.max_attempts = args.target_count * 3
    
    print(f"\n{'='*80}")
    print(f"半导体QA生成系统 - 最终优化版 + 全局质量筛选 🚀")
    print(f"{'='*80}")
    print(f"输入: {args.input}")
    print(f"输出: {args.output}")
    print(f"模型: {args.model_path}")
    print(f"服务器: {args.host}:{args.port}")
    
    # ⭐ 显示质量筛选配置
    print(f"\n📊 质量筛选配置：")
    print(f"  目标数量: {args.target_count} 个（{args.quality_filter}质量）")
    print(f"  最大尝试: {args.max_attempts} 次")
    print(f"  质量过滤: {args.quality_filter}")
    print(f"  输出格式: {args.output_format}")
    
    print(f"\n核心特点：")
    print(f"  1. 每次SELECT用所有子QA生成多跳问题（完全按用户模板）")
    print(f"  2. 问题筛选（6大标准）")
    print(f"  3. 答案重生成（强调围绕子QA，不发散）")
    print(f"  4. ⭐ 全局质量筛选（只保留符合质量标准的QA）")
    
    print(f"\n✨ 优化功能：")
    print(f"  • 全局JSON解析容错（3层容错机制）")
    print(f"  • 桥联合理性检查（过滤不合理组合）")
    print(f"  • 实时成功率统计")
    if args.use_embedding:
        print(f"  • 语义embedding模式（更准确的相关QA查找）")
    
    print(f"\n功能配置：")
    print(f"  动态规划: {'✓' if args.enable_dynamic_planning else '✗'}")
    print(f"  问题筛选: {'✓' if args.enable_qa_filtering else '✗'}")
    print(f"  答案重生成: {'✓' if args.enable_answer_regeneration else '✗'}")
    print(f"  桥联检查: {'✓' if args.enable_bridge_check else '✗'}")
    print(f"  语义embedding: {'✓' if args.use_embedding else '✗'}")
    print(f"  调试模式: {'✓' if args.debug else '✗'}")
    print(f"  质量报告: {'✓' if args.generate_report else '✗'}")
    print(f"{'='*80}\n")
    
    # 加载数据
    try:
        qa_data = load_qa_data(args.input)
        qa_data = validate_qa_data(qa_data)
        
        if len(qa_data) == 0:
            print("[ERROR] 无有效数据")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 数据加载失败: {e}")
        sys.exit(1)
    
    # 初始化知识库（支持embedding）
    try:
        kb = EnhancedSemiconductorKB(
            qa_data, 
            use_embedding=args.use_embedding,
            embedding_batch_size=args.embedding_batch_size,
            embedding_model_path=args.embedding_model_path
        )
    except Exception as e:
        print(f"[ERROR] 知识库初始化失败: {e}")
        sys.exit(1)
    
    # 初始化LLM
    try:
        llm_client = LLMAPIClient(
            model_path=args.model_path,
            server_type=args.server_type,
            host=args.host,
            port=args.port
        )
        
        if not llm_client.is_connected:
            print(f"[WARNING] LLM服务器未连接")
    except Exception as e:
        print(f"[ERROR] LLM初始化失败: {e}")
        sys.exit(1)
    
    # 初始化Agent
    try:
        async with llm_client:
            agent = FinalSemiconductorQAAgent(
                knowledge_base=kb,
                llm_client=llm_client,
                tokenizer_path=args.tokenizer_path,
                max_turns=args.max_turns,
                max_hops=args.max_hops,
                use_dynamic_planning=args.enable_dynamic_planning,
                enable_qa_filtering=args.enable_qa_filtering,
                enable_answer_regeneration=args.enable_answer_regeneration,
                enable_bridge_check=args.enable_bridge_check,
                debug_mode=args.debug
            )
            
            # ⭐⭐⭐ 批量生成（带质量筛选） ⭐⭐⭐
            print(f"\n{'='*80}")
            print(f"开始生成QA（带全局质量筛选）")
            print(f"{'='*80}\n")
            
            stats = await generate_batch_with_quality_filter(
                agent=agent,
                save_path=args.output,
                batch_size=args.batch_size,
                target_count=args.target_count,
                max_attempts=args.max_attempts,
                quality_filter=args.quality_filter,
                output_format=args.output_format
            )
            
            # 知识库统计
            kb_stats = kb.get_usage_stats()
            print_usage_distribution(kb_stats)
            
            # ⭐ 生成质量报告
            if args.generate_report:
                report_path = f"{args.output}/quality_report.json"
                generate_quality_report(stats['all_results'], report_path)
            
            # 合并输出
            if args.merge_output:
                merge_generated_qa(args.output)
            
            print(f"\n{'='*80}")
            print(f"生成完成！ 🎉")
            print(f"{'='*80}")
            print(f"✅ 符合质量标准: {stats['qualified_count']}/{args.target_count}")
            print(f"📊 总尝试次数: {stats['attempt_count']}")
            print(f"📈 成功率: {stats['success_rate']*100:.1f}%")
            print(f"📁 输出目录: {args.output}")
            
            # 质量分布
            if 'quality_distribution' in stats:
                print(f"\n📊 质量分布:")
                for quality, count in stats['quality_distribution'].items():
                    print(f"   {quality}: {count}")
            
            # 多跳分布
            if 'hop_distribution' in stats:
                print(f"\n🔗 多跳分布:")
                for hops, count in sorted(stats['hop_distribution'].items()):
                    print(f"   {hops}跳: {count}")
            
            # Embedding统计
            if args.use_embedding and kb.use_embedding:
                print(f"\n💡 语义embedding模式已启用")
                print(f"   - 模型: {kb.embedding_model_name if hasattr(kb, 'embedding_model_name') else 'all-MiniLM-L6-v2'}")
                print(f"   - QA数量: {len(kb.qa_embeddings)}")
                print(f"   - 向量维度: {kb.qa_embeddings.shape[1]}")
            
            print(f"{'='*80}\n")
            
    except KeyboardInterrupt:
        print("\n[INTERRUPT] 用户中断")
        print(f"[INFO] 已保存文件在: {args.output}")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
