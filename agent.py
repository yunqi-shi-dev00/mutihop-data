"""
半导体QA生成系统 - 增强Agent模块
包含所有原版功能 + 新增的多跳生成、问题筛选、答案重生成流程
"""

import json
import copy
import uuid
import random
import asyncio
from collections import defaultdict
from typing import Dict, List, Any, Optional
from transformers import AutoTokenizer

from prompts import SemiconductorQAPrompts
from knowledge_base import EnhancedSemiconductorKB, SemiconductorQAEntity, AgentMemory
from llm_client import LLMAPIClient


class EnhancedSemiconductorQAAgent:
    """增强版Agent - 原版所有功能 + 新增流程（组合→筛选→答案生成→优化）"""
    
    def __init__(self, knowledge_base: EnhancedSemiconductorKB, 
                 llm_client: LLMAPIClient, 
                 tokenizer_path: str,
                 max_turns: int = 16,
                 use_dynamic_planning: bool = True,
                 enable_qa_filtering: bool = True,
                 enable_answer_regeneration: bool = True,
                 debug_mode: bool = True):
        """
        初始化增强Agent
        
        Args:
            knowledge_base: 知识库
            llm_client: LLM客户端
            tokenizer_path: tokenizer路径
            max_turns: 最大迭代轮数
            use_dynamic_planning: 是否使用动态规划
            enable_qa_filtering: 是否启用问题筛选
            enable_answer_regeneration: 是否启用答案重生成
            debug_mode: 是否输出调试信息
        """
        self.kb = knowledge_base
        self.llm_client = llm_client
        self.max_turns = max_turns
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        
        # 🆕 新增：动态规划开关
        self.use_dynamic_planning = use_dynamic_planning
        if use_dynamic_planning:
            self.current_stage = 'early'
            self.stage_thresholds = {'early': 0.6, 'mid': 0.2}
            print(f"[Agent] ✓ 启用动态规划策略")
        else:
            print(f"[Agent] 使用原版生成策略")
        
        # 🆕 新增：新流程开关
        self.enable_qa_filtering = enable_qa_filtering
        self.enable_answer_regeneration = enable_answer_regeneration
        self.debug_mode = debug_mode
        
        if enable_qa_filtering:
            print(f"[Agent] ✓ 启用问题筛选流程")
        if enable_answer_regeneration:
            print(f"[Agent] ✓ 启用答案重生成流程")
        if debug_mode:
            print(f"[Agent] ✓ 启用调试模式")
    
    # ============ 阶段管理（动态规划） ============
    
    def update_generation_stage(self):
        """🆕 更新生成阶段"""
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
        """🆕 智能选择根QA"""
        if not self.use_dynamic_planning:
            # 原版：随机选择
            return random.choice(self.kb.qa_ids)
        
        # 动态规划：基于阶段选择
        self.update_generation_stage()
        
        if self.current_stage == 'early':
            # 早期：随机探索
            return random.choice(self.kb.qa_ids)
        
        elif self.current_stage == 'mid':
            # 中期：平衡探索与利用
            # 70%概率选择低频，30%随机
            if random.random() < 0.7:
                return self.kb.select_underutilized_qa()
            else:
                return random.choice(self.kb.qa_ids)
        
        else:  # late
            # 后期：优先低频QA
            return self.kb.select_underutilized_qa()
    
    # ============ LLM调用相关 ============
    
    async def call_llm(self, prompt: str, temperature: float = 0.8) -> str:
        """✅ 原版：调用LLM（完全保留）"""
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
        """✅ 原版：提取QA信息（完全保留）"""
        if self.debug_mode:
            print(f"  [DEBUG-提取] 提取实体 {entity.id} 的关键信息...")
        
        # 提取关键概念
        try:
            content = entity.qa_data.get('question', '') + ' ' + entity.qa_data.get('answer', '')
            prompt = SemiconductorQAPrompts.extract_key_concepts.format(content=content)
            text = await self.call_llm(prompt, temperature=0.7)
            
            concepts_list = json.loads(text.split('```json')[1].split('```')[0].strip())
            entity.key_concepts = [item['concept'] for item in concepts_list]
        except Exception as e:
            if self.debug_mode:
                print(f"  [DEBUG-提取] 关键概念提取失败: {e}")
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
                print(f"  [DEBUG-提取] 摘要提取失败: {e}")
            entity.summary = "待生成"
        
        # 查找相关QA
        if self.use_dynamic_planning:
            entity.related_qas = self.kb.find_related_qas_prioritized(entity.id, top_k=10)
        else:
            entity.related_qas = self.kb.find_related_qas(entity.id, top_k=10)
        
        return entity
    
    # ============ QA构建方法（原版） ============
    
    async def construct_base_qa(self, entity: SemiconductorQAEntity) -> Dict:
        """✅ 原版：构建基础QA（完全保留）"""
        if self.debug_mode:
            print(f"  [DEBUG-构建] 构建基础QA...")
        
        content = entity.repr()
        prompt = SemiconductorQAPrompts.base_qa.format(content=content)
        text = await self.call_llm(prompt)
        
        base_qa = json.loads(text.split('```json')[1].split('```')[0].strip())
        return base_qa
    
    async def construct_link_qa(self, entityA: SemiconductorQAEntity, 
                                entityB: SemiconductorQAEntity) -> Dict:
        """✅ 原版：构建关联QA（完全保留）"""
        if self.debug_mode:
            print(f"  [DEBUG-桥联] 连接实体 {entityA.id} 和 {entityB.id}...")
        
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
        """✅ 原版：组合两个问答（完全保留）"""
        if self.debug_mode:
            print(f"  [DEBUG-合成] 组合两个问答...")
        
        prompt = SemiconductorQAPrompts.compose_qa.format(
            questionA=json.dumps({'question': questionA['question'], 'answer': questionA['answer']}, ensure_ascii=False),
            questionB=json.dumps({'question': questionB['question'], 'answer': questionB['answer']}, ensure_ascii=False),
            statements=memory.statements_repr(additional=[questionB['statement']])
        )
        text = await self.call_llm(prompt)
        combined = json.loads(text.split('```json')[1].split('```')[0].strip())
        return combined
    
    # ============ 🆕 新增：多跳QA生成（支持2-3跳）============
    
    async def generate_multihop_qa(self, root_entity: SemiconductorQAEntity,
                                   num_hops: int = 2) -> Optional[Dict]:
        """
        🆕 生成多跳QA（支持2-3跳，使用增强模板）
        
        Args:
            root_entity: 根QA实体
            num_hops: 跳数（2或3）
        
        Returns:
            包含多跳问题、参考答案、推理链的字典
        """
        if self.debug_mode:
            print(f"\n  [DEBUG-多跳] ========== 开始生成{num_hops}跳问答 ==========")
        
        # 收集单跳QA
        entities_chain = [root_entity]
        single_hops = [root_entity.qa_data]
        
        # 逐跳构建链条
        for hop in range(1, num_hops):
            if self.debug_mode:
                print(f"  [DEBUG-多跳] 查找第{hop+1}跳...")
            
            prev_entity = entities_chain[-1]
            if self.use_dynamic_planning:
                neighbor_ids = self.kb.find_related_qas_prioritized(prev_entity.id, top_k=5)
            else:
                neighbor_ids = prev_entity.related_qas[:5]
            
            # 排除已使用的
            used_ids = [e.id for e in entities_chain]
            neighbor_ids = [nid for nid in neighbor_ids if nid not in used_ids]
            
            if not neighbor_ids:
                if self.debug_mode:
                    print(f"  [DEBUG-多跳] 无法找到第{hop+1}跳的相关QA，终止")
                return None
            
            neighbor_id = random.choice(neighbor_ids)
            neighbor_data = self.kb.get_qa(neighbor_id)
            neighbor_entity = SemiconductorQAEntity(neighbor_id, neighbor_data, self.kb)
            neighbor_entity = await self.extract_qa_info(neighbor_entity)
            
            # 更新使用统计
            if self.use_dynamic_planning:
                self.kb.update_usage([neighbor_id])
            
            entities_chain.append(neighbor_entity)
            single_hops.append(neighbor_data)
            
            if self.debug_mode:
                print(f"  [DEBUG-多跳] 第{hop+1}跳: {neighbor_id}")
        
        # 生成桥接信息
        bridge_info = self._generate_bridge_info(entities_chain)
        
        # 格式化单跳QA
        single_hop_str = "\n\n".join([
            f"单跳QA-{i+1} (来自论文: {qa.get('paper_name', 'unknown')}):\n"
            f"问题: {qa['question']}\n"
            f"答案: {qa['answer']}"
            for i, qa in enumerate(single_hops)
        ])
        
        if self.debug_mode:
            print(f"  [DEBUG-多跳] 调用LLM生成{num_hops}跳问答...")
        
        # 使用增强版Prompt生成多跳QA
        prompt = SemiconductorQAPrompts.compose_qa_multihop.format(
            num_hops=len(single_hops),
            single_hop_qas=single_hop_str,
            bridge_info=bridge_info
        )
        
        try:
            text = await self.call_llm(prompt, temperature=0.8)
            multihop_qa = json.loads(text.split('```json')[1].split('```')[0].strip())
            
            # 添加元数据
            multihop_qa['num_hops'] = num_hops
            multihop_qa['source_qa_ids'] = [e.id for e in entities_chain]
            multihop_qa['source_papers'] = list(set([qa.get('paper_name', 'unknown') for qa in single_hops]))
            multihop_qa['bridge_type'] = self._infer_bridge_type(entities_chain)
            
            if self.debug_mode:
                print(f"  [DEBUG-多跳] 多跳QA生成成功")
                print(f"  [DEBUG-多跳] 问题: {multihop_qa['question'][:80]}...")
            
            return multihop_qa
            
        except Exception as e:
            if self.debug_mode:
                print(f"  [DEBUG-多跳] 生成失败: {e}")
            return None
    
    def _generate_bridge_info(self, entities_chain: List[SemiconductorQAEntity]) -> str:
        """生成桥接信息"""
        bridge_lines = []
        for i in range(len(entities_chain) - 1):
            entityA = entities_chain[i]
            entityB = entities_chain[i + 1]
            bridge_lines.append(
                f"桥接{i+1}: {entityA.name} 的答案中提到的概念与 {entityB.name} 的问题相关联"
            )
        return "\n".join(bridge_lines)
    
    def _infer_bridge_type(self, entities_chain: List[SemiconductorQAEntity]) -> str:
        """推断桥接类型"""
        # 简单推断：默认为因果关系
        return "causal"
    
    # ============ 🆕 新增：问题评估流程 ============
    
    async def evaluate_question(self, question: str, sub_qa_pairs: List[Dict]) -> Dict:
        """
        🆕 评估生成的问题是否符合标准
        
        Args:
            question: 待评估的问题
            sub_qa_pairs: 子问答对列表
        
        Returns:
            评估结果字典 {'passed': bool, 'reason': str}
        """
        if self.debug_mode:
            print(f"\n  [DEBUG-筛选] ========== 开始问题评估 ==========")
            print(f"  [DEBUG-筛选] 问题: {question[:80]}...")
        
        # 格式化子问答对
        sub_qa_content = "\n\n".join([
            f"子问答对-{i+1}:\n"
            f"问题: {qa['question']}\n"
            f"答案: {qa['answer']}\n"
            f"来源: {qa.get('paper_name', 'unknown')}"
            for i, qa in enumerate(sub_qa_pairs)
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
                # 如果格式不正确，默认不通过
                passed = False
                reason = f"评估格式异常: {text[:50]}"
            
            if self.debug_mode:
                print(f"  [DEBUG-筛选] 评估结果: {'✓ 通过' if passed else '✗ 未通过'}")
                if not passed:
                    print(f"  [DEBUG-筛选] 原因: {reason}")
            
            return {
                'passed': passed,
                'reason': reason,
                'raw_response': text
            }
            
        except Exception as e:
            if self.debug_mode:
                print(f"  [DEBUG-筛选] 评估失败: {e}")
            return {
                'passed': False,
                'reason': f"评估异常: {str(e)}",
                'raw_response': ""
            }
    
    # ============ 🆕 新增：答案重新生成流程 ============
    
    async def regenerate_answer(self, question: str, reference_answer: str,
                                sub_qa_pairs: List[Dict], reasoning_steps: List[str]) -> Dict:
        """
        🆕 为筛选后的问题重新生成最终答案
        
        Args:
            question: 问题
            reference_answer: 参考答案
            sub_qa_pairs: 子问答对列表
            reasoning_steps: 推理步骤
        
        Returns:
            生成结果字典
        """
        if self.debug_mode:
            print(f"\n  [DEBUG-答案] ========== 开始重新生成答案 ==========")
        
        # 格式化子问答对
        sub_qa_str = "\n\n".join([
            f"子问答对-{i+1}:\n"
            f"问题: {qa['question']}\n"
            f"答案: {qa['answer']}"
            for i, qa in enumerate(sub_qa_pairs)
        ])
        
        # 格式化推理步骤
        reasoning_str = "\n".join(reasoning_steps) if reasoning_steps else "无"
        
        # 调用答案生成模板
        prompt = SemiconductorQAPrompts.answer_regeneration.format(
            question=question,
            reference_answer=reference_answer,
            sub_qa_pairs=sub_qa_str,
            reasoning_steps=reasoning_str
        )
        
        try:
            text = await self.call_llm(prompt, temperature=0.7)
            result = json.loads(text.split('```json')[1].split('```')[0].strip())
            
            if self.debug_mode:
                print(f"  [DEBUG-答案] 答案重新生成成功")
                print(f"  [DEBUG-答案] 置信度: {result.get('confidence', 0.0)}")
            
            return result
            
        except Exception as e:
            if self.debug_mode:
                print(f"  [DEBUG-答案] 答案生成失败: {e}")
            return {
                'final_answer': reference_answer,  # 失败时返回参考答案
                'confidence': 0.5,
                'completeness_check': {
                    'covers_all_aspects': False,
                    'shows_reasoning_chain': False,
                    'is_universal': False
                }
            }
    
    # ============ Action选择（原版） ============
    
    async def choose_action(self, state: str, ready_to_exit: bool = False) -> Dict:
        """✅ 原版：选择下一步操作（完全保留）"""
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
    
    # ============ 验证和检查方法（原版） ============
    
    async def check_info_cover(self, statement: str, prior_statements: str) -> bool:
        """✅ 原版：检查信息覆盖（完全保留）"""
        prompt = SemiconductorQAPrompts.check_info_cover.format(
            prior=prior_statements,
            current=statement
        )
        text = await self.call_llm(prompt, temperature=0.3)
        result = json.loads(text.split('```json')[1].split('```')[0].strip())
        return result['judgement'] == 'yes'
    
    async def check_qa_valid(self, state: str) -> bool:
        """✅ 原版：检查QA有效性（完全保留）"""
        prompt = SemiconductorQAPrompts.qa_valid_check.format(question=state)
        text = await self.call_llm(prompt, temperature=0.3)
        result = json.loads(text.split('```json')[1].split('```')[0].strip())
        return 'yes' in result['judgement']
    
    async def check_alternative_answer(self, question: str, gt_answer: str,
                                      pred_answer: str, statements: str) -> bool:
        """✅ 原版：检查替代答案（完全保留）"""
        prompt = SemiconductorQAPrompts.check_alternative_ans.format(
            question=question,
            gt_answer=gt_answer,
            pred_answer=pred_answer,
            statements=statements
        )
        text = await self.call_llm(prompt, temperature=0.3)
        return 'yes' in text.lower()
    
    # ============ 直接生成和LLM判断（原版） ============
    
    async def direct_generate(self, question: str, n: int = 1) -> List[str]:
        """✅ 原版：直接生成答案（完全保留）"""
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
        """✅ 原版：LLM判断答案正确性（完全保留）"""
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
    
    # ============ 🆕 主生成流程（增强版）============
    
    async def generate(self, semaphore: asyncio.Semaphore, save_path: str):
        """
        🆕 生成一个复杂QA（增强流程：原版迭代 + 多跳生成 + 筛选 + 答案重生成）
        """
        async with semaphore:
            if self.debug_mode:
                print(f"\n{'='*80}")
                print(f"[DEBUG] ==================== 开始新的QA生成任务 ====================")
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
            memory.edit_history.append(f"从 QA-{root_id} 创建基础问题\n问题: {base_qa['question']}\n答案: {base_qa['answer']}")
            
            print(f"\n[BASE QA] {base_qa['question']}")
            
            ready_to_exit = False
            action_stats = defaultdict(int)
            
            # Step 3: 迭代优化（原版逻辑，保留所有action）
            for turn in range(self.max_turns):
                print(f"\n--- 第 {turn+1} 轮 ---")
                
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
                
                # 执行不同的动作
                if action['action'] == 'FUZZ':
                    q_new = action['question']
                    memory_new.edit_history.append(f"FUZZ操作将问题修改为: {q_new}")
                
                elif action['action'] == 'EXIT':
                    print("[INFO] 问题生成完成，退出")
                    break
                
                elif action['action'] == 'none':
                    assert turn == 0
                    q_new = base_qa['question']
                
                elif action['action'] == 'SELECT':
                    # 找到目标实体
                    target = None
                    for e in memory.relevant:
                        if e.id == action['target'] or e.url == action['target']:
                            target = e
                            break
                    
                    if target is None:
                        print(f"[WARNING] 未找到目标 {action['target']}")
                        continue
                    
                    # 找邻居（带优先级）
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
                    print(f"[SELECT] {target.id} -> {neighbor_id}")
                    
                    # 更新使用统计
                    self.kb.update_usage([neighbor_id])
                    
                    neighbor_data = self.kb.get_qa(neighbor_id)
                    neighbor_entity = SemiconductorQAEntity(neighbor_id, neighbor_data, self.kb)
                    neighbor_entity = await self.extract_qa_info(neighbor_entity)
                    
                    # 构建关联QA
                    try:
                        link_qa = await self.construct_link_qa(target, neighbor_entity)
                    except Exception as e:
                        print(f"[WARNING] 构建关联QA失败: {e}")
                        continue
                    
                    # 检查重复
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
                    
                    # 组合QA（多跳推理的核心）
                    try:
                        combine_qa = await self.combine_qa(memory.qa, link_qa, memory)
                        q_new = combine_qa['question']
                    except Exception as e:
                        print(f"[WARNING] 组合QA失败: {e}")
                        continue
                    
                    memory_new.relevant.append(neighbor_entity)
                    memory_new.statements.append(link_qa['statement'])
                    memory_new.edit_history.append(f"选择 '{target.name}' 及其相关实体 '{neighbor_entity.name}'")
                    memory_new.edit_history.append(f"构建关联QA: Q={link_qa['question'][:50]}... A={link_qa['answer'][:50]}...")
                    memory_new.edit_history.append(f"组合后新问题: '{q_new[:100]}...'")
                
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
                        q_new, answers, memory.qa['answer']
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
            
            # Step 4: 🆕 尝试生成多跳QA（2-3跳）
            multihop_result = None
            if len(memory.relevant) >= 2:
                # 根据已有实体数量决定跳数
                max_hops = min(len(memory.relevant), 3)
                num_hops = random.choice([2, 3]) if max_hops == 3 else 2
                
                if self.debug_mode:
                    print(f"\n[DEBUG] 尝试生成{num_hops}跳QA...")
                
                multihop_result = await self.generate_multihop_qa(
                    root_entity=memory.relevant[0],
                    num_hops=num_hops
                )
            
            # Step 5: 🆕 问题筛选流程
            final_question = memory.qa['question']
            final_answer = memory.qa['answer']
            passed_filtering = True
            
            if self.enable_qa_filtering and multihop_result:
                if self.debug_mode:
                    print(f"\n[DEBUG] 开始问题筛选流程...")
                
                # 准备子问答对
                sub_qa_pairs = [e.qa_data for e in memory.relevant]
                
                # 评估问题
                eval_result = await self.evaluate_question(
                    multihop_result['question'],
                    sub_qa_pairs
                )
                
                passed_filtering = eval_result['passed']
                
                if passed_filtering:
                    final_question = multihop_result['question']
                    final_answer = multihop_result.get('answer', memory.qa['answer'])
                    print(f"[FILTER] ✓ 问题通过筛选")
                else:
                    print(f"[FILTER] ✗ 问题未通过筛选，使用迭代结果")
            
            # Step 6: 🆕 答案重新生成流程
            if self.enable_answer_regeneration and multihop_result and passed_filtering:
                if self.debug_mode:
                    print(f"\n[DEBUG] 开始答案重新生成流程...")
                
                sub_qa_pairs = [e.qa_data for e in memory.relevant]
                reasoning_steps = multihop_result.get('reasoning_steps', [])
                
                regen_result = await self.regenerate_answer(
                    final_question,
                    final_answer,
                    sub_qa_pairs,
                    reasoning_steps
                )
                
                if regen_result.get('confidence', 0) >= 0.6:
                    final_answer = regen_result['final_answer']
                    print(f"[REGEN] ✓ 答案重新生成成功（置信度: {regen_result['confidence']}）")
                else:
                    print(f"[REGEN] 置信度较低，保留原答案")
            
            # Step 7: 保存结果
            output = {
                'uid': memory.uid,
                'question': final_question,
                'answer': final_answer,
                'source_qa_ids': [e.id for e in memory.relevant],
                'source_papers': list(set([e.qa_data.get('paper_name', 'unknown') for e in memory.relevant])),
                'statements': memory.statements,
                'edit_history': memory.edit_history,
                'action_stats': dict(action_stats),
                'num_turns': turn + 1,
                'has_multihop': multihop_result is not None,
                'passed_filtering': passed_filtering,
                'answer_regenerated': self.enable_answer_regeneration and multihop_result and passed_filtering
            }
            
            if multihop_result:
                output['multihop_metadata'] = {
                    'num_hops': multihop_result.get('num_hops', 0),
                    'reasoning_steps': multihop_result.get('reasoning_steps', []),
                    'quality_indicators': multihop_result.get('quality_indicators', {})
                }
            
            # 保存
            import os
            os.makedirs(save_path, exist_ok=True)
            output_file = os.path.join(save_path, f"{memory.uid}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            print(f"\n[DONE] QA已保存: {output_file}")
            print(f"       最终问题: {final_question[:80]}...")
            print(f"       答案长度: {len(final_answer)} 字符")
            
            return output
