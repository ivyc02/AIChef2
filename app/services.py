import json
import difflib
import json
import difflib
import time
from typing import Optional
from .models import RecipeStep, RecipeResponse, RecipeListResponse
from core.retriever import retrieve_docs
# ✅ 引入新的优选函数
from core.generator import smart_select_and_comment, generate_rag_answer, generate_food_image, refine_prompt_with_llm 
from langchain_openai import ChatOpenAI
from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME

class RecipeService:
    def __init__(self):
        # 初始化 LLM 客户端
        self.llm = None
        if LLM_API_KEY:
            self.llm = ChatOpenAI(model=LLM_MODEL_NAME, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0.7)

    def get_recipe_response(self, query: str) -> Optional[RecipeResponse]:
        print(f"🔍 [Service] 用户搜索: {query}")
        
        # 1. 【扩大召回】从数据库拿 Top 3，而不是 Top 1
        # 这样即使向量检索把最佳结果排在了第 2 或 第 3，AI 也能把它捞回来
        candidates = retrieve_docs(query, top_k=6)
        
        # 2. 【AI 优选】让大模型来挑，并生成推荐语
        # 返回值: (选中的索引, 推荐语)
        selected_index, ai_message = smart_select_and_comment(query, candidates)
        
        # 确保索引不越界 (防止 AI 瞎返回 "index: 99")
        if selected_index < 0 or selected_index >= len(candidates):
            selected_index = 0
            
        # 3. 锁定最终的最佳菜谱
        best_match = candidates[selected_index]
        print(f"🎯 [Service] AI 选中了第 {selected_index} 项: {best_match['name']}")


        # === 数据清洗与解析 ===
        raw_instructions = best_match.get('instructions', [])
        if isinstance(raw_instructions, str):
            try: raw_instructions = json.loads(raw_instructions)
            except: raw_instructions = []

        raw_tags = best_match.get('tags', [])
        if isinstance(raw_tags, str):
            try: raw_tags = json.loads(raw_tags)
            except: raw_tags = []

        formatted_steps = []
        for idx, step in enumerate(raw_instructions):
            img_link = step.get('image_url') or step.get('imgLink')
            if not img_link or img_link == "null": img_link = None
            
            formatted_steps.append(
                RecipeStep(
                    step_index=idx + 1,
                    description=step.get('description', ''),
                    image_url=img_link
                )
            )

        # === 核心修改：强制现场生成一张，因为数据库里的图不可用 ===
        # cover_image = best_match.get('image') # 忽略旧图
        
        # 构造Prompt: 菜名 + 标签
        # gen_prompt = f"{best_match.get('name', '')}, {','.join(raw_tags)}"
         
        # LLM 优化
        refined_prompt = refine_prompt_with_llm(best_match.get('name', ''), raw_tags)
        generated_url = generate_food_image(refined_prompt, is_refined=True)
        
        if generated_url:
            cover_image = generated_url
        else:
            # 兜底：如果生图失败，暂时还是返回 None (或者原来的图，看需求)
            cover_image = None
                 # TODO: 这里应该异步把 cover_image 存回数据库，避免每次都生成
                 # 为了演示方便，暂时只返回给前端显示

        return RecipeResponse(
            recipe_id=str(best_match.get('id', 'unknown')),
            recipe_name=best_match.get('name', '未命名'),
            tags=raw_tags,
            cover_image=cover_image,
            steps=formatted_steps,
            message=ai_message # 这里是 AI 针对选中菜谱写的推荐语
        )

    def _optimize_query(self, query: str, refinement: str) -> str:
        """
        利用 LLM 根据用户反馈优化搜索词
        """
        if not self.llm or not refinement:
            return query
            
        system_prompt = """
        你是一个搜索关键词优化助手。用户正在搜索菜谱，并给出了一些补充调整意见。
        请根据用户的初始搜索词和补充意见，重写一个更精准的搜索关键词。
        
        【规则】
        1. 输出**仅**包含新的搜索词，不要有任何解释。
        2. 如果用户说“不要辣”，新词可以包含“清淡”或“不辣”。
        3. 保持简短精炼。
        """
        
        user_prompt = f"初始搜索词：{query}\n用户补充意见：{refinement}\n\n请重写搜索词："
        
        try:
             from langchain_core.messages import SystemMessage, HumanMessage
             response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
             ])
             new_query = response.content.strip()
             print(f"🔄 [Service] 搜索词优化: '{query}' + '{refinement}' -> '{new_query}'")
             return new_query
        except Exception as e:
            print(f"⚠️ Query optimization failed: {e}")
            return query

    def get_recipe_list_response(self, query: str, limit: int = 5, refinement: str = None, preferences: dict = None) -> Optional[RecipeListResponse]:
        """
        获取多个菜谱推荐列表 (支持去重 + 上下文改进 + 用户偏好过滤)
        """
        # 1. 如果有改进意见，先优化搜索词
        search_query = query
        if refinement:
            search_query = self._optimize_query(query, refinement)
            
        print(f"🔍 [Service] 执行搜索: {search_query}, 目标数量: {limit}, 原始Query: {query}, 偏好: {preferences}")
        
        # 2. 扩大召回 (为了去重，且保证数量够，我们取 3 倍)
        # 此时传入 user preferences 进行底层过滤
        candidates = retrieve_docs(search_query, top_k=limit * 3, preferences=preferences)
        if not candidates:
            # 如果优化后的词搜不到，尝试回退到原始词
            if search_query != query:
                print("⚠️ 优化后的词无结果，回退到原始搜索词...")
                candidates = retrieve_docs(query, top_k=limit * 3)
                
            if not candidates:
                return None
            
        # 3. 去重与格式化
        formatted_list = []
        seen_names = [] # 存 (name, id) 用于比较

        def is_similar(name1, name2):
            # 简单去空格小写比较
            n1 = name1.strip().lower()
            n2 = name2.strip().lower()
            if n1 == n2: return True
            #由于菜谱名称往往较短，只要包含关系或相似度高都算重复
            if n1 in n2 or n2 in n1: return True
            return difflib.SequenceMatcher(None, n1, n2).ratio() > 0.8

        for doc in candidates:
            # 如果已经够数了，停止处理
            if len(formatted_list) >= limit:
                break
                
            recipe_name = doc.get('name', '未命名')
            
            # 检查重复
            is_dup = False
            for existing_name in seen_names:
                if is_similar(recipe_name, existing_name):
                    is_dup = True
                    break
            
            if is_dup:
                continue
                
            seen_names.append(recipe_name)
            
            # --- 数据清洗 (保持原有逻辑) ---
            raw_instructions = doc.get('instructions', [])
            if isinstance(raw_instructions, str):
                try: raw_instructions = json.loads(raw_instructions)
                except: raw_instructions = []

            raw_tags = doc.get('tags', [])
            if isinstance(raw_tags, str):
                try: raw_tags = json.loads(raw_tags)
                except: raw_tags = []

            # 格式化步骤
            formatted_steps = []
            for idx, step in enumerate(raw_instructions):
                img_link = step.get('image_url') or step.get('imgLink')
                if not img_link or img_link == "null": img_link = None
                
                formatted_steps.append(
                    RecipeStep(
                        step_index=idx + 1,
                        description=step.get('description', ''),
                        image_url=img_link
                    )
                )
            
            # 此处稍微调整得更有 AI 味一点
            ai_comment = f"匹配度 {int(doc.get('score', 0) * 100)}%"
            if refinement and "辣" in refinement and "辣" not in str(raw_tags):
                 ai_comment += " | 已为您筛选不辣的做法"

            formatted_list.append(
                RecipeResponse(
                    recipe_id=str(doc.get('id', 'unknown')),
                    recipe_name=recipe_name,
                    tags=raw_tags,
                    cover_image=None, # 强制置空，忽略数据库坏链，确保下方并发逻辑会为每个菜谱生图
                    steps=formatted_steps,
                    message=ai_comment 
                )
            )

        # === 4. 并行生成图片 (Parallel Image Generation) ===
        # === 4. 串行生成图片 + LLM 防幻觉优化 (Serial + Anti-Hallucination) ===
        # 针对免费模型：必须串行以防限流
        # 针对幻觉问题：先用 DeepSeek 写 Prompt
        
        for item in formatted_list:
            if not item.cover_image:
                # 1. LLM 优化 Prompt (防幻觉)
                print(f"🧠 [List] Refining prompt for: {item.recipe_name}...")
                refined_prompt = refine_prompt_with_llm(item.recipe_name, item.tags)
                
                # 2. 调用生图 (带重试)
                print(f"🎨 [List] Generating image (Serial)...")
                new_url = generate_food_image(refined_prompt, is_refined=True)
                
                if new_url:
                    item.cover_image = new_url
                
                # 3. 冷却防止限流
                time.sleep(1.5)

        # 4. 生成综述
        # 注意：这里传给 summarizer 的是原始 query (或者组合 query)，让 AI 知道用户意图
        user_intent = query
        if refinement:
            user_intent = f"{query} ({refinement})"
            
        list_summary = generate_rag_answer(user_intent, [
            {'name': c.recipe_name, 'tags': c.tags} for c in formatted_list
        ])

        return RecipeListResponse(
            candidates=formatted_list,
            ai_message=list_summary
        )

    def consult_chef(self, query: str, context: str, history: list) -> str:
        """
        AI 顾问交互接口
        """
        # 构建 prompt
        system_prompt = """
        你是一位高端家庭餐厅的主厨顾问。你的任务是根据当前的“搜索结果上下文”和“对话历史”，回答用户的追问。
        
        【要求】:
        1. 语气专业、优雅、幽默（参考之前的设定）。
        2. 如果用户想换口味，请基于列表里的其他菜推荐，或者给出烹饪建议。
        3. 字数控制在 100 字左右。
        """
        
        # 简单拼接历史
        history_str = "\n".join([f"{h['role']}: {h['content']}" for h in history[-4:]])

        user_prompt = f"""
        【当前菜谱列表上下文】：
        {context}

        【对话历史】：
        {history_str}

        【用户新问题】：
        {query}

        请主厨作答：
        """
        
        if not self.llm:
             return "👨‍🍳 抱歉，AI 厨师目前无法连接大脑 (API Key Missing)。"

        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            return response.content.strip()
        except Exception as e:
            print(f"Chat Error: {e}")
            return "👨‍🍳 抱歉，厨房太忙了，请稍后再试。"


