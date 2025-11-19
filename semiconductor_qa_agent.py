# # """
# # 半导体领域复杂QA生成Agent
# # 支持vLLM和SGLang推理框架
# # """

# # import re
# # import time
# # import random
# # import uuid
# # import json
# # import copy
# # import asyncio
# # import aiohttp
# # import requests
# # import numpy as np
# # from collections import defaultdict
# # from transformers import AutoTokenizer
# # from typing import Dict, List, Any, Optional
# # import tqdm


# # # ============ Prompts ============

# # class SemiconductorQAPrompts:
# #     """半导体领域QA构建Prompts"""
    
# #     base_qa = '''你是一个半导体领域的QA构建专家。基于给定的半导体知识材料，提出一个简单但需要专业知识才能回答的问题。确保问题清晰、可解、答案唯一。

# # # 半导体知识材料
# # {content}

# # 输出JSON格式：
# # ```json
# # {{
# #     "question": "提出的问题",
# #     "answer": "问题答案",
# #     "statement": "该问答对涉及的核心事实陈述",
# #     "key_concepts": ["关键概念1", "关键概念2"]
# # }}
# # ```
# # '''

# #     link_qa = '''你是一个半导体领域的QA构建专家。给定两个半导体概念的信息，构建一个问题，其中答案是{conceptA}，问题上下文涉及{conceptB}。确保问题需要专业的半导体知识。

# # # 概念A ({conceptA}) 的信息：
# # ```txt
# # {contentA}
# # ```

# # # 概念B ({conceptB}) 的信息：
# # ```txt
# # {contentB}
# # ```

# # 输出JSON格式：
# # ```json
# # {{
# #     "question": "提出的问题",
# #     "answer": "问题答案",
# #     "statement": "连接两个概念的核心事实",
# #     "key_concepts": ["涉及的关键概念"]
# # }}
# # ```
# # '''

# #     compose_qa = '''你是一个半导体领域的QA构建专家。将两个问题组合成一个更复杂的问题。第二个问题的答案关联到第一个问题中的某个实体。组合后的问题应移除第二个问题答案的直接信息，但保持第一个问题的答案不变。

# # 第一个问题：
# # ```
# # {questionA}
# # ```

# # 第二个问题：
# # ```
# # {questionB}
# # ```

# # 相关的技术陈述：
# # ```
# # {statements}
# # ```

# # 输出JSON格式：
# # ```json
# # {{
# #     "question": "组合后的问题",
# #     "answer": "答案（与第一个问题相同）",
# #     "note": "如何组合的简要说明"
# # }}
# # ```
# # '''

# #     compose_qa_by_statement = '''你是一个半导体领域的QA构建专家。将一个技术概念融入现有的问答对。该概念通过陈述与问答对连接。组合后应移除直接连接信息，使问题更具挑战性，但保持原答案不变。

# # 现有问答对：
# # ```
# # {question}
# # ```

# # 要融入的技术概念和陈述：
# # ```
# # {entity}
# # ```

# # 支撑性技术陈述：
# # ```
# # {statements}
# # ```

# # 输出JSON格式：
# # ```json
# # {{
# #     "question": "改进后的问题",
# #     "answer": "答案（保持不变）",
# #     "note": "如何融入概念的说明"
# # }}
# # ```
# # '''

# #     action = '''你是一个半导体领域的QA构建专家。基于当前问答对和相关信息，选择一个操作来提升问题难度。

# # 当前问答对：
# # {question}

# # 可选操作：
# # {actions}
# # '''

# #     SELECT = '''SELECT: 从相关概念列表中选择一个概念。外部工具会将该概念相关的信息融入问题，替换为需要推理的子问题。

# # 如果选择SELECT，输出JSON格式：
# # ```json
# # {{
# #     "action": "SELECT",
# #     "target": "选中概念的ID（必须来自相关概念列表）",
# #     "note": "选择该概念的理由"
# # }}
# # ```'''

# #     FUZZ = '''FUZZ: 模糊化问题中的1处信息，使问题更具挑战性。确保模糊化后问题仍然清晰且答案唯一。仅当某些信息过于直接指向答案时使用。

# # 如果选择FUZZ，输出JSON格式：
# # ```json
# # {{
# #     "action": "FUZZ",
# #     "question": "模糊化后的问题",
# #     "note": "为何以及如何进行模糊化"
# # }}
# # ```'''

# #     EXIT = '''EXIT: 当问题满足以下所有条件时退出：
# # - 需要深入的半导体专业知识才能回答
# # - 提供的信息足够模糊，没有单一信息能直接指向答案

# # 如果选择EXIT，输出JSON格式：
# # ```json
# # {{
# #     "action": "EXIT",
# #     "note": "为何选择退出"
# # }}
# # ```'''

# #     BRAINSTORM = '''BRAINSTORM: 头脑风暴与当前问答对相关的半导体概念（如工艺节点、材料、器件类型、物理效应等）。这些概念将被融入问题以增加难度。确保概念的事实准确性。

# # 如果选择BRAINSTORM，输出JSON格式：
# # ```json
# # {{
# #     "action": "BRAINSTORM",
# #     "entities": [
# #         {{
# #             "name": "概念名称",
# #             "concept_id": "概念在知识库中的ID（如果有）",
# #             "statement": "连接该概念与当前问答的事实陈述"
# #         }}
# #     ]
# # }}
# # ```'''

# #     extract_key_concepts = '''从以下半导体知识内容中提取关键技术概念（材料、工艺、器件、物理效应等）。

# # 内容：
# # ```txt
# # {content}
# # ```

# # 输出JSON格式的概念列表：
# # ```json
# # [
# #     {{"concept": "概念名", "type": "概念类型（材料/工艺/器件/效应等）"}},
# #     ...
# # ]
# # ```
# # '''

# #     summarize_qa = '''总结以下半导体问答对的核心技术要点。

# # 问答对：
# # ```txt
# # 问题: {question}
# # 答案: {answer}
# # ```

# # 输出格式：
# # <summary>核心技术摘要</summary>
# # <key_points>
# # - 关键点1
# # - 关键点2
# # </key_points>
# # '''

# #     check_info_cover = '''检查新陈述的信息是否已被先前陈述完全覆盖。

# # 先前的技术陈述：
# # ```txt
# # {prior}
# # ```

# # 待检查的陈述：
# # ```txt
# # {current}
# # ```

# # 分析后给出判断：

# # # 分析
# # // 你的分析

# # # 最终判断
# # ```json
# # {{
# #     "judgement": "yes 或 no"
# # }}
# # ```
# # '''

# #     check_alternative_ans = '''判断预测答案是否也是该半导体问题的正确答案。预测答案与标准答案不同，检查其是否满足问题的所有约束。

# # 问题: {question}

# # 标准答案: {gt_answer}

# # 支撑标准答案的技术事实：
# # ```txt
# # {statements}
# # ```

# # 预测答案: {pred_answer}

# # ```json
# # {{
# #     "judgement": "yes 或 no"
# # }}
# # ```
# # '''

# #     qa_valid_check = '''检查该半导体问答对的有效性。

# # 问答对有效当且仅当：
# # 1. 问题不是简单拼接多个问题
# # 2. 提供的答案是唯一正确答案
# # 3. 问题有唯一答案
# # 4. 基于相关技术陈述可以解答

# # 问答对和相关信息：
# # {question}

# # 分析后给出判断：

# # # 分析
# # // 你的分析

# # # 最终判断
# # ```json
# # {{
# #     "judgement": "yes 或 no"
# # }}
# # ```
# # '''

# #     direct_gen_check = """回答以下半导体技术问题，将答案放在<answer></answer>标签内。\n\n{question}"""
    
# #     llm_judge = """你是一个评估助手。判断预测答案是否等价于标准答案。

# # 问题: {question}

# # 标准答案: {gt_answer}

# # 预测答案: {pred_answer}

# # 如果等价回答"Correct"，否则回答"Incorrect"。不要包含其他文字。
# # """


# # # ============ Knowledge Base ============

# # class SemiconductorKnowledgeBase:
# #     """半导体知识库：管理QA数据和概念关系"""
    
# #     def __init__(self, qa_data: List[Dict]):
# #         self.qa_data = {qa['id']: qa for qa in qa_data}
# #         self.qa_ids = list(self.qa_data.keys())
        
# #         self.concept_to_qas = defaultdict(list)
# #         self.qa_to_concepts = defaultdict(list)
# #         self.paper_to_qas = defaultdict(list)
        
# #         self._build_indexes()
    
# #     def _build_indexes(self):
# #         """构建索引"""
# #         for qa_id, qa in self.qa_data.items():
# #             paper = qa.get('paper_name', 'unknown')
# #             self.paper_to_qas[paper].append(qa_id)
            
# #             concepts = self._extract_concepts_simple(qa['question'] + ' ' + qa['answer'])
# #             for concept in concepts:
# #                 self.concept_to_qas[concept].append(qa_id)
# #                 self.qa_to_concepts[qa_id].append(concept)
    
# #     def _extract_concepts_simple(self, text: str) -> List[str]:
# #         """简单概念提取"""
# #         keywords = [
# #             '氧化物', '薄膜晶体管', 'TFT', '载流子', '迁移率', '阈值电压',
# #             '氧空位', '栅极', '源极', '漏极', '沟道', '介电层',
# #             'IGZO', 'LTPS', 'a-Si', 'OLED', 'LCD',
# #             '溅射', '退火', '刻蚀', '沉积', '钝化',
# #             '电子', '空穴', '能带', '费米能级', '态密度',
# #             '半导体', '晶体管', '器件', '材料', '工艺'
# #         ]
        
# #         concepts = []
# #         for keyword in keywords:
# #             if keyword in text:
# #                 concepts.append(keyword)
# #         return list(set(concepts))
    
# #     def find_related_qas(self, qa_id: str, top_k: int = 5) -> List[str]:
# #         """找到相关的QA"""
# #         if qa_id not in self.qa_to_concepts:
# #             return random.sample(self.qa_ids, min(top_k, len(self.qa_ids)))
        
# #         concepts = self.qa_to_concepts[qa_id]
# #         scores = defaultdict(int)
        
# #         for concept in concepts:
# #             for related_qa_id in self.concept_to_qas[concept]:
# #                 if related_qa_id != qa_id:
# #                     scores[related_qa_id] += 1
        
# #         sorted_qas = sorted(scores.items(), key=lambda x: x[1], reverse=True)
# #         related_ids = [qa_id for qa_id, _ in sorted_qas[:top_k]]
        
# #         if len(related_ids) < top_k:
# #             remaining = [qid for qid in self.qa_ids if qid != qa_id and qid not in related_ids]
# #             related_ids.extend(random.sample(remaining, min(top_k - len(related_ids), len(remaining))))
        
# #         return related_ids
    
# #     def get_qa(self, qa_id: str) -> Dict:
# #         return self.qa_data.get(qa_id)
    
# #     def get_qa_repr(self, qa_id: str) -> str:
# #         qa = self.get_qa(qa_id)
# #         if not qa:
# #             return ""
        
# #         concepts = self.qa_to_concepts.get(qa_id, [])
# #         concept_str = ', '.join(concepts) if concepts else '无'
        
# #         return f"""ID: {qa_id}
# # 问题: {qa['question']}
# # 答案: {qa['answer']}
# # 来源论文: {qa.get('paper_name', 'unknown')}
# # 关键概念: {concept_str}
# # """


# # class SemiconductorQAEntity:
# #     """半导体QA实体"""
    
# #     def __init__(self, qa_id: str, qa_data: Dict, kb: SemiconductorKnowledgeBase):
# #         self.id = qa_id
# #         self.qa_data = qa_data
# #         self.kb = kb
# #         self.summary = None
# #         self.key_concepts = []
# #         self.related_qas = []
    
# #     @property
# #     def name(self):
# #         return f"QA-{self.id}"
    
# #     @property
# #     def url(self):
# #         return self.id
    
# #     def repr(self):
# #         """生成实体的文本表示，仅使用question和answer"""
# #         concepts_str = ', '.join(self.key_concepts) if self.key_concepts else '待提取'
# #         related_str = ', '.join([f"QA-{rid}" for rid in self.related_qas[:3]]) if self.related_qas else '无'
        
# #         # 只使用question和answer字段
# #         question = self.qa_data.get('question', '')
# #         answer = self.qa_data.get('answer', '')
# #         paper_name = self.qa_data.get('paper_name', 'unknown')
        
# #         return f"""# QA实体 {self.id}

# # ## 问题
# # {question}

# # ## 答案
# # {answer}

# # ## 来源
# # 论文: {paper_name}

# # ## 关键概念
# # {concepts_str}

# # ## 相关QA
# # {related_str}

# # ## 摘要
# # {self.summary or '待生成'}
# # """
    
# #     def dict(self):
# #         return {
# #             'id': self.id,
# #             'name': self.name,
# #             'url': self.url,
# #             'qa_data': self.qa_data,
# #             'summary': self.summary,
# #             'key_concepts': self.key_concepts,
# #             'related_qas': self.related_qas
# #         }


# # class AgentMemory:
# #     """Agent记忆"""
    
# #     def __init__(self):
# #         self.qa = dict(question=None, answer=None)
# #         self.statements = []
# #         self.relevant = []
# #         self.edit_history = []
# #         self.qa_history = []
# #         self.uid = None
    
# #     def repr(self):
# #         relevant = '\n'.join([f'- [{e.name}] (ID: {e.id})' for e in self.relevant])
# #         statements = '\n'.join(self.statements)
# #         return f"""
# # 当前问题: {self.qa['question']}
# # 当前答案: {self.qa['answer']}

# # 相关技术陈述：
# # ```txt
# # {statements}
# # ```

# # 相关QA实体列表：
# # ```txt
# # {relevant}
# # ```
# # """
    
# #     def statements_repr(self, additional=None):
# #         return '\n'.join(self.statements + (additional or []))
    
# #     def dict(self):
# #         return {
# #             'qa': self.qa,
# #             'relevant': [e.dict() for e in self.relevant],
# #             'statements': self.statements,
# #             'edit_history': self.edit_history,
# #             'qa_history': self.qa_history,
# #             'uid': self.uid
# #         }


# # # ============ LLM Client ============

# # class LLMAPIClient:
# #     """统一的LLM API客户端，支持vLLM和SGLang"""
    
# #     def __init__(self, model_path: str, server_type: str = "vllm", 
# #                  host: str = "localhost", port: int = 8000, max_retries: int = 3):
# #         self.model_path = model_path
# #         self.server_type = server_type.lower()
# #         self.base_url = f"http://{host}:{port}"
# #         self.session = None
# #         self.max_retries = max_retries
# #         self.is_connected = False
        
# #         print(f"\n{'='*60}")
# #         print(f"[LLM] 初始化 {server_type.upper()} 客户端")
# #         print(f"[LLM] 模型: {model_path}")
# #         print(f"[LLM] 服务器: {self.base_url}")
# #         print(f"{'='*60}\n")
        
# #         self._check_server()
    
# #     def _check_server(self):
# #         """检查服务器是否可用"""
# #         test_url = f"{self.base_url}/v1/models"
        
# #         try:
# #             res = requests.get(test_url, timeout=10)
# #             if res.status_code == 200:
# #                 print(f"[LLM] ✓ 服务器连接成功")
# #                 self.is_connected = True
# #                 # 打印服务器信息
# #                 models_info = res.json()
# #                 print(f"[LLM] 可用模型: {models_info}")
# #                 return
# #         except requests.exceptions.RequestException as e:
# #             print(f"[WARNING] ✗ 无法连接到服务器 {self.base_url}: {e}")
        
# #         print(f"[WARNING] 请确保已启动 {self.server_type} 服务")
    
# #     async def __aenter__(self):
# #         """异步上下文管理器入口"""
# #         self.session = aiohttp.ClientSession()
# #         return self
    
# #     async def __aexit__(self, exc_type, exc_val, exc_tb):
# #         """异步上下文管理器出口"""
# #         if self.session:
# #             await self.session.close()
    
# #     async def async_generate(self, prompt: str, sampling_kwargs: Dict):
# #         """异步生成，使用聊天格式"""
# #         for attempt in range(self.max_retries):
# #             try:
# #                 return await self._vllm_chat_generate(prompt, sampling_kwargs)
# #             except aiohttp.ClientError as e:
# #                 if attempt == self.max_retries - 1:
# #                     raise
# #                 wait_time = 2 ** attempt
# #                 print(f"[RETRY] 第{attempt + 1}次重试，等待{wait_time}秒...")
# #                 await asyncio.sleep(wait_time)
# #             except Exception as e:
# #                 raise
    
# #     async def _vllm_chat_generate(self, prompt: str, sampling_kwargs: Dict):
# #         """vLLM聊天格式生成"""
# #         if not self.session:
# #             raise RuntimeError("Session not initialized. Use async context manager.")
            
# #         n = sampling_kwargs.get('n', 1)
        
# #         # 使用聊天格式
# #         messages = [
# #             {"role": "user", "content": prompt}
# #         ]
        
# #         payload = {
# #             "model": self.model_path,
# #             "messages": messages,
# #             "max_tokens": sampling_kwargs.get('max_new_tokens', 8192),
# #             "temperature": sampling_kwargs.get('temperature', 0.8),
# #             "top_p": sampling_kwargs.get('top_p', 0.95),
# #             "top_k": sampling_kwargs.get('top_k', -1),
# #             "n": n,
# #             "stream": False
# #         }
        
# #         # 移除None值
# #         payload = {k: v for k, v in payload.items() if v is not None}
        
# #         print(f"[DEBUG] 请求payload: {json.dumps(payload, ensure_ascii=False)[:500]}...")
        
# #         async with self.session.post(
# #             url=f"{self.base_url}/v1/chat/completions",  # 使用聊天端点
# #             json=payload,
# #             timeout=aiohttp.ClientTimeout(total=300)
# #         ) as response:
# #             if response.status != 200:
# #                 error_text = await response.text()
# #                 print(f"[ERROR] 服务器返回错误: {response.status}, {error_text}")
# #                 raise aiohttp.ClientResponseError(
# #                     request_info=response.request_info,
# #                     history=response.history,
# #                     status=response.status,
# #                     message=f"HTTP {response.status}: {error_text}"
# #                 )
            
# #             result = await response.json()
# #             print(f"[DEBUG] 响应: {json.dumps(result, ensure_ascii=False)[:500]}...")
            
# #             if n == 1:
# #                 return {"text": result['choices'][0]['message']['content']}
# #             else:
# #                 texts = [choice['message']['content'] for choice in result['choices']]
# #                 return {"text": texts}


# # # ============ Agent ============

# # class SemiconductorQAAgent:
# #     """半导体领域QA生成Agent"""
    
# #     def __init__(self, knowledge_base: SemiconductorKnowledgeBase, 
# #                  llm_client, max_turns: int = 16):
# #         self.kb = knowledge_base
# #         self.llm_client = llm_client
# #         self.max_turns = max_turns
# #         self.tokenizer = AutoTokenizer.from_pretrained("/mnt/data/LLM/lhy/models/Qwen/Qwen2.5-14B-Instruct")
    
# #     async def call_llm(self, prompt: str) -> str:
# #         """调用LLM"""
# #         prompt = self.tokenizer.apply_chat_template(
# #             [{"role": "user", "content": prompt}], 
# #             add_generation_prompt=True, 
# #             tokenize=False
# #         )
        
# #         max_new_tokens = 8000 - self.tokenizer([prompt], return_length=True)["length"][0]
# #         max_new_tokens = max(max_new_tokens, 512)
        
# #         sampling_kwargs = {
# #             "temperature": 0.8,
# #             "top_p": 0.95,
# #             "top_k": 1000,
# #             "max_new_tokens": max_new_tokens,
# #             "n": 1,
# #             "stop_token_ids": [151645, 151643]
# #         }
        
# #         try:
# #             output = await self.llm_client.async_generate(prompt, sampling_kwargs)
# #             response = output["text"]
# #             return response
# #         except Exception as e:
# #             print(f"[ERROR] LLM调用失败: {e}")
# #             raise
    
# #     async def extract_qa_info(self, entity: SemiconductorQAEntity) -> SemiconductorQAEntity:
# #         """提取QA实体的详细信息"""
# #         print(f"[INFO] 提取 QA-{entity.id} 的信息")
        
# #         try:
# #             # 生成摘要
# #             prompt = SemiconductorQAPrompts.summarize_qa.format(
# #                 question=entity.qa_data['question'],
# #                 answer=entity.qa_data['answer']
# #             )
# #             summary_text = await self.call_llm(prompt)
            
# #             if '<summary>' in summary_text and '</summary>' in summary_text:
# #                 entity.summary = summary_text.split('<summary>')[1].split('</summary>')[0].strip()
            
# #             # 提取关键概念
# #             concept_prompt = SemiconductorQAPrompts.extract_key_concepts.format(
# #                 content=entity.qa_data['question'] + '\n' + entity.qa_data['answer']
# #             )
# #             concept_text = await self.call_llm(concept_prompt)
            
# #             if '```json' in concept_text:
# #                 try:
# #                     concepts_list = json.loads(concept_text.split('```json')[1].split('```')[0].strip())
# #                     entity.key_concepts = [c['concept'] for c in concepts_list]
# #                 except:
# #                     entity.key_concepts = self.kb.qa_to_concepts.get(entity.id, [])
# #         except Exception as e:
# #             print(f"[WARNING] 提取信息失败: {e}")
# #             entity.key_concepts = self.kb.qa_to_concepts.get(entity.id, [])
        
# #         # 找相关QA
# #         entity.related_qas = self.kb.find_related_qas(entity.id, top_k=5)
        
# #         return entity
    
# #     async def construct_base_qa(self, entity: SemiconductorQAEntity) -> Dict:
# #         """构建基础QA"""
# #         prompt = SemiconductorQAPrompts.base_qa.format(content=entity.repr())
# #         text = await self.call_llm(prompt)
        
# #         base_qa = json.loads(text.split('```json')[1].split('```')[0].strip())
# #         return base_qa
    
# #     async def choose_action(self, state: str, ready_to_exit: bool = False) -> Dict:
# #         """选择下一步操作"""
# #         actions = [
# #             SemiconductorQAPrompts.FUZZ,
# #             SemiconductorQAPrompts.SELECT,
# #         ]
# #         random.shuffle(actions)
        
# #         if ready_to_exit:
# #             actions.append(SemiconductorQAPrompts.EXIT)
        
# #         prompt = SemiconductorQAPrompts.action.format(
# #             question=state,
# #             actions='\n\n'.join(actions)
# #         )
        
# #         text = await self.call_llm(prompt)
# #         action = json.loads(text.split('```json')[1].split('```')[0].strip())
        
# #         assert action['action'] in ['SELECT', 'FUZZ', 'EXIT', 'BRAINSTORM']
# #         return action
    
