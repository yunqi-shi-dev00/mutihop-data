#!/usr/bin/env python3
"""
快速修复 key_concepts 错误的脚本
错误: sequence item 0: expected str instance, dict found
"""

fix_content = '''
# ========== 修复1：SemiconductorQAEntity.repr() 方法 ==========

# 位置：knowledge_base_new.py 约第418行
# 找到 class SemiconductorQAEntity 中的 repr() 方法

def repr(self):
    """生成实体的文本表示"""
    # ⭐ 修复：兼容字典和字符串两种格式
    if self.key_concepts:
        # 如果第一个元素是字符串
        if isinstance(self.key_concepts[0], str):
            concepts_str = ', '.join(self.key_concepts)
        # 如果第一个元素是字典（新格式：{"name": "...", "type": "..."}）
        elif isinstance(self.key_concepts[0], dict):
            concepts_str = ', '.join([c.get('name', str(c)) for c in self.key_concepts])
        else:
            # 其他情况，转为字符串
            concepts_str = ', '.join([str(c) for c in self.key_concepts])
    else:
        concepts_str = '待提取'
        
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


# ========== 修复2：确保 dict() 方法也兼容 ==========

# 位置：knowledge_base_new.py 约第460行
# 在 class SemiconductorQAEntity 中的 dict() 方法

def dict(self):
    # ⭐ 确保 key_concepts 是字符串列表
    if self.key_concepts and isinstance(self.key_concepts[0], dict):
        key_concepts_str = [c.get('name', str(c)) for c in self.key_concepts]
    else:
        key_concepts_str = self.key_concepts
    
    return {
        'id': self.id,
        'name': self.name,
        'url': self.url,
        'qa_data': self.qa_data,
        'summary': self.summary,
        'key_concepts': key_concepts_str,  # 使用转换后的
        'related_qas': self.related_qas
    }
'''

print("=" * 60)
print("修复方法：key_concepts 错误")
print("=" * 60)
print()
print("错误信息：")
print("  [ERROR] 构建基础QA失败: sequence item 0: expected str instance, dict found")
print()
print("原因：")
print("  - extract_key_concepts 返回的是字典列表")
print("  - 但 repr() 方法中使用 ', '.join() 期望字符串列表")
print()
print("=" * 60)
print("修复代码：")
print("=" * 60)
print(fix_content)
print()
print("=" * 60)
print("修改文件：knowledge_base_new.py")
print("修改位置：")
print("  1. class SemiconductorQAEntity 的 repr() 方法（约第418行）")
print("  2. class SemiconductorQAEntity 的 dict() 方法（约第460行）")
print("=" * 60)
