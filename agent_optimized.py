"""
半导体QA生成系统 - 优化Agent
真正的融合：在SELECT action内部添加筛选和答案重生成
保持原版核心完全不变
"""

import json
import copy
import uuid
import random
import asyncio
from collections import defaultdict
from typing import Dict, List, Any, Optional
from transformers import AutoTokenizer

from prompts_optimized import SemiconductorQAPrompts
from knowledge_base import EnhancedSemiconductorKB, SemiconductorQAEntity, AgentMemory
from llm_client import LLMAPIClient


class OptimizedSemiconductorQAAgent:
    """
    优化版Agent - 在原版SELECT action内部融合筛选和答案重生成
    
    核心思路：
    1. 保持action机制不变（SELECT/FUZZ/EXIT/BRAINSTORM）
    2. 保持迭代循环结构不变
    3. 在SELECT执行时：组合 → 筛选 → 答案重生成
    4. 多跳自然形成：SELECT执行N次 = N跳
    """
    
    def __init__(self, knowledge_base: EnhancedSemiconductorKB, 
                 llm_client: LLMAPIClient, 
                 tokenizer_path: str,
                 max_turns: int = 16,
                 use_dynamic_planning: bool = True,
                 enable_qa_filtering: bool = True,
                 enable_answer_regeneration: bool = True,
                 debug_mode: bool = True):
        """
        初始化优化Agent
        
        Args:
            knowledge_base: 知识库
            llm_client: LLM客户端
            tokenizer_path: tokenizer路径
            max_turns: 最大迭代轮数
            use_dynamic_planning: 是否使用动态规划
            enable_qa_filtering: 是否在SELECT后筛选问题
            enable_answer_regeneration: 是否在SELECT后重生成答案
            debug_mode: 是否输出调试信息
        """
        self.kb = knowledge_base
        self.llm_client = llm_client
        self.max_turns = max_turns
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        
        # 动态规划开关
        self.use_dynamic_planning = use_dynamic_planning
        if use_dynamic_planning:
            self.current_stage = 'early'
            self.stage_thresholds = {'early': 0.6, 'mid': 0.2}
            print(f"[Agent] ✓ 启用动态规划策略")
        else:
            print(f"[Agent] 使用原版生成策略")
        
        # 🔧 优化功能开关（在SELECT内部执行）
        self.enable_qa_filtering = enable_qa_filtering
        self.enable_answer_regeneration = enable_answer_regeneration
        self.debug_mode = debug_mode
        
        if enable_qa_filtering:
            print(f"[Agent] ✓ 启用问题筛选（在SELECT后执行）")
        if enable_answer_regeneration:
            print(f"[Agent] ✓ 启用答案重生成（在SELECT后执行）")
        if debug_mode:
            print(f"[Agent] ✓ 启用调试模式")
    
    # ============ 阶段管理（动态规划）============
    
    def update_generation_stage(self):
        """更新生成阶段"""
        if not self.use_dynamic_planning:
            return
        
        stats = self.kb.get_usage_stats()
        active_rate = stats['active_papers'] / stats['total_papers']
        
        old_stage = self.current_stage
        
        if active_rate > self.stage_thresholds['early']:
            self.current_stage = 'early'
        elif active_rate > self.stage_thresholds['mid']:
            self.current_stage = 'mid'
        else:
            self.current_stage = 'late'
        
        if old_stage != self.current_stage:
            print(f"\n[STAGE] 阶段切换: {old_stage} → {self.current_stage}")
            print(f"        活跃论文率: {active_rate*100:.1f}%")
    
    def select_root_qa_smart(self) -> str:
        """智能选择根QA"""
        if not self.use_dynamic_planning:
            return random.choice(self.kb.qa_ids)
        
        self.update_generation_stage()
        
        if self.current_stage == 'early':
            return random.choice(self.kb.qa_ids)
        elif self.current_stage == 'mid':
            if random.random() < 0.7:
                return self.kb.select_underutilized_qa()
            else:
                return random.choice(self.kb.qa_ids)
        else:  # late
            return self.kb.select_underutilized_qa()
    
    # ============ LLM调用 ============
    
    async def call_llm(self, prompt: str, temperature: float = 0.8) -> str:
        """调用LLM"""
        prompt_formatted = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
            tokenize=False
        )
        
        max_new_tokens = 8000 - self.tokenizer([prompt_formatted], return_length=True)["length"][0]
        max_new_tokens = max(max_new_tokens, 512)
        
        sampling_kwargs = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 1000,
            "max_new_tokens": max_new_tokens,
            "n": 1,
            "stop_token_ids": [151645, 151643]
        }
        
        output = await self.llm_client.async_generate(prompt_formatted, sampling_kwargs)
        return output["text"]
    
    # ============ QA实体信息提取 ============
    
    async def extract_qa_info(self, entity: SemiconductorQAEntity) -> SemiconductorQAEntity:
        """提取QA信息"""
        if self.debug_mode:
            print(f"    [提取] 实体 {entity.id} 关键信息...")
        
        # 提取关键概念
        try:
            content = entity.qa_data.get('question', '') + ' ' + entity.qa_data.get('answer', '')
            prompt = SemiconductorQAPrompts.extract_key_concepts.format(content=content)
            text = await self.call_llm(prompt, temperature=0.7)
            
            concepts_list = json.loads(text.split('```json')[1].split('```')[0].strip())
            entity.key_concepts = [item['concept'] for item in concepts_list]
        except Exception as e:
            if self.debug_mode:
                print(f"    [提取] 关键概念提取失败: {e}")
            entity.key_concepts = []
        
        # 提取摘要
        try:
            question = entity.qa_data.get('question', '')
            answer = entity.qa_data.get('answer', '')
            prompt = SemiconductorQAPrompts.summarize_qa.format(question=question, answer=answer)
            text = await self.call_llm(prompt, temperature=0.7)
            
            if '<summary>' in text and '</summary>' in text:
                entity.summary = text.split('<summary>')[1].split('</summary>')[0].strip()
            else:
                entity.summary = text[:100]
        except Exception as e:
            if self.debug_mode:
                print(f"    [提取] 摘要提取失败: {e}")
            entity.summary = "待生成"
        
        # 查找相关QA
        if self.use_dynamic_planning:
            entity.related_qas = self.kb.find_related_qas_prioritized(entity.id, top_k=10)
        else:
            entity.related_qas = self.kb.find_related_qas(entity.id, top_k=10)
        
        return entity
    
    # ============ QA构建方法 ============
    
    async def construct_base_qa(self, entity: SemiconductorQAEntity) -> Dict:
        """构建基础QA"""
        if self.debug_mode:
            print(f"    [构建] 基础QA...")
        
        content = entity.repr()
        prompt = SemiconductorQAPrompts.base_qa.format(content=content)
        text = await self.call_llm(prompt)
        
        base_qa = json.loads(text.split('```json')[1].split('```')[0].strip())
        return base_qa
    
    async def construct_link_qa(self, entityA: SemiconductorQAEntity, 
                                entityB: SemiconductorQAEntity) -> Dict:
        """构建关联QA"""
        if self.debug_mode:
            print(f"    [桥联] 连接 {entityA.id} 和 {entityB.id}...")
        
        prompt = SemiconductorQAPrompts.link_qa.format(
            conceptA=entityA.name,
            conceptB=entityB.name,
            contentA=entityA.repr(),
            contentB=entityB.repr()
        )
        text = await self.call_llm(prompt)
        link_qa = json.loads(text.split('```json')[1].split('```')[0].strip())
        return link_qa
    
    async def combine_qa(self, questionA: Dict, questionB: Dict, memory: AgentMemory) -> Dict:
        """
        组合两个问答（生成参考答案）
        注意：这里生成的answer是参考答案，后续会重新生成最终答案
        """
        if self.debug_mode:
            print(f"    [合成] 组合问答（生成参考答案）...")
        
        prompt = SemiconductorQAPrompts.compose_qa.format(
            questionA=json.dumps({'question': questionA['question'], 'answer': questionA['answer']}, ensure_ascii=False),
            questionB=json.dumps({'question': questionB['question'], 'answer': questionB['answer']}, ensure_ascii=False),
            statements=memory.statements_repr(additional=[questionB['statement']])
        )
        text = await self.call_llm(prompt)
        combined = json.loads(text.split('```json')[1].split('```')[0].strip())
        return combined
    
    # ============ 🔧 优化：在SELECT后执行的筛选和答案重生成 ============
    
    async def evaluate_question_inline(self, question: str, 
                                       relevant_entities: List[SemiconductorQAEntity]) -> Dict:
        """
        🔧 在SELECT后立即评估问题
        
        Args:
            question: 组合后的问题
            relevant_entities: 已使用的相关实体列表
        
        Returns:
            评估结果 {'passed': bool, 'reason': str}
        """
        if self.debug_mode:
            print(f"    [筛选] 评估问题质量...")
        
        # 格式化子问答对
        sub_qa_content = "\n\n".join([
            f"子问答对-{i+1}:\n"
            f"问题: {e.qa_data['question']}\n"
            f"答案: {e.qa_data['answer']}\n"
            f"来源: {e.qa_data.get('paper_name', 'unknown')}"
            for i, e in enumerate(relevant_entities)
        ])
        
        # 调用评估模板
        prompt = SemiconductorQAPrompts.question_evaluation.format(
            sub_qa_content=sub_qa_content,
            question_to_evaluate=question
        )
        
        try:
            text = await self.call_llm(prompt, temperature=0.3)
            
            # 解析评估结果
            if '【是】' in text:
                passed = True
                reason = "问题通过所有评估标准"
            elif '【否】' in text:
                passed = False
                reason = "问题未通过评估标准"
            else:
                passed = False
                reason = f"评估格式异常: {text[:50]}"
            
            if self.debug_mode:
                print(f"    [筛选] {'✓ 通过' if passed else '✗ 未通过'}")
            
            return {'passed': passed, 'reason': reason, 'raw_response': text}
            
        except Exception as e:
            if self.debug_mode:
                print(f"    [筛选] 评估失败: {e}")
            return {'passed': False, 'reason': f"评估异常: {str(e)}", 'raw_response': ""}
    
    async def regenerate_answer_inline(self, question: str, reference_answer: str,
                                       relevant_entities: List[SemiconductorQAEntity],
                                       statements: List[str]) -> Dict:
        """
        🔧 在SELECT后立即重生成答案（参考答案 → 最终答案）
        
        强调：基于子QA，不发散，避免引入错误
        
        Args:
            question: 组合后的问题
            reference_answer: 组合时生成的参考答案
            relevant_entities: 已使用的相关实体列表
            statements: 技术陈述列表
        
        Returns:
            生成结果
        """
        if self.debug_mode:
            print(f"    [答案] 重新生成最终答案（基于子QA）...")
        
        # 格式化子问答对
        sub_qa_str = "\n\n".join([
            f"子问答对-{i+1}:\n"
            f"问题: {e.qa_data['question']}\n"
            f"答案: {e.qa_data['answer']}"
            for i, e in enumerate(relevant_entities)
        ])
        
        # 格式化技术陈述
        statements_str = "\n".join(statements)
        
        # 调用答案生成模板
        prompt = SemiconductorQAPrompts.answer_regeneration.format(
            question=question,
            reference_answer=reference_answer,
            sub_qa_pairs=sub_qa_str,
            statements=statements_str
        )
        
        try:
            text = await self.call_llm(prompt, temperature=0.7)
            result = json.loads(text.split('```json')[1].split('```')[0].strip())
            
            if self.debug_mode:
                grounded = result.get('grounded_check', {})
                print(f"    [答案] 生成成功")
                print(f"    [答案] 置信度: {result.get('confidence', 0.0):.2f}")
                print(f"    [答案] 基于子QA: {grounded.get('all_info_from_subqa', False)}")
            
            return result
            
        except Exception as e:
            if self.debug_mode:
                print(f"    [答案] 生成失败: {e}")
            return {
                'final_answer': reference_answer,
                'reasoning_trace': '',
                'confidence': 0.5,
                'grounded_check': {
                    'all_info_from_subqa': False,
                    'no_external_knowledge': False,
                    'complete_reasoning': False
                }
            }
    
    # ============ Action选择 ============
    
    async def choose_action(self, state: str, ready_to_exit: bool = False) -> Dict:
        """选择下一步操作"""
        actions = [
            SemiconductorQAPrompts.FUZZ,
            SemiconductorQAPrompts.SELECT,
        ]
        random.shuffle(actions)
        
        if ready_to_exit:
            actions.append(SemiconductorQAPrompts.EXIT)
        
        prompt = SemiconductorQAPrompts.action.format(
            question=state,
            actions='\n\n'.join(actions)
        )
        
        text = await self.call_llm(prompt)
        action = json.loads(text.split('```json')[1].split('```')[0].strip())
        
        assert action['action'] in ['SELECT', 'FUZZ', 'EXIT', 'BRAINSTORM']
        return action
    
    # ============ 验证和检查方法 ============
    
    async def check_info_cover(self, statement: str, prior_statements: str) -> bool:
        """检查信息覆盖"""
        prompt = SemiconductorQAPrompts.check_info_cover.format(
            prior=prior_statements,
            current=statement
        )
        text = await self.call_llm(prompt, temperature=0.3)
        result = json.loads(text.split('```json')[1].split('```')[0].strip())
        return result['judgement'] == 'yes'
    
    async def check_qa_valid(self, state: str) -> bool:
        """检查QA有效性"""
        prompt = SemiconductorQAPrompts.qa_valid_check.format(question=state)
        text = await self.call_llm(prompt, temperature=0.3)
        result = json.loads(text.split('```json')[1].split('```')[0].strip())
        return 'yes' in result['judgement']
    
    async def check_alternative_answer(self, question: str, gt_answer: str,
                                      pred_answer: str, statements: str) -> bool:
        """检查替代答案"""
        prompt = SemiconductorQAPrompts.check_alternative_ans.format(
            question=question,
            gt_answer=gt_answer,
            pred_answer=pred_answer,
            statements=statements
        )
        text = await self.call_llm(prompt, temperature=0.3)
        return 'yes' in text.lower()
    
    # ============ 直接生成和LLM判断 ============
    
    async def direct_generate(self, question: str, n: int = 1) -> List[str]:
        """直接生成答案"""
        prompt = SemiconductorQAPrompts.direct_gen_check.format(question=question)
        prompt = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
            tokenize=False
        )
        
        max_new_tokens = 8000 - self.tokenizer([prompt], return_length=True)["length"][0]
        max_new_tokens = max(max_new_tokens, 512)
        
        sampling_kwargs = {
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 1000,
            "max_new_tokens": max_new_tokens,
            "n": n,
            "stop_token_ids": [151645, 151643]
        }
        
        output = await self.llm_client.async_generate(prompt, sampling_kwargs)
        texts = [output["text"]] if not isinstance(output["text"], list) else output["text"]
        
        answers = []
        for text in texts:
            if '<answer>' in text and '</answer>' in text:
                answers.append(text.split('<answer>')[1].split('</answer>')[0].strip())
            else:
                answers.append(None)
        
        return answers
    
    async def llm_judge_answer(self, question: str, answers: List[str], 
                              gt_answer: str) -> List[bool]:
        """LLM判断答案正确性"""
        corrects = []
        for ans in answers:
            if ans is None:
                corrects.append(False)
            else:
                prompt = SemiconductorQAPrompts.llm_judge.format(
                    question=question,
                    gt_answer=gt_answer,
                    pred_answer=ans
                )
                text = await self.call_llm(prompt, temperature=0.3)
                corrects.append('Correct' in text)
        return corrects
    
    # ============ 🎯 主生成流程（在SELECT内部融合优化）============
    
    async def generate(self, semaphore: asyncio.Semaphore, save_path: str):
        """
        生成一个复杂QA
        
        核心优化：在SELECT action执行时，组合 → 筛选 → 答案重生成
        """
        async with semaphore:
            if self.debug_mode:
                print(f"\n{'='*80}")
                print(f"[开始] 新的QA生成任务")
                print(f"{'='*80}")
            
            # Step 1: 智能选择根QA
            root_id = self.select_root_qa_smart()
            root_qa_data = self.kb.get_qa(root_id)
            
            memory = AgentMemory()
            memory.uid = str(uuid.uuid4())
            
            print(f"\n{'='*60}")
            print(f"[START] 生成QA，根实体: QA-{root_id}")
            if self.use_dynamic_planning:
                print(f"        阶段: {self.current_stage}")
            print(f"{'='*60}\n")
            
            # 更新使用统计
            self.kb.update_usage([root_id])
            
            # 创建根实体
            root_entity = SemiconductorQAEntity(root_id, root_qa_data, self.kb)
            root_entity = await self.extract_qa_info(root_entity)
            memory.relevant.append(root_entity)
            
            # Step 2: 构建基础QA
            try:
                base_qa = await self.construct_base_qa(root_entity)
            except Exception as e:
                print(f"[ERROR] 构建基础QA失败: {e}")
                return None
            
            if not (isinstance(base_qa, dict) and all(k in base_qa for k in ['question', 'answer', 'statement'])):
                print("[ERROR] 基础QA格式错误")
                return None
            
            memory.qa['question'] = base_qa['question']
            memory.qa['answer'] = base_qa['answer']
            memory.statements.append(base_qa['statement'])
            memory.qa_history.append(base_qa)
            memory.edit_history.append(f"从 QA-{root_id} 创建基础问题")
            
            print(f"\n[BASE QA] {base_qa['question']}")
            
            ready_to_exit = False
            action_stats = defaultdict(int)
            num_hops = 1  # 记录跳数
            
            # Step 3: ⭐ 迭代优化循环（原版结构，在SELECT内部融合优化）
            for turn in range(self.max_turns):
                print(f"\n{'--- 第 ' + str(turn+1) + ' 轮 ---'}")
                
                state = memory.repr()
                
                if turn == 0:
                    action = {'action': 'none'}
                else:
                    try:
                        action = await self.choose_action(state, ready_to_exit)
                    except Exception as e:
                        print(f"[WARNING] 选择动作失败: {e}")
                        continue
                
                action_stats[action['action']] += 1
                print(f"[ACTION] {action['action']} - {action.get('note', '')}")
                
                q_new = None
                memory_new = copy.deepcopy(memory)
                memory_new.edit_history.append(f"动作: {action['action']}. 说明: {action.get('note', '')}")
                
                # ============ 执行不同的Action ============
                
                if action['action'] == 'FUZZ':
                    # ✅ 原版FUZZ逻辑
                    q_new = action['question']
                    memory_new.edit_history.append(f"FUZZ操作: {q_new[:50]}...")
                
                elif action['action'] == 'EXIT':
                    # ✅ 原版EXIT逻辑
                    print("[INFO] 问题生成完成，退出")
                    break
                
                elif action['action'] == 'none':
                    # ✅ 原版初始化逻辑
                    assert turn == 0
                    q_new = base_qa['question']
                
                elif action['action'] == 'SELECT':
                    # ⭐⭐⭐ 这里是核心优化点 ⭐⭐⭐
                    # 原版SELECT逻辑 + 筛选 + 答案重生成
                    
                    if self.debug_mode:
                        print(f"  [SELECT] ========== 开始SELECT流程 ==========")
                    
                    # (1) 找到目标实体（原版逻辑）
                    target = None
                    for e in memory.relevant:
                        if e.id == action['target'] or e.url == action['target']:
                            target = e
                            break
                    
                    if target is None:
                        print(f"[WARNING] 未找到目标 {action['target']}")
                        continue
                    
                    # (2) 找邻居（原版逻辑，带动态规划）
                    if self.use_dynamic_planning:
                        candidates = self.kb.find_related_qas_prioritized(target.id, top_k=10)
                    else:
                        candidates = target.related_qas
                    
                    exist_ids = [e.id for e in memory.relevant]
                    candidates = [c for c in candidates if c not in exist_ids]
                    
                    if not candidates:
                        print(f"[WARNING] QA-{target.id} 没有可用的相关QA")
                        continue
                    
                    neighbor_id = random.choice(candidates)
                    print(f"  [SELECT] {target.id} -> {neighbor_id}")
                    
                    # 更新使用统计
                    self.kb.update_usage([neighbor_id])
                    
                    neighbor_data = self.kb.get_qa(neighbor_id)
                    neighbor_entity = SemiconductorQAEntity(neighbor_id, neighbor_data, self.kb)
                    neighbor_entity = await self.extract_qa_info(neighbor_entity)
                    
                    # (3) 构建关联QA（原版逻辑）
                    try:
                        link_qa = await self.construct_link_qa(target, neighbor_entity)
                    except Exception as e:
                        print(f"[WARNING] 构建关联QA失败: {e}")
                        continue
                    
                    # (4) 检查重复（原版逻辑）
                    try:
                        duplicate = await self.check_info_cover(
                            link_qa['statement'],
                            memory_new.statements_repr()
                        )
                    except Exception as e:
                        print(f"[WARNING] 检查重复失败: {e}")
                        continue
                    
                    if duplicate:
                        print("[WARNING] 陈述重复，跳过")
                        continue
                    
                    # (5) 组合QA（原版逻辑，生成参考答案）
                    try:
                        combine_qa_result = await self.combine_qa(memory.qa, link_qa, memory)
                        q_new = combine_qa_result['question']
                        reference_answer = combine_qa_result['answer']  # 这是参考答案
                    except Exception as e:
                        print(f"[WARNING] 组合QA失败: {e}")
                        continue
                    
                    # (6) 🔧 优化：立即筛选问题
                    if self.enable_qa_filtering:
                        memory_new.relevant.append(neighbor_entity)  # 临时添加，用于评估
                        
                        eval_result = await self.evaluate_question_inline(
                            q_new,
                            memory_new.relevant
                        )
                        
                        if not eval_result['passed']:
                            print(f"  [SELECT] ✗ 问题未通过筛选，跳过此轮")
                            memory_new.relevant.pop()  # 移除临时添加的
                            continue
                        
                        print(f"  [SELECT] ✓ 问题通过筛选")
                    else:
                        memory_new.relevant.append(neighbor_entity)
                    
                    # (7) 🔧 优化：立即重生成答案（参考答案 → 最终答案）
                    if self.enable_answer_regeneration:
                        memory_new.statements.append(link_qa['statement'])  # 临时添加
                        
                        regen_result = await self.regenerate_answer_inline(
                            q_new,
                            reference_answer,
                            memory_new.relevant,
                            memory_new.statements
                        )
                        
                        # 检查答案是否基于子QA
                        grounded_check = regen_result.get('grounded_check', {})
                        if grounded_check.get('all_info_from_subqa', False) and regen_result.get('confidence', 0) >= 0.6:
                            final_answer = regen_result['final_answer']
                            print(f"  [SELECT] ✓ 使用重生成答案（置信度: {regen_result['confidence']:.2f}）")
                        else:
                            final_answer = reference_answer
                            print(f"  [SELECT] ⚠ 使用参考答案（置信度低或未基于子QA）")
                    else:
                        final_answer = reference_answer
                        memory_new.statements.append(link_qa['statement'])
                    
                    # (8) 更新memory（使用最终答案）
                    memory_new.qa['answer'] = final_answer  # ⭐ 关键：用重生成的最终答案
                    memory_new.edit_history.append(f"SELECT: '{target.name}' → '{neighbor_entity.name}'")
                    memory_new.edit_history.append(f"组合问题: {q_new[:80]}...")
                    memory_new.edit_history.append(f"最终答案: {final_answer[:80]}...")
                    
                    num_hops += 1  # 记录跳数
                    
                    if self.debug_mode:
                        print(f"  [SELECT] 当前跳数: {num_hops}")
                        print(f"  [SELECT] ========== SELECT流程完成 ==========")
                
                # ============ 验证和测试（原版逻辑）============
                
                if q_new is None:
                    continue
                
                print(f"\n[NEW Q] {q_new}\n")
                memory_new.qa['question'] = q_new
                
                # 验证有效性
                try:
                    valid = await self.check_qa_valid(memory_new.repr())
                except Exception as e:
                    print(f"[WARNING] 验证有效性失败: {e}")
                    valid = False
                
                if not valid:
                    print(f"[WARNING] 第{turn+1}轮QA无效")
                    continue
                
                # 直接生成测试
                try:
                    answers = await self.direct_generate(q_new, n=4)
                except Exception as e:
                    print(f"[WARNING] 直接生成失败: {e}")
                    continue
                
                try:
                    corrects = await self.llm_judge_answer(
                        q_new, answers, memory_new.qa['answer']
                    )
                except Exception as e:
                    print(f"[WARNING] LLM判断失败: {e}")
                    continue
                
                correct_count = sum(corrects)
                print(f"[TEST] 正确率: {correct_count}/4")
                
                if correct_count >= 2:
                    memory = memory_new
                    ready_to_exit = True
                    print("[INFO] 测试通过，可以选择退出")
                else:
                    print("[INFO] 测试未通过，继续迭代")
            
            # Step 4: 保存结果
            output = {
                'uid': memory.uid,
                'question': memory.qa['question'],
                'answer': memory.qa['answer'],
                'source_qa_ids': [e.id for e in memory.relevant],
                'source_papers': list(set([e.qa_data.get('paper_name', 'unknown') for e in memory.relevant])),
                'statements': memory.statements,
                'edit_history': memory.edit_history,
                'action_stats': dict(action_stats),
                'num_turns': turn + 1,
                'num_hops': num_hops,
                'qa_filtering_enabled': self.enable_qa_filtering,
                'answer_regeneration_enabled': self.enable_answer_regeneration
            }
            
            # 保存
            import os
            os.makedirs(save_path, exist_ok=True)
            output_file = os.path.join(save_path, f"{memory.uid}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            print(f"\n[DONE] QA已保存: {output_file}")
            print(f"       最终问题: {memory.qa['question'][:80]}...")
            print(f"       跳数: {num_hops}")
            print(f"       答案长度: {len(memory.qa['answer'])} 字符")
            
            return output