# #     async def construct_link_qa(self, entityA: SemiconductorQAEntity, 
# #                                entityB: SemiconductorQAEntity) -> Dict:
# #         """构建关联QA"""
# #         prompt = SemiconductorQAPrompts.link_qa.format(
# #             conceptA=entityA.name,
# #             conceptB=entityB.name,
# #             contentA=entityA.repr(),
# #             contentB=entityB.repr()
# #         )
# #         text = await self.call_llm(prompt)
# #         link_qa = json.loads(text.split('```json')[1].split('```')[0].strip())
# #         return link_qa
    
# #     async def combine_qa(self, questionA: Dict, questionB: Dict, memory: AgentMemory) -> Dict:
# #         """组合两个问答"""
# #         prompt = SemiconductorQAPrompts.compose_qa.format(
# #             questionA=json.dumps({'question': questionA['question'], 'answer': questionA['answer']}, ensure_ascii=False),
# #             questionB=json.dumps({'question': questionB['question'], 'answer': questionB['answer']}, ensure_ascii=False),
# #             statements=memory.statements_repr(additional=[questionB['statement']])
# #         )
# #         text = await self.call_llm(prompt)
# #         combined = json.loads(text.split('```json')[1].split('```')[0].strip())
# #         return combined
    
# #     async def check_info_cover(self, statement: str, prior_statements: str) -> bool:
# #         """检查信息覆盖"""
# #         prompt = SemiconductorQAPrompts.check_info_cover.format(
# #             prior=prior_statements,
# #             current=statement
# #         )
# #         text = await self.call_llm(prompt)
# #         result = json.loads(text.split('```json')[1].split('```')[0].strip())
# #         return result['judgement'] == 'yes'
    
# #     async def check_qa_valid(self, state: str) -> bool:
# #         """检查QA有效性"""
# #         prompt = SemiconductorQAPrompts.qa_valid_check.format(question=state)
# #         text = await self.call_llm(prompt)
# #         result = json.loads(text.split('```json')[1].split('```')[0].strip())
# #         return 'yes' in result['judgement']
    
# #     async def direct_generate(self, question: str, n: int = 1) -> List[str]:
# #         """直接生成答案"""
# #         prompt = SemiconductorQAPrompts.direct_gen_check.format(question=question)
# #         prompt = self.tokenizer.apply_chat_template(
# #             [{"role": "user", "content": prompt}],
# #             add_generation_prompt=True,
# #             tokenize=False
# #         )
        
# #         max_new_tokens = 8000 - self.tokenizer([prompt], return_length=True)["length"][0]
# #         max_new_tokens = max(max_new_tokens, 512)
        
# #         sampling_kwargs = {
# #             "temperature": 0.6,
# #             "top_p": 0.95,
# #             "top_k": 1000,
# #             "max_new_tokens": max_new_tokens,
# #             "n": n,
# #             "stop_token_ids": [151645, 151643]
# #         }
        
# #         output = await self.llm_client.async_generate(prompt, sampling_kwargs)
# #         texts = [o["text"] for o in output] if isinstance(output["text"], list) else [output["text"]]
        
# #         answers = []
# #         for text in texts:
# #             if '<answer>' in text and '</answer>' in text:
# #                 answers.append(text.split('<answer>')[1].split('</answer>')[0].strip())
# #             else:
# #                 answers.append(None)
        
# #         return answers
    
# #     async def llm_judge_answer(self, question: str, answers: List[str], 
# #                               gt_answer: str) -> List[bool]:
# #         """LLM判断答案正确性"""
# #         corrects = []
# #         for ans in answers:
# #             if ans is None:
# #                 corrects.append(False)
# #             else:
# #                 prompt = SemiconductorQAPrompts.llm_judge.format(
# #                     question=question,
# #                     gt_answer=gt_answer,
# #                     pred_answer=ans
# #                 )
# #                 text = await self.call_llm(prompt)
# #                 corrects.append('Correct' in text)
# #         return corrects
    
# #     async def check_alternative_answer(self, question: str, gt_answer: str,
# #                                       pred_answer: str, statements: str) -> bool:
# #         """检查替代答案"""
# #         prompt = SemiconductorQAPrompts.check_alternative_ans.format(
# #             question=question,
# #             gt_answer=gt_answer,
# #             pred_answer=pred_answer,
# #             statements=statements
# #         )
# #         text = await self.call_llm(prompt)
# #         return 'yes' in text.lower()
    
# #     async def generate(self, semaphore: asyncio.Semaphore, save_path: str):
# #         """生成一个复杂QA"""
# #         async with semaphore:
# #             # 随机选择根QA
# #             root_id = random.choice(self.kb.qa_ids)
# #             root_qa_data = self.kb.get_qa(root_id)
            
# #             memory = AgentMemory()
# #             memory.uid = str(uuid.uuid4())
            
# #             print(f"\n{'='*60}")
# #             print(f"[START] 生成QA，根实体: QA-{root_id}")
# #             print(f"{'='*60}\n")
            
# #             # 创建根实体
# #             root_entity = SemiconductorQAEntity(root_id, root_qa_data, self.kb)
# #             root_entity = await self.extract_qa_info(root_entity)
# #             memory.relevant.append(root_entity)
            
# #             # 构建基础QA
# #             try:
# #                 base_qa = await self.construct_base_qa(root_entity)
# #             except Exception as e:
# #                 print(f"[ERROR] 构建基础QA失败: {e}")
# #                 return None
            
# #             if not (isinstance(base_qa, dict) and all(k in base_qa for k in ['question', 'answer', 'statement'])):
# #                 print("[ERROR] 基础QA格式错误")
# #                 return None
            
# #             memory.qa['question'] = base_qa['question']
# #             memory.qa['answer'] = base_qa['answer']
# #             memory.statements.append(base_qa['statement'])
# #             memory.qa_history.append(base_qa)
# #             memory.edit_history.append(f"从 QA-{root_id} 创建基础问题\n问题: {base_qa['question']}\n答案: {base_qa['answer']}")
            
# #             print(f"\n[BASE QA] {base_qa['question']}")
            
# #             ready_to_exit = False
# #             action_stats = defaultdict(int)
            
# #             # 迭代优化
# #             for turn in range(self.max_turns):
# #                 print(f"\n--- 第 {turn+1} 轮 ---")
                
# #                 state = memory.repr()
                
# #                 if turn == 0:
# #                     action = {'action': 'none'}
# #                 else:
# #                     try:
# #                         action = await self.choose_action(state, ready_to_exit)
# #                     except Exception as e:
# #                         print(f"[WARNING] 选择动作失败: {e}")
# #                         continue
                
# #                 action_stats[action['action']] += 1
# #                 print(f"[ACTION] {action['action']} - {action.get('note', '')}")
                
# #                 q_new = None
# #                 memory_new = copy.deepcopy(memory)
# #                 memory_new.edit_history.append(f"动作: {action['action']}. 说明: {action.get('note', '')}")
                
# #                 # 执行不同的动作
# #                 if action['action'] == 'FUZZ':
# #                     q_new = action['question']
# #                     memory_new.edit_history.append(f"FUZZ操作将问题修改为: {q_new}")
                
# #                 elif action['action'] == 'EXIT':
# #                     print("[INFO] 问题生成完成，退出")
# #                     break
                
# #                 elif action['action'] == 'none':
# #                     assert turn == 0
# #                     q_new = base_qa['question']
                
# #                 elif action['action'] == 'SELECT':
# #                     # 找到目标实体
# #                     target = None
# #                     for e in memory.relevant:
# #                         if e.id == action['target'] or e.url == action['target']:
# #                             target = e
# #                             break
                    
# #                     if target is None:
# #                         print(f"[WARNING] 未找到目标 {action['target']}")
# #                         continue
                    
# #                     # 找邻居
# #                     candidates = target.related_qas
# #                     exist_ids = [e.id for e in memory.relevant]
# #                     candidates = [c for c in candidates if c not in exist_ids]
                    
# #                     if not candidates:
# #                         print(f"[WARNING] QA-{target.id} 没有可用的相关QA")
# #                         continue
                    
# #                     neighbor_id = random.choice(candidates)
# #                     print(f"[SELECT] {target.id} -> {neighbor_id}")
                    
# #                     neighbor_data = self.kb.get_qa(neighbor_id)
# #                     neighbor_entity = SemiconductorQAEntity(neighbor_id, neighbor_data, self.kb)
# #                     neighbor_entity = await self.extract_qa_info(neighbor_entity)
                    
# #                     # 构建关联QA
# #                     try:
# #                         link_qa = await self.construct_link_qa(target, neighbor_entity)
# #                     except Exception as e:
# #                         print(f"[WARNING] 构建关联QA失败: {e}")
# #                         continue
                    
# #                     # 检查重复
# #                     try:
# #                         duplicate = await self.check_info_cover(
# #                             link_qa['statement'],
# #                             memory_new.statements_repr()
# #                         )
# #                     except Exception as e:
# #                         print(f"[WARNING] 检查重复失败: {e}")
# #                         continue
                    
# #                     if duplicate:
# #                         print("[WARNING] 陈述重复，跳过")
# #                         continue
                    
# #                     # 组合QA
# #                     try:
# #                         combine_qa = await self.combine_qa(memory.qa, link_qa, memory)
# #                         q_new = combine_qa['question']
# #                     except Exception as e:
# #                         print(f"[WARNING] 组合QA失败: {e}")
# #                         continue
                    
# #                     memory_new.relevant.append(neighbor_entity)
# #                     memory_new.statements.append(link_qa['statement'])
# #                     memory_new.edit_history.append(f"选择 '{target.name}' 及其相关实体 '{neighbor_entity.name}'")
# #                     memory_new.edit_history.append(f"构建关联QA: Q={link_qa['question'][:50]}... A={link_qa['answer'][:50]}...")
# #                     memory_new.edit_history.append(f"组合后新问题: '{q_new[:100]}...'")
                
# #                 print(f"\n[NEW Q] {q_new}\n")
# #                 memory_new.qa['question'] = q_new
                
# #                 # 验证有效性
# #                 try:
# #                     valid = await self.check_qa_valid(memory_new.repr())
# #                 except Exception as e:
# #                     print(f"[WARNING] 验证有效性失败: {e}")
# #                     valid = False
                
# #                 if not valid:
# #                     print(f"[WARNING] 第{turn+1}轮QA无效")
# #                     continue
                
# #                 # 直接生成测试
# #                 try:
# #                     answers = await self.direct_generate(q_new, n=4)
# #                 except Exception as e:
# #                     print(f"[WARNING] 直接生成失败: {e}")
# #                     continue
                
# #                 try:
# #                     corrects = await self.llm_judge_answer(
# #                         q_new, answers, memory.qa['answer']
# #                     )
# #                 except Exception as e:
# #                     print(f"[WARNING] LLM判断失败: {e}")
# #                     continue
                
# #                 # 检查替代答案
# #                 is_alternative = False
# #                 for pred_ans, correct in zip(answers, corrects):
# #                     if pred_ans and not correct:
# #                         try:
# #                             is_alternative = await self.check_alternative_answer(
# #                                 q_new, memory.qa['answer'], pred_ans,
# #                                 memory.statements_repr()
# #                             )
# #                         except Exception as e:
# #                             print(f"[WARNING] 检查替代答案失败: {e}")
                        
# #                         if is_alternative:
# #                             break
                
# #                 if is_alternative:
# #                     print(f"[WARNING] 存在替代答案 '{pred_ans[:50]}...'，跳过")
# #                     continue
                
# #                 # 更新记忆
# #                 memory = memory_new
# #                 acc = f"{sum(corrects)}/{len(corrects)}"
# #                 print(f"[RESULT] 直接生成准确率: {acc}")
                
# #                 memory.qa_history.append({
# #                     'question': q_new,
# #                     'answer': memory.qa['answer'],
# #                     'direct_gen_acc': acc
# #                 })
# #                 memory.edit_history.append(f"直接生成准确率: {acc}")
                
# #                 if not any(corrects):
# #                     ready_to_exit = True
# #                     print(f"[INFO] 第{turn+1}轮问题LLM全部答错，准备退出")
                
# #                 print(f"[STATS] 动作统计: {dict(action_stats)}")
            
# #             # 保存结果
# #             output_file = f"{save_path}/{memory.uid}.jsonl"
# #             with open(output_file, 'w', encoding='utf-8') as f:
# #                 f.write(json.dumps(memory.dict(), ensure_ascii=False))
            
# #             print(f"\n[SAVED] {output_file}")
# #             print(f"{'='*60}\n")
            
# #             return memory


# # # ============ Batch Generation ============

# # async def generate_batch(agent: SemiconductorQAAgent, 
# #                         save_path: str, 
# #                         batch_size: int = 128,
# #                         total: int = 1024):
# #     """批量生成QA"""
# #     semaphore = asyncio.Semaphore(batch_size)
# #     tasks = [agent.generate(semaphore, save_path) for _ in range(total)]
    
# #     print(f"\n{'='*60}")
# #     print(f"[BATCH] 开始生成 {total} 个QA，并发数: {batch_size}")
# #     print(f"{'='*60}\n")
    
# #     results = await asyncio.gather(*tasks, return_exceptions=True)
    
# #     # 统计结果
# #     success = sum(1 for r in results if r is not None and not isinstance(r, Exception))
# #     failed = total - success
    
# #     print(f"\n{'='*60}")
# #     print(f"[BATCH] 完成！成功: {success}, 失败: {failed}")
# #     print(f"{'='*60}\n")
    
# #     return results


# # # ============ Main ============

# # def main():
# #     """主函数"""
# #     import argparse
# #     import os
    
# #     parser = argparse.ArgumentParser(description="半导体领域QA生成")
# #     parser.add_argument('--input', type=str, required=True, help='输入JSONL文件路径')
# #     parser.add_argument('--output', type=str, required=True, help='输出目录')
# #     parser.add_argument('--model_path', type=str, required=True, help='本地模型路径或名称')
# #     parser.add_argument('--server_type', type=str, default='vllm', 
# #                        choices=['vllm', 'sglang'], help='推理框架类型')
# #     parser.add_argument('--host', type=str, default='localhost', help='服务器地址')
# #     parser.add_argument('--port', type=int, default=8000, help='服务器端口')
# #     parser.add_argument('--batch_size', type=int, default=32, help='并发数')
# #     parser.add_argument('--total', type=int, default=100, help='生成总数')
# #     parser.add_argument('--max_turns', type=int, default=16, help='最大迭代轮数')
    
# #     args = parser.parse_args()
    
# #     # 加载数据
# #     print(f"\n{'='*60}")
# #     print(f"[LOAD] 加载数据: {args.input}")
# #     print(f"{'='*60}\n")
    
# #     qa_data = []
# #     with open(args.input, 'r', encoding='utf-8') as f:
# #         for line in tqdm.tqdm(f, desc="Loading"):
# #             qa_data.append(json.loads(line))
    
# #     print(f"\n[LOAD] ✓ 加载了 {len(qa_data)} 条QA数据\n")
    
# #     # 构建知识库
# #     print(f"{'='*60}")
# #     print("[KB] 构建知识库...")
# #     print(f"{'='*60}\n")
    
# #     kb = SemiconductorKnowledgeBase(qa_data)
    
# #     print(f"[KB] 知识库统计:")
# #     print(f"  - QA数量: {len(kb.qa_data)}")
# #     print(f"  - 概念数量: {len(kb.concept_to_qas)}")
# #     print(f"  - 论文数量: {len(kb.paper_to_qas)}")
    
# #     # 创建输出目录
# #     os.makedirs(args.output, exist_ok=True)
# #     print(f"\n[OUTPUT] 输出目录: {args.output}\n")
    
# #     # 初始化LLM客户端
# #     llm_client = LLMAPIClient(
# #         model_path=args.model_path,
# #         server_type=args.server_type,
# #         host=args.host,
# #         port=args.port
# #     )
    
# #     # 创建Agent
# #     agent = SemiconductorQAAgent(kb, llm_client, max_turns=args.max_turns)
    
# #     # 运行生成
# #     async def run():
# #         async with llm_client:
# #             results = await generate_batch(
# #                 agent,
# #                 args.output,
# #                 batch_size=args.batch_size,
# #                 total=args.total
# #             )
# #         return results
    
# #     print(f"\n{'='*60}")
# #     print(f"[INFO] 开始生成...")
# #     print(f"{'='*60}\n")
    
# #     results = asyncio.run(run())
    
# #     print(f"\n{'='*60}")
# #     print(f"[DONE] 所有结果已保存到: {args.output}")
# #     print(f"{'='*60}\n")


# # if __name__ == "__main__":
# #     main()





# import re
# import time
# import random
# import uuid
# import json
# import copy
# import asyncio
# import aiohttp
# import requests
# from collections import defaultdict
# from transformers import AutoTokenizer
# from typing import Dict, List, Any, Optional
# import tqdm
# import os


# # ============ 专家8维度标准的Prompts ============

# class ExpertQAPrompts:
#     """融合专家8维度评估标准的Prompts"""
    
#     # ===== 多跳问题生成（核心） =====
#     compose_multihop_qa = '''你是半导体领域的多跳QA构建专家。基于给定的{num_hops}个单跳问答，生成一个高质量的多跳问题及答案。

# # 单跳问答列表

# {single_hop_qas}

# # 桥接关系

# {bridge_info}

# ---

# <think>
# 首先，我需要理解这{num_hops}个单跳问答之间的逻辑关系。

# 让我分析：
# 1. 识别每个问答的核心技术点
# 2. 理解桥接关系如何连接它们
# 3. 确定组合后的推理逻辑链

# 接下来，我将基于以下原则设计多跳问题：
# - 问题必须展现完整的推理链条
# - 问题需要逻辑推理才能解答，体现{num_hops}步依赖关系
# - 问题描述要清晰、完整、专业、具有通用性
# - 避免使用"基于上述"、"根据前面"等依赖性表述
# - 确保问题具有技术深度，不是简单拼接
# - 问题必须是单一问题，不包含多个疑问点
# </think>

# ## 【核心要求】（严格执行）

# ### 1. 问题设计准则：

# **(1) 因果链完整性**
# - 问题需呈现完整技术逻辑链：机制A → 参数B → 现象C
# - 体现{num_hops}步推理的必要性

# **(2) 通用性（严格执行）**
# - ✓ 问题必须具有通用性，不局限于特定论文
# - ✗ 禁止使用"本文"、"本研究"、"本实验"等自指表述
# - ✗ 禁止引用文献或文章自定义的专有名词
# - ✓ 确保不读论文也能理解问题含义

# **(3) 单一性（严格执行）**
# - ✓ 问题只包含一个核心疑问点
# - ✗ 禁止连接多个子问题
# - ✗ 禁止在一个句子中包含多个疑问点

# 错误示例：
# "在氧化物薄膜晶体管中，如何通过调控氧分压实现高迁移率？并分析其对器件稳定性的影响？"（包含2个问题）

# 正确示例：
# "在氧化物薄膜晶体管制备中，氧分压参数如何通过影响氧空位浓度进而调控载流子迁移率和器件长期稳定性？"（单一问题，完整推理链）

# **(4) 可追溯性**
# - 问题基于给定的单跳问答生成
# - 答案能够基于给定的单跳答案推导得出

# **(5) 简洁凝练**
# - 问题长度控制在20-40词
# - 避免冗余描述

# ### 2. 答案生成准则：

# **(1) 完整性（严格执行）**
# - ✓ 必须完整回答问题的所有方面
# - ✓ 必须体现{num_hops}步推理过程
# - ✗ 禁止仅引导句，必须提供实质性内容
# - ✗ 禁止只回答某一个子问题

# **(2) 准确性（严格执行）**
# - ✓ 答案必须准确无误
# - ✓ 必须基于给定的单跳答案逻辑推导
# - ✗ 不得脱离原始信息

# **(3) 通用性（严格执行）**
# - ✓ 答案具有通用性，不特指论文
# - ✗ 禁止使用"本文"、"本研究"等表述
# - ✗ 禁止引用文献或文章自定义的专有名词
# - ✓ 确保不读论文也能理解答案含义

# **(4) 逻辑连贯性**
# - 答案需体现清晰的推理过程
# - 每一步推理都要明确
# - 展现步骤之间的因果关系

# **(5) 答案策略（根据桥接类型）**
# - causal（因果）: 体现完整因果链，最终答案应是因果推理的结论
# - hierarchical（层次）: 综合各层次信息，形成完整认知
# - comparison（比较）: 给出比较分析的综合结论
# - temporal（时序）: 总结发展趋势或演进规律

# ### 3. 推理步骤要求：

# - 必须包含{num_hops}个清晰的推理步骤
# - 每个步骤对应一个单跳问答的核心内容
# - 步骤之间要有明确的逻辑连接词
# - 每个步骤长度至少15个字

# ## 【禁止事项】

# × 禁止使用"本文/本研究/本实验"等论文自指表述
# × 禁止问题中出现"基于上述"、"根据前面"等依赖性表述
# × 禁止提问孤立概念
# × 禁止复合问题（严格执行）
# × 禁止问题或答案中引用文献或文章自定义专有名词
# × 禁止特指论文内容
# × 禁止答案不完整（仅引导句）
# × 禁止答案只回答部分问题

# ---

# 输出JSON格式：
# ```json
# {{
#     "multihop_question": "多跳问题（单一、通用、{num_hops}步推理链）",
#     "multihop_answer": "多跳答案（完整、准确、基于单跳答案推导）",
#     "reasoning_steps": [
#         {{"step": 1, "content": "第一步推理内容（至少15字）", "based_on": "单跳QA-1"}},
#         {{"step": 2, "content": "第二步推理内容（至少15字）", "based_on": "单跳QA-2"}}
#     ],
#     "key_concepts": ["核心概念1", "核心概念2"],
#     "bridge_type": "{bridge_type}",
#     "quality_check": {{
#         "is_single_question": true,
#         "is_universal": true,
#         "no_paper_reference": true,
#         "answer_complete": true,
#         "answer_based_on_single_hops": true
#     }}
# }}
# ```
# '''

#     # ===== 8维度质量评估 =====
#     evaluate_8dimensions = '''你是半导体领域的QA质量评估专家。基于8个核心维度评估以下多跳问答的质量。

# # 待评估的问答

# **问题：**
# {question}

# **答案：**
# {answer}

# **推理步骤：**
# {reasoning_steps}

# **单跳问答依据：**
# {single_hop_qas}

# ---

# ## 8维度评估标准（一票否决机制）

# ### 1. 问题通用性 (Question Universality)
# - [ ] 问题是否依据子问题答案生成？
# - [ ] 问题是否具有实际意义和通用性？
# - [ ] 问题是否只是简单的子问题组合？（禁止）
# - [ ] 问题中是否引用文献或文章自定义的专有名词？（禁止）
# - [ ] 是否是多跳问题？（必须是）
# - [ ] 是否使用"本文"、"本研究"等自指表述？（禁止）

# **一票否决**: 使用自指、引用专有名词、非多跳 → `low`

