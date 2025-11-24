"""
工具函数模块（增强版 + 全局质量筛选）
"""

import json
import os
import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Any, Optional
import tqdm


# ============ 数据加载和验证 ============

def load_qa_data(file_path: str) -> List[Dict]:
    """加载QA数据"""
    print(f"\n[LOAD] 加载数据: {file_path}")
    
    qa_data = []
    
    if file_path.endswith('.jsonl'):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    qa = json.loads(line.strip())
                    qa_data.append(qa)
                except json.JSONDecodeError as e:
                    print(f"[WARNING] 行 {line_num} JSON解析失败: {e}")
    elif file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                qa_data = data
            else:
                qa_data = [data]
    else:
        raise ValueError(f"不支持的文件格式: {file_path}")
    
    print(f"[LOAD] ✓ 加载了 {len(qa_data)} 条数据")
    return qa_data


def validate_qa_data(qa_data: List[Dict]) -> List[Dict]:
    """验证QA数据"""
    print(f"\n[VALIDATE] 验证数据...")
    
    valid_data = []
    required_fields = ['question', 'answer']
    
    for i, qa in enumerate(qa_data):
        # 确保有id
        if 'id' not in qa:
            qa['id'] = str(i)
        
        # 检查必需字段
        if all(field in qa for field in required_fields):
            valid_data.append(qa)
        else:
            print(f"[WARNING] 数据 {qa.get('id', i)} 缺少必需字段")
    
    print(f"[VALIDATE] ✓ 验证通过: {len(valid_data)}/{len(qa_data)}")
    return valid_data


# ============ ⭐⭐⭐ 核心：质量评估函数 ⭐⭐⭐ ============

def evaluate_overall_quality(result: Dict) -> str:
    """
    评估单个QA结果的整体质量
    
    评估维度：
    1. 多跳数量（final_qa_count）
    2. 答案长度
    3. 是否通过内部筛选
    4. 轮数（是否正常完成）
    
    Returns:
        'high', 'medium', 'low'
    """
    if not result or not isinstance(result, dict):
        return 'low'
    
    score = 0
    max_score = 10
    
    # 1. 多跳数量（权重: 4分）
    final_qa_count = result.get('final_qa_count', 1)
    if final_qa_count >= 3:
        score += 4
    elif final_qa_count == 2:
        score += 3
    elif final_qa_count == 1:
        score += 1
    
    # 2. 答案长度（权重: 2分）
    answer = result.get('answer', '')
    answer_len = len(answer)
    if answer_len >= 200:
        score += 2
    elif answer_len >= 100:
        score += 1
    
    # 3. 问题长度（权重: 1分）
    question = result.get('question', '')
    question_len = len(question)
    if question_len >= 50:
        score += 1
    
    # 4. 轮数合理性（权重: 1分）
    num_turns = result.get('num_turns', 0)
    max_turns = result.get('max_turns', 16)
    if 3 <= num_turns < max_turns:  # 正常完成，不是超时退出
        score += 1
    
    # 5. 陈述数量（权重: 1分）
    statements = result.get('statements', [])
    if len(statements) >= 2:
        score += 1
    
    # 6. 编辑历史（权重: 1分）
    edit_history = result.get('edit_history', [])
    if len(edit_history) >= 3:
        score += 1
    
    # 计算质量等级
    score_ratio = score / max_score
    
    if score_ratio >= 0.7:
        return 'high'
    elif score_ratio >= 0.4:
        return 'medium'
    else:
        return 'low'


# ============ ⭐⭐⭐ 核心：带质量筛选的批量生成 ⭐⭐⭐ ============

