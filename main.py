import uvicorn
import os
import sys
import pandas as pd
import sqlite3
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from test_agent import SQLAutoAgent

# --- 配置 ---
DB_NAME = "uploaded_data.db"

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    api_key: str
    base_url: str
    model_name: str
    db_path: str

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        file_copy = io.BytesIO(contents)
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext == '.csv':
            df = pd.read_csv(file_copy)
        elif ext in ['.xlsx', '.xls']:
            # 確保環境中已安裝 pip install openpyxl
            df = pd.read_excel(file_copy, engine='openpyxl')
        else:
            return {"status": "error", "message": f"不支持 {ext} 格式"}
        
        # 清理字段名：去除引號和空格，防止 SQL 注入與錯誤
        df.columns = [str(c).strip().replace(' ', '_').replace('"', '').replace("'", "") for c in df.columns]
        
        conn = sqlite3.connect(DB_NAME)
        df.to_sql('data_table', conn, if_exists='replace', index=False)
        conn.close()
        return {"status": "success", "db_path": DB_NAME}
    except Exception as e:
        return {"status": "error", "message": f"讀取失敗: {str(e)}"}

@app.get("/get_suggestions")
async def get_suggestions(api_key: str = "", base_url: str = "", model_name: str = ""):
    if not os.path.exists(DB_NAME):
        return {"suggestions": []}
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema_info = ""
        for table in tables:
            t_name = table[0]
            cursor.execute(f"PRAGMA table_info({t_name})")
            cols = [col[1] for col in cursor.fetchall()]
            schema_info += f"表名: {t_name}, 字段: {', '.join(cols)}\n"
        conn.close()

        agent = SQLAutoAgent(api_key, base_url, model_name, DB_NAME)
        prompt = f"根據結構提出3個數據分析問題。要求：簡短有力，每行一個，不要序號，直接返回問題文本。\n{schema_info}"
        raw_res = agent.run(prompt)
        # 過濾 AI 可能包含的廢話
        suggestions = [s.strip() for s in raw_res.split('\n') if len(s.strip()) > 4][:3]
        return {"suggestions": suggestions}
    except Exception as e:
        # 建議將異常捕獲寫為具體的 Exception，避免捕獲 SystemExit 等關鍵信號
        return {"suggestions": ["分析數據整體分布", "查詢數值最高項", "按類別匯總數據"]}

@app.post("/ask")
async def ask_database(request: QueryRequest):
    try:
        agent = SQLAutoAgent(request.api_key, request.base_url, request.model_name, request.db_path)
        result = agent.run(request.question)
        return {"status": "success", "answer": result}
    except Exception as e:
        return {"status": "error", "answer": str(e)}

@app.get("/")
async def serve_index():
    return FileResponse(resource_path("index.html"))

@app.get("/wechat_qr.jpg")
async def get_qr():
    return FileResponse(resource_path("wechat_qr.jpg"))

if __name__ == "__main__":
    # 云端环境不需要打开浏览器，直接打印监听地址
    print(f"🚀 Chat2Data Pro 已启动，正在监听容器内部端口: http://0.0.0.0:8244")
    
    # 启动 Uvicorn 服务，绑定到 0.0.0.0 允许外部访问
    uvicorn.run(app, host="0.0.0.0", port=8244, log_config=None)