# ### 2. 回答相关性 (Relevance)
# - [ ] 回答是否精准聚焦问题核心？
# - [ ] 是否存在答非所问、偏离主题或遗漏关键点？
# - [ ] 答案是否只是仅引导句未提供实质性内容？（禁止）
# - [ ] 答案是否和问题的主要逻辑相关？

# **一票否决**: 仅引导句、完全偏离 → `low`

# ### 3. 逻辑一致性 (Logical Consistency)
# - [ ] 回答的推理过程是否清晰、连贯、无矛盾？
# - [ ] 是否存在逻辑跳跃、断裂或自相矛盾？
# - [ ] 是否存在答案中断？
# - [ ] 答案是否只是泛泛而谈？

# **一票否决**: 逻辑混乱、不相关 → `low`

# ### 4. 术语使用 (Terminology Usage)
# - [ ] 专业术语的使用是否准确、恰当、完整？
# - [ ] 是否存在术语误用、滥用、缺失或概念性错误？
# - [ ] 术语描述是否完整（不能缩写）？

# **一票否决**: 关键术语严重错误 → `low`

# ### 5. 事实正确性 (Factual Correctness)
# - [ ] 技术细节、参数、原理是否符合行业共识？
# - [ ] 是否存在事实性错误或过时信息？

# **一票否决**: 明显事实错误 → `low`

# ### 6. 答案通用性 (Answer Universality)
# - [ ] 答案是否特指论文？（禁止）
# - [ ] 答案是否具有通用性？
# - [ ] 答案中是否引用文献或文章自定义的专有名词？（禁止）
# - [ ] 答案是否使用"本文"、"本研究"等自指表述？（禁止）

# **一票否决**: 自指、专有名词、特指论文 → `low`

# ### 7. 答案准确完整性 (Answer Completeness)
# - [ ] 答案是否准确回答了问题？（严格执行）
# - [ ] 答案是否完整回答了问题（回答了各个子问题）？（严格执行）
# - [ ] 答案是否简洁凝练，无冗余？
# - [ ] 答案是否只回答了部分问题？（禁止）
# - [ ] 答案中是否有错误？

# **一票否决**: 不准确、不完整、有错误 → `low`

# ### 8. 答案可靠性 (Answer Reliability)
# - [ ] 答案是否依据子问题的答案回答的？（严格执行）
# - [ ] 答案是否可以从子问题答案中逻辑推导得出？
# - [ ] 答案是否脱离了原始信息？（禁止）

# **一票否决**: 不基于单跳答案、脱离原始信息 → `low`

# ---

# 输出JSON格式：
# ```json
# {{
#     "dimension_scores": {{
#         "question_universality": {{"score": "high/medium/low", "issues": [], "veto": false}},
#         "relevance": {{"score": "high/medium/low", "issues": [], "veto": false}},
#         "logical_consistency": {{"score": "high/medium/low", "issues": [], "veto": false}},
#         "terminology_usage": {{"score": "high/medium/low", "issues": [], "veto": false}},
#         "factual_correctness": {{"score": "high/medium/low", "issues": [], "veto": false}},
#         "answer_universality": {{"score": "high/medium/low", "issues": [], "veto": false}},
#         "answer_completeness": {{"score": "high/medium/low", "issues": [], "veto": false}},
#         "answer_reliability": {{"score": "high/medium/low", "issues": [], "veto": false}}
#     }},
#     "overall_quality": "high/medium/low",
#     "veto_triggered": false,
#     "veto_reasons": [],
#     "specific_issues": {{
#         "question_issues": [],
#         "answer_issues": []
#     }},
#     "improvement_suggestions": [],
#     "suitable_for_rl": true
# }}
# ```
# '''

#     # ===== 精炼优化 =====
#     refine_qa = '''你是半导体领域的QA优化专家。基于质量评估结果，精炼优化以下问答。

# # 当前问答

# **问题：** {question}
# **答案：** {answer}

# # 质量问题

# {quality_issues}

# ---

# ## 优化目标（优先级排序）

# ### 1. 消除一票否决问题（最高优先级）
# - 移除"本文"、"本研究"等自指表述
# - 移除文献专有名词，替换为通用术语
# - 确保答案完整回答问题
# - 确保答案基于单跳答案推导

# ### 2. 提升通用性
# - 将特指论文的内容改为通用表述
# - 确保不读论文也能理解

# ### 3. 优化逻辑连贯性
# - 确保推理链清晰
# - 消除逻辑跳跃

# ### 4. 完善答案内容
# - 补充缺失的推理步骤
# - 确保回答问题的所有方面

# ---

# 输出JSON格式：
# ```json
# {{
#     "refined_question": "优化后的问题",
#     "refined_answer": "优化后的答案",
#     "changes_made": ["改进1", "改进2"],
#     "remaining_issues": [],
#     "expected_quality": "high/medium"
# }}
# ```
# '''

#     # ===== 最终验证 =====
#     final_validation = '''对以下问答进行最终质量验证（25项检查清单）。

# **问题：** {question}
# **答案：** {answer}

# ---

# ## 检查清单（全部通过才能批准）

# ### 问题检查（10项）
# - [ ] 1. 问题具有通用性，不特指论文
# - [ ] 2. 问题无"本文"、"本研究"等自指表述
# - [ ] 3. 问题无文献或文章自定义专有名词
# - [ ] 4. 问题是多跳问题（有推理链）
# - [ ] 5. 问题是单一问题（不包含多个疑问点）
# - [ ] 6. 问题清晰、专业、可解
# - [ ] 7. 问题长度适中（20-40词）
# - [ ] 8. 问题基于单跳问答生成
# - [ ] 9. 不读论文也能理解问题
# - [ ] 10. 问题具有实际意义

# ### 答案检查（10项）
# - [ ] 1. 答案完整回答了问题（所有方面）
# - [ ] 2. 答案准确无误
# - [ ] 3. 答案基于单跳答案逻辑推导
# - [ ] 4. 答案具有通用性，不特指论文
# - [ ] 5. 答案无"本文"、"本研究"等自指表述
# - [ ] 6. 答案无文献或文章自定义专有名词
# - [ ] 7. 答案提供实质性内容（非仅引导句）
# - [ ] 8. 答案逻辑清晰、连贯
# - [ ] 9. 答案术语准确、完整
# - [ ] 10. 不读论文也能理解答案

# ### 推理链检查（5项）
# - [ ] 1. 推理步骤数量正确
# - [ ] 2. 每步推理清晰明确
# - [ ] 3. 步骤之间有逻辑连接
# - [ ] 4. 推理链完整、无跳跃
# - [ ] 5. 每步至少15字

# ---

# 输出JSON格式：
# ```json
# {{
#     "is_approved": true,
#     "checks_passed": 25,
#     "checks_failed": 0,
#     "failed_items": [],
#     "overall_quality": "high",
#     "suitable_for_rl": true
# }}
# ```
# '''

#     # ===== 辅助工具 =====
#     extract_concepts_llm = '''从QA中提取关键技术概念。

# 问题：{question}
# 答案：{answer}

# 输出JSON格式：
# ```json
# {{
#     "key_concepts": [
#         {{"name": "概念名", "type": "材料/工艺/器件/效应/参数", "importance": "high"}}
#     ]
# }}
# ```
# '''


# # ============ LLM Client ============

# class LLMClient:
#     """统一LLM客户端"""
    
#     def __init__(self, model_path: str, host: str = "localhost", port: int = 8000):
#         self.model_path = model_path
#         self.base_url = f"http://{host}:{port}"
#         self.session = None
#         self.tokenizer = AutoTokenizer.from_pretrained(model_path)
#         print(f"[LLM] 初始化: {self.base_url}")
#         self._check_server()
    
#     def _check_server(self):
#         """检查服务器连接"""
#         try:
#             response = requests.get(f"{self.base_url}/v1/models", timeout=5)
#             if response.status_code == 200:
#                 print(f"[LLM] ✓ 服务器连接成功")
#             else:
#                 print(f"[WARNING] 服务器响应异常: {response.status_code}")
#         except Exception as e:
#             print(f"[WARNING] 无法连接到服务器: {e}")
    
#     async def __aenter__(self):
#         self.session = aiohttp.ClientSession()
#         return self
    
#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         if self.session:
#             await self.session.close()
    
#     async def call(self, prompt: str, max_tokens: int = 12288, temperature: float = 0.8) -> str:
#         """调用LLM"""
#         messages = [{"role": "user", "content": prompt}]
        
#         payload = {
#             "model": self.model_path,
#             "messages": messages,
#             "max_tokens": max_tokens,
#             "temperature": temperature,
#             "top_p": 0.95
#         }
        
#         try:
#             async with self.session.post(
#                 f"{self.base_url}/v1/chat/completions",
#                 json=payload,
#                 timeout=aiohttp.ClientTimeout(total=300)
#             ) as response:
#                 result = await response.json()
#                 return result['choices'][0]['message']['content']
#         except Exception as e:
#             print(f"[ERROR] LLM调用失败: {e}")
#             raise
    
#     def parse_json(self, text: str) -> Dict:
#         """解析JSON响应"""
#         try:
#             if '```json' in text:
#                 text = text.split('```json')[1].split('```')[0].strip()
#             return json.loads(text)
#         except Exception as e:
#             print(f"[WARNING] JSON解析失败: {e}")
#             print(f"[DEBUG] 原始文本: {text[:200]}...")
#             return {}


# # ============ Knowledge Base with Smart Linking ============

# class SemiconductorKB:
#     """半导体知识库 - 智能链接版（基于桥接实体）"""
    
#     def __init__(self, qa_data: List[Dict], llm: LLMClient):
#         self.qa_data = {qa['id']: qa for qa in qa_data}
#         self.qa_ids = list(self.qa_data.keys())
#         self.llm = llm
        
#         # 索引
#         self.concept_cache = {}
#         self.paper_to_qas = defaultdict(list)
#         self.qa_to_paper = {}
        
#         # 🆕 桥接索引（核心）
#         self.entity_to_qas = defaultdict(list)  # 实体 -> 包含该实体的QA
#         self.qa_to_entities = defaultdict(list)  # QA -> 包含的实体
        
#         self._build_indexes()
        
#         print(f"[KB] 加载 {len(self.qa_data)} 条单跳QA")
#         print(f"[KB] 论文数量: {len(self.paper_to_qas)}")
    
#     def _build_indexes(self):
#         """构建所有索引"""
#         for qa_id, qa in self.qa_data.items():
#             # Paper索引
#             paper_name = qa.get('paper_name', 'unknown')
#             self.paper_to_qas[paper_name].append(qa_id)
#             self.qa_to_paper[qa_id] = paper_name
            
#             # 🆕 实体索引（简单提取）
#             entities = self._extract_entities_simple(qa['question'], qa['answer'])
#             for entity in entities:
#                 self.entity_to_qas[entity].append(qa_id)
#                 self.qa_to_entities[qa_id].append(entity)
        
#         # 统计
#         print(f"[KB] 提取到 {len(self.entity_to_qas)} 个桥接实体")
#         avg_entities = sum(len(v) for v in self.qa_to_entities.values()) / len(self.qa_to_entities)
#         print(f"[KB] 平均每个QA包含 {avg_entities:.1f} 个实体")
    
#     def _extract_entities_simple(self, question: str, answer: str) -> List[str]:
#         """
#         简单实体提取（规则+关键词）
#         实体包括：材料、工艺、器件、参数、效应等
#         """
#         text = question + ' ' + answer
        
#         # 半导体领域关键实体（扩展版）
#         entities = []
        
#         # 材料类
#         materials = [
#             'IGZO', 'LTPS', 'a-Si', 'poly-Si', 'SiO2', 'Al2O3', 'HfO2',
#             '氧化物', '硅', '氮化硅', '氧化硅', '金属氧化物',
#             '氧化铟镓锌', '多晶硅', '非晶硅'
#         ]
        
#         # 器件类
#         devices = [
#             'TFT', '薄膜晶体管', 'OLED', 'LCD', 'LED',
#             'MOSFET', '晶体管', '二极管', '电容', '电阻'
#         ]
        
#         # 工艺类
#         processes = [
#             '溅射', '退火', '刻蚀', '沉积', '钝化', '离子注入',
#             '化学气相沉积', 'CVD', 'PVD', '氧化', '扩散', '光刻'
#         ]
        
#         # 参数类
#         parameters = [
#             '迁移率', '阈值电压', '开关比', '亚阈值摆幅', '漏电流',
#             '载流子浓度', '电导率', '能带', '功函数', '介电常数',
#             '氧分压', '温度', '厚度', '浓度'
#         ]
        
#         # 效应/机制类
#         effects = [
#             '氧空位', '缺陷', '陷阱态', '界面态', '载流子',
#             '电子', '空穴', '复合', '散射', '隧穿',
#             '费米能级', '态密度', '能带弯曲'
#         ]
        
#         all_keywords = materials + devices + processes + parameters + effects
        
#         for keyword in all_keywords:
#             if keyword in text:
#                 entities.append(keyword)
        
#         return list(set(entities))
    
#     async def extract_concepts(self, qa_id: str) -> List[str]:
#         """LLM提取概念（更深度）"""
#         if qa_id in self.concept_cache:
#             return self.concept_cache[qa_id]
        
#         qa = self.qa_data[qa_id]
#         prompt = ExpertQAPrompts.extract_concepts_llm.format(
#             question=qa['question'],
#             answer=qa['answer']
#         )
        
#         try:
#             response = await self.llm.call(prompt, max_tokens=512)
#             data = self.llm.parse_json(response)
#             concepts = [c['name'] for c in data.get('key_concepts', [])]
#             self.concept_cache[qa_id] = concepts
#             return concepts
#         except:
#             return self.qa_to_entities.get(qa_id, [])
    
#     def get_qa(self, qa_id: str) -> Dict:
#         return self.qa_data.get(qa_id)
    
#     def find_bridgeable_qas(self, qa_id: str, max_candidates: int = 20) -> List[Dict]:
#         """
#         🆕 找到可以和qa_id桥接的其他QA（核心方法）
        
#         逻辑：
#         1. 提取qa_id的答案中的实体
#         2. 找到"问题"中包含这些实体的其他QA
#         3. 确保来自不同paper（增加多样性）
#         4. 返回候选列表
        
#         Returns:
#             [{'qa_id': ..., 'bridge_entity': ..., 'score': ...}]
#         """
#         qa = self.get_qa(qa_id)
#         if not qa:
#             return []
        
#         source_paper = self.qa_to_paper.get(qa_id, 'unknown')
        
#         # 从答案中提取实体（这些实体可能出现在下一跳的问题中）
#         answer_entities = self._extract_entities_simple('', qa['answer'])
        
#         candidates = []
#         seen_qas = set()
        
#         for entity in answer_entities:
#             # 找到问题中包含该实体的QA
#             for candidate_id in self.entity_to_qas.get(entity, []):
#                 if candidate_id == qa_id or candidate_id in seen_qas:
#                     continue
                
#                 candidate_qa = self.get_qa(candidate_id)
#                 candidate_paper = self.qa_to_paper.get(candidate_id, 'unknown')
                
#                 # 🔑 关键：检查实体是否在候选QA的"问题"中
#                 if entity in candidate_qa['question']:
#                     # 计算桥接分数
#                     score = 1.0
                    
#                     # 🎯 不同paper加分（鼓励跨领域）
#                     if candidate_paper != source_paper and source_paper != 'unknown':
#                         score += 0.5
                    
#                     # 实体在问题开头加分（更可能是核心概念）
#                     if candidate_qa['question'].find(entity) < len(candidate_qa['question']) * 0.3:
#                         score += 0.3
                    
#                     candidates.append({
#                         'qa_id': candidate_id,
#                         'bridge_entity': entity,
#                         'score': score,
#                         'paper': candidate_paper,
#                         'question_preview': candidate_qa['question'][:60]
#                     })
                    
#                     seen_qas.add(candidate_id)
        
#         # 按分数排序
#         candidates.sort(key=lambda x: x['score'], reverse=True)
        
#         return candidates[:max_candidates]
    
#     def select_single_hops_smart(self, num_hops: int = 2) -> List[str]:
#         """
#         🆕 智能选择可链接的单跳QA（基于桥接实体）
        
#         策略：
#         1. 随机选择第一个QA（来自任意paper）
#         2. 找到能与第一个桥接的第二个QA（优先不同paper）
#         3. 如果num_hops=3，继续找能与第二个桥接的第三个
        
#         确保：跨paper + 有逻辑连接
#         """
#         if num_hops < 2:
#             return random.sample(self.qa_ids, min(num_hops, len(self.qa_ids)))
        
#         selected_ids = []
#         selected_papers = set()
        
#         # 第一跳：随机选择
#         first_id = random.choice(self.qa_ids)
#         selected_ids.append(first_id)
#         selected_papers.add(self.qa_to_paper.get(first_id, 'unknown'))
        
#         print(f"[LINK] 第1跳: {first_id} (paper: {self.qa_to_paper.get(first_id, 'unknown')})")
        
#         # 后续跳：基于桥接选择
#         for hop_idx in range(1, num_hops):
#             prev_id = selected_ids[-1]
            
#             # 找可桥接的候选
#             candidates = self.find_bridgeable_qas(prev_id, max_candidates=20)
            
#             if not candidates:
#                 print(f"[WARNING] 第{hop_idx+1}跳：没有可桥接的QA，降级为随机选择")
#                 # 降级：随机选择一个未选过的
#                 remaining = [qid for qid in self.qa_ids if qid not in selected_ids]
#                 if remaining:
#                     selected_ids.append(random.choice(remaining))
#                 continue
            
#             # 🎯 优先选择不同paper的候选
#             diff_paper_candidates = [
#                 c for c in candidates
#                 if c['paper'] not in selected_papers and c['paper'] != 'unknown'
#             ]
            
#             if diff_paper_candidates:
#                 chosen = diff_paper_candidates[0]
#             else:
#                 # 如果没有不同paper的，选分数最高的
#                 chosen = candidates[0]
            
#             selected_ids.append(chosen['qa_id'])
#             selected_papers.add(chosen['paper'])
            
#             print(f"[LINK] 第{hop_idx+1}跳: {chosen['qa_id']} "
#                   f"(paper: {chosen['paper']}, "
#                   f"桥接实体: {chosen['bridge_entity']}, "
#                   f"分数: {chosen['score']:.2f})")
#             print(f"       问题: {chosen['question_preview']}...")
        
#         return selected_ids
    
#     def get_bridge_info(self, qa_ids: List[str]) -> str:
#         """
#         生成桥接信息描述（用于prompt）
#         """
#         if len(qa_ids) < 2:
#             return "单个问答，无桥接关系"
        
#         bridge_desc = []
        
#         for i in range(len(qa_ids) - 1):
#             qa1 = self.get_qa(qa_ids[i])
#             qa2 = self.get_qa(qa_ids[i+1])
            
#             # 找共同实体
#             entities1 = set(self._extract_entities_simple(qa1['question'], qa1['answer']))
#             entities2 = set(self._extract_entities_simple(qa2['question'], qa2['answer']))
            
#             # 重点：qa1的答案中的实体在qa2的问题中
#             answer_entities1 = set(self._extract_entities_simple('', qa1['answer']))
#             question_entities2 = set(self._extract_entities_simple(qa2['question'], ''))
            
#             bridge_entities = answer_entities1 & question_entities2
            
#             if bridge_entities:
#                 bridge_desc.append(
#                     f"QA-{i+1}的答案中提到的'{list(bridge_entities)[0]}'是QA-{i+2}问题的核心概念，"
#                     f"形成因果推理链。"
#                 )
#             else:
#                 # 备用：找共同实体
#                 common = entities1 & entities2
#                 if common:
#                     bridge_desc.append(
#                         f"QA-{i+1}和QA-{i+2}通过共同概念'{list(common)[0]}'连接。"
#                     )
#                 else:
#                     bridge_desc.append(
#                         f"QA-{i+1}和QA-{i+2}在技术领域上相关。"
#                     )
        
#         return '\n'.join(bridge_desc)


# # ============ QA Generator Agent (Updated) ============

# class ExpertQAAgent:
#     """融合专家8维度标准的QA生成Agent（使用智能链接）"""
    
#     def __init__(self, kb: SemiconductorKB, llm: LLMClient, 
#                  max_turns: int = 8, max_refine: int = 3):
#         self.kb = kb
#         self.llm = llm
#         self.max_turns = max_turns
#         self.max_refine = max_refine
#         print(f"[Agent] 初始化 (最大轮数={max_turns}, 最大精炼={max_refine})")
    
#     async def generate_multihop_qa(self, single_hops: List[Dict], 
#                                 bridge_info: str = "") -> Dict:
#         num_hops = len(single_hops)
        
#         # ✅ 235B 可以使用完整内容，不需要截断！
#         single_hop_str = "\n\n".join([
#             f"QA-{i+1} (来自论文: {qa.get('paper_name', 'unknown')}):\n"
#             f"问题: {qa['question']}\n"  # 完整问题
#             f"答案: {qa['answer']}"      # 完整答案
#             for i, qa in enumerate(single_hops)
#         ])
        
#         prompt = ExpertQAPrompts.compose_multihop_qa.format(
#             num_hops=num_hops,
#             single_hop_qas=single_hop_str,
#             bridge_info=bridge_info,  # 完整桥接信息
#             bridge_type="causal"
#         )
        
#         # 🆕 增加 max_tokens
#         response = await self.llm.call(prompt, max_tokens=12288)
#         multihop = self.llm.parse_json(response)
        
#         return multihop
    
#     async def evaluate_quality(self, question: str, answer: str,
#                               reasoning_steps: List[Dict],
#                               single_hops: List[Dict]) -> Dict:
#         """8维度质量评估"""
#         # 格式化推理步骤
#         steps_str = "\n".join([
#             f"步骤{s['step']}: {s['content']}"
#             for s in reasoning_steps
#         ])
        
#         # 格式化单跳QA
#         single_hop_str = "\n".join([
#             f"QA-{i+1}: Q={qa['question'][:50]}... A={qa['answer'][:50]}..."
#             for i, qa in enumerate(single_hops)
#         ])
        
#         prompt = ExpertQAPrompts.evaluate_8dimensions.format(
#             question=question,
#             answer=answer,
#             reasoning_steps=steps_str,
#             single_hop_qas=single_hop_str
#         )
        
#         response = await self.llm.call(prompt, max_tokens=1024)
#         evaluation = self.llm.parse_json(response)
        
#         return evaluation
    
#     async def refine_qa(self, question: str, answer: str, 
#                        quality_issues: Dict) -> Dict:
#         """精炼优化QA"""
#         issues_str = json.dumps(quality_issues, ensure_ascii=False, indent=2)
        
#         prompt = ExpertQAPrompts.refine_qa.format(
#             question=question,
#             answer=answer,
#             quality_issues=issues_str
#         )
        
#         response = await self.llm.call(prompt, max_tokens=1024)
#         refined = self.llm.parse_json(response)
        
#         return refined
    
#     async def final_validate(self, question: str, answer: str) -> Dict:
#         """最终验证（25项检查）"""
#         prompt = ExpertQAPrompts.final_validation.format(
#             question=question,
#             answer=answer
#         )
        