recipe_service = RecipeService()


# import json  # <--- 1. 必须补上这个！
# from typing import Optional
# from .models import RecipeStep, RecipeResponse

# # ✅ 直接引入你在 core 里写好的检索函数
# from core.retriever import retrieve_docs
# from core.generator import generate_rag_answer

# class RecipeService:
#     def get_recipe_response(self, query: str) -> Optional[RecipeResponse]:
#         """
#         业务逻辑：
#         1. 检索 (Retrieve) -> 拿到 raw data
#         2. 生成 (Generate) -> 拿到 AI 推荐语
#         3. 清洗 (Parse) -> 拿到结构化步骤
#         4. 组装返回
#         """
#         print(f"🔍 [Service] 正在为用户搜索: {query}")
        
#         # 1. 检索
#         results = retrieve_docs(query, top_k=1)
        
#         if not results:
#             print("⚠️ [Service] 未找到匹配结果")
#             return None
            
#         best_match = results[0]
        
#         # # =======================================================
#         # # ✅ 2. 数据清洗：从 JSON 字符串还原回 List
#         # # =======================================================
        
#         # # --- 处理 Instructions ---
#         # raw_instructions = best_match.get('instructions', [])
#         # # 如果它是字符串 (因为 Chroma 存成了 string)，我们需要把它转回 list
#         # if isinstance(raw_instructions, str):
#         #     try:
#         #         raw_instructions = json.loads(raw_instructions)
#         #     except json.JSONDecodeError:
#         #         print("❌ 解析 instructions JSON 失败，使用空列表")
#         #         raw_instructions = []

#         # # --- 处理 Tags ---
#         # raw_tags = best_match.get('tags', [])
#         # if isinstance(raw_tags, str):
#         #     try:
#         #         raw_tags = json.loads(raw_tags)
#         #     except json.JSONDecodeError:
#         #         raw_tags = []

#         # # 3. 格式化步骤 (组装 Steps)
#         # formatted_steps = []
#         # for idx, step in enumerate(raw_instructions):
#         #     # 处理图片链接
#         #     img_link = step.get('imgLink')
#         #     if not img_link or img_link == "null":
#         #         img_link = None

#         #     formatted_steps.append(
#         #         RecipeStep(
#         #             step_index=idx + 1,
#         #             description=step.get('description', ''),
#         #             image_url=img_link
#         #         )
#         #     )

#         # # 4. 返回标准结构
#         # return RecipeResponse(
#         #     recipe_id=str(best_match.get('id', 'unknown')),
#         #     recipe_name=best_match.get('name', '未命名菜谱'),
            
#         #     # <--- 2. 这里要用解析好的 raw_tags，而不是原始的 best_match['tags']
#         #     tags=raw_tags, 
            
#         #     cover_image=best_match.get('image'),
#         #     steps=formatted_steps,
#         #     message=f"✨ 为您找到【{best_match.get('name')}】的最佳做法："
#         # )
#         # 2. 【核心新增】调用大模型生成推荐语 (Generator) - 稍微花点时间
#         # 把 query (用户想吃啥) 和 results (库里有啥) 传给 AI
#         # 注意：这会增加 API 的延迟（通常 1-2 秒），取决于模型速度
#         ai_message = generate_rag_answer(query, results)
        
#         # 3. 数据清洗 (保持不变)
#         raw_instructions = best_match.get('instructions', [])
#         if isinstance(raw_instructions, str):
#             try:
#                 raw_instructions = json.loads(raw_instructions)
#             except:
#                 raw_instructions = []

#         raw_tags = best_match.get('tags', [])
#         if isinstance(raw_tags, str):
#             try:
#                 raw_tags = json.loads(raw_tags)
#             except:
#                 raw_tags = []

#         formatted_steps = []
#         for idx, step in enumerate(raw_instructions):
#             img_link = step.get('imgLink')
#             if not img_link or img_link == "null":
#                 img_link = None
#             formatted_steps.append(
#                 RecipeStep(
#                     step_index=idx + 1,
#                     description=step.get('description', ''),
#                     image_url=img_link
#                 )
#             )

#         # 4. 组装返回
#         return RecipeResponse(
#             recipe_id=str(best_match.get('id', 'unknown')),
#             recipe_name=best_match.get('name', '未命名'),
#             tags=raw_tags,
#             cover_image=best_match.get('image'),
#             steps=formatted_steps,
            
#             # ✅ 这里填入 AI 生成的话！
#             message=ai_message
#         )
# # 创建单例实例
# recipe_service = RecipeService()