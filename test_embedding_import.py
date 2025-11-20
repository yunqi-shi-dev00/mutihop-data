#!/usr/bin/env python3
"""测试embedding依赖导入"""

print("=" * 60)
print("测试 sentence-transformers 导入")
print("=" * 60)

# 测试1: 导入sentence_transformers
print("\n[测试1] 导入 sentence_transformers...")
try:
    from sentence_transformers import SentenceTransformer
    print("✓ SentenceTransformer 导入成功")
except ImportError as e:
    print(f"✗ SentenceTransformer 导入失败: {e}")
except Exception as e:
    print(f"✗ 导入时出现其他错误: {e}")

# 测试2: 导入numpy
print("\n[测试2] 导入 numpy...")
try:
    import numpy as np
    print(f"✓ numpy 导入成功 (版本: {np.__version__})")
except ImportError as e:
    print(f"✗ numpy 导入失败: {e}")

# 测试3: 导入sklearn
print("\n[测试3] 导入 sklearn...")
try:
    from sklearn.metrics.pairwise import cosine_similarity
    print("✓ sklearn.metrics.pairwise.cosine_similarity 导入成功")
except ImportError as e:
    print(f"✗ sklearn 导入失败: {e}")
    print("   请安装: pip install scikit-learn")

# 测试4: 所有依赖一起导入
print("\n[测试4] 一次性导入所有依赖...")
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    print("✓ 所有依赖导入成功！")
    EMBEDDING_AVAILABLE = True
except Exception as e:
    print(f"✗ 导入失败: {e}")
    EMBEDDING_AVAILABLE = False

# 测试5: 测试加载模型
if EMBEDDING_AVAILABLE:
    print("\n[测试5] 尝试加载embedding模型...")
    try:
        print("   正在加载 all-MiniLM-L6-v2 模型（首次会下载）...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"✓ 模型加载成功")
        
        # 测试编码
        test_text = ["测试文本"]
        embedding = model.encode(test_text)
        print(f"✓ 编码测试成功 (向量维度: {embedding.shape[1]})")
    except Exception as e:
        print(f"✗ 模型加载失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