#         response = await self.llm.call(prompt, max_tokens=512)
#         validation = self.llm.parse_json(response)
        
#         return validation
    
#     async def generate_one(self, save_path: str) -> Optional[Dict]:
#         """生成一个高质量多跳QA（使用智能链接）"""
#         uid = str(uuid.uuid4())
#         start_time = time.time()
        
#         # 1. 🆕 智能选择可链接的单跳QA
#         num_hops = random.choice([2, 3])
#         root_ids = self.kb.select_single_hops_smart(num_hops)
#         single_hops = [self.kb.get_qa(qid) for qid in root_ids]
        
#         # 🆕 生成桥接信息
#         bridge_info = self.kb.get_bridge_info(root_ids)
        
#         print(f"\n{'='*60}")
#         print(f"[START] UID={uid[:8]}")
#         print(f"[BRIDGE] {bridge_info}")
        
#         # 2. 生成初始多跳QA
#         try:
#             multihop = await self.generate_multihop_qa(single_hops, bridge_info)
#         except Exception as e:
#             print(f"[ERROR] 生成失败: {e}")
#             return None
        
#         if not multihop or 'multihop_question' not in multihop:
#             print("[ERROR] 生成的多跳QA格式错误")
#             return None
        
#         question = multihop['multihop_question']
#         answer = multihop['multihop_answer']
#         reasoning_steps = multihop.get('reasoning_steps', [])
        
#         print(f"[INIT Q] {question[:80]}...")
#         print(f"[INIT A] {answer[:80]}...")
        
#         # 3. 迭代优化（最多max_refine次）
#         evaluation = {}
#         for refine_iter in range(self.max_refine):
#             print(f"\n--- 精炼迭代 {refine_iter+1}/{self.max_refine} ---")
            
#             # 评估质量
#             try:
#                 evaluation = await self.evaluate_quality(
#                     question, answer, reasoning_steps, single_hops
#                 )
#             except Exception as e:
#                 print(f"[ERROR] 质量评估失败: {e}")
#                 break
            
#             overall_quality = evaluation.get('overall_quality', 'low')
#             veto_triggered = evaluation.get('veto_triggered', False)
            
#             print(f"[QUALITY] {overall_quality}")
            
#             if veto_triggered:
#                 print(f"[VETO] 一票否决: {evaluation.get('veto_reasons', [])}")
            
#             # 如果达到high质量，退出优化循环
#             if overall_quality == 'high' and not veto_triggered:
#                 print("[SUCCESS] 达到high质量！")
#                 break
            
#             # 如果是low且有一票否决，尝试修复
#             if overall_quality == 'low' or veto_triggered:
#                 print("[REFINE] 尝试修复...")
                
#                 try:
#                     refined = await self.refine_qa(
#                         question, answer,
#                         evaluation.get('specific_issues', {})
#                     )
                    
#                     question = refined.get('refined_question', question)
#                     answer = refined.get('refined_answer', answer)
                    
#                     print(f"[REFINED Q] {question[:80]}...")
#                     print(f"[REFINED A] {answer[:80]}...")
#                 except Exception as e:
#                     print(f"[ERROR] 精炼失败: {e}")
#                     break
#             else:
#                 # medium质量，可以接受，退出
#                 print("[ACCEPT] medium质量，可接受")
#                 break
        
#         # 4. 最终验证
#         try:
#             validation = await self.final_validate(question, answer)
#         except Exception as e:
#             print(f"[ERROR] 最终验证失败: {e}")
#             validation = {'is_approved': False}
        
#         is_approved = validation.get('is_approved', False)
#         checks_passed = validation.get('checks_passed', 0)
        
#         print(f"\n[VALIDATION] 通过检查: {checks_passed}/25")
        
#         if not is_approved:
#             print(f"[REJECT] 未通过最终验证")
#             print(f"[FAILED] {validation.get('failed_items', [])}")
#             overall_quality = 'low'
#             suitable_for_rl = False
#         else:
#             print(f"[APPROVED] ✓ 通过所有检查")
#             overall_quality = validation.get('overall_quality', 'high')
#             suitable_for_rl = True
        
#         # 计算耗时
#         total_time = time.time() - start_time
        
#         # 5. 保存结果
#         result = {
#             'uid': uid,
#             'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            
#             # 输入数据
#             'single_hop_ids': root_ids,
#             'single_hops': single_hops,
#             'num_hops': num_hops,
#             'bridge_info': bridge_info,  # 🆕 桥接信息
            
#             # 生成的多跳QA
#             'multihop_question': question,
#             'multihop_answer': answer,
#             'reasoning_steps': reasoning_steps,
#             'key_concepts': multihop.get('key_concepts', []),
#             'bridge_type': multihop.get('bridge_type', 'causal'),
            
#             # 质量评估
#             'quality_evaluation': evaluation,
#             'final_validation': validation,
            
#             # 生成过程信息
#             'generation_metadata': {
#                 'refine_iterations': refine_iter + 1 if 'refine_iter' in locals() else 0,
#                 'total_time_seconds': round(total_time, 2),
#                 'model_used': self.llm.model_path,
#                 'generation_params': {
#                     'max_turns': self.max_turns,
#                     'max_refine': self.max_refine
#                 },
#                 'linking_strategy': 'smart_bridge'  # 🆕 链接策略
#             },
            
#             # 最终标记
#             'overall_quality': overall_quality,
#             'suitable_for_rl': suitable_for_rl,
#             'quality_score': self._calculate_quality_score(evaluation)
#         }
        
#         print(f"\n[SUMMARY] 质量={overall_quality}, RL适用={suitable_for_rl}, 耗时={total_time:.1f}s")
#         print(f"{'='*60}\n")
        
#         return result
    
#     def _calculate_quality_score(self, evaluation: Dict) -> float:
#         """计算质量分数"""
#         if not evaluation or 'dimension_scores' not in evaluation:
#             return 0.0
        
#         score_map = {'high': 1.0, 'medium': 0.6, 'low': 0.0}
#         scores = []
        
#         for dim_info in evaluation['dimension_scores'].values():
#             score_str = dim_info.get('score', 'low')
#             scores.append(score_map.get(score_str, 0.0))
        
#         return round(sum(scores) / len(scores), 3) if scores else 0.0


# # ============ Batch Generation with Quality Control ============

# def _append_to_jsonl(data: Dict, directory: str, filename: str):
#     """追加到JSONL文件"""
#     filepath = os.path.join(directory, filename)
#     with open(filepath, 'a', encoding='utf-8') as f:
#         f.write(json.dumps(data, ensure_ascii=False) + '\n')


# async def generate_batch(agent: ExpertQAAgent, save_path: str, 
#                         target_count: int = 100, 
#                         concurrency: int = 16,
#                         quality_filter: str = 'high',
#                         output_format: str = 'jsonl',
#                         max_attempts: int = None):
#     """
#     批量生成（带质量控制和数量控制）
    
#     Args:
#         agent: QA生成Agent
#         save_path: 输出目录
#         target_count: 目标生成数量（符合quality_filter的数量）
#         concurrency: 并发数
#         quality_filter: 质量过滤器
#             - 'high': 只保留high质量
#             - 'medium+': 保留high和medium质量
#             - 'all': 保留所有
#         output_format: 输出格式
#             - 'jsonl': 所有结果在一个.jsonl文件中（推荐）
#             - 'json': 每个结果单独.json文件
#             - 'both': 同时输出两种格式
#         max_attempts: 最多尝试生成次数，默认为target_count的3倍
    
#     Returns:
#         合格的结果列表
#     """
#     if max_attempts is None:
#         max_attempts = target_count * 3
    
#     semaphore = asyncio.Semaphore(concurrency)
#     qualified_results = []
#     all_results = []
#     attempt_count = 0
    
#     print(f"\n{'='*60}")
#     print(f"[BATCH] 批量生成任务")
#     print(f"  - 目标数量: {target_count} 个（{quality_filter}质量）")
#     print(f"  - 并发数: {concurrency}")
#     print(f"  - 最大尝试: {max_attempts}")
#     print(f"  - 输出格式: {output_format}")
#     print(f"  - 链接策略: 智能桥接（优先跨paper）")
#     print(f"{'='*60}\n")
    
#     async def generate_with_semaphore():
#         async with semaphore:
#             return await agent.generate_one(save_path)
    
#     # 进度条
#     pbar = tqdm.tqdm(total=target_count, desc=f"生成{quality_filter}质量QA")
    
#     while len(qualified_results) < target_count and attempt_count < max_attempts:
#         # 计算本轮需要生成的数量
#         remaining = target_count - len(qualified_results)
#         batch_size = min(concurrency, remaining * 2, max_attempts - attempt_count)
        
#         # 生成一批
#         tasks = [generate_with_semaphore() for _ in range(batch_size)]
#         batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         # 筛选合格结果
#         for result in batch_results:
#             attempt_count += 1
#             all_results.append(result)
            
#             if isinstance(result, dict) and result is not None:
#                 quality = result.get('overall_quality', 'low')
                
#                 # 根据quality_filter判断是否合格
#                 is_qualified = False
#                 if quality_filter == 'high' and quality == 'high':
#                     is_qualified = True
#                 elif quality_filter == 'medium+' and quality in ['high', 'medium']:
#                     is_qualified = True
#                 elif quality_filter == 'all':
#                     is_qualified = True
                
#                 if is_qualified:
#                     qualified_results.append(result)
#                     pbar.update(1)
                    
#                     # 实时保存（防止中断丢失数据）
#                     if output_format in ['jsonl', 'both']:
#                         _append_to_jsonl(result, save_path, 'qualified_results.jsonl')
                    
#                     if output_format in ['json', 'both']:
#                         json_file = os.path.join(save_path, f"{result['uid']}.json")
#                         with open(json_file, 'w', encoding='utf-8') as f:
#                             json.dump(result, f, ensure_ascii=False, indent=2)
        
#         # 打印进度
#         success_rate = len(qualified_results) / attempt_count if attempt_count > 0 else 0
#         print(f"\r[PROGRESS] 合格: {len(qualified_results)}/{target_count}, "
#               f"尝试: {attempt_count}/{max_attempts}, "
#               f"成功率: {success_rate*100:.1f}%", end='')
    
#     print()  # 换行
#     pbar.close()
    
#     # 保存所有结果（包括不合格的，用于分析）
#     print(f"\n{'='*60}")
#     print(f"[SAVE] 保存结果...")
    
#     all_jsonl = os.path.join(save_path, 'all_results.jsonl')
#     with open(all_jsonl, 'w', encoding='utf-8') as f:
#         for result in all_results:
#             if isinstance(result, dict):
#                 f.write(json.dumps(result, ensure_ascii=False) + '\n')
#     print(f"  - JSONL (全部): {all_jsonl}")
    
#     if output_format in ['jsonl', 'both']:
#         qualified_jsonl = os.path.join(save_path, 'qualified_results.jsonl')
#         print(f"  - JSONL (合格): {qualified_jsonl}")
    
#     if output_format in ['json', 'both']:
#         print(f"  - JSON (合格): {len(qualified_results)} 个文件")
    
#     # 统计
#     success = len([r for r in all_results if isinstance(r, dict)])
#     high_quality = len([r for r in qualified_results if r.get('overall_quality') == 'high'])
#     suitable_for_rl = len([r for r in qualified_results if r.get('suitable_for_rl')])
    
#     print(f"\n{'='*60}")
#     print(f"[BATCH] 完成！")
#     print(f"  - 目标数量: {target_count}")
#     print(f"  - 实际获得: {len(qualified_results)}")
#     print(f"  - 总尝试数: {attempt_count}")
#     print(f"  - 成功生成: {success}")
#     print(f"  - High质量: {high_quality}")
#     print(f"  - RL适用: {suitable_for_rl}")
#     print(f"  - 成功率: {len(qualified_results)/attempt_count*100:.1f}%")
#     print(f"{'='*60}\n")
    
#     return qualified_results


# # ============ Quality Report ============

# def generate_quality_report(results: List[Dict], output_path: str):
#     """生成质量报告"""
#     print(f"\n[REPORT] 生成质量报告...")
    
#     # 过滤有效结果
#     valid_results = [r for r in results if isinstance(r, dict) and 'quality_evaluation' in r]
    
#     if not valid_results:
#         print("[WARNING] 没有有效结果可供分析")
#         return
    
#     # 统计
#     total = len(valid_results)
#     quality_dist = defaultdict(int)
#     dimension_stats = defaultdict(lambda: defaultdict(int))
#     veto_reasons = defaultdict(int)
    
#     for r in valid_results:
#         # 总体质量分布
#         quality = r.get('overall_quality', 'unknown')
#         quality_dist[quality] += 1
        
#         # 各维度统计
#         eval_data = r.get('quality_evaluation', {})
#         if 'dimension_scores' in eval_data:
#             for dim, info in eval_data['dimension_scores'].items():
#                 score = info.get('score', 'unknown')
#                 dimension_stats[dim][score] += 1
        
#         # 一票否决原因
#         if eval_data.get('veto_triggered'):
#             for reason in eval_data.get('veto_reasons', []):
#                 veto_reasons[reason] += 1
    
#     # 生成报告
#     report = {
#         'metadata': {
#             'generation_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
#             'total_results': total
#         },
#         'summary': {
#             'total_count': total,
#             'quality_distribution': dict(quality_dist),
#             'high_quality_rate': quality_dist['high'] / total if total > 0 else 0,
#             'suitable_for_rl_rate': sum(1 for r in valid_results if r.get('suitable_for_rl')) / total if total > 0 else 0
#         },
#         'dimension_statistics': {
#             dim: dict(scores) for dim, scores in dimension_stats.items()
#         },
#         'veto_analysis': {
#             'total_veto_count': sum(veto_reasons.values()),
#             'veto_rate': sum(veto_reasons.values()) / total if total > 0 else 0,
#             'veto_reasons': dict(sorted(veto_reasons.items(), key=lambda x: x[1], reverse=True))
#         }
#     }
    
#     # 保存报告
#     with open(output_path, 'w', encoding='utf-8') as f:
#         json.dump(report, f, ensure_ascii=False, indent=2)
    
#     # 打印摘要
#     print(f"\n{'='*60}")
#     print(f"[REPORT] 质量报告摘要")
#     print(f"{'='*60}")
#     print(f"总计: {total} 个QA")
#     print(f"质量分布: {dict(quality_dist)}")
#     print(f"High质量率: {report['summary']['high_quality_rate']*100:.1f}%")
#     print(f"RL适用率: {report['summary']['suitable_for_rl_rate']*100:.1f}%")
    
#     if veto_reasons:
#         print(f"\n一票否决原因（前5）:")
#         for reason, count in list(veto_reasons.items())[:5]:
#             print(f"  - {reason}: {count}次")
    
#     print(f"\n报告已保存: {output_path}")
#     print(f"{'='*60}\n")


# # ============ Main ============

# async def main_async(args):
#     """异步主函数"""
#     import time as time_module
#     start_time = time_module.time()
    
#     # 1. 加载数据
#     print(f"\n{'='*60}")
#     print(f"[LOAD] 加载数据: {args.input}")
#     print(f"{'='*60}\n")
    
#     qa_data = []
#     with open(args.input, 'r', encoding='utf-8') as f:
#         for line in tqdm.tqdm(f, desc="Loading"):
#             qa_data.append(json.loads(line))
    
#     print(f"\n[LOAD] ✓ 加载了 {len(qa_data)} 条单跳QA数据\n")
    
#     # 2. 初始化
#     async with LLMClient(args.model_path, args.host, args.port) as llm:
#         kb = SemiconductorKB(qa_data, llm)
#         agent = ExpertQAAgent(
#             kb, llm, 
#             max_turns=args.max_turns,
#             max_refine=args.max_refine
#         )
        
#         # 3. 生成（带数量控制）
#         results = await generate_batch(
#             agent, 
#             args.output, 
#             target_count=args.target_count,
#             concurrency=args.batch_size,
#             quality_filter=args.quality_filter,
#             output_format=args.output_format,
#             max_attempts=args.max_attempts
#         )
        
#         # 4. 生成质量报告
#         if args.generate_report:
#             report_path = os.path.join(args.output, 'quality_report.json')
#             generate_quality_report(results, report_path)
    
#     # 统计时间
#     total_time = time_module.time() - start_time
#     print(f"\n[TIME] 总耗时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
#     if results:
#         print(f"[TIME] 平均每个QA: {total_time/len(results):.1f}秒")
#     print(f"\n[DONE] 所有任务完成！")


# def main():
#     import argparse
    
#     parser = argparse.ArgumentParser(
#         description="半导体领域多跳QA生成 - 融合专家8维度标准 + 智能桥接",
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog="""
# 示例用法:

# # 1. 生成1000个high质量的多跨paper多跳QA（推荐）
# python script.py \\
#     --input data/single_hop_qa.jsonl \\
#     --output results/ \\
#     --model_path Qwen2.5-14B-Instruct \\
#     --target_count 1000 \\
#     --quality_filter high \\
#     --output_format jsonl \\
#     --generate_report

# # 2. 快速测试（10个）
# python script.py \\
#     --input data/single_hop_qa.jsonl \\
#     --output test_results/ \\
#     --model_path Qwen2.5-14B-Instruct \\
#     --target_count 10 \\
#     --quality_filter all \\
#     --output_format both \\
#     --batch_size 4

# 智能链接说明:
#   - 自动从不同paper中选择单跳QA
#   - 基于"桥接实体"建立逻辑连接
#   - QA1的答案中的实体是QA2问题的核心概念
#   - 形成真正的跨领域推理链

# 输出文件说明:
#   - qualified_results.jsonl: 合格结果（按quality_filter筛选）
#   - all_results.jsonl: 所有结果（包括不合格的）
#   - {uid}.json: 单个QA文件（如果output_format=json/both）
#   - quality_report.json: 质量统计报告（如果--generate_report）
  
# 每个结果包含:
#   - bridge_info: 详细的桥接关系说明
#   - single_hops: 来源单跳QA（包含paper_name）
#   - linking_strategy: 使用的链接策略
#         """
#     )
    
#     # 输入输出
#     parser.add_argument('--input', type=str, required=True, 
#                        help='输入JSONL文件路径（单跳QA数据，必须包含paper_name字段）')
#     parser.add_argument('--output', type=str, required=True, 
#                        help='输出目录')
    
#     # LLM配置
#     parser.add_argument('--model_path', type=str, required=True,
#                        help='模型路径或名称')
#     parser.add_argument('--host', type=str, default='localhost',
#                        help='LLM服务器地址 (默认: localhost)')
#     parser.add_argument('--port', type=int, default=8000,
#                        help='LLM服务器端口 (默认: 8000)')
    
#     # ===== 数量控制（核心参数） =====
#     parser.add_argument('--target_count', type=int, default=100,
#                        help='目标生成数量（符合quality_filter的数量，默认: 100）')
#     parser.add_argument('--max_attempts', type=int, default=None,
#                        help='最大尝试次数（默认: target_count的3倍）')
#     parser.add_argument('--quality_filter', type=str, default='high',
#                        choices=['high', 'medium+', 'all'],
#                        help='质量过滤器 (默认: high)\n'
#                             '  high: 只保留high质量\n'
#                             '  medium+: 保留high和medium质量\n'
#                             '  all: 保留所有')
    
#     # ===== 输出格式（核心参数） =====
#     parser.add_argument('--output_format', type=str, default='jsonl',
#                        choices=['jsonl', 'json', 'both'],
#                        help='输出格式 (默认: jsonl)\n'
#                             '  jsonl: 所有结果在一个.jsonl文件中（推荐）\n'
#                             '  json: 每个结果单独.json文件\n'
#                             '  both: 同时输出两种格式')
    
#     # 生成参数
#     parser.add_argument('--batch_size', type=int, default=16,
#                        help='并发数 (默认: 16)')
#     parser.add_argument('--max_turns', type=int, default=8,
#                        help='最大优化轮数 (默认: 8)')
#     parser.add_argument('--max_refine', type=int, default=3,
#                        help='最大精炼次数 (默认: 3)')
    
#     # 其他
#     parser.add_argument('--generate_report', action='store_true',
#                        help='生成详细质量报告')
    
#     args = parser.parse_args()
    
#     # 创建输出目录
#     os.makedirs(args.output, exist_ok=True)
    
#     # 打印配置
#     print(f"\n{'='*60}")
#     print(f"半导体多跨paper多跳QA生成 - 专家8维度标准 + 智能桥接")
#     print(f"{'='*60}")
#     print(f"[CONFIG] 输入: {args.input}")
#     print(f"[CONFIG] 输出: {args.output}")
#     print(f"[CONFIG] 模型: {args.model_path}")
#     print(f"[CONFIG] 服务器: {args.host}:{args.port}")
#     print(f"")
#     print(f"[数量控制]")
#     print(f"  - 目标数量: {args.target_count} 个（{args.quality_filter}质量）")
#     print(f"  - 最大尝试: {args.max_attempts or args.target_count*3}")
#     print(f"  - 质量过滤: {args.quality_filter}")
#     print(f"")
#     print(f"[输出格式]")
#     print(f"  - 格式: {args.output_format}")
#     if args.output_format in ['jsonl', 'both']:
#         print(f"  - JSONL文件: qualified_results.jsonl (合格), all_results.jsonl (全部)")
#     if args.output_format in ['json', 'both']:
#         print(f"  - JSON文件: 每个QA一个文件")
#     print(f"")
#     print(f"[智能链接]")
#     print(f"  - 策略: 基于桥接实体的跨paper链接")
#     print(f"  - 原理: QA1答案中的实体 → QA2问题的核心概念")
#     print(f"  - 优先: 选择不同paper的QA（最大化多样性）")
#     print(f"")
#     print(f"[生成参数]")
#     print(f"  - 并发数: {args.batch_size}")
#     print(f"  - 最大优化轮数: {args.max_turns}")
#     print(f"  - 最大精炼次数: {args.max_refine}")
#     print(f"  - 质量报告: {'是' if args.generate_report else '否'}")
#     print(f"{'='*60}\n")
    
#     # 运行
#     asyncio.run(main_async(args))


# if __name__ == "__main__":
#     main()





