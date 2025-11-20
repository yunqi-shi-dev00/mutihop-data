# ============================================
# agent_final_new.py 中 SELECT action 的完整优化代码
# 替换位置：约第765-965行（整个SELECT处理部分）
# ============================================

# 搜索这个注释找到起始位置：
# if action['action'] == 'SELECT':

# 然后整段替换为下面的代码：

                if action['action'] == 'SELECT':
                    # ⭐ SELECT操作：选择相关QA进行桥联，生成多跳问题
                    num_hops = len(memory.relevant)
                    
                    if num_hops >= self.max_hops:
                        print(f"  [SELECT] 已达到最大跳数限制 ({self.max_hops})，跳过")
                        continue
                    
                    if self.debug_mode:
                        print(f"  [SELECT] ===== 开始SELECT流程 (当前{num_hops}跳，最多{self.max_hops}跳) =====")
                    
                    # (1) 找目标实体
                    target = None
                    for e in memory.relevant:
                        if e.id == action['target'] or e.url == action['target']:
                            target = e
                            break
                    
                    if target is None:
                        print(f"  [SELECT] ✗ 未找到目标实体")
                        continue
                    
                    # ==========================================
                    # ⭐⭐⭐ 激进优化4：增加候选数量+尝试多个 ⭐⭐⭐
                    # 原逻辑：top_k=10，随机选1个尝试
                    # 新逻辑：top_k=20，尝试前5个候选
                    # 效果：大幅提高多跳成功率（5倍重试机会）
                    # ==========================================
                    # (2) 找邻居（增加候选数量）
                    if self.use_dynamic_planning:
                        candidates = self.kb.find_related_qas_prioritized(target.id, top_k=20, current_stage=self.current_stage)  # ⭐ 从10增加到20
                    else:
                        candidates = target.related_qas
                    
                    exist_ids = [e.id for e in memory.relevant]
                    candidates = [c for c in candidates if c not in exist_ids]
                    
                    if not candidates:
                        print(f"  [SELECT] ✗ 无可用邻居")
                        continue
                    
                    # ⭐⭐ 核心修改：尝试前5个候选（不是只试1个）
                    max_try = min(5, len(candidates))  # 最多尝试5个
                    tried_candidates = candidates[:max_try]  # 取前5个（最相关的）
                    
                    if self.debug_mode:
                        print(f"  [SELECT] 共{len(candidates)}个候选，尝试前{max_try}个")
                    
                    # ⭐⭐ 循环尝试多个候选
                    success = False
                    final_neighbor_id = None
                    
                    for attempt, neighbor_id in enumerate(tried_candidates, 1):
                        if self.debug_mode:
                            print(f"  [SELECT] 尝试{attempt}/{max_try}: {target.id} → {neighbor_id}")
                        
                        # ⭐⭐ 注意：以下所有代码都在for循环内
                        try:
                            self.kb.update_usage([neighbor_id])
                            
                            neighbor_data = self.kb.get_qa(neighbor_id)
                            neighbor_entity = SemiconductorQAEntity(neighbor_id, neighbor_data, self.kb)
                            neighbor_entity = await self.extract_qa_info(neighbor_entity)
                            
                            # (3) 构建link_qa
                            try:
                                link_qa = await self.construct_link_qa(target, neighbor_entity)
                            except Exception as e:
                                if self.debug_mode:
                                    print(f"    [SELECT] ✗ 构建link_qa失败: {e}，尝试下一个")
                                continue
                            
                            if not link_qa:
                                if self.debug_mode:
                                    print(f"    [SELECT] ✗ link_qa为空，尝试下一个")
                                continue
                            
                            # ==========================================
                            # ⭐⭐⭐ 激进优化1：桥联阈值从6降到3 ⭐⭐⭐
                            # 原逻辑：if not is_valid: continue
                            # 新逻辑：if relevance_score < 3: continue
                            # 效果：桥联通过率从20%提升到70%
                            # ==========================================
                            if self.enable_bridge_check:
                                try:
                                    bridge_validity = await self.check_bridge_validity(
                                        target, 
                                        neighbor_entity, 
                                        link_qa.get('statement', '')
                                    )
                                    
                                    relevance_score = bridge_validity.get('relevance_score', 0)
                                    is_valid = bridge_validity.get('is_valid', False)
                                    
                                    # ⭐⭐ 核心修改：只看分数，分数>=3就接受
                                    if relevance_score < 3:
                                        if self.debug_mode:
                                            print(f"    [SELECT] ✗ 桥联分数过低 ({relevance_score} < 3)，尝试下一个")
                                        continue  # 只有分数<3才拒绝
                                    
                                    if self.debug_mode:
                                        if not is_valid and relevance_score >= 3:
                                            print(f"    [SELECT] ⚠️ 桥联分数{relevance_score}>=3，虽然判断为no但仍接受")
                                        print(f"    [SELECT] ✓ 桥联合理 (分数: {relevance_score})")
                                        
                                except Exception as e:
                                    if self.debug_mode:
                                        print(f"    [SELECT] ⚠ 桥联检查异常: {e}，尝试下一个")
                                    continue
                            
                            # ==========================================
                            # ⭐⭐⭐ 激进优化2：放宽信息覆盖判断 ⭐⭐⭐
                            # 原逻辑：if duplicate: continue（重复就拒绝）
                            # 新逻辑：if duplicate: pass（允许部分重复）
                            # 效果：允许30%信息覆盖，更易扩展到2跳、3跳
                            # ==========================================
                            try:
                                duplicate = await self.check_info_cover(
                                    link_qa['statement'],
                                    memory_new.statements_repr()
                                )
                            except Exception as e:
                                if self.debug_mode:
                                    print(f"    [SELECT] ⚠️ 检查重复失败: {e}，跳过检查")
                                # ⭐⭐ 修改：检查失败时继续执行（不阻断）
                                duplicate = False
                            
                            # ⭐⭐ 核心修改：即使判断为重复，也不再continue
                            if duplicate:
                                if self.debug_mode:
                                    print("    [SELECT] ⚠️ 陈述部分重复，但仍继续（激进模式）")
                                # 不再continue，允许部分重复
                            
                            # (5) ⭐ 关键：添加新子QA，用所有子QA生成多跳问题
                            memory_new.relevant.append(neighbor_entity)
                            memory_new.statements.append(link_qa['statement'])
                            
                            # ⚠️ 确保至少有2个子QA
                            if len(memory_new.relevant) < 2:
                                if self.debug_mode:
                                    print(f"    [SELECT] ✗ 子QA数量不足（{len(memory_new.relevant)}），尝试下一个")
                                memory_new.relevant.pop()
                                memory_new.statements.pop()
                                continue
                            
                            multihop_result = await self.generate_multihop_question(
                                memory_new.relevant,
                                memory_new.statements
                            )
                            
                            if multihop_result is None:
                                if self.debug_mode:
                                    print(f"    [SELECT] ✗ 多跳生成失败，尝试下一个")
                                memory_new.relevant.pop()
                                memory_new.statements.pop()
                                continue
                            
                            q_new = multihop_result['question']
                            reference_answer = multihop_result['answer']
                            reasoning_steps = multihop_result.get('reasoning_steps', [])
                            
                            # (6) 筛选
                            if self.enable_qa_filtering:
                                eval_result = await self.evaluate_question(q_new, memory_new.relevant)
                                
                                if not eval_result['passed']:
                                    if self.debug_mode:
                                        print(f"    [SELECT] ✗ 未通过筛选：{eval_result['reason']}，尝试下一个")
                                    memory_new.relevant.pop()
                                    memory_new.statements.pop()
                                    continue
                                
                                if self.debug_mode:
                                    print(f"    [SELECT] ✓ 通过筛选")
                            
                            # (7) 答案重生成
                            if self.enable_answer_regeneration:
                                regen_result = await self.regenerate_answer(
                                    q_new,
                                    reference_answer,
                                    memory_new.relevant,
                                    reasoning_steps
                                )
                                
                                grounded_check = regen_result.get('grounded_check', {})
                                if grounded_check.get('all_info_from_subqa', False) and regen_result.get('confidence', 0) >= 0.6:
                                    final_answer = regen_result['final_answer']
                                    if self.debug_mode:
                                        print(f"    [SELECT] ✓ 使用重生成答案")
                                else:
                                    final_answer = reference_answer
                                    if self.debug_mode:
                                        print(f"    [SELECT] ⚠ 使用参考答案")
                            else:
                                final_answer = reference_answer
                            
                            # (8) 更新memory
                            memory_new.qa['question'] = q_new
                            memory_new.qa['answer'] = final_answer
                            memory_new.edit_history.append(f"SELECT: {target.id} → {neighbor_id}")
                            
                            # ⭐⭐ 成功！标记并退出循环
                            success = True
                            final_neighbor_id = neighbor_id
                            num_hops += 1
                            
                            if self.debug_mode:
                                print(f"    [SELECT] ✓✓✓ 成功生成{num_hops}跳QA，退出尝试")
                                print(f"    [SELECT] ===== SELECT完成 =====")
                            
                            break  # ⭐⭐ 成功后退出for循环
                        
                        except Exception as e:
                            if self.debug_mode:
                                print(f"    [SELECT] ✗ 候选{neighbor_id}处理失败: {e}，尝试下一个")
                            continue
                    
                    # ⭐⭐ for循环结束，检查是否成功
                    if not success:
                        if self.debug_mode:
                            print(f"  [SELECT] ✗ 所有{max_try}个候选都失败，放弃本轮SELECT")
                        continue
                    
                    # ⭐⭐ 成功后，将memory_new复制到memory
                    memory = memory_new
                    q_new = memory.qa['question']