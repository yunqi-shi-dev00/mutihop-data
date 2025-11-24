"""
测试质量筛选功能
用于验证 evaluate_overall_quality 函数是否正常工作
"""

import json
from utils import evaluate_overall_quality


def test_quality_evaluation():
    """测试质量评估函数"""
    
    print("="*80)
    print("测试质量评估函数")
    print("="*80)
    print()
    
    # 测试用例
    test_cases = [
        {
            "name": "高质量QA（3跳，答案长）",
            "result": {
                "uid": "test-1",
                "question": "在氧化物薄膜晶体管中，如何通过调控氧分压实现高迁移率和稳定性？",
                "answer": "在氧化物薄膜晶体管（TFT）制备过程中，氧分压是影响器件性能的关键工艺参数。首先，氧分压直接决定了氧化物薄膜中的氧空位浓度。当氧分压较低时，薄膜中形成较多氧空位，这些氧空位作为施主缺陷，增加自由载流子（电子）浓度，从而提高载流子迁移率。其次，适当的氧空位浓度可以优化载流子输运特性，使得电子更容易在晶粒间跳跃，减少散射，进一步提升迁移率。然而，过多的氧空位会导致载流子浓度过高，引起阈值电压负移和亚阈值特性恶化，影响器件的开关性能和稳定性。因此，需要通过精确控制氧分压，在氧空位浓度和器件稳定性之间找到最佳平衡点，实现高迁移率和良好稳定性的统一。",
                "final_qa_count": 3,
                "num_turns": 8,
                "statements": ["陈述1", "陈述2", "陈述3"],
                "edit_history": ["编辑1", "编辑2", "编辑3", "编辑4"]
            },
            "expected": "high"
        },
        {
            "name": "中等质量QA（2跳，答案中等）",
            "result": {
                "uid": "test-2",
                "question": "IGZO薄膜晶体管的迁移率为何高于a-Si TFT？",
                "answer": "IGZO（铟镓锌氧化物）薄膜晶体管相比非晶硅（a-Si）TFT具有更高的载流子迁移率，主要原因在于其电子传输机制的差异。在IGZO中，电子主要通过金属阳离子（In、Ga、Zn）的重叠s轨道传输，这种传输方式对薄膜的结构无序性不敏感，因此即使在非晶态下也能保持较高的电子迁移率。",
                "final_qa_count": 2,
                "num_turns": 5,
                "statements": ["陈述1", "陈述2"],
                "edit_history": ["编辑1", "编辑2", "编辑3"]
            },
            "expected": "medium"
        },
        {
            "name": "低质量QA（1跳，答案短）",
            "result": {
                "uid": "test-3",
                "question": "什么是TFT？",
                "answer": "薄膜晶体管。",
                "final_qa_count": 1,
                "num_turns": 2,
                "statements": ["陈述1"],
                "edit_history": ["编辑1"]
            },
            "expected": "low"
        },
        {
            "name": "边界案例（4跳但答案极短）",
            "result": {
                "uid": "test-4",
                "question": "如何优化OLED显示器的TFT背板？",
                "answer": "通过调控工艺参数。",
                "final_qa_count": 4,
                "num_turns": 12,
                "statements": ["陈述1", "陈述2", "陈述3", "陈述4"],
                "edit_history": ["编辑1", "编辑2", "编辑3", "编辑4", "编辑5"]
            },
            "expected": "medium"  # 虽然4跳，但答案太短
        }
    ]
    
    # 运行测试
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        name = test_case["name"]
        result = test_case["result"]
        expected = test_case["expected"]
        
        # 评估质量
        actual = evaluate_overall_quality(result)
        
        # 显示详细信息
        print(f"测试 {i}: {name}")
        print(f"  问题: {result['question'][:50]}...")
        print(f"  答案长度: {len(result['answer'])} 字符")
        print(f"  多跳数量: {result['final_qa_count']}")
        print(f"  轮数: {result['num_turns']}")
        print(f"  期望质量: {expected}")
        print(f"  实际质量: {actual}")
        
        # 检查结果
        if actual == expected:
            print(f"  ✅ 通过")
            passed += 1
        else:
            print(f"  ❌ 失败")
            failed += 1
        
        print()
    
    # 总结
    print("="*80)
    print(f"测试总结: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    print("="*80)
    print()
    
    return passed == len(test_cases)


def test_quality_filter_logic():
    """测试质量筛选逻辑"""
    
    print("="*80)
    print("测试质量筛选逻辑")
    print("="*80)
    print()
    
    # 模拟生成结果
    mock_results = [
        {"uid": "1", "final_qa_count": 3, "answer": "A" * 250, "question": "Q" * 60, "num_turns": 5, "statements": ["S1", "S2"], "edit_history": ["E1", "E2", "E3"]},  # high
        {"uid": "2", "final_qa_count": 2, "answer": "A" * 150, "question": "Q" * 50, "num_turns": 6, "statements": ["S1", "S2"], "edit_history": ["E1", "E2", "E3"]},  # medium
        {"uid": "3", "final_qa_count": 1, "answer": "A" * 50, "question": "Q" * 30, "num_turns": 3, "statements": ["S1"], "edit_history": ["E1"]},  # low
        {"uid": "4", "final_qa_count": 4, "answer": "A" * 300, "question": "Q" * 70, "num_turns": 8, "statements": ["S1", "S2", "S3"], "edit_history": ["E1", "E2", "E3", "E4"]},  # high
        {"uid": "5", "final_qa_count": 2, "answer": "A" * 100, "question": "Q" * 40, "num_turns": 4, "statements": ["S1"], "edit_history": ["E1", "E2"]},  # medium
    ]
    
    # 测试不同的quality_filter
    filters = ['high', 'medium+', 'all']
    
    for quality_filter in filters:
        print(f"质量过滤器: {quality_filter}")
        
        qualified = []
        for result in mock_results:
            quality = evaluate_overall_quality(result)
            
            # 筛选逻辑（和 generate_batch_with_quality_filter 一致）
            is_qualified = False
            if quality_filter == 'high' and quality == 'high':
                is_qualified = True
            elif quality_filter == 'medium+' and quality in ['high', 'medium']:
                is_qualified = True
            elif quality_filter == 'all':
                is_qualified = True
            
            if is_qualified:
                qualified.append(result)
        
        print(f"  输入: {len(mock_results)} 个QA")
        print(f"  输出: {len(qualified)} 个QA")
        print(f"  筛选率: {len(qualified)/len(mock_results)*100:.1f}%")
        print()
    
    print("="*80)
    print()


if __name__ == "__main__":
    print()
    print("🧪 质量筛选功能测试")
    print()
    
    # 测试1: 质量评估函数
    test1_pass = test_quality_evaluation()
    
    # 测试2: 筛选逻辑
    test_quality_filter_logic()
    
    # 总结
    if test1_pass:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查 evaluate_overall_quality 函数")