class SemiconductorQAPrompts:
    """半导体领域QA构建Prompts（全面升级到专家质量标准）"""
    
    # ===== 1. 基础QA生成（升级版） =====
    base_qa = '''你是一个半导体领域的QA构建专家。基于给定的半导体知识材料，提出一个简单但需要专业知识才能回答的问题。

# 半导体知识材料
{content}

---

<think>
我需要从给定材料中提取核心技术信息：
1. 识别关键技术参数、工艺条件或物理机制
2. 确定可以提问的核心疑问点
3. 设计一个清晰、可解、答案唯一的问题
4. 确保问题具有专业深度但不过度复杂
</think>

## 【核心要求】

### 问题设计：
- ✓ 问题清晰、专业、可解
- ✓ 答案唯一且可从材料中提取
- ✓ 问题长度15-30词
- ✗ 禁止使用"本文"、"本研究"等自指表述
- ✗ 禁止引用特定文献或专有名词
- ✗ 禁止提出无法从材料回答的问题

### 答案要求：
- ✓ 答案准确、具体、完整
- ✓ 答案长度适中（10-50字）
- ✓ 基于材料内容，不添加外部信息
- ✗ 禁止模糊、笼统的答案
- ✗ 禁止仅引导句，必须有实质内容

### 陈述要求：
- ✓ 陈述应概括问答的核心技术事实
- ✓ 陈述长度20-40字
- ✓ 陈述应具有通用性

---

输出JSON格式：
```json
{{
    "question": "提出的问题（清晰、专业、可解）",
    "answer": "问题答案（准确、具体、完整）",
    "statement": "该问答对涉及的核心事实陈述（通用、凝练）",
    "key_concepts": ["关键概念1", "关键概念2"]
}}
```
'''

    # ===== 2. 关联QA构建（升级版） =====
    link_qa = '''你是一个半导体领域的QA构建专家。给定两个半导体概念的信息，构建一个关联问题。

# 概念A ({conceptA}) 的信息：
```txt
{contentA}
```

# 概念B ({conceptB}) 的信息：
```txt
{contentB}
```

---

<think>
我需要建立两个概念之间的逻辑联系：
1. 分析概念A的核心技术特征
2. 分析概念B的核心技术特征
3. 找到它们之间的因果、层次或比较关系
4. 设计一个问题，答案指向概念A，问题上下文涉及概念B
5. 构建连接两者的技术陈述
</think>

## 【核心要求】

### 问题设计：
- ✓ 答案必须是概念A的核心信息
- ✓ 问题上下文必须涉及概念B
- ✓ 问题需要专业的半导体知识才能回答
- ✓ 问题具有通用性，不局限于特定论文
- ✗ 禁止使用"本文"、"本研究"等自指表述
- ✗ 禁止简单拼接两个概念

### 答案要求：
- ✓ 答案必须准确反映概念A的信息
- ✓ 答案中需体现与概念B的关联
- ✓ 答案长度20-60字
- ✗ 禁止答案脱离给定信息

### 陈述要求：
- ✓ 陈述应明确两个概念的连接关系
- ✓ 陈述具有事实性、通用性
- ✓ 陈述长度20-50字

---

输出JSON格式：
```json
{{
    "question": "关联问题（答案指向概念A，上下文涉及概念B）",
    "answer": "问题答案（基于概念A，体现与概念B的关联）",
    "statement": "连接两个概念的核心技术事实",
    "key_concepts": ["涉及的关键概念1", "涉及的关键概念2"]
}}
```
'''

    # ===== 3. 多跳QA组合（专家模板） =====
    compose_qa_multihop = '''你是一个半导体领域的QA构建专家。基于给定的{num_hops}个单跳问答，生成一个高质量的多跳问题及答案。

# 单跳问答列表

{single_hop_qas}

# 桥接关系

{bridge_info}

---

<think>
首先，我需要理解这{num_hops}个单跳问答之间的逻辑关系。

让我分析：
1. 识别每个问答的核心技术点
2. 理解桥接关系如何连接它们
3. 确定组合后的推理逻辑链

接下来，我将基于以下原则设计多跳问题：
- 问题必须展现完整的推理链条
- 问题需要逻辑推理才能解答，体现{num_hops}步依赖关系
- 问题描述要清晰、完整、专业、具有通用性
- 避免使用"基于上述"、"根据前面"等依赖性表述
- 确保问题具有技术深度，不是简单拼接
- 问题必须是单一问题，不包含多个疑问点
</think>

## 【核心要求】（严格执行）

### 1. 问题设计准则：

**(1) 因果链完整性**
- 问题需呈现完整技术逻辑链：机制A → 参数B → 现象C
- 体现{num_hops}步推理的必要性

**(2) 通用性（严格执行）**
- 问题必须具有通用性，不局限于特定论文
- 禁止使用"本文"、"本研究"、"本实验"等自指表述
- 禁止引用文献或文章自定义的专有名词
- 确保不读论文也能理解问题含义

**(3) 单一性（严格执行）**
- 问题只包含一个核心疑问点
- 禁止连接多个子问题
- 禁止在一个句子中包含多个疑问点

错误示例：
"在氧化物薄膜晶体管中，如何通过调控氧分压实现高迁移率？并分析其对器件稳定性的影响？"（包含2个问题）

正确示例：
"在氧化物薄膜晶体管制备中，氧分压参数如何通过影响氧空位浓度进而调控载流子迁移率和器件长期稳定性？"（单一问题，完整推理链）

**(4) 可追溯性**
- 问题基于给定的单跳问答生成
- 答案能够基于给定的单跳答案推导得出

**(5) 简洁凝练**
- 问题长度控制在20-40词
- 避免冗余描述

### 2. 答案生成准则：

**(1) 完整性（严格执行）**
- 必须完整回答问题的所有方面
- 必须体现{num_hops}步推理过程
- 禁止仅引导句，必须提供实质性内容
- 禁止只回答某一个子问题

**(2) 准确性（严格执行）**
- 答案必须准确无误
- 必须基于给定的单跳答案逻辑推导
- 不得脱离原始信息

**(3) 通用性（严格执行）**
- 答案具有通用性，不特指论文
- 禁止使用"本文"、"本研究"等表述
- 禁止引用文献或文章自定义的专有名词
- 确保不读论文也能理解答案含义

**(4) 逻辑连贯性**
- 答案需体现清晰的推理过程
- 每一步推理都要明确
- 展现步骤之间的因果关系

**(5) 答案策略**
- 体现完整因果链，最终答案应是推理的结论
- 综合各步信息，形成完整认知
- 答案长度适中（50-150字）

### 3. 推理步骤要求：

- 必须包含{num_hops}个清晰的推理步骤
- 每个步骤对应一个单跳问答的核心内容
- 步骤之间要有明确的逻辑连接词
- 每个步骤长度至少15个字

## 【禁止事项】

× 禁止使用"本文/本研究/本实验"等论文自指表述
× 禁止问题中出现"基于上述"、"根据前面"等依赖性表述
× 禁止提问孤立概念
× 禁止复合问题（严格执行）
× 禁止问题或答案中引用文献或文章自定义专有名词
× 禁止特指论文内容
× 禁止答案不完整（仅引导句）
× 禁止答案只回答部分问题

---

输出JSON格式：
```json
{{
    "question": "组合后的{num_hops}跳问题（单一问题，体现完整推理链）",
    "answer": "最终答案（完整、准确、通用，体现{num_hops}步推理）",
    "reasoning_steps": [
        "第一步：[基于单跳QA-1的核心内容，至少15字]",
        "第二步：[基于单跳QA-2的核心内容，承接第一步，至少15字]"
    ],
    "quality_indicators": {{
        "has_complete_reasoning_chain": true,
        "is_single_question": true,
        "is_universal": true,
        "answer_completeness": "complete"
    }}
}}
```
'''

    # ✅ 保留原版compose_qa（向后兼容，但也升级）
    compose_qa = '''你是一个半导体领域的QA构建专家。将两个问题组合成一个更复杂的问题。

第一个问题：
```
{questionA}
```

第二个问题：
```
{questionB}
```

相关的技术陈述：
```
{statements}
```

---

<think>
我需要：
1. 理解两个问题之间的逻辑关系
2. 识别第二个问题的答案如何关联到第一个问题
3. 设计组合策略：隐藏第二个问题的答案，作为推理条件
4. 保持第一个问题的答案不变
5. 确保组合后的问题自然、连贯
</think>

## 【核心要求】

### 组合策略：
- ✓ 第二个问题的答案关联到第一个问题中的某个实体
- ✓ 组合后应移除第二个问题答案的直接信息
- ✓ 保持第一个问题的答案不变
- ✓ 组合后的问题应自然、连贯、专业
- ✗ 禁止简单拼接
- ✗ 禁止使用"基于"、"根据"等依赖性表述

### 质量标准：
- ✓ 组合后是单一问题，不包含多个疑问点
- ✓ 问题具有通用性，不特指论文
- ✓ 答案准确，基于给定信息
- ✗ 禁止答案改变
- ✗ 禁止引入外部信息

---

输出JSON格式：
```json
{{
    "question": "组合后的问题（单一、自然、更复杂）",
    "answer": "答案（与第一个问题相同）",
    "note": "如何组合的简要说明（20字内）"
}}
```
'''

    # ===== 4. Action选择（升级版） =====
    action = '''你是一个半导体领域的QA构建专家。基于当前问答对和相关信息，选择一个操作来提升问题难度。

# 当前问答对
{question}

# 可选操作
{actions}

---

<think>
我需要分析当前问答对的状态：
1. 问题的复杂度如何？
2. 是否有可以融入的相关概念？
3. 是否有信息过于直接？
4. 是否已经足够难，可以退出？

基于分析，我将选择最合适的操作。
</think>

## 【选择原则】

- **SELECT**: 当有相关概念可以融入，增加推理深度时
- **FUZZ**: 当某些信息过于直接指向答案时
- **EXIT**: 当问题已经足够复杂，需要专业知识才能回答时
- **BRAINSTORM**: 当需要引入新的技术概念时

## 【质量标准】

- ✓ 选择的操作应提升问题质量
- ✓ 理由应清晰、具体
- ✗ 禁止无意义的操作
- ✗ 禁止降低问题质量

---

输出JSON格式（根据选择的操作）：
见下方各操作的详细格式
'''

    SELECT = '''SELECT: 从相关概念列表中选择一个概念，融入问题以增加推理深度。

<think>
我需要：
1. 分析当前问题的核心疑问
2. 识别哪个相关概念能增加推理链
3. 确保选择的概念与当前问题有逻辑连接
4. 预期融入后的问题会更具挑战性
</think>

## 【选择标准】

- ✓ 概念与当前问题有明确的因果或层次关系
- ✓ 融入后能形成更长的推理链
- ✓ 概念具有专业性，需要领域知识
- ✗ 禁止选择无关概念
- ✗ 禁止选择过于简单的概念

---

输出JSON格式：
```json
{{
    "action": "SELECT",
    "target": "选中概念的ID（必须来自相关概念列表）",
    "note": "选择该概念的理由（说明如何增加推理深度，20-40字）"
}}
```
'''

    FUZZ = '''FUZZ: 模糊化问题中的1处信息，使问题更具挑战性，需要更多推理。

<think>
我需要：
1. 识别问题中过于直接指向答案的信息
2. 选择一个可以模糊化的关键信息
3. 设计模糊化策略（替换为更通用的描述、隐藏具体参数等）
4. 确保模糊化后问题仍然清晰且答案唯一
</think>

## 【模糊化标准】

- ✓ 选择过于直接的信息进行模糊化
- ✓ 模糊化后问题仍然清晰、可解
- ✓ 答案保持唯一
- ✓ 模糊化增加推理需求，而非增加歧义
- ✗ 禁止模糊化导致答案不唯一
- ✗ 禁止过度模糊导致无法回答

---

输出JSON格式：
```json
{{
    "action": "FUZZ",
    "question": "模糊化后的问题（清晰、可解、更具挑战）",
    "note": "为何以及如何进行模糊化（20-40字）"
}}
```
'''

    EXIT = '''EXIT: 当问题满足退出条件时选择退出。

<think>
我需要检查：
1. 问题是否需要深入的半导体专业知识？
2. 信息是否足够模糊，没有单一信息直接指向答案？
3. 问题是否已经足够复杂？
4. 继续迭代是否还能显著提升质量？

如果以上全部满足，应该退出。
</think>

## 【退出标准】（必须全部满足）

- ✓ 问题需要深入的半导体专业知识才能回答
- ✓ 问题具有多步推理链
- ✓ 没有单一信息能直接指向答案
- ✓ 问题清晰、专业、可解
- ✓ 答案唯一且准确

---

输出JSON格式：
```json
{{
    "action": "EXIT",
    "note": "为何选择退出（说明问题已满足质量标准，20-40字）"
}}
```
'''

    BRAINSTORM = '''BRAINSTORM: 头脑风暴与当前问答对相关的半导体概念，用于后续融入问题。

<think>
我需要：
1. 分析当前问答对涉及的技术领域
2. 思考相关的材料、工艺、器件、物理效应等概念
3. 确保概念的事实准确性
4. 构建概念与当前问答的连接陈述
</think>

## 【头脑风暴标准】

- ✓ 概念与当前问答有明确的技术关联
- ✓ 概念具有专业性和准确性
- ✓ 连接陈述应具有事实性
- ✓ 概念能增加问题的技术深度
- ✗ 禁止无关概念
- ✗ 禁止虚构技术事实

---

输出JSON格式：
```json
{{
    "action": "BRAINSTORM",
    "entities": [
        {{
            "name": "概念名称（准确、专业）",
            "concept_id": "概念在知识库中的ID（如果有，否则为null）",
            "statement": "连接该概念与当前问答的事实陈述（20-50字）"
        }}
    ]
}}
```
'''

    # ===== 5. 其他辅助Prompts（升级版） =====
    
    extract_key_concepts = '''从以下半导体知识内容中提取关键技术概念。

内容：
```txt
{content}
```

---

<think>
我需要识别：
1. 材料相关概念（如IGZO、LTPS、a-Si等）
2. 工艺相关概念（如溅射、退火、刻蚀等）
3. 器件相关概念（如TFT、OLED、LCD等）
4. 参数相关概念（如迁移率、阈值电压等）
5. 物理效应/机制（如氧空位、载流子等）
</think>

## 【提取标准】

- ✓ 概念应具有专业性和明确性
- ✓ 概念应在内容中有明确提及
- ✓ 概念分类应准确
- ✗ 禁止提取通用词汇
- ✗ 禁止提取不相关概念

---

输出JSON格式：
```json
[
    {{"concept": "概念名", "type": "材料/工艺/器件/效应/参数"}},
    {{"concept": "概念名", "type": "材料/工艺/器件/效应/参数"}}
]
```
'''

    summarize_qa = '''总结以下半导体问答对的核心技术要点。

问答对：
```txt
问题: {question}
答案: {answer}
```

---

<think>
我需要：
1. 提取问答的核心技术主题
2. 识别关键的技术参数或结论
3. 归纳2-3个关键点
4. 用凝练的语言表达
</think>

## 【总结标准】

- ✓ 摘要应准确反映核心技术内容（20-40字）
- ✓ 关键点应具体、明确（每点10-20字）
- ✓ 关键点数量2-4个
- ✗ 禁止遗漏核心信息
- ✗ 禁止添加不相关内容

---

输出格式：
<summary>核心技术摘要</summary>
<key_points>
- 关键点1
- 关键点2
- 关键点3
</key_points>
'''

    check_info_cover = '''检查新陈述的信息是否已被先前陈述完全覆盖。

先前的技术陈述：
```txt
{prior}
```

待检查的陈述：
```txt
{current}
```

---

<think>
我需要：
1. 提取待检查陈述的核心信息点
2. 逐一对比先前陈述是否已包含
3. 判断是否有新信息
4. 给出明确结论
</think>

## 【判断标准】

- **yes**: 当前陈述的所有核心信息点都已被先前陈述覆盖
- **no**: 当前陈述包含至少一个先前陈述未覆盖的信息点

## 【分析要求】

- ✓ 分析应具体、明确
- ✓ 逐点对比
- ✗ 禁止模糊判断

---

输出格式：

# 分析
// 逐点对比分析（50-100字）

# 最终判断
```json
{{
    "judgement": "yes 或 no",
    "reason": "判断理由（20-40字）"
}}
```
'''

    check_alternative_ans = '''判断预测答案是否也是该半导体问题的正确答案。

问题: {question}

标准答案: {gt_answer}

支撑标准答案的技术事实：
```txt
{statements}
```

预测答案: {pred_answer}

---

<think>
我需要：
1. 理解问题的所有约束条件
2. 分析标准答案满足哪些条件
3. 检查预测答案是否也满足这些条件
4. 判断预测答案是否也正确
</think>

## 【判断标准】

- **yes**: 预测答案满足问题的所有约束，也是正确答案
- **no**: 预测答案不满足问题的某些约束，不是正确答案

## 【分析要求】

- ✓ 分析应基于问题约束和技术事实
- ✓ 逐条检查约束满足情况
- ✗ 禁止主观判断

---

输出格式：

# 分析
// 约束满足情况分析（50-100字）

# 最终判断
```json
{{
    "judgement": "yes 或 no",
    "reason": "判断理由（20-40字）"
}}
```
'''

    qa_valid_check = '''检查该半导体问答对的有效性。

问答对和相关信息：
{question}

---

<think>
我需要检查：
1. 问题是否是简单拼接？
2. 答案是否唯一正确？
3. 问题是否有唯一答案？
4. 是否可以基于相关陈述解答？
</think>

## 【有效性标准】（必须全部满足）

1. ✓ 问题不是简单拼接多个问题
2. ✓ 提供的答案是唯一正确答案
3. ✓ 问题有唯一答案（不存在多个正确答案）
4. ✓ 基于相关技术陈述可以解答

## 【无效情况】（任一满足即无效）

- × 问题包含多个疑问点
- × 答案不正确或不唯一
- × 问题有多个正确答案
- × 陈述不足以支撑答案

---

输出格式：

# 分析
// 逐条检查有效性（80-150字）

# 最终判断
```json
{{
    "judgement": "yes 或 no",
    "invalid_reasons": ["无效原因1", "无效原因2"],
    "confidence": "high/medium/low"
}}
```
'''

    direct_gen_check = """回答以下半导体技术问题，将答案放在<answer></answer>标签内。

问题：
{question}

---

要求：
- 答案应准确、具体、完整
- 答案长度适中（20-100字）
- 如果不确定，说明不确定的原因
- 不要添加无关信息

<answer>你的答案</answer>
"""
    
    llm_judge = """你是一个评估助手。判断预测答案是否等价于标准答案。

问题: {question}

标准答案: {gt_answer}

预测答案: {pred_answer}

---

判断标准：
- 如果预测答案的核心含义与标准答案一致，即使表述不同也视为等价
- 如果预测答案包含标准答案的所有关键信息，视为等价
- 如果预测答案有明显错误或缺失关键信息，视为不等价

如果等价回答"Correct"，否则回答"Incorrect"。不要包含其他文字。
"""

    # 🆕 新增：答案完整性验证（专家标准）
    verify_answer_completeness = '''验证以下多跳问答的答案是否完整回答了问题。

问题：
{question}

答案：
{answer}

推理步骤：
{reasoning_steps}

---

<think>
我需要检查：
1. 答案是否回答了问题的所有方面？
2. 推理步骤是否完整（{num_hops}步）？
3. 答案是否基于单跳答案逻辑推导？
4. 答案长度是否适中（50-150字）？
5. 答案是否具有通用性？
</think>

## 【验证标准】

### 1. 答案完整性：
- ✓ 回答问题的所有方面
- ✓ 没有遗漏关键信息
- ✗ 仅引导句，无实质内容

### 2. 推理链完整性：
- ✓ 包含{num_hops}个清晰步骤
- ✓ 每步至少15字
- ✓ 步骤之间有逻辑连接

### 3. 准确性：
- ✓ 基于单跳答案推导
- ✓ 不脱离原始信息
- ✗ 添加外部信息

### 4. 通用性：
- ✓ 不特指论文
- ✗ 使用"本文"等自指

### 5. 答案长度：
- ✓ 50-150字为最佳
- ⚠️ <50字可能不完整
- ⚠️ >150字可能冗余

---

输出JSON格式：
```json
{{
    "is_complete": true/false,
    "missing_aspects": ["缺失的方面1", "缺失的方面2"],
    "reasoning_chain_complete": true/false,
    "reasoning_chain_issues": ["问题1", "问题2"],
    "answer_length_appropriate": true/false,
    "answer_length": {{字数}},
    "is_based_on_single_hops": true/false,
    "is_universal": true/false,
    "overall_score": 0-10,
    "detailed_feedback": "详细反馈（50-100字）"
}}
```
'''

    # 🆕 新增：多跳QA质量综合评估（8维度标准）
    evaluate_multihop_quality = '''你是半导体领域的QA质量评估专家。基于8个核心维度评估以下多跳问答的质量。

# 待评估的多跳问答

**问题：**
{question}

**答案：**
{answer}

**推理步骤：**
{reasoning_steps}

**单跳问答依据：**
{single_hop_qas}

---

<think>
我需要从以下8个维度全面评估这个多跳问答：
1. 问题通用性 - 是否具有通用性，不局限于特定论文
2. 回答相关性 - 答案是否精准聚焦问题核心
3. 逻辑一致性 - 推理过程是否清晰、连贯、无矛盾
4. 术语使用 - 专业术语是否准确、恰当、完整
5. 事实正确性 - 技术细节是否符合行业共识
6. 答案通用性 - 答案是否具有通用性，不特指论文
7. 答案准确完整性 - 答案是否准确且完整回答问题
8. 答案可靠性 - 答案是否基于单跳答案推导

每个维度我需要给出：high/medium/low评分，并指出具体问题。
</think>

## 【8维度评估标准】（一票否决机制）

### 1. 问题通用性 (Question Universality)
**检查点：**
- [ ] 问题是否依据子问题答案生成？
- [ ] 问题是否具有实际意义和通用性？
- [ ] 问题是否只是简单的子问题组合？（禁止）
- [ ] 问题中是否引用文献或文章自定义的专有名词？（禁止）
- [ ] 是否是多跳问题？（必须是）
- [ ] 是否使用"本文"、"本研究"等自指表述？（禁止）

**评分规则：**
- **low**: 使用自指、引用专有名词、非多跳、简单拼接
- **medium**: 部分通用，但有改进空间
- **high**: 完全通用，具有实际意义，是真正的多跳问题

**一票否决**: 使用自指、引用专有名词、非多跳 → `low`

---

### 2. 回答相关性 (Relevance)
**检查点：**
- [ ] 回答是否精准聚焦问题核心？
- [ ] 是否存在答非所问、偏离主题或遗漏关键点？
- [ ] 答案是否只是仅引导句未提供实质性内容？（禁止）
- [ ] 答案是否和问题的主要逻辑相关？

**评分规则：**
- **low**: 答非所问、仅引导句、完全偏离
- **medium**: 部分相关，但遗漏关键点
- **high**: 精准聚焦，完全相关

**一票否决**: 仅引导句、完全偏离 → `low`

---

### 3. 逻辑一致性 (Logical Consistency)
**检查点：**
- [ ] 回答的推理过程是否清晰、连贯、无矛盾？
- [ ] 是否存在逻辑跳跃、断裂或自相矛盾？
- [ ] 是否存在答案中断？
- [ ] 答案是否只是泛泛而谈？

**评分规则：**
- **low**: 逻辑混乱、自相矛盾、不相关
- **medium**: 基本连贯，但有小跳跃
- **high**: 清晰连贯，逻辑严密

**一票否决**: 逻辑混乱、不相关 → `low`

---

### 4. 术语使用 (Terminology Usage)
**检查点：**
- [ ] 专业术语的使用是否准确、恰当、完整？
- [ ] 是否存在术语误用、滥用、缺失或概念性错误？
- [ ] 术语描述是否完整（不能缩写）？

**评分规则：**
- **low**: 关键术语严重错误、大量误用
- **medium**: 术语基本正确，但不够完整
- **high**: 术语准确、恰当、完整

**一票否决**: 关键术语严重错误 → `low`

---

### 5. 事实正确性 (Factual Correctness)
**检查点：**
- [ ] 技术细节、参数、原理是否符合行业共识？
- [ ] 是否存在事实性错误或过时信息？

**评分规则：**
- **low**: 明显事实错误
- **medium**: 事实基本正确，但有细节问题
- **high**: 事实完全正确

**一票否决**: 明显事实错误 → `low`

---

### 6. 答案通用性 (Answer Universality)
**检查点：**
- [ ] 答案是否特指论文？（禁止）
- [ ] 答案是否具有通用性？
- [ ] 答案中是否引用文献或文章自定义的专有名词？（禁止）
- [ ] 答案是否使用"本文"、"本研究"等自指表述？（禁止）

**评分规则：**
- **low**: 自指、专有名词、特指论文
- **medium**: 部分通用，但有改进空间
- **high**: 完全通用

**一票否决**: 自指、专有名词、特指论文 → `low`

---

### 7. 答案准确完整性 (Answer Completeness)
**检查点：**
- [ ] 答案是否准确回答了问题？（严格执行）
- [ ] 答案是否完整回答了问题（回答了各个子问题）？（严格执行）
- [ ] 答案是否简洁凝练，无冗余？
- [ ] 答案是否只回答了部分问题？（禁止）
- [ ] 答案中是否有错误？

**评分规则：**
- **low**: 不准确、不完整、有错误
- **medium**: 基本准确完整，但有小遗漏
- **high**: 准确完整，简洁凝练

**一票否决**: 不准确、不完整、有错误 → `low`

---

### 8. 答案可靠性 (Answer Reliability)
**检查点：**
- [ ] 答案是否依据子问题的答案回答的？（严格执行）
- [ ] 答案是否可以从子问题答案中逻辑推导得出？
- [ ] 答案是否脱离了原始信息？（禁止）

**评分规则：**
- **low**: 不基于单跳答案、脱离原始信息
- **medium**: 基本基于单跳，但有添加
- **high**: 完全基于单跳答案推导

**一票否决**: 不基于单跳答案、脱离原始信息 → `low`

---

## 【输出格式】

```json
{{
    "dimension_scores": {{
        "question_universality": {{
            "score": "high/medium/low",
            "issues": ["问题1", "问题2"],
            "veto": false,
            "feedback": "具体反馈（20-40字）"
        }},
        "relevance": {{
            "score": "high/medium/low",
            "issues": [],
            "veto": false,
            "feedback": "具体反馈"
        }},
        "logical_consistency": {{
            "score": "high/medium/low",
            "issues": [],
            "veto": false,
            "feedback": "具体反馈"
        }},
        "terminology_usage": {{
            "score": "high/medium/low",
            "issues": [],
            "veto": false,
            "feedback": "具体反馈"
        }},
        "factual_correctness": {{
            "score": "high/medium/low",
            "issues": [],
            "veto": false,
            "feedback": "具体反馈"
        }},
        "answer_universality": {{
            "score": "high/medium/low",
            "issues": [],
            "veto": false,
            "feedback": "具体反馈"
        }},
        "answer_completeness": {{
            "score": "high/medium/low",
            "issues": [],
            "veto": false,
            "feedback": "具体反馈"
        }},
        "answer_reliability": {{
            "score": "high/medium/low",
            "issues": [],
            "veto": false,
            "feedback": "具体反馈"
        }}
    }},
    "overall_quality": "high/medium/low",
    "veto_triggered": false,
    "veto_reasons": [],
    "specific_issues": {{
        "question_issues": ["问题问题1", "问题问题2"],
        "answer_issues": ["答案问题1", "答案问题2"]
    }},
    "improvement_suggestions": [
        "改进建议1",
        "改进建议2"
    ],
    "suitable_for_rl": true,
    "quality_score": 0-10
}}
```
'''

    # 🆕 新增：多跳QA精炼优化
    refine_multihop_qa = '''你是半导体领域的QA优化专家。基于质量评估结果，精炼优化以下多跳问答。

# 当前多跳问答

**问题：** {question}
**答案：** {answer}

# 质量评估结果

{quality_issues}

---

<think>
我需要：
1. 识别所有质量问题
2. 按优先级排序（一票否决问题优先）
3. 逐一修复问题
4. 确保修复后不引入新问题
5. 保持答案的准确性和可追溯性
</think>

## 【优化目标】（优先级排序）

### 1. 消除一票否决问题（最高优先级）
- 移除"本文"、"本研究"等自指表述
- 移除文献专有名词，替换为通用术语
- 确保答案完整回答问题
- 确保答案基于单跳答案推导

### 2. 提升通用性
- 将特指论文的内容改为通用表述
- 确保不读论文也能理解

### 3. 优化逻辑连贯性
- 确保推理链清晰
- 消除逻辑跳跃
- 增加逻辑连接词

### 4. 完善答案内容
- 补充缺失的推理步骤
- 确保回答问题的所有方面
- 移除冗余信息

### 5. 优化术语使用
- 修正术语错误
- 补充术语描述
- 确保术语完整性

---

## 【优化原则】

- ✓ 保持答案的核心含义和准确性
- ✓ 基于单跳答案推导，不添加外部信息
- ✓ 优化后的问题和答案应更清晰、更专业
- ✗ 禁止改变答案的核心含义
- ✗ 禁止添加无法从单跳答案推导的信息

---

输出JSON格式：
```json
{{
    "refined_question": "优化后的问题（清晰、通用、专业）",
    "refined_answer": "优化后的答案（完整、准确、通用）",
    "refined_reasoning_steps": [
        "优化后的推理步骤1",
        "优化后的推理步骤2"
    ],
    "changes_made": [
        "改进1：具体说明修改了什么",
        "改进2：具体说明修改了什么"
    ],
    "remaining_issues": [
        "仍存在的问题1（如果有）",
        "仍存在的问题2（如果有）"
    ],
    "expected_quality": "high/medium",
    "improvement_confidence": "high/medium/low"
}}
```
'''

    # 🆕 新增：最终质量验证（25项检查清单）
    final_quality_validation = '''对以下多跳问答进行最终质量验证（25项检查清单）。

**问题：** {question}
**答案：** {answer}
**推理步骤：** {reasoning_steps}

---

<think>
我需要逐项检查25个质量标准：
- 问题检查（10项）
- 答案检查（10项）
- 推理链检查（5项）

只有全部通过才能批准。
</think>

## 【检查清单】（全部通过才能批准）

### 问题检查（10项）

1. [ ] ✓ 问题具有通用性，不特指论文
2. [ ] ✓ 问题无"本文"、"本研究"等自指表述
3. [ ] ✓ 问题无文献或文章自定义专有名词
4. [ ] ✓ 问题是多跳问题（有推理链）
5. [ ] ✓ 问题是单一问题（不包含多个疑问点）
6. [ ] ✓ 问题清晰、专业、可解
7. [ ] ✓ 问题长度适中（20-40词）
8. [ ] ✓ 问题基于单跳问答生成
9. [ ] ✓ 不读论文也能理解问题
10. [ ] ✓ 问题具有实际意义

### 答案检查（10项）

1. [ ] ✓ 答案完整回答了问题（所有方面）
2. [ ] ✓ 答案准确无误
3. [ ] ✓ 答案基于单跳答案逻辑推导
4. [ ] ✓ 答案具有通用性，不特指论文
5. [ ] ✓ 答案无"本文"、"本研究"等自指表述
6. [ ] ✓ 答案无文献或文章自定义专有名词
7. [ ] ✓ 答案提供实质性内容（非仅引导句）
8. [ ] ✓ 答案逻辑清晰、连贯
9. [ ] ✓ 答案术语准确、完整
10. [ ] ✓ 不读论文也能理解答案

### 推理链检查（5项）

1. [ ] ✓ 推理步骤数量正确（{num_hops}步）
2. [ ] ✓ 每步推理清晰明确
3. [ ] ✓ 步骤之间有逻辑连接
4. [ ] ✓ 推理链完整、无跳跃
5. [ ] ✓ 每步至少15字

---

## 【验证结果】

输出JSON格式：
```json
{{
    "is_approved": true/false,
    "checks_passed": 0-25,
    "checks_failed": 0-25,
    "failed_items": [
        "未通过的检查项1",
        "未通过的检查项2"
    ],
    "overall_quality": "high/medium/low",
    "suitable_for_rl": true/false,
    "confidence": "high/medium/low",
    "final_feedback": "综合反馈（50-100字）"
}}
```
'''


