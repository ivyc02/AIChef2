# AIChef - Intelligent Recipe Assistant

[English](#english) | [中文说明](#chinese)

<a name="english"></a>
## English Documentation

AIChef is an intelligent recipe recommendation system built with **RAG (Retrieval-Augmented Generation)** technology. It combines local vector search with Large Language Models (DeepSeek/Qwen) to provide personalized, context-aware cooking advice.

### Prerequisites

Before starting, please ensure your system meets the following requirements:

1.  **Node.js**: **Version 18** .
    *   Verify with: `node -v`
2.  **Python**: **Version 3.10+**.
    *   Verify with: `python --version`


---

### Option 1: One-Click Deployment (Windows Only)

If you are on Windows, we provide an automated script for quick startup.

1.  **Configure Environment**: Create a `.env` file in the `AIChef` directory and fill in your API Key (see Configuration Guide below).
2.  **Run Script**: Double-click the `start.bat` file in the project folder.
3.  **Automatic Setup**: The script will automatically:
    *   Create a Python virtual environment and install dependencies.
    *   Install Node.js dependencies for the frontend.
    *   **Simultaneously launch** the Backend (port 8000) and Frontend (port 5173).
4.  **Access**: Open the website in your browser, like `http://localhost:5173`.

---

### Option 2: Manual Installation

For Mac/Linux users or those who prefer the command line.

#### Step 1: Backend Setup

1.  **Navigate to project root**:
    ```bash
    cd AIChef
    ```

2.  **Configure Environment (.env)**:
    Create a `.env` file in this directory with the following content:
    ```ini
    # SiliconFlow / DeepSeek API (For Logic & Chat)
    SILICONFLOW_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
    # Cost-effective model for chat
    SILICONFLOW_MODEL_NAME=deepseek-ai/DeepSeek-V3.2
    
    # Image Generation Model
    SILICONFLOW_IMAGE_MODEL=Kwai-Kolors/Kolors
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start Backend**:
    ```bash
    python run.py
    ```

#### Step 2: Frontend Setup

1.  **Open a new terminal** (Keep the backend running).

2.  **Navigate to frontend**:
    ```bash
    cd frontend
    ```

3.  **Install Dependencies**:
    ```bash
    npm install
    ```

4.  **Start Frontend**:
    ```bash
    npm run dev
    ```

5.  **Access**:
    Open `http://localhost:5173` in your browser.

---

### Key Features

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS.
- **Backend**: FastAPI (High-performance async framework).
- **AI Core**:
    - **LLM**: DeepSeek-V3 / Qwen (Intent understanding, prompt engineering).
    - **Image**: Kwai-Kolors (Real-time high-quality food image generation).
    - **RAG**: ChromaDB Vector Search + BAAI Embedding.
- **Highlights**: Smart deduplication, Context-aware multi-turn chat, Automatic image generation, Offline caching.

### FAQ

- **Q: Why do images load slowly?**
  A: To ensure compatibility with free API tiers, distinct requests are processed serially (with a 1.5s delay) to avoid rate limiting.
- **Q: Error "Module not found"?**
  A: Ensure you are running frontend commands specifically inside the `frontend` directory.

---
<br/>

<a name="chinese"></a>
## 中文说明

AIChef 是一个基于 **RAG (检索增强生成)** 技术构建的智能菜谱推荐系统。它结合了本地向量检索与大语言模型 (DeepSeek/Qwen)，为您提供个性化、具有上下文感知能力的烹饪建议。

### 环境准备

在开始之前，请确保您的电脑已经安装了以下软件：

1.  **Node.js**: **版本 18** 
    *   验证命令: `node -v`
2.  **Python**: **版本 3.10+**。
    *   验证命令: `python --version`

---

### 方式一：Windows 一键极速部署 (推荐)

如果您使用的是 Windows 系统，我们为您准备了自动化脚本。

1.  **配置环境**: 在 `AIChef` 目录下创建一个名为 `.env` 的文件，填入您的 API Key（参考下方配置指南）。
2.  **双击运行**: 在文件夹中搜索并双击 `start.bat` 文件。
3.  **自动执行**: 脚本会自动完成以下操作：
    *   创建 Python 虚拟环境并安装依赖。
    *   进入前端目录安装 Node 依赖。
    *   **同时启动** 后端 (8000端口) 和 前端 (5173端口)。
4.  **访问**: 打开浏览器访问前端网页，如 `http://localhost:5173`。

---

### 方式二：终端手动安装教程

如果您习惯使用命令行，或者使用的是 Mac/Linux，请按照以下步骤操作。

#### 第一步：后端设置

1.  **进入项目目录**:
    ```bash
    cd AIChef
    ```

2.  **配置环境变量 (.env)**:
    在当前目录下新建 `.env` 文件，复制以下内容并修改：
    ```ini
    # SiliconFlow / DeepSeek API (用于对话和逻辑)
    SILICONFLOW_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
    # 免费/低成本对话模型
    SILICONFLOW_MODEL_NAME=deepseek-ai/DeepSeek-V3.2
    
    # 生图模型配置 (免费)
    SILICONFLOW_IMAGE_MODEL=Kwai-Kolors/Kolors
    ```

3.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **启动后端服务**:
    ```bash
    python run.py
    ```

#### 第二步：前端设置

1.  **打开一个新的终端窗口** (不要关闭后端的)。

2.  **进入前端目录**:
    ```bash
    cd frontend
    ```

3.  **安装 Node 依赖**:
    ```bash
    npm install
    ```
    *(如果下载慢，可以使用 cnpm 或配置 npm 镜像)*

4.  **启动前端服务**:
    ```bash
    npm run dev
    ```

5.  **访问项目**:
    打开浏览器访问前端网页，如 `http://localhost:5173`。

---

### 技术架构简述

- **前端**: React 18, Vite, TypeScript, Tailwind CSS。
- **后端**: FastAPI (高性能异步框架)。
- **AI 核心**:
    - **LLM**: DeepSeek-V3 / Qwen (负责理解意图、生成推荐语、优化 Prompt)。
    - **Image**: Kwai-Kolors (负责根据菜谱实时生成高清配图)。
    - **RAG**: ChromaDB 向量检索 + BAAI Embedding。
- **特性**: 智能去重、多轮对话上下文记忆、自动生图、离线缓存优化。

### 常见问题

- **Q: 为什么图片加载慢？**
  A: 为了保证免费且有图，系统采用了串行生图策略（每张间隔1.5秒）。这是为了防止触发免费 API 的限流机制。
- **Q: 报错 "Module not found"?**
  A: 请检查是否在错误的目录下运行了命令。前端命令必须在 `frontend` 文件夹下运行。
