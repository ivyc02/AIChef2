import os
from dotenv import load_dotenv

# 1. 自动加载 .env 文件
# 获取项目根目录 (AIChef/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# 2. 数据库配置
# ⚠️ 注意：请去 data 文件夹确认你的数据库文件夹叫什么名字
# 如果是 chroma_db_baai 就写这个，如果是 chroma_db_v3 就改一下
DB_PATH = os.path.join(ROOT_DIR, "data", "chroma_db_baai")
DB_PATH_V3 = os.path.join(ROOT_DIR, "data", "chroma_db_v3")
COLLECTION_NAME = "recipe_collection_v3"

# Embedding 模型 (用于检索)
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
# 强制使用国内镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 3. 大模型配置 (支持 SiliconFlow 或 Google Gemini)
# 优先读取 SiliconFlow，如果没有则尝试读取 Gemini
LLM_API_KEY = os.getenv("SILICONFLOW_API_KEY")
LLM_BASE_URL = os.getenv("SILICONFLOW_BASE_URL")
LLM_MODEL_NAME = (os.getenv("SILICONFLOW_MODEL_NAME") or "").split("#")[0].strip()
IMAGE_MODEL_NAME = os.getenv("SILICONFLOW_IMAGE_MODEL", "Qwen/Qwen-Image").strip()



# 简单检查
if not LLM_API_KEY:
    print("⚠️ 警告: 未检测到 SiliconFlow API 配置，生成功能将无法使用。")