# ============ LLM Client (完全保留原版) ============
# （代码保持不变）"""
完全兼容增强版 - 半导体领域复杂QA生成Agent
原版所有功能 + 三大核心优化（消耗追踪、动态规划、兜底机制）
"""

import re
import time
import random
import uuid
import json
import copy
import asyncio
import aiohttp
import requests
import numpy as np
from collections import defaultdict
from transformers import AutoTokenizer
from typing import Dict, List, Any, Optional, Tuple
import tqdm
import os


# ============ Prompts (完全保留原版) ============

class SemiconductorQAPrompts:
    """半导体领域QA构建Prompts（完整保留 + 高质量多跳生成）"""
    
    base_qa = '''你是一个半导体领域的QA构建专家。基于给定的半导体知识材料，提出一个简单但需要专业知识才能回答的问题。确保问题清晰、可解、答案唯一。

# 半导体知识材料
{content}

输出JSON格式：
```json
{{
    "question": "提出的问题",
    "answer": "问题答案",
    "statement": "该问答对涉及的核心事实陈述",
    "key_concepts": ["关键概念1", "关键概念2"]
}}
```
'''

    link_qa = '''你是一个半导体领域的QA构建专家。给定两个半导体概念的信息，构建一个问题，其中答案是{conceptA}，问题上下文涉及{conceptB}。确保问题需要专业的半导体知识。

# 概念A ({conceptA}) 的信息：
```txt
{contentA}
```

# 概念B ({conceptB}) 的信息：
```txt
{contentB}
```

输出JSON格式：
```json
{{
    "question": "提出的问题",
    "answer": "问题答案",
    "statement": "连接两个概念的核心事实",
    "key_concepts": ["涉及的关键概念"]
}}
```
'''

    # 🆕 改进版：高质量多跳QA生成
    compose_qa_multihop = '''你是一个半导体领域的QA构建专家。基于给定的{num_hops}个单跳问答，生成一个高质量的多跳问题及答案。

# 单跳问答列表

{single_hop_qas}

# 桥接关系

{bridge_info}

---

<think>
首先，我需要理解这{num_hops}个单跳问答之间的逻辑关系。

让我分析：
1. 识别每个问答的核心技术点
2. 理解桥接关系如何连接它们
3. 确定组合后的推理逻辑链

接下来，我将基于以下原则设计多跳问题：
- 问题必须展现完整的推理链条
- 问题需要逻辑推理才能解答，体现{num_hops}步依赖关系
- 问题描述要清晰、完整、专业、具有通用性
- 避免使用"基于上述"、"根据前面"等依赖性表述
- 确保问题具有技术深度，不是简单拼接
- 问题必须是单一问题，不包含多个疑问点
</think>

## 【核心要求】（严格执行）

### 1. 问题设计准则：

**(1) 因果链完整性**
- 问题需呈现完整技术逻辑链：机制A → 参数B → 现象C
- 体现{num_hops}步推理的必要性

**(2) 通用性（严格执行）**
- 问题必须具有通用性，不局限于特定论文
- 禁止使用"本文"、"本研究"、"本实验"等自指表述
- 禁止引用文献或文章自定义的专有名词
- 确保不读论文也能理解问题含义

**(3) 单一性（严格执行）**
- 问题只包含一个核心疑问点
- 禁止连接多个子问题
- 禁止在一个句子中包含多个疑问点

错误示例：
"在氧化物薄膜晶体管中，如何通过调控氧分压实现高迁移率？并分析其对器件稳定性的影响？"（包含2个问题）

正确示例：
"在氧化物薄膜晶体管制备中，氧分压参数如何通过影响氧空位浓度进而调控载流子迁移率和器件长期稳定性？"（单一问题，完整推理链）

**(4) 可追溯性**
- 问题基于给定的单跳问答生成
- 答案能够基于给定的单跳答案推导得出

**(5) 简洁凝练**
- 问题长度控制在20-40词
- 避免冗余描述

### 2. 答案生成准则：

**(1) 完整性（严格执行）**
- 必须完整回答问题的所有方面
- 必须体现{num_hops}步推理过程
- 禁止仅引导句，必须提供实质性内容
- 禁止只回答某一个子问题

**(2) 准确性（严格执行）**
- 答案必须准确无误
- 必须基于给定的单跳答案逻辑推导
- 不得脱离原始信息

**(3) 通用性（严格执行）**
- 答案具有通用性，不特指论文
- 禁止使用"本文"、"本研究"等表述
- 禁止引用文献或文章自定义的专有名词
- 确保不读论文也能理解答案含义

**(4) 逻辑连贯性**
- 答案需体现清晰的推理过程
- 每一步推理都要明确
- 展现步骤之间的因果关系

**(5) 答案策略**
- 体现完整因果链，最终答案应是推理的结论
- 综合各步信息，形成完整认知
- 答案长度适中（50-150字）

### 3. 推理步骤要求：

- 必须包含{num_hops}个清晰的推理步骤
- 每个步骤对应一个单跳问答的核心内容
- 步骤之间要有明确的逻辑连接词
- 每个步骤长度至少15个字

## 【禁止事项】

× 禁止使用"本文/本研究/本实验"等论文自指表述
× 禁止问题中出现"基于上述"、"根据前面"等依赖性表述
× 禁止提问孤立概念
× 禁止复合问题（严格执行）
× 禁止问题或答案中引用文献或文章自定义专有名词
× 禁止特指论文内容
× 禁止答案不完整（仅引导句）
× 禁止答案只回答部分问题

---

输出JSON格式：
```json
{{
    "question": "组合后的{num_hops}跳问题（单一问题，体现完整推理链）",
    "answer": "最终答案（完整、准确、通用，体现{num_hops}步推理）",
    "reasoning_steps": [
        "第一步：[基于单跳QA-1的核心内容，至少15字]",
        "第二步：[基于单跳QA-2的核心内容，承接第一步，至少15字]"
    ],
    "quality_indicators": {{
        "has_complete_reasoning_chain": true,
        "is_single_question": true,
        "is_universal": true,
        "answer_completeness": "complete"
    }}
}}
```
'''

    # ✅ 保留原版compose_qa（向后兼容）
    compose_qa = '''你是一个半导体领域的QA构建专家。将两个问题组合成一个更复杂的问题。第二个问题的答案关联到第一个问题中的某个实体。组合后的问题应移除第二个问题答案的直接信息，但保持第一个问题的答案不变。

第一个问题：
```
{questionA}
```

第二个问题：
```
{questionB}
```

相关的技术陈述：
```
{statements}
```

输出JSON格式：
```json
{{
    "question": "组合后的问题",
    "answer": "答案（与第一个问题相同）",
    "note": "如何组合的简要说明"
}}
```
'''

    compose_qa_by_statement = '''你是一个半导体领域的QA构建专家。将一个技术概念融入现有的问答对。该概念通过陈述与问答对连接。组合后应移除直接连接信息，使问题更具挑战性，但保持原答案不变。

现有问答对：
```
{question}
```

要融入的技术概念和陈述：
```
{entity}
```

支撑性技术陈述：
```
{statements}
```

输出JSON格式：
```json
{{
    "question": "改进后的问题",
    "answer": "答案（保持不变）",
    "note": "如何融入概念的说明"
}}
```
'''

    action = '''你是一个半导体领域的QA构建专家。基于当前问答对和相关信息，选择一个操作来提升问题难度。

当前问答对：
{question}

可选操作：
{actions}
'''

    SELECT = '''SELECT: 从相关概念列表中选择一个概念。外部工具会将该概念相关的信息融入问题，替换为需要推理的子问题。

如果选择SELECT，输出JSON格式：
```json
{{
    "action": "SELECT",
    "target": "选中概念的ID（必须来自相关概念列表）",
    "note": "选择该概念的理由"
}}
```'''

    FUZZ = '''FUZZ: 模糊化问题中的1处信息，使问题更具挑战性。确保模糊化后问题仍然清晰且答案唯一。仅当某些信息过于直接指向答案时使用。

如果选择FUZZ，输出JSON格式：
```json
{{
    "action": "FUZZ",
    "question": "模糊化后的问题",
    "note": "为何以及如何进行模糊化"
}}
```'''

    EXIT = '''EXIT: 当问题满足以下所有条件时退出：
- 需要深入的半导体专业知识才能回答
- 提供的信息足够模糊，没有单一信息能直接指向答案

如果选择EXIT，输出JSON格式：
```json
{{
    "action": "EXIT",
    "note": "为何选择退出"
}}
```'''

    BRAINSTORM = '''BRAINSTORM: 头脑风暴与当前问答对相关的半导体概念（如工艺节点、材料、器件类型、物理效应等）。这些概念将被融入问题以增加难度。确保概念的事实准确性。

如果选择BRAINSTORM，输出JSON格式：
```json
{{
    "action": "BRAINSTORM",
    "entities": [
        {{
            "name": "概念名称",
            "concept_id": "概念在知识库中的ID（如果有）",
            "statement": "连接该概念与当前问答的事实陈述"
        }}
    ]
}}
```'''

    extract_key_concepts = '''从以下半导体知识内容中提取关键技术概念（材料、工艺、器件、物理效应等）。

内容：
```txt
{content}
```

输出JSON格式的概念列表：
```json
[
    {{"concept": "概念名", "type": "概念类型（材料/工艺/器件/效应等）"}},
    ...
]
```
'''

    summarize_qa = '''总结以下半导体问答对的核心技术要点。

问答对：
```txt
问题: {question}
答案: {answer}
```

输出格式：
<summary>核心技术摘要</summary>
<key_points>
- 关键点1
- 关键点2
</key_points>
'''

    check_info_cover = '''检查新陈述的信息是否已被先前陈述完全覆盖。

先前的技术陈述：
```txt
{prior}
```

待检查的陈述：
```txt
{current}
```

分析后给出判断：

# 分析
// 你的分析

# 最终判断
```json
{{
    "judgement": "yes 或 no"
}}
```
'''

    check_alternative_ans = '''判断预测答案是否也是该半导体问题的正确答案。预测答案与标准答案不同，检查其是否满足问题的所有约束。

问题: {question}

标准答案: {gt_answer}

支撑标准答案的技术事实：
```txt
{statements}
```

预测答案: {pred_answer}

```json
{{
    "judgement": "yes 或 no"
}}
```
'''

    qa_valid_check = '''检查该半导体问答对的有效性。

问答对有效当且仅当：
1. 问题不是简单拼接多个问题
2. 提供的答案是唯一正确答案
3. 问题有唯一答案
4. 基于相关技术陈述可以解答

问答对和相关信息：
{question}

分析后给出判断：

# 分析
// 你的分析

# 最终判断
```json
{{
    "judgement": "yes 或 no"
}}
```
'''

    direct_gen_check = """回答以下半导体技术问题，将答案放在<answer></answer>标签内。\n\n{question}"""
    
    llm_judge = """你是一个评估助手。判断预测答案是否等价于标准答案。

问题: {question}

标准答案: {gt_answer}

预测答案: {pred_answer}

如果等价回答"Correct"，否则回答"Incorrect"。不要包含其他文字。
"""

    # 🆕 新增：答案验证Prompt
    verify_answer_completeness = '''验证以下多跳问答的答案是否完整回答了问题。

问题：
{question}

答案：
{answer}

推理步骤：
{reasoning_steps}

验证标准：
1. 答案是否回答了问题的所有方面？
2. 推理步骤是否完整（{num_hops}步）？
3. 答案是否基于单跳答案逻辑推导？
4. 答案长度是否适中（50-150字）？

输出JSON格式：
```json
{{
    "is_complete": true/false,
    "missing_aspects": ["缺失的方面1", ...],
    "reasoning_chain_complete": true/false,
    "answer_length_appropriate": true/false,
    "overall_score": 0-10
}}
```
'''

    compose_qa_by_statement = '''你是一个半导体领域的QA构建专家。将一个技术概念融入现有的问答对。该概念通过陈述与问答对连接。组合后应移除直接连接信息，使问题更具挑战性，但保持原答案不变。

现有问答对：
```
{question}
```

要融入的技术概念和陈述：
```
{entity}
```

支撑性技术陈述：
```
{statements}
```

输出JSON格式：
```json
{{
    "question": "改进后的问题",
    "answer": "答案（保持不变）",
    "note": "如何融入概念的说明"
}}
```
'''

    action = '''你是一个半导体领域的QA构建专家。基于当前问答对和相关信息，选择一个操作来提升问题难度。

当前问答对：
{question}

可选操作：
{actions}
'''

    SELECT = '''SELECT: 从相关概念列表中选择一个概念。外部工具会将该概念相关的信息融入问题，替换为需要推理的子问题。

如果选择SELECT，输出JSON格式：
```json
{{
    "action": "SELECT",
    "target": "选中概念的ID（必须来自相关概念列表）",
    "note": "选择该概念的理由"
}}
```'''

    FUZZ = '''FUZZ: 模糊化问题中的1处信息，使问题更具挑战性。确保模糊化后问题仍然清晰且答案唯一。仅当某些信息过于直接指向答案时使用。

如果选择FUZZ，输出JSON格式：
```json
{{
    "action": "FUZZ",
    "question": "模糊化后的问题",
    "note": "为何以及如何进行模糊化"
}}
```'''

    EXIT = '''EXIT: 当问题满足以下所有条件时退出：
- 需要深入的半导体专业知识才能回答
- 提供的信息足够模糊，没有单一信息能直接指向答案

如果选择EXIT，输出JSON格式：
```json
{{
    "action": "EXIT",
    "note": "为何选择退出"
}}
```'''

    BRAINSTORM = '''BRAINSTORM: 头脑风暴与当前问答对相关的半导体概念（如工艺节点、材料、器件类型、物理效应等）。这些概念将被融入问题以增加难度。确保概念的事实准确性。

如果选择BRAINSTORM，输出JSON格式：
```json
{{
    "action": "BRAINSTORM",
    "entities": [
        {{
            "name": "概念名称",
            "concept_id": "概念在知识库中的ID（如果有）",
            "statement": "连接该概念与当前问答的事实陈述"
        }}
    ]
}}
```'''

    extract_key_concepts = '''从以下半导体知识内容中提取关键技术概念（材料、工艺、器件、物理效应等）。

内容：
```txt
{content}
```

输出JSON格式的概念列表：
```json
[
    {{"concept": "概念名", "type": "概念类型（材料/工艺/器件/效应等）"}},
    ...
]
```
'''

    summarize_qa = '''总结以下半导体问答对的核心技术要点。

问答对：
```txt
问题: {question}
答案: {answer}
```

输出格式：
<summary>核心技术摘要</summary>
<key_points>
- 关键点1
- 关键点2
</key_points>
'''

    check_info_cover = '''检查新陈述的信息是否已被先前陈述完全覆盖。

先前的技术陈述：
```txt
{prior}
```

待检查的陈述：
```txt
{current}
```

分析后给出判断：

# 分析
// 你的分析

# 最终判断
```json
{{
    "judgement": "yes 或 no"
}}
```
'''

    check_alternative_ans = '''判断预测答案是否也是该半导体问题的正确答案。预测答案与标准答案不同，检查其是否满足问题的所有约束。

问题: {question}

标准答案: {gt_answer}

支撑标准答案的技术事实：
```txt
{statements}
```

预测答案: {pred_answer}

```json
{{
    "judgement": "yes 或 no"
}}
```
'''

    qa_valid_check = '''检查该半导体问答对的有效性。

问答对有效当且仅当：
1. 问题不是简单拼接多个问题
2. 提供的答案是唯一正确答案
3. 问题有唯一答案
4. 基于相关技术陈述可以解答

问答对和相关信息：
{question}

分析后给出判断：

# 分析
// 你的分析

# 最终判断
```json
{{
    "judgement": "yes 或 no"
}}
```
'''

    direct_gen_check = """回答以下半导体技术问题，将答案放在<answer></answer>标签内。\n\n{question}"""
    
    llm_judge = """你是一个评估助手。判断预测答案是否等价于标准答案。

问题: {question}

标准答案: {gt_answer}

预测答案: {pred_answer}

如果等价回答"Correct"，否则回答"Incorrect"。不要包含其他文字。
"""


# ============ LLM Client (完全保留原版逻辑) ============

class LLMAPIClient:
    """统一的LLM API客户端，支持vLLM和SGLang（原版完整保留）"""
    
    def __init__(self, model_path: str, server_type: str = "vllm", 
                 host: str = "localhost", port: int = 8000, max_retries: int = 3):
        self.model_path = model_path
        self.server_type = server_type.lower()
        self.base_url = f"http://{host}:{port}"
        self.session = None
        self.max_retries = max_retries
        self.is_connected = False
        
        print(f"\n{'='*60}")
        print(f"[LLM] 初始化 {server_type.upper()} 客户端")
        print(f"[LLM] 模型: {model_path}")
        print(f"[LLM] 服务器: {self.base_url}")
        print(f"{'='*60}\n")
        
        self._check_server()
    
    def _check_server(self):
        """检查服务器是否可用"""
        test_url = f"{self.base_url}/v1/models"
        
        try:
            res = requests.get(test_url, timeout=10)
            if res.status_code == 200:
                print(f"[LLM] ✓ 服务器连接成功")
                self.is_connected = True
                models_info = res.json()
                print(f"[LLM] 可用模型: {models_info}")
                return
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] ✗ 无法连接到服务器 {self.base_url}: {e}")
        
        print(f"[WARNING] 请确保已启动 {self.server_type} 服务")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def async_generate(self, prompt: str, sampling_kwargs: Dict):
        """异步生成，使用聊天格式"""
        for attempt in range(self.max_retries):
            try:
                return await self._vllm_chat_generate(prompt, sampling_kwargs)
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"[RETRY] 第{attempt + 1}次重试，等待{wait_time}秒...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                raise
    
    async def _vllm_chat_generate(self, prompt: str, sampling_kwargs: Dict):
        """vLLM聊天格式生成"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
            
        n = sampling_kwargs.get('n', 1)
        
        # 使用聊天格式
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        payload = {
            "model": self.model_path,
            "messages": messages,
            "max_tokens": sampling_kwargs.get('max_new_tokens', 8192),
            "temperature": sampling_kwargs.get('temperature', 0.8),
            "top_p": sampling_kwargs.get('top_p', 0.95),
            "top_k": sampling_kwargs.get('top_k', -1),
            "n": n,
            "stream": False
        }
        
        # 移除None值
        payload = {k: v for k, v in payload.items() if v is not None}
        
        async with self.session.post(
            url=f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"[ERROR] 服务器返回错误: {response.status}, {error_text}")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"HTTP {response.status}: {error_text}"
                )
            
            result = await response.json()
            
            if n == 1:
                return {"text": result['choices'][0]['message']['content']}
            else:
                texts = [choice['message']['content'] for choice in result['choices']]
                return {"text": texts}


# ============ 优化1: 增强的知识库（消耗追踪 + 原版所有功能） ============

class EnhancedSemiconductorKB:
    """增强版知识库 - 原版功能 + 消耗追踪"""
    
    def __init__(self, qa_data: List[Dict]):
        self.qa_data = {qa['id']: qa for qa in qa_data}
        self.qa_ids = list(self.qa_data.keys())
        
        # ✅ 原版索引（完全保留）
        self.concept_to_qas = defaultdict(list)
        self.qa_to_concepts = defaultdict(list)
        self.paper_to_qas = defaultdict(list)
        self.qa_to_paper = {}
        
        # 🆕 新增：消耗追踪系统
        self.paper_usage = defaultdict(int)
        self.paper_total_qa = defaultdict(int)
        self.paper_usage_rate = {}
        self.completed_papers = set()
        self.active_papers = set()
        self.paper_quality_score = defaultdict(float)
        
        self._build_indexes()
        self._initialize_usage_tracking()
        
        print(f"[KB] 加载 {len(self.qa_data)} 条QA数据")
        print(f"[KB] 论文数量: {len(self.paper_to_qas)}")
        print(f"[KB] 活跃论文: {len(self.active_papers)}")
    
    def _build_indexes(self):
        """构建索引（原版逻辑）"""
        for qa_id, qa in self.qa_data.items():
            paper = qa.get('paper_name', 'unknown')
            self.paper_to_qas[paper].append(qa_id)
            self.qa_to_paper[qa_id] = paper
            
            concepts = self._extract_concepts_simple(qa['question'] + ' ' + qa['answer'])
            for concept in concepts:
                self.concept_to_qas[concept].append(qa_id)
                self.qa_to_concepts[qa_id].append(concept)
    
    def _initialize_usage_tracking(self):
        """🆕 初始化消耗追踪"""
        for paper_name, qa_list in self.paper_to_qas.items():
            self.paper_total_qa[paper_name] = len(qa_list)
            self.paper_usage[paper_name] = 0
            self.paper_usage_rate[paper_name] = 0.0
            self.active_papers.add(paper_name)
            self.paper_quality_score[paper_name] = 1.0
    
    def _extract_concepts_simple(self, text: str) -> List[str]:
        """简单概念提取（原版逻辑）"""
        keywords = [
            '氧化物', '薄膜晶体管', 'TFT', '载流子', '迁移率', '阈值电压',
            '氧空位', '栅极', '源极', '漏极', '沟道', '介电层',
            'IGZO', 'LTPS', 'a-Si', 'OLED', 'LCD',
            '溅射', '退火', '刻蚀', '沉积', '钝化',
            '电子', '空穴', '能带', '费米能级', '态密度',
            '半导体', '晶体管', '器件', '材料', '工艺'
        ]
        
        concepts = []
        for keyword in keywords:
            if keyword in text:
                concepts.append(keyword)
        return list(set(concepts))
    
    # ✅ 原版方法：find_related_qas（完全保留）
    def find_related_qas(self, qa_id: str, top_k: int = 5) -> List[str]:
        """找到相关的QA（原版逻辑）"""
        if qa_id not in self.qa_to_concepts:
            return random.sample(self.qa_ids, min(top_k, len(self.qa_ids)))
        
        concepts = self.qa_to_concepts[qa_id]
        scores = defaultdict(int)
        
        for concept in concepts:
            for related_qa_id in self.concept_to_qas[concept]:
                if related_qa_id != qa_id:
                    scores[related_qa_id] += 1
        
        sorted_qas = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        related_ids = [qa_id for qa_id, _ in sorted_qas[:top_k]]
        
        if len(related_ids) < top_k:
            remaining = [qid for qid in self.qa_ids if qid != qa_id and qid not in related_ids]
            related_ids.extend(random.sample(remaining, min(top_k - len(related_ids), len(remaining))))
        
        return related_ids
    
    # 🆕 新增：基于优先级的相关QA查找
    def find_related_qas_prioritized(self, qa_id: str, top_k: int = 5) -> List[str]:
        """找到相关的QA（带优先级）"""
        if qa_id not in self.qa_to_concepts:
            # 按论文优先级排序
            active_papers = list(self.active_papers)
            active_papers.sort(key=lambda p: self.get_paper_priority(p), reverse=True)
            
            candidates = []
            for paper in active_papers:
                candidates.extend(self.paper_to_qas[paper])
                if len(candidates) >= top_k:
                    break
            
            return random.sample(candidates, min(top_k, len(candidates)))
        
        concepts = self.qa_to_concepts[qa_id]
        scores = defaultdict(float)
        
        for concept in concepts:
            for related_qa_id in self.concept_to_qas[concept]:
                if related_qa_id != qa_id:
                    scores[related_qa_id] += 1.0
                    
                    # 加上论文优先级权重
                    paper = self.qa_to_paper.get(related_qa_id, 'unknown')
                    priority = self.get_paper_priority(paper)
                    scores[related_qa_id] += priority / 10.0
        
        sorted_qas = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        related_ids = [qa_id for qa_id, _ in sorted_qas[:top_k]]
        
        if len(related_ids) < top_k:
            remaining = [qid for qid in self.qa_ids if qid != qa_id and qid not in related_ids]
            related_ids.extend(random.sample(remaining, min(top_k - len(related_ids), len(remaining))))
        
        return related_ids
    
    # 🆕 新增：论文优先级计算
    def get_paper_priority(self, paper_name: str) -> float:
        """计算论文的选择优先级"""
        if paper_name in self.completed_papers:
            return 0.0
        
        usage_rate = self.paper_usage_rate.get(paper_name, 0.0)
        quality = self.paper_quality_score.get(paper_name, 1.0)
        
        # 使用率越低，优先级越高
        priority = (1.0 - usage_rate) * 10.0
        priority *= quality
        
        return priority
    
    # 🆕 新增：更新使用统计
    def update_usage(self, qa_ids: List[str]):
        """更新使用统计"""
        for qa_id in qa_ids:
            paper_name = self.qa_to_paper.get(qa_id, 'unknown')
            if paper_name == 'unknown':
                continue
            
            self.paper_usage[paper_name] += 1
            total = self.paper_total_qa[paper_name]
            usage_rate = self.paper_usage[paper_name] / total
            self.paper_usage_rate[paper_name] = usage_rate
            
            # 自动标记完成
            if usage_rate >= 0.8 and paper_name not in self.completed_papers:
                self.completed_papers.add(paper_name)
                self.active_papers.discard(paper_name)
                print(f"[KB] ✓ 论文完成: {paper_name} (使用率: {usage_rate*100:.1f}%)")
    
    # 🆕 新增：获取消耗统计
    def get_usage_stats(self) -> Dict:
        """获取消耗统计"""
        total_papers = len(self.paper_to_qas)
        active_papers = len(self.active_papers)
        completed_papers = len(self.completed_papers)
        
        overall_coverage = completed_papers / total_papers if total_papers > 0 else 0.0
        
        low_usage_papers = [
            (paper, rate) for paper, rate in self.paper_usage_rate.items()
            if rate < 0.3 and paper in self.active_papers
        ]
        low_usage_papers.sort(key=lambda x: x[1])
        
        return {
            'total_papers': total_papers,
            'active_papers': active_papers,
            'completed_papers': completed_papers,
            'overall_coverage': overall_coverage,
            'low_usage_papers': low_usage_papers[:10],
            'usage_distribution': {
                '0-20%': sum(1 for r in self.paper_usage_rate.values() if r < 0.2),
                '20-40%': sum(1 for r in self.paper_usage_rate.values() if 0.2 <= r < 0.4),
                '40-60%': sum(1 for r in self.paper_usage_rate.values() if 0.4 <= r < 0.6),
                '60-80%': sum(1 for r in self.paper_usage_rate.values() if 0.6 <= r < 0.8),
                '80-100%': sum(1 for r in self.paper_usage_rate.values() if r >= 0.8)
            }
        }
    
    # ✅ 原版方法：get_qa（完全保留）
    def get_qa(self, qa_id: str) -> Dict:
        return self.qa_data.get(qa_id)
    
    # ✅ 原版方法：get_qa_repr（完全保留）
    def get_qa_repr(self, qa_id: str) -> str:
        qa = self.get_qa(qa_id)
        if not qa:
            return ""
        
        concepts = self.qa_to_concepts.get(qa_id, [])
        concept_str = ', '.join(concepts) if concepts else '无'
        
        return f"""ID: {qa_id}
问题: {qa['question']}
答案: {qa['answer']}
来源论文: {qa.get('paper_name', 'unknown')}
关键概念: {concept_str}
"""


# ============ QA实体类（原版完整保留） ============

class SemiconductorQAEntity:
    """半导体QA实体（原版完整保留）"""
    
    def __init__(self, qa_id: str, qa_data: Dict, kb: EnhancedSemiconductorKB):
        self.id = qa_id
        self.qa_data = qa_data
        self.kb = kb
        self.summary = None
        self.key_concepts = []
        self.related_qas = []
    
    @property
    def name(self):
        return f"QA-{self.id}"
    
    @property
    def url(self):
        return self.id
    
    def repr(self):
        """生成实体的文本表示"""
        concepts_str = ', '.join(self.key_concepts) if self.key_concepts else '待提取'
        related_str = ', '.join([f"QA-{rid}" for rid in self.related_qas[:3]]) if self.related_qas else '无'
        
        question = self.qa_data.get('question', '')
        answer = self.qa_data.get('answer', '')
        paper_name = self.qa_data.get('paper_name', 'unknown')
        
        return f"""# QA实体 {self.id}

## 问题
{question}

## 答案
{answer}

## 来源
论文: {paper_name}

## 关键概念
{concepts_str}

## 相关QA
{related_str}

## 摘要
{self.summary or '待生成'}
"""
    
    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'qa_data': self.qa_data,
            'summary': self.summary,
            'key_concepts': self.key_concepts,
            'related_qas': self.related_qas
        }


# ============ Agent记忆类（原版完整保留） ============

class AgentMemory:
    """Agent记忆（原版完整保留）"""
    
    def __init__(self):
        self.qa = dict(question=None, answer=None)
        self.statements = []
        self.relevant = []
        self.edit_history = []
        self.qa_history = []
        self.uid = None
    
    def repr(self):
        relevant = '\n'.join([f'- [{e.name}] (ID: {e.id})' for e in self.relevant])
        statements = '\n'.join(self.statements)
        return f"""
当前问题: {self.qa['question']}
当前答案: {self.qa['answer']}

相关技术陈述：
```txt
{statements}
```

相关QA实体列表：
```txt
{relevant}
```
"""
    
    def statements_repr(self, additional=None):
        return '\n'.join(self.statements + (additional or []))
    
    def dict(self):
        return {
            'qa': self.qa,
            'relevant': [e.dict() for e in self.relevant],
            'statements': self.statements,
            'edit_history': self.edit_history,
            'qa_history': self.qa_history,
            'uid': self.uid
        }


# ============ 优化2: 增强的Agent（原版所有功能 + 动态规划） ============

