from langchain_openai import ChatOpenAI
from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
import re
import ast

# 初始化客户端 (使用 LangChain 统一接口)
llm = None

# 1. 优先检查 SiliconFlow / DeepSeek (OpenAI 兼容接口)
if LLM_API_KEY:
    print(f"✅ 使用 SiliconFlow/DeepSeek API (model: {LLM_MODEL_NAME})")
    llm = ChatOpenAI(
        model=LLM_MODEL_NAME,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0.7
    )
else:
    print("⚠️ 未配置 SiliconFlow API Key，生成功能将不可用。")

class MockResponse:
    def __init__(self, content):
        self.content = content

def safe_invoke(messages):
    """
    统一的 LLM 调用封装
    """
    if not llm:
        return MockResponse("🤖 (未配置 API Key，请查看下方菜谱)")

    try:
        # 直接调用配置好的 LLM
        return llm.invoke(messages)
    except Exception as e:
        print(f"❌ [SafeInvoke] LLM 调用失败: {e}")
        return MockResponse("🤖 (AI 服务暂时不可用，请检查 API Key 或网络)")

def smart_select_and_comment(query: str, candidates: list):
    """
    智能优选 Rerank (灵活版)
    不再死板过滤，而是侧重于“推荐 + 建议”
    """
    if not llm:
        return 0, "API Key 未配置，默认推荐："
    
    if not candidates:
        return 0, "没有候选菜谱。"

    # 1. 构建候选列表
    candidates_str = ""
    for i, doc in enumerate(candidates):
        snippet = doc.get('content', '')[:150].replace('\n', ' ')
        candidates_str += (
            f"选项[{i}]: {doc.get('name')}\n"
            f"   - 标签: {doc.get('tags', [])}\n"
            f"   - 简介: {snippet}...\n\n"
        )

    # =====================================================
    # ✅ 优化后的 Prompt：更像一个懂得变通的大厨
    # =====================================================
    system_prompt = """
    你是一位聪明、幽默且懂变通的私家大厨。你的任务是从给定的候选菜谱中，为用户推荐**最合适**的一道。

    【推荐逻辑】：
    1. **找最大公约数**：优先选择食材、口味最接近用户需求的菜。
    2. **借壳上市 (Bridging) - 核心能力**：
       - 如果推荐的菜谱缺少用户手里的某个食材，**必须**在理由里建议用户“在第几步加进去”。
       - 例如：用户有“玉米”，但你推荐了《牛肉丸汤》（原谱没玉米），请说：“虽然原谱没写，但我强烈建议您在煮丸子时把玉米粒加进去，增加清甜口感。”
    3. **幽默处理离谱搭配**：
       - 如果用户给出了离谱的搭配（例如“西瓜炒牛肉”），请**不要**强行推荐。
       - 请用**幽默**的语气吐槽，并给出合理的烹饪理由（如“强扭的瓜不甜”）。
    4. **灵活处理忌口**：
       - 如果用户说“不要辣”，但候选项全都有辣，**不要拒绝回答！** 请选一个最容易“去辣”的菜，并告诉用户怎么改（如“把辣椒油换成香油”）。

    【输出格式】：
    - 请直接返回一行：索引数字 ||| 推荐理由
    - **严禁使用 Emoji**。
    - 理由要简短（50字以内）。
    """

    user_prompt = f"""
    用户需求：【{query}】

    候选列表：
    {candidates_str}

    请做出你的选择：
    """

    try:
        # LangChain 调用
        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
        
        response_msg = safe_invoke(messages)
        content = response_msg.content
        
        # --- 增强解析逻辑 ---
        # 1. 如果是列表 (Multipart)，拼接
        if isinstance(content, list):
             content = " ".join([str(c) for c in content])
        
        # 2. 如果是字典 (或类似结构)，尝试提取 text
        if isinstance(content, dict):
            content = content.get('text', str(content))
            
        # 3. 如果是字符串但看起来像字典 (Stringified Dict)
        content = str(content).strip()
        if content.startswith("{") and "text" in content:
            try:
                val = ast.literal_eval(content)
                if isinstance(val, dict) and 'text' in val:
                    content = val['text']
            except:
                pass # 解析失败就保留原样

        content = str(content).strip()

        # print(f"🤖 [Generator] AI 建议: {content}") 

        # --- 解析逻辑 (保持鲁棒性) ---
        if "|||" in content:
            index_part, reason = content.split("|||", 1)
            match = re.search(r'\d+', index_part)
            if match:
                return int(match.group()), reason.strip()
        
        # 兜底：如果 AI 直接说了数字开头
        match = re.search(r'^\d+', content)
        if match:
             return int(match.group()), f"为您推荐【{candidates[int(match.group())]['name']}】"

        # 彻底无法解析
        return 0, f"试试这道【{candidates[0]['name']}】，应该不错！"

    except Exception as e:
        print(f"❌ [Generator] 报错: {e}")
        return 0, "为您推荐以下菜谱："

def generate_rag_answer(query: str, candidates: list) -> str:
    """
    为搜索结果列表生成一段 "厨师顾问" 风格的综述
    """
    if not llm:
        return "🤖 AI 厨师正在休息（未配置 API Key），请直接查看下方菜谱。"
        
    if not candidates:
        return "抱歉，没有找到相关菜谱，我也很难为您提供建议。"

    # 1. 简要构建候选信息
    candidates_summary = ""
    for i, doc in enumerate(candidates[:5]):
        candidates_summary += f"- {doc.get('name')} (标签: {doc.get('tags')})\n"

    system_prompt = """
    你是一位高端家庭餐厅的主厨顾问，性格幽默风趣。用户的需求可能只是几个食材名。
    你的任务是根据搜索到的菜谱列表，给用户一段**专业、优雅且得体**的开场建议。
    
    【核心任务】：
    1.  **语气**：专业且幽默，但**严禁使用 Emoji**。
    2.  **总结亮点**：概括推荐菜品的特色。
    3.  **主动桥接 (Bridging)**：
        - 仔细对比【用户想吃的】和【搜索到的】。
        - 如果搜到的菜谱**缺少**用户提到的某个食材（比如用户有“青豆”，但搜到的菜里没有），请务必在生成的内容里**建议用户把它加进去**。
        - 话术示例：“虽然库里的《牛肉丸汤》没写青豆，但我建议您出锅前撒一把青豆，颜色更漂亮，口感也更丰富。”
    4.  **幽默排雷**：
        - 遇到黑暗料理组合（如“巧克力炖蒜”），必须先幽默吐槽（基于烹饪原理），再推荐正常菜谱。
        - 话术示例：“大蒜配巧克力...除非是为了驱赶吸血鬼，否则我建议咱们还是分开吃吧。”
    5.  **字数**：控制在 100 字以内。
    """

    
    user_prompt = f"""
    用户想吃/有的食材：【{query}】
    搜索到的菜谱：
    {candidates_summary}

    请给用户一段简短的高级感推荐语：
    """

    try:
        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
        
        response = safe_invoke(messages)
        content = response.content
        
         # --- 增强解析逻辑 ---
        if isinstance(content, list):
             content = " ".join([str(c) for c in content])
             
        if isinstance(content, dict):
            content = content.get('text', str(content))

        content = str(content).strip()
        
        # 处理 Stringified Dict (例如 SiliconFlow/DeepSeek 偶尔返回的格式)
        if content.startswith("{") and "text" in content:
            try:
                import ast
                val = ast.literal_eval(content)
                if isinstance(val, dict) and 'text' in val:
                    content = val['text']
            except:
                pass

        print(f"✅ AI 响应内容: {content[:50]}...")
        return content
            
    except Exception as e:
        print(f"❌ [Generator] Summary 报错: {e}")
        return f"基于您的食材偏好，我为您甄选了以下几道值得尝试的美味佳肴。"
