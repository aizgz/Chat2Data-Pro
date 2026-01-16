import uvicorn
import webbrowser
import os
import sys
import pandas as pd
import sqlite3
import io
import socket
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from threading import Timer
from test_agent import SQLAutoAgent

# --- 全局配置 ---
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
            df = pd.read_excel(file_copy)
        else:
            return {"status": "error", "message": f"不支持 {ext} 格式"}
        
        # 欄位清理：去掉空格和換行，防止 SQL 語法錯誤
        df.columns = [str(c).strip().replace(' ', '_').replace('\n', '') for c in df.columns]
        
        conn = sqlite3.connect(DB_NAME)
        df.to_sql('data_table', conn, if_exists='replace', index=False)
        conn.close()
        return {"status": "success", "db_path": DB_NAME}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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

        # 使用 SQLAutoAgent 生成 3 個智能建議
        agent = SQLAutoAgent(api_key, base_url, model_name, DB_NAME)
        prompt = f"請根據以下數據結構，提出3個用戶最感興趣的分析問題（如趨勢、對比、統計）。要求：簡短、無需序號、每行一個問題。結構如下：\n{schema_info}"
        
        raw_res = agent.run(prompt)
        suggestions = [s.strip() for s in raw_res.split('\n') if len(s.strip()) > 5][:3]
        return {"suggestions": suggestions}
    except:
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

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def open_browser():
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    local_ip = get_host_ip()
    print(f"\n🚀 Chat2Data Pro 啟動成功！")
    print(f"🔗 本機訪問: http://127.0.0.1:8000")
    print(f"🌐 局域網訪問: http://{local_ip}:8000\n")
    Timer(1.5, open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)