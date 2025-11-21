"""
半导体QA生成系统 - 知识库模块
包含增强的知识库、QA实体类和Agent记忆类
"""

import random
from collections import defaultdict
from typing import Dict, List, Any


class EnhancedSemiconductorKB:
    """增强版知识库 - 原版功能 + 消耗追踪 + 动态规划"""
    
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
    
    # 🆕 新增：选择低使用率QA
    def select_underutilized_qa(self) -> str:
        """选择低使用率的论文中的QA"""
        # 获取使用率最低的论文
        low_usage_papers = [
            (paper, rate) for paper, rate in self.paper_usage_rate.items()
            if paper in self.active_papers
        ]
        
        if not low_usage_papers:
            return random.choice(self.qa_ids)
        
        low_usage_papers.sort(key=lambda x: x[1])
        selected_paper = low_usage_papers[0][0]
        
        return random.choice(self.paper_to_qas[selected_paper])
    
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
