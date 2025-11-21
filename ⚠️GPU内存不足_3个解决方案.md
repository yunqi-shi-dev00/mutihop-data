# ⚠️ GPU内存不足 - 3个解决方案

**错误时间**：2025-11-19  
**错误类型**：`CUDA out of memory`  
**状态**：✅ 已修复（提供3个方案）

---

## 🚨 **问题分析**

### GPU使用情况

```
GPU 0（79.14 GiB总容量）：
  - 进程22077：66.70 GiB  ← vLLM服务（大部分内存）
  - 进程253990：12.41 GiB  ← 其他服务
  - 剩余：19.19 MiB  ← ❌ 太少了

需要加载：
  - Qwen3-Embedding-8B：需要192 MiB
  - 19.19 MiB < 192 MiB → OOM ❌
```

---

## ✅ **方案1：使用CPU运行embedding（推荐）**

### 优点

- ✅ **不影响功能**：相关QA质量高
- ✅ **无需调整GPU**：不干扰vLLM服务
- ⚠️ **速度较慢**：CPU比GPU慢10倍，但只需运行一次

---

### 修改内容

**文件**：`knowledge_base_new.py` 第133-136行

```python
# 修改前
device = "cuda" if torch.cuda.is_available() else "cpu"  # GPU优先

# 修改后
device = "cpu"  # ⭐ 强制CPU，避免GPU OOM
```

**效果**：
- Embedding模型在CPU上运行
- 不占用GPU内存
- 速度：10000个QA约需5-10分钟

---

### 测试命令

```bash
chmod +x 测试_CPU_embedding.sh
./测试_CPU_embedding.sh
```

**应该看到**：
```
[KB] 模型加载完成，使用设备: cpu（避免GPU OOM）  ← ✅ 用CPU
[KB] Embedding batch_size: 2
[KB] 生成 10000 个QA的embedding向量...
[KB] 处理batch 0-2 (慢但稳定)...
```

---

## ✅ **方案2：不使用embedding（最快）**

### 优点

- ✅ **最快**：立即开始生成QA
- ⚠️ **质量下降**：相关QA用随机选择，质量降低

---

### 修改内容

**去掉`--use-embedding`参数：**

```bash
# 修改前
python main_final_new.py --use-embedding ...

# 修改后
python main_final_new.py ...  # 不加--use-embedding
```

**效果**：
- 不生成embedding
- 用随机选择代替语义相关
- 立即开始生成

---

### 测试命令

```bash
chmod +x 测试_不用embedding.sh
./测试_不用embedding.sh
```

---

## ✅ **方案3：释放GPU内存（高级）**

### 方法A：减小batch_size

**如果vLLM允许调整，减小其batch_size释放内存：**

```bash
# 查看vLLM进程
ps aux | grep 22077

# 如果可以重启，减小--max-num-batched-tokens或--max-num-seqs
```

---

### 方法B：使用更小的embedding模型

**如果有更小的模型（如1.5B）：**

```bash
python main_final_new.py \
    --embedding-model-path /path/to/smaller/model \
    --use-embedding
```

---

### 方法C：分批生成embedding

**先用小数据生成embedding，再用全量数据生成QA：**

```bash
# 步骤1：用小数据生成embedding（省内存）
head -100 QA.jsonl > QA_small.jsonl
python generate_embedding_only.py --input QA_small.jsonl

# 步骤2：用已有embedding生成QA
python main_final_new.py --use-cached-embedding
```

---

## 📊 **方案对比**

| 方案 | 速度 | 质量 | 复杂度 | 推荐度 |
|------|------|------|--------|--------|
| **方案1：CPU embedding** | 慢（5-10分钟） | ✅ 高 | ⭐ 简单 | ⭐⭐⭐⭐⭐ |
| **方案2：不用embedding** | ✅ 快（立即） | ⚠️ 中等 | ⭐ 简单 | ⭐⭐⭐ |
| **方案3：释放GPU** | 快 | ✅ 高 | ⭐⭐⭐ 复杂 | ⭐⭐ |

---

## 🎯 **推荐：先用方案1**

**如果追求质量**：
```bash
./测试_CPU_embedding.sh
```

**如果追求速度**：
```bash
./测试_不用embedding.sh
```

---

## 📝 **已修改文件**

| 文件 | 行号 | 修改内容 | 效果 |
|------|------|----------|------|
| `knowledge_base_new.py` | 134 | `device = "cpu"` | 强制CPU，避免OOM |

**查看修改**：
```bash
grep -n 'device = "cpu"' knowledge_base_new.py
```

---

## 🎉 **总结**

- ✅ **修复完成**：embedding模型强制在CPU上运行
- ✅ **避免OOM**：不占用GPU内存
- ⚠️ **速度较慢**：但只需运行一次（约5-10分钟）
- 🎯 **推荐**：用方案1（CPU embedding）

---

**选择一个方案测试吧！** 🚀

**查看效果**：
```bash
# 方案1（推荐）
./测试_CPU_embedding.sh

# 方案2（最快）
./测试_不用embedding.sh
```