async def generate_batch_with_quality_filter(
    agent,
    save_path: str,
    batch_size: int = 4,
    target_count: int = 100,
    max_attempts: int = 300,
    quality_filter: str = 'all',
    output_format: str = 'jsonl'
):
    """
    批量生成QA（带全局质量筛选）
    
    Args:
        agent: QA生成Agent
        save_path: 输出目录
        batch_size: 并发数
        target_count: 目标生成数量（符合quality_filter的数量）
        max_attempts: 最大尝试次数
        quality_filter: 质量过滤器
            - 'high': 只保留high质量
            - 'medium+': 保留high和medium质量
            - 'all': 保留所有
        output_format: 输出格式
            - 'jsonl': 所有结果在一个.jsonl文件中（推荐）
            - 'json': 每个结果单独.json文件
            - 'both': 同时输出两种格式
    
    Returns:
        统计信息字典
    """
    # 创建输出目录
    os.makedirs(save_path, exist_ok=True)
    
    # 状态变量
    qualified_results = []  # 符合质量标准的结果
    all_results = []  # 所有结果（包括不合格的）
    attempt_count = 0
    quality_distribution = defaultdict(int)
    hop_distribution = defaultdict(int)
    
    # 信号量（控制并发）
    semaphore = asyncio.Semaphore(batch_size)
    
    print(f"\n{'='*80}")
    print(f"[BATCH] 批量生成任务（带质量筛选）")
    print(f"  目标数量: {target_count} 个（{quality_filter}质量）")
    print(f"  并发数: {batch_size}")
    print(f"  最大尝试: {max_attempts}")
    print(f"  输出格式: {output_format}")
    print(f"{'='*80}\n")
    
    # 进度条
    pbar = tqdm.tqdm(total=target_count, desc=f"生成{quality_filter}质量QA")
    
    # 辅助函数：保存单个结果
    def save_single_result(result: Dict, is_qualified: bool):
        """保存单个结果"""
        # 保存到all_results.jsonl（所有结果）
        all_jsonl = os.path.join(save_path, 'all_results.jsonl')
        with open(all_jsonl, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        # 如果是合格结果，额外保存
        if is_qualified:
            if output_format in ['jsonl', 'both']:
                qualified_jsonl = os.path.join(save_path, 'qualified_results.jsonl')
                with open(qualified_jsonl, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
            
            if output_format in ['json', 'both']:
                json_file = os.path.join(save_path, f"{result['uid']}.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 主循环
    start_time = time.time()
    
    while len(qualified_results) < target_count and attempt_count < max_attempts:
        # 计算本轮需要生成的数量
        remaining = target_count - len(qualified_results)
        batch_count = min(batch_size, remaining * 2, max_attempts - attempt_count)
        
        # 生成一批
        tasks = [agent.generate(semaphore, save_path) for _ in range(batch_count)]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for result in batch_results:
            attempt_count += 1
            
            # 跳过异常
            if isinstance(result, Exception):
                print(f"\n[ERROR] 生成失败: {result}")
                all_results.append(None)
                continue
            
            # 跳过None
            if result is None:
                all_results.append(None)
                continue
            
            # 保存到all_results
            all_results.append(result)
            
            # ⭐⭐⭐ 评估质量 ⭐⭐⭐
            quality = evaluate_overall_quality(result)
            quality_distribution[quality] += 1
            
            # 统计多跳分布
            final_qa_count = result.get('final_qa_count', 1)
            hop_distribution[final_qa_count] += 1
            
            # ⭐⭐⭐ 根据quality_filter判断是否合格 ⭐⭐⭐
            is_qualified = False
            
            if quality_filter == 'high' and quality == 'high':
                is_qualified = True
            elif quality_filter == 'medium+' and quality in ['high', 'medium']:
                is_qualified = True
            elif quality_filter == 'all':
                is_qualified = True
            
            # 保存结果
            save_single_result(result, is_qualified)
            
            # 如果合格，加入qualified_results
            if is_qualified:
                qualified_results.append(result)
                pbar.update(1)
        
        # 打印进度
        success_rate = len(qualified_results) / attempt_count if attempt_count > 0 else 0
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / attempt_count if attempt_count > 0 else 0
        
        print(f"\r[PROGRESS] 合格: {len(qualified_results)}/{target_count}, "
              f"尝试: {attempt_count}/{max_attempts}, "
              f"成功率: {success_rate*100:.1f}%, "
              f"平均耗时: {avg_time:.1f}s/个", end='')
    
    print()  # 换行
    pbar.close()
    
    # 统计
    total_time = time.time() - start_time
    success_count = len([r for r in all_results if r is not None])
    
    print(f"\n{'='*80}")
    print(f"[BATCH] 完成！")
    print(f"  目标数量: {target_count}")
    print(f"  实际获得: {len(qualified_results)}")
    print(f"  总尝试数: {attempt_count}")
    print(f"  成功生成: {success_count}")
    print(f"  成功率: {len(qualified_results)/attempt_count*100:.1f}%")
    print(f"  总耗时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
    if qualified_results:
        print(f"  平均耗时: {total_time/len(qualified_results):.1f}秒/个")
    print(f"{'='*80}\n")
    
    # 返回统计信息
    return {
        'qualified_count': len(qualified_results),
        'attempt_count': attempt_count,
        'success_count': success_count,
        'success_rate': len(qualified_results) / attempt_count if attempt_count > 0 else 0,
        'total_time': total_time,
        'avg_time': total_time / len(qualified_results) if qualified_results else 0,
        'quality_distribution': dict(quality_distribution),
        'hop_distribution': dict(hop_distribution),
        'all_results': all_results,
        'qualified_results': qualified_results
    }


# ============ 原有的批量生成函数（向后兼容） ============

async def generate_batch_with_monitoring(agent, save_path: str, 
                                        batch_size: int = 4, 
                                        target_count: int = 100):
    """
    批量生成（原版，无质量筛选）
    保留用于向后兼容
    """
    return await generate_batch_with_quality_filter(
        agent=agent,
        save_path=save_path,
        batch_size=batch_size,
        target_count=target_count,
        max_attempts=target_count * 3,
        quality_filter='all',
        output_format='jsonl'
    )


# ============ 质量报告生成 ============

def generate_quality_report(all_results: List[Dict], output_path: str):
    """
    生成详细质量报告
    
    Args:
        all_results: 所有生成结果（包括不合格的）
        output_path: 报告输出路径
    """
    print(f"\n[REPORT] 生成质量报告...")
    
    # 过滤有效结果
    valid_results = [r for r in all_results if isinstance(r, dict) and r is not None]
    
    if not valid_results:
        print("[WARNING] 没有有效结果可供分析")
        return
    
    # 统计
    total = len(valid_results)
    quality_dist = defaultdict(int)
    hop_dist = defaultdict(int)
    turn_dist = defaultdict(int)
    answer_lengths = []
    question_lengths = []
    
    for result in valid_results:
        # 质量分布
        quality = evaluate_overall_quality(result)
        quality_dist[quality] += 1
        
        # 多跳分布
        final_qa_count = result.get('final_qa_count', 1)
        hop_dist[final_qa_count] += 1
        
        # 轮数分布
        num_turns = result.get('num_turns', 0)
        turn_dist[num_turns] += 1
        
        # 长度统计
        answer_lengths.append(len(result.get('answer', '')))
        question_lengths.append(len(result.get('question', '')))
    
    # 计算平均值
    avg_answer_len = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
    avg_question_len = sum(question_lengths) / len(question_lengths) if question_lengths else 0
    avg_turns = sum(turn_dist.keys()) / len(turn_dist) if turn_dist else 0
    
    # 生成报告
    report = {
        'metadata': {
            'generation_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'total_results': total
        },
        'summary': {
            'total_count': total,
            'quality_distribution': dict(quality_dist),
            'high_quality_rate': quality_dist['high'] / total if total > 0 else 0,
            'medium_quality_rate': quality_dist['medium'] / total if total > 0 else 0,
            'low_quality_rate': quality_dist['low'] / total if total > 0 else 0
        },
        'hop_distribution': dict(sorted(hop_dist.items())),
        'turn_distribution': dict(sorted(turn_dist.items())),
        'length_statistics': {
            'avg_answer_length': round(avg_answer_len, 2),
            'avg_question_length': round(avg_question_len, 2),
            'max_answer_length': max(answer_lengths) if answer_lengths else 0,
            'max_question_length': max(question_lengths) if question_lengths else 0,
            'min_answer_length': min(answer_lengths) if answer_lengths else 0,
            'min_question_length': min(question_lengths) if question_lengths else 0
        },
        'turn_statistics': {
            'avg_turns': round(avg_turns, 2),
            'max_turns': max(turn_dist.keys()) if turn_dist else 0,
            'min_turns': min(turn_dist.keys()) if turn_dist else 0
        }
    }
    
    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    print(f"\n{'='*80}")
    print(f"[REPORT] 质量报告摘要")
    print(f"{'='*80}")
    print(f"总计: {total} 个QA")
    
    print(f"\n质量分布:")
    for quality in ['high', 'medium', 'low']:
        count = quality_dist[quality]
        rate = count / total * 100 if total > 0 else 0
        print(f"  {quality}: {count} ({rate:.1f}%)")
    
    print(f"\n多跳分布:")
    for hops, count in sorted(hop_dist.items()):
        rate = count / total * 100 if total > 0 else 0
        print(f"  {hops}跳: {count} ({rate:.1f}%)")
    
    print(f"\n长度统计:")
    print(f"  平均问题长度: {avg_question_len:.0f} 字符")
    print(f"  平均答案长度: {avg_answer_len:.0f} 字符")
    
    print(f"\n报告已保存: {output_path}")
    print(f"{'='*80}\n")


# ============ 其他工具函数 ============

def merge_generated_qa(output_dir: str):
    """合并生成的QA文件"""
    print(f"\n[MERGE] 合并输出文件...")
    
    all_qa = []
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json') and f != 'quality_report.json']
    
    for json_file in json_files:
        file_path = os.path.join(output_dir, json_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                qa = json.load(f)
                all_qa.append(qa)
        except Exception as e:
            print(f"[WARNING] 读取 {json_file} 失败: {e}")
    
    if all_qa:
        merged_file = os.path.join(output_dir, 'all_qa_merged.jsonl')
        with open(merged_file, 'w', encoding='utf-8') as f:
            for qa in all_qa:
                f.write(json.dumps(qa, ensure_ascii=False) + '\n')
        
        print(f"[MERGE] ✓ 合并了 {len(all_qa)} 个QA到: {merged_file}")
    else:
        print(f"[MERGE] 没有找到QA文件")


def print_usage_distribution(kb_stats: Dict):
    """打印知识库使用分布"""
    print(f"\n{'='*80}")
    print(f"[KB] 知识库使用统计")
    print(f"{'='*80}")
    print(f"总论文数: {kb_stats['total_papers']}")
    print(f"活跃论文数: {kb_stats['active_papers']}")
    print(f"总QA数: {kb_stats['total_qas']}")
    print(f"已使用QA数: {kb_stats['used_qas']}")
    print(f"使用率: {kb_stats['usage_rate']*100:.1f}%")
    
    if 'paper_usage' in kb_stats:
        print(f"\n论文使用分布（前10）:")
        sorted_papers = sorted(
            kb_stats['paper_usage'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for paper, count in sorted_papers[:10]:
            print(f"  {paper[:50]}: {count}")
    
    print(f"{'='*80}\n")