class EnhancedSemiconductorQAAgent:
    """增强版Agent - 原版所有功能 + 动态规划策略"""
    
    def __init__(self, knowledge_base: EnhancedSemiconductorKB, 
                 llm_client: LLMAPIClient, max_turns: int = 16,
                 use_dynamic_planning: bool = True):
        self.kb = knowledge_base
        self.llm_client = llm_client
        self.max_turns = max_turns
        self.tokenizer = AutoTokenizer.from_pretrained("/mnt/data/LLM/lhy/models/Qwen/Qwen2.5-14B-Instruct")
        
        # 🆕 新增：动态规划开关
        self.use_dynamic_planning = use_dynamic_planning
        if use_dynamic_planning:
            self.current_stage = 'early'
            self.stage_thresholds = {'early': 0.6, 'mid': 0.2}
            print(f"[Agent] ✓ 启用动态规划策略")
        else:
            print(f"[Agent] 使用原版生成策略")
    
    # 🆕 新增：更新生成阶段
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
    
    # 🆕 新增：智能选择根QA（带动态规划）
    def select_root_qa_smart(self) -> str:
        """智能选择根QA"""
        if not self.use_dynamic_planning:
            # 原版：随机选择
            return random.choice(self.kb.qa_ids)
        
        # 动态规划：基于阶段选择
        self.update_generation_stage()
        
        if self.current_stage == 'early':
            # 早期：优先选择高优先级论文
            paper_priorities = {
                paper: self.kb.get_paper_priority(paper)
                for paper in self.kb.active_papers
            }
            if not paper_priorities:
                return random.choice(self.kb.qa_ids)
            
            sorted_papers = sorted(paper_priorities.items(), key=lambda x: x[1], reverse=True)
            top_papers = [p for p, _ in sorted_papers[:3]]  # 取前3
            selected_paper = random.choice(top_papers)
            return random.choice(self.kb.paper_to_qas[selected_paper])
        
        elif self.current_stage == 'late':
            # 后期：强制选择低使用率论文
            low_usage_papers = [
                paper for paper, rate in self.kb.paper_usage_rate.items()
                if rate < 0.5 and paper in self.kb.active_papers
            ]
            if low_usage_papers:
                selected_paper = random.choice(low_usage_papers)
                return random.choice(self.kb.paper_to_qas[selected_paper])
        
        # 中期或其他情况：随机
        return random.choice(self.kb.qa_ids)
    
    # ✅ 原版方法：call_llm（完全保留）
    async def call_llm(self, prompt: str) -> str:
        """调用LLM（原版逻辑）"""
        prompt = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], 
            add_generation_prompt=True, 
            tokenize=False
        )
        
        max_new_tokens = 8000 - self.tokenizer([prompt], return_length=True)["length"][0]
        max_new_tokens = max(max_new_tokens, 512)
        
        sampling_kwargs = {
            "temperature": 0.8,
            "top_p": 0.95,
            "top_k": 1000,
            "max_new_tokens": max_new_tokens,
            "n": 1,
            "stop_token_ids": [151645, 151643]
        }
        
        try:
            output = await self.llm_client.async_generate(prompt, sampling_kwargs)
            response = output["text"]
            return response
        except Exception as e:
            print(f"[ERROR] LLM调用失败: {e}")
            raise
    
    # ✅ 原版方法：extract_qa_info（完全保留）
    async def extract_qa_info(self, entity: SemiconductorQAEntity) -> SemiconductorQAEntity:
        """提取QA实体的详细信息（原版逻辑）"""
        print(f"[INFO] 提取 QA-{entity.id} 的信息")
        
        try:
            # 生成摘要
            prompt = SemiconductorQAPrompts.summarize_qa.format(
                question=entity.qa_data['question'],
                answer=entity.qa_data['answer']
            )
            summary_text = await self.call_llm(prompt)
            
            if '<summary>' in summary_text and '</summary>' in summary_text:
                entity.summary = summary_text.split('<summary>')[1].split('</summary>')[0].strip()
            
            # 提取关键概念
            concept_prompt = SemiconductorQAPrompts.extract_key_concepts.format(
                content=entity.qa_data['question'] + '\n' + entity.qa_data['answer']
            )
            concept_text = await self.call_llm(concept_prompt)
            
            if '```json' in concept_text:
                try:
                    concepts_list = json.loads(concept_text.split('```json')[1].split('```')[0].strip())
                    entity.key_concepts = [c['concept'] for c in concepts_list]
                except:
                    entity.key_concepts = self.kb.qa_to_concepts.get(entity.id, [])
        except Exception as e:
            print(f"[WARNING] 提取信息失败: {e}")
            entity.key_concepts = self.kb.qa_to_concepts.get(entity.id, [])
        
        # 找相关QA（带优先级）
        if self.use_dynamic_planning:
            entity.related_qas = self.kb.find_related_qas_prioritized(entity.id, top_k=5)
        else:
            entity.related_qas = self.kb.find_related_qas(entity.id, top_k=5)
        
        return entity
    
    # ✅ 原版方法：construct_base_qa（完全保留）
    async def construct_base_qa(self, entity: SemiconductorQAEntity) -> Dict:
        """构建基础QA（原版逻辑）"""
        prompt = SemiconductorQAPrompts.base_qa.format(content=entity.repr())
        text = await self.call_llm(prompt)
        
        base_qa = json.loads(text.split('```json')[1].split('```')[0].strip())
        return base_qa
    
    # ✅ 原版方法：choose_action（完全保留）
    async def choose_action(self, state: str, ready_to_exit: bool = False) -> Dict:
        """选择下一步操作（原版逻辑）"""
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
    
    # ✅ 原版方法：construct_link_qa（完全保留）
    async def construct_link_qa(self, entityA: SemiconductorQAEntity, 
                                entityB: SemiconductorQAEntity) -> Dict:
        """构建关联QA（原版逻辑）"""
        prompt = SemiconductorQAPrompts.link_qa.format(
            conceptA=entityA.name,
            conceptB=entityB.name,
            contentA=entityA.repr(),
            contentB=entityB.repr()
        )
        text = await self.call_llm(prompt)
        link_qa = json.loads(text.split('```json')[1].split('```')[0].strip())
        return link_qa
    
    # ✅ 原版方法：combine_qa（完全保留）
    async def combine_qa(self, questionA: Dict, questionB: Dict, memory: AgentMemory) -> Dict:
        """组合两个问答（原版逻辑）"""
        prompt = SemiconductorQAPrompts.compose_qa.format(
            questionA=json.dumps({'question': questionA['question'], 'answer': questionA['answer']}, ensure_ascii=False),
            questionB=json.dumps({'question': questionB['question'], 'answer': questionB['answer']}, ensure_ascii=False),
            statements=memory.statements_repr(additional=[questionB['statement']])
        )
        text = await self.call_llm(prompt)
        combined = json.loads(text.split('```json')[1].split('```')[0].strip())
        return combined
    
    # ✅ 原版方法：check_info_cover（完全保留）
    async def check_info_cover(self, statement: str, prior_statements: str) -> bool:
        """检查信息覆盖（原版逻辑）"""
        prompt = SemiconductorQAPrompts.check_info_cover.format(
            prior=prior_statements,
            current=statement
        )
        text = await self.call_llm(prompt)
        result = json.loads(text.split('```json')[1].split('```')[0].strip())
        return result['judgement'] == 'yes'
    
    # ✅ 原版方法：check_qa_valid（完全保留）
    async def check_qa_valid(self, state: str) -> bool:
        """检查QA有效性（原版逻辑）"""
        prompt = SemiconductorQAPrompts.qa_valid_check.format(question=state)
        text = await self.call_llm(prompt)
        result = json.loads(text.split('```json')[1].split('```')[0].strip())
        return 'yes' in result['judgement']
    
    # ✅ 原版方法：direct_generate（完全保留）
    async def direct_generate(self, question: str, n: int = 1) -> List[str]:
        """直接生成答案（原版逻辑）"""
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
    
    # ✅ 原版方法：llm_judge_answer（完全保留）
    async def llm_judge_answer(self, question: str, answers: List[str], 
                              gt_answer: str) -> List[bool]:
        """LLM判断答案正确性（原版逻辑）"""
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
                text = await self.call_llm(prompt)
                corrects.append('Correct' in text)
        return corrects
    
    # ✅ 原版方法：check_alternative_answer（完全保留）
    async def check_alternative_answer(self, question: str, gt_answer: str,
                                      pred_answer: str, statements: str) -> bool:
        """检查替代答案（原版逻辑）"""
        prompt = SemiconductorQAPrompts.check_alternative_ans.format(
            question=question,
            gt_answer=gt_answer,
            pred_answer=pred_answer,
            statements=statements
        )
        text = await self.call_llm(prompt)
        return 'yes' in text.lower()
    
    # 🆕 新增：显式多跳QA生成（使用改进版Prompt）
    async def generate_multihop_qa_explicit(self, root_entity: SemiconductorQAEntity,
                                           num_hops: int = 2) -> Dict:
        """
        显式生成多跳QA（使用高质量Prompt）
        
        Args:
            root_entity: 根QA实体
            num_hops: 跳数（2或3）
        
        Returns:
            包含多跳问题、答案、推理链的字典
        """
        print(f"\n[MULTIHOP] 开始生成{num_hops}跳问答（高质量模式）")
        
        # 收集单跳QA
        entities_chain = [root_entity]
        single_hops = [root_entity.qa_data]
        
        # 逐跳构建链条
        for hop in range(1, num_hops):
            print(f"  - 查找第{hop+1}跳...")
            
            prev_entity = entities_chain[-1]
            if self.use_dynamic_planning:
                neighbor_ids = self.kb.find_related_qas_prioritized(prev_entity.id, top_k=5)
            else:
                neighbor_ids = prev_entity.related_qas[:5]
            
            if not neighbor_ids:
                print(f"  [WARNING] 无法找到第{hop+1}跳的相关QA")
                break
            
            neighbor_id = random.choice(neighbor_ids)
            neighbor_data = self.kb.get_qa(neighbor_id)
            neighbor_entity = SemiconductorQAEntity(neighbor_id, neighbor_data, self.kb)
            neighbor_entity = await self.extract_qa_info(neighbor_entity)
            
            # 更新使用统计
            if self.use_dynamic_planning:
                self.kb.update_usage([neighbor_id])
            
            entities_chain.append(neighbor_entity)
            single_hops.append(neighbor_data)
        
        # 生成桥接信息
        bridge_info = self._generate_bridge_info(entities_chain)
        
        # 格式化单跳QA
        single_hop_str = "\n\n".join([
            f"单跳QA-{i+1} (来自论文: {qa.get('paper_name', 'unknown')}):\n"
            f"问题: {qa['question']}\n"
            f"答案: {qa['answer']}"
            for i, qa in enumerate(single_hops)
        ])
        
        # 🆕 使用改进版Prompt
        prompt = SemiconductorQAPrompts.compose_qa_multihop.format(
            num_hops=len(single_hops),
            single_hop_qas=single_hop_str,
            bridge_info=bridge_info
        )
        
        try:
            text = await self.call_llm(prompt)
            result = json.loads(text.split('```json')[1].split('```')[0].strip())
        except Exception as e:
            print(f"  [ERROR] 高质量生成失败: {e}")
            return None
        
        # 验证输出格式
        required_keys = ['question', 'answer', 'reasoning_steps', 'quality_indicators']
        if not all(key in result for key in required_keys):
            print(f"  [WARNING] 生成结果缺少必要字段")
            return None
        
        # 🆕 验证答案完整性
        verification = await self.verify_answer_completeness(
            result['question'],
            result['answer'],
            result['reasoning_steps'],
            len(single_hops)
        )
        
        # 组装最终结果
        final_result = {
            'multihop_question': result['question'],
            'multihop_answer': result['answer'],
            'num_hops': len(single_hops),
            'reasoning_steps': result['reasoning_steps'],
            'entities_chain': [e.id for e in entities_chain],
            'bridge_info': bridge_info,
            'quality_indicators': result.get('quality_indicators', {}),
            'verification': verification,
            'generation_method': 'high_quality_explicit'
        }
        
        print(f"[MULTIHOP] ✓ 完成{len(single_hops)}跳问答生成")
        print(f"           问题: {result['question'][:60]}...")
        print(f"           验证分数: {verification.get('overall_score', 0)}/10")
        
        return final_result
    
    def _generate_bridge_info(self, entities_chain: List[SemiconductorQAEntity]) -> str:
        """生成桥接关系描述"""
        if len(entities_chain) < 2:
            return "单个问答，无桥接关系"
        
        bridge_desc = []
        for i in range(len(entities_chain) - 1):
            qa1 = entities_chain[i].qa_data
            qa2 = entities_chain[i+1].qa_data
            
            # 找共同概念
            concepts1 = set(self.kb.qa_to_concepts.get(entities_chain[i].id, []))
            concepts2 = set(self.kb.qa_to_concepts.get(entities_chain[i+1].id, []))
            common = concepts1 & concepts2
            
            if common:
                bridge_desc.append(
                    f"QA-{i+1}和QA-{i+2}通过共同概念'{list(common)[0]}'连接，"
                    f"形成因果推理链。"
                )
            else:
                bridge_desc.append(
                    f"QA-{i+1}和QA-{i+2}在技术领域上相关。"
                )
        
        return '\n'.join(bridge_desc) if bridge_desc else "通过技术领域关联"
    
    # 🆕 新增：验证答案完整性
    async def verify_answer_completeness(self, question: str, answer: str,
                                        reasoning_steps: List[str], 
                                        num_hops: int) -> Dict:
        """验证答案是否完整回答了问题"""
        steps_str = '\n'.join([f"{i+1}. {step}" for i, step in enumerate(reasoning_steps)])
        
        prompt = SemiconductorQAPrompts.verify_answer_completeness.format(
            question=question,
            answer=answer,
            reasoning_steps=steps_str,
            num_hops=num_hops
        )
        
        try:
            text = await self.call_llm(prompt)
            verification = json.loads(text.split('```json')[1].split('```')[0].strip())
            return verification
        except Exception as e:
            print(f"  [WARNING] 验证失败: {e}")
            return {
                'is_complete': False,
                'overall_score': 0
            }
    
    # ✅ 改进原版combine_qa方法（增加验证）
    async def combine_qa_verified(self, questionA: Dict, questionB: Dict, 
                                  memory: AgentMemory) -> Dict:
        """
        组合两个问答（带验证增强）
        
        在原版combine_qa基础上增加答案验证
        """
        # 先用原版方法生成
        combined = await self.combine_qa(questionA, questionB, memory)
        
        # 验证答案完整性
        verification = await self.verify_answer_completeness(
            combined['question'],
            combined['answer'],
            [questionA.get('statement', ''), questionB.get('statement', '')],
            2  # 组合了2个QA
        )
        
        combined['verification'] = verification
        combined['verified_score'] = verification.get('overall_score', 0)
        
        # 如果验证分数低，记录警告
        if verification.get('overall_score', 0) < 6:
            print(f"  [WARNING] 组合QA验证分数低: {verification.get('overall_score')}/10")
            print(f"           缺失方面: {verification.get('missing_aspects', [])}")
        
        return combined
    
    # ✅ 原版方法：generate（完全保留并增强）
    async def generate(self, semaphore: asyncio.Semaphore, save_path: str):
        """生成一个复杂QA（原版逻辑 + 动态规划增强）"""
        async with semaphore:
            # 🆕 智能选择根QA（如果启用动态规划）
            root_id = self.select_root_qa_smart()
            root_qa_data = self.kb.get_qa(root_id)
            
            memory = AgentMemory()
            memory.uid = str(uuid.uuid4())
            
            print(f"\n{'='*60}")
            print(f"[START] 生成QA，根实体: QA-{root_id}")
            if self.use_dynamic_planning:
                print(f"        阶段: {self.current_stage}")
            print(f"{'='*60}\n")
            
            # 🆕 更新使用统计
            self.kb.update_usage([root_id])
            
            # 创建根实体
            root_entity = SemiconductorQAEntity(root_id, root_qa_data, self.kb)
            root_entity = await self.extract_qa_info(root_entity)
            memory.relevant.append(root_entity)
            
            # 构建基础QA
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
            
            # 迭代优化（原版逻辑）
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
                
                # 执行不同的动作（原版逻辑）
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
                    
                    # 🆕 更新使用统计
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
                    
                    # 组合QA（这里就是多跳生成的核心！）
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
                
                # 检查替代答案
                is_alternative = False
                for pred_ans, correct in zip(answers, corrects):
                    if pred_ans and not correct:
                        try:
                            is_alternative = await self.check_alternative_answer(
                                q_new, memory.qa['answer'], pred_ans,
                                memory.statements_repr()
                            )
                        except Exception as e:
                            print(f"[WARNING] 检查替代答案失败: {e}")
                        
                        if is_alternative:
                            break
                
                if is_alternative:
                    print(f"[WARNING] 存在替代答案 '{pred_ans[:50]}...'，跳过")
                    continue
                
                # 更新记忆
                memory = memory_new
                acc = f"{sum(corrects)}/{len(corrects)}"
                print(f"[RESULT] 直接生成准确率: {acc}")
                
                memory.qa_history.append({
                    'question': q_new,
                    'answer': memory.qa['answer'],
                    'direct_gen_acc': acc
                })
                memory.edit_history.append(f"直接生成准确率: {acc}")
                
                if not any(corrects):
                    ready_to_exit = True
                    print(f"[INFO] 第{turn+1}轮问题LLM全部答错，准备退出")
                
                print(f"[STATS] 动作统计: {dict(action_stats)}")
            
            # 🆕 添加多跳QA的显式标记
            # 最终的memory.qa就是多跳QA
            final_multihop = {
                'multihop_question': memory.qa['question'],
                'multihop_answer': memory.qa['answer'],
                'num_hops': len(memory.relevant),
                'entities_chain': [e.id for e in memory.relevant],
                'statements': memory.statements,
                'reasoning_steps': [
                    {
                        'step': i+1,
                        'content': stmt,
                        'based_on': f"QA-{memory.relevant[i].id}"
                    }
                    for i, stmt in enumerate(memory.statements)
                ],
                'qa_history': memory.qa_history,
                'action_stats': dict(action_stats)
            }
            
            # 保存结果
            result = memory.dict()
            result['final_multihop_qa'] = final_multihop  # 🆕 显式保存多跳QA
            
            if self.use_dynamic_planning:
                result['generation_stage'] = self.current_stage
                result['use_dynamic_planning'] = True
            
            output_file = f"{save_path}/{memory.uid}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(result, ensure_ascii=False))
            
            print(f"\n[MULTIHOP] 最终问答:")
            print(f"  问题: {final_multihop['multihop_question'][:80]}...")
            print(f"  答案: {final_multihop['multihop_answer'][:80]}...")
            print(f"  跳数: {final_multihop['num_hops']}")
            print(f"\n[SAVED] {output_file}")
            print(f"{'='*60}\n")
            
            return memory
        """生成一个复杂QA（原版逻辑 + 动态规划增强）"""
        async with semaphore:
            # 🆕 智能选择根QA（如果启用动态规划）
            root_id = self.select_root_qa_smart()
            root_qa_data = self.kb.get_qa(root_id)
            
            memory = AgentMemory()
            memory.uid = str(uuid.uuid4())
            
            print(f"\n{'='*60}")
            print(f"[START] 生成QA，根实体: QA-{root_id}")
            if self.use_dynamic_planning:
                print(f"        阶段: {self.current_stage}")
            print(f"{'='*60}\n")
            
            # 🆕 更新使用统计
            self.kb.update_usage([root_id])
            
            # 创建根实体
            root_entity = SemiconductorQAEntity(root_id, root_qa_data, self.kb)
            root_entity = await self.extract_qa_info(root_entity)
            memory.relevant.append(root_entity)
            
            # 构建基础QA
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
            
            # 迭代优化（原版逻辑）
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
                
                # 执行不同的动作（原版逻辑）
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
                    
                    # 🆕 更新使用统计
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
                    
                    # 组合QA
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
                
                # 检查替代答案
                is_alternative = False
                for pred_ans, correct in zip(answers, corrects):
                    if pred_ans and not correct:
                        try:
                            is_alternative = await self.check_alternative_answer(
                                q_new, memory.qa['answer'], pred_ans,
                                memory.statements_repr()
                            )
                        except Exception as e:
                            print(f"[WARNING] 检查替代答案失败: {e}")
                        
                        if is_alternative:
                            break
                
                if is_alternative:
                    print(f"[WARNING] 存在替代答案 '{pred_ans[:50]}...'，跳过")
                    continue
                
                # 更新记忆
                memory = memory_new
                acc = f"{sum(corrects)}/{len(corrects)}"
                print(f"[RESULT] 直接生成准确率: {acc}")
                
                memory.qa_history.append({
                    'question': q_new,
                    'answer': memory.qa['answer'],
                    'direct_gen_acc': acc
                })
                memory.edit_history.append(f"直接生成准确率: {acc}")
                
                if not any(corrects):
                    ready_to_exit = True
                    print(f"[INFO] 第{turn+1}轮问题LLM全部答错，准备退出")
                
                print(f"[STATS] 动作统计: {dict(action_stats)}")
            
            # 保存结果
            result = memory.dict()
            if self.use_dynamic_planning:
                result['generation_stage'] = self.current_stage
                result['use_dynamic_planning'] = True
            
            output_file = f"{save_path}/{memory.uid}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(result, ensure_ascii=False))
            
            print(f"\n[SAVED] {output_file}")
            print(f"{'='*60}\n")
            
            return memory


# ============ 优化3: 带监控的批量生成 ============

async def generate_batch_with_monitoring(agent: EnhancedSemiconductorQAAgent, 
                        save_path: str, 
                        batch_size: int = 128,
                        total: int = 1024):
    """批量生成QA（原版逻辑 + 监控增强）"""
    semaphore = asyncio.Semaphore(batch_size)
    tasks = [agent.generate(semaphore, save_path) for _ in range(total)]
    
    print(f"\n{'='*60}")
    print(f"[BATCH] 开始生成 {total} 个QA，并发数: {batch_size}")
    if agent.use_dynamic_planning:
        print(f"[BATCH] ✓ 启用动态规划策略")
    print(f"{'='*60}\n")
    
    # 🆕 覆盖进度记录
    coverage_history = []
    last_report = 0
    
    results = []
    for i, coro in enumerate(asyncio.as_completed(tasks)):
        try:
            result = await coro
            results.append(result)
            
            # 🆕 每100个记录一次
            if (i + 1) - last_report >= 100:
                stats = agent.kb.get_usage_stats()
                coverage_history.append({
                    'completed': i + 1,
                    'coverage': stats['overall_coverage'],
                    'active_papers': stats['active_papers'],
                    'stage': agent.current_stage if agent.use_dynamic_planning else 'N/A'
                })
                
                print(f"\n[监控] 已完成={i+1}/{total}, "
                      f"覆盖率={stats['overall_coverage']*100:.1f}%, "
                      f"活跃论文={stats['active_papers']}")
                
                if stats['low_usage_papers']:
                    low_str = ', '.join([f"{p}({r*100:.1f}%)" for p, r in stats['low_usage_papers'][:3]])
                    print(f"       低使用率论文: {low_str}")
                
                last_report = i + 1
        except Exception as e:
            print(f"[ERROR] 生成失败: {e}")
            results.append(None)
    
    # 保存覆盖历史
    history_file = os.path.join(save_path, 'coverage_history.json')
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(coverage_history, f, ensure_ascii=False, indent=2)
    
    # 统计结果
    success = sum(1 for r in results if r is not None)
    failed = total - success
    
    print(f"\n{'='*60}")
    print(f"[BATCH] 完成！成功: {success}, 失败: {failed}")
    print(f"{'='*60}\n")
    
    return results


# ============ 优化4: 兜底保障机制 ============

async def ensure_full_coverage(agent: EnhancedSemiconductorQAAgent,
                               save_path: str,
                               target_coverage: float = 0.8):
    """兜底机制：确保达到目标覆盖率"""
    stats = agent.kb.get_usage_stats()
    current_coverage = stats['overall_coverage']
    
    if current_coverage >= target_coverage:
        print(f"[兜底] ✓ 已达到目标覆盖率 {target_coverage*100}%")
        return []
    
    print(f"\n{'='*60}")
    print(f"[兜底] 启动强制覆盖模式")
    print(f"  - 当前覆盖: {current_coverage*100:.1f}%")
    print(f"  - 目标覆盖: {target_coverage*100}%")
    print(f"  - 剩余论文: {len(agent.kb.active_papers)}")
    print(f"{'='*60}\n")
    
    additional_results = []
    semaphore = asyncio.Semaphore(16)  # 兜底阶段降低并发
    
    # 为低使用率论文生成
    low_usage_papers = [
        paper for paper, rate in agent.kb.paper_usage_rate.items()
        if rate < target_coverage and paper in agent.kb.active_papers
    ]
    
    tasks = []
    for paper in low_usage_papers:
        # 临时修改agent，强制从该论文选择
        async def generate_for_paper(paper_name):
            async with semaphore:
                # 保存原始选择方法
                original_select = agent.select_root_qa_smart
                
                # 临时替换为强制选择该论文
                def force_select():
                    return random.choice(agent.kb.paper_to_qas[paper_name])
                
                agent.select_root_qa_smart = force_select
                
                try:
                    result = await agent.generate(semaphore, save_path)
                    return result
                finally:
                    # 恢复原始方法
                    agent.select_root_qa_smart = original_select
        
        tasks.append(generate_for_paper(paper))
    
    print(f"[兜底] 为 {len(tasks)} 篇论文生成QA...")
    
    for result in await asyncio.gather(*tasks, return_exceptions=True):
        if isinstance(result, Exception):
            print(f"[WARNING] 兜底生成失败: {result}")
        elif result is not None:
            additional_results.append(result)
    
    final_stats = agent.kb.get_usage_stats()
    print(f"\n[兜底] 完成!")
    print(f"  - 补充生成: {len(additional_results)} 个QA")
    print(f"  - 最终覆盖率: {final_stats['overall_coverage']*100:.1f}%")
    print(f"{'='*60}\n")
    
    return additional_results


# ============ 主函数 ============

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="增强版半导体领域QA生成 - 原版功能+三大优化")
    parser.add_argument('--input', type=str, required=True, help='输入JSONL文件路径')
    parser.add_argument('--output', type=str, required=True, help='输出目录')
    parser.add_argument('--model_path', type=str, required=True, help='本地模型路径或名称')
    parser.add_argument('--server_type', type=str, default='vllm', 
                       choices=['vllm', 'sglang'], help='推理框架类型')
    parser.add_argument('--host', type=str, default='localhost', help='服务器地址')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    parser.add_argument('--batch_size', type=int, default=32, help='并发数')
    parser.add_argument('--total', type=int, default=100, help='生成总数')
    parser.add_argument('--max_turns', type=int, default=16, help='最大迭代轮数（原版）')
    
    # 🆕 新增参数
    parser.add_argument('--use_dynamic_planning', action='store_true',
                       help='启用动态规划策略（三大优化）')
    parser.add_argument('--enable_fallback', action='store_true',
                       help='启用兜底机制')
    parser.add_argument('--target_coverage', type=float, default=0.8,
                       help='目标覆盖率（用于兜底）')
    
    args = parser.parse_args()
    
    # 加载数据
    print(f"\n{'='*60}")
    print(f"[LOAD] 加载数据: {args.input}")
    print(f"{'='*60}\n")
    
    qa_data = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in tqdm.tqdm(f, desc="Loading"):
            qa_data.append(json.loads(line))
    
    print(f"\n[LOAD] ✓ 加载了 {len(qa_data)} 条QA数据\n")
    
    # 构建知识库
    print(f"{'='*60}")
    print("[KB] 构建知识库...")
    print(f"{'='*60}\n")
    
    kb = EnhancedSemiconductorKB(qa_data)
    
    print(f"[KB] 知识库统计:")
    print(f"  - QA数量: {len(kb.qa_data)}")
    print(f"  - 概念数量: {len(kb.concept_to_qas)}")
    print(f"  - 论文数量: {len(kb.paper_to_qas)}")
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    print(f"\n[OUTPUT] 输出目录: {args.output}\n")
    
    # 初始化LLM客户端
    llm_client = LLMAPIClient(
        model_path=args.model_path,
        server_type=args.server_type,
        host=args.host,
        port=args.port
    )
    
    # 创建Agent
    agent = EnhancedSemiconductorQAAgent(
        kb, 
        llm_client, 
        max_turns=args.max_turns,
        use_dynamic_planning=args.use_dynamic_planning
    )
    
    # 运行生成
    async def run():
        async with llm_client:
            # 阶段1：批量生成
            results = await generate_batch_with_monitoring(
                agent,
                args.output,
                batch_size=args.batch_size,
                total=args.total
            )
            
            # 阶段2：兜底（可选）
            if args.enable_fallback:
                additional = await ensure_full_coverage(
                    agent,
                    args.output,
                    target_coverage=args.target_coverage
                )
                results.extend(additional)
            
            # 生成报告
            if args.use_dynamic_planning:
                stats = agent.kb.get_usage_stats()
                report = {
                    'total_generated': len([r for r in results if r is not None]),
                    'coverage_stats': stats,
                    'optimization_enabled': True
                }
                
                report_file = os.path.join(args.output, 'generation_report.json')
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                print(f"\n[REPORT] 生成报告已保存: {report_file}")
                print(f"\n最终统计:")
                print(f"  - 总生成: {report['total_generated']}")
                print(f"  - 论文覆盖率: {stats['overall_coverage']*100:.1f}%")
                print(f"  - 已完成论文: {stats['completed_papers']}/{stats['total_papers']}")
        
        return results
    
    print(f"\n{'='*60}")
    print(f"[INFO] 开始生成...")
    if args.use_dynamic_planning:
        print(f"[INFO] ✓ 启用动态规划策略")
        print(f"[INFO] ✓ 启用消耗追踪系统")
    if args.enable_fallback:
        print(f"[INFO] ✓ 启用兜底机制（目标覆盖率: {args.target_coverage*100}%）")
    print(f"{'='*60}\n")
    
    results = asyncio.run(run())
    
    print(f"\n{'='*60}")
    print(f"[DONE] 所有结果已保存到: {args.output}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()