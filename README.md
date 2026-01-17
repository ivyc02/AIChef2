# AIChef - Intelligent Recipe Assistant

AIChef is a Retrieval-Augmented Generation (RAG) system that combines vector search with a Large Language Model (LLM) to provide personalized, context-aware recipe recommendations.

## Technical Summary

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Uvicorn
- **AI/RAG**: ChromaDB (Vector Store), OpenAI-compatible APIs (SiliconFlow/DeepSeek)
- **Key Capabilities**: Semantic search, recipe deduplication, context-aware chat, and user preference tracking.

## Installation & Setup

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: **Version 18** (Crucial for frontend compatibility)
- **Package Manager**: npm (included with Node.js)

### 1. Environment Setup (Node.js v18)

This project requires **Node.js version 18**. If you are using `nvm` (Node Version Manager), run the following commands in your terminal to ensure you are on the correct version:

```bash
# Install Node.js v18
nvm install 18

# Switch to Node.js v18
nvm use 18

# Verify version (should output v18.x.x)
node -v
```

> **Note**: If `nvm use 18` fails on Windows, try running your terminal as Administrator.

### 2. Backend Setup

1.  Create a `.env` file in the project root (same level as this README) with your API credentials:
    ```env
    SILICONFLOW_API_KEY=your_api_key
    SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
    SILICONFLOW_MODEL_NAME=your_model_name
    ```

2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the backend:
    ```bash
    # From project root
    python run.py
    ```

### 3. Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies and start the server:
    ```bash
    # Ensure you are using Node 18
    npm install
    npm run dev
    ```

3.  Open the website in your browser.

## Quick Start (Windows)

A `start.bat` script is included for convenience. Ensure you have installed the prerequisites above first.

1.  Double-click `start.bat`.
2.  The script will launch both the backend and frontend services.