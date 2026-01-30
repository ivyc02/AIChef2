from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 引入我们定义好的模型和服务
from .models import QueryRequest, RecipeResponse, RecipeListResponse, ConsultRequest
from .services import recipe_service

# 初始化 APP
app = FastAPI(
    title="AIChef RAG API",
    description="智能菜谱检索接口 - 返回包含步骤图的结构化数据",
    version="1.0.0"
)

# --- 数据库初始化 ---
from . import sql_models
from core.database import engine, SessionLocal, get_db
from sqlalchemy.orm import Session
from fastapi import Depends

# 自动创建表结构 (如果不存在)
sql_models.Base.metadata.create_all(bind=engine)

# 初始化默认用户 (方案 A)
def init_default_user():
    db = SessionLocal()
    try:
        user = db.query(sql_models.User).filter(sql_models.User.username == "default").first()
        if not user:
            default_user = sql_models.User(username="default", preferences={})
            db.add(default_user)
            db.commit()
            print("✅ Default user created.")
    except Exception as e:
        print(f"⚠️ Failed to init default user: {e}")
    finally:
        db.close()

init_default_user()

# --- 用户身份依赖 (User Dependency) ---
from fastapi import Header

def get_current_user(
    x_username: str = Header("default", alias="X-Username"), 
    db: Session = Depends(get_db)
):
    """
    根据请求头 X-Username 获取当前用户对象。
    如果用户不存在，则自动创建。
    """
    # 1. 尝试查找
    user = db.query(sql_models.User).filter(sql_models.User.username == x_username).first()
    
    # 2. 如果不存在，自动注册
    if not user:
        print(f"🆕 Creating new user: {x_username}")
        try:
            user = sql_models.User(username=x_username, preferences={})
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            # 防止并发创建冲突
            db.rollback()
            user = db.query(sql_models.User).filter(sql_models.User.username == x_username).first()
            if not user:
                raise HTTPException(status_code=500, detail="Failed to create user")
                
    return user

# --- 跨域配置 (CORS) ---
# 允许前端 (Vue/React/小程序) 访问接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请改为具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "AIChef API is running!"}

@app.post("/api/search", response_model=RecipeListResponse)
def search_recipe(
    request: QueryRequest, 
    current_user: sql_models.User = Depends(get_current_user) # 注入当前用户
):
    """
    🔍 核心搜索接口 - 支持返回列表
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="搜索词不能为空")

    # 获取当前用户的偏好
    user_prefs = current_user.preferences or {}
    print(f"👤 [Search] User: {current_user.username}, Prefs: {user_prefs}")

    result = recipe_service.get_recipe_list_response(
        request.query, 
        request.limit, 
        request.refinement,
        preferences=user_prefs
    )
    
    # 404 处理
    if not result or not result.candidates:
        raise HTTPException(
            status_code=404, 
            detail=f"抱歉，暂未收录关于“{request.query}”的菜谱，请尝试其他关键词。"
        )
    
    return result

@app.post("/api/consult")
def consult_chef_api(request: ConsultRequest):
    """
    AI 厨师交互接口
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    reply = recipe_service.consult_chef(request.query, request.context, request.history)
    return {"reply": reply}

from .models import UserProfile
# --- 用户相关接口 ---
@app.get("/api/user/profile")
def get_user_profile(user: sql_models.User = Depends(get_current_user)):
    """获取当前用户的配置"""
    return {"username": user.username, "preferences": user.preferences}

@app.post("/api/user/profile")
def update_user_profile(
    profile: UserProfile, 
    user: sql_models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """更新用户偏好设置"""
    
    # Update preferences
    if profile.preferences is not None:
         user.preferences = profile.preferences
    
    db.commit()
    db.refresh(user)
    return {"message": "Profile updated", "preferences": user.preferences}

# 仅用于直接调试 main.py 时使用
# 实际建议在根目录用 run.py 启动
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)