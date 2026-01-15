import uvicorn
import webbrowser
import os
import sys
import pandas as pd
import sqlite3
import io
import socket
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from threading import Timer
from test_agent import SQLAutoAgent

# --- 打包資源路徑修復 (PyInstaller 必備) ---
def resource_path(relative_path):
    """ 獲取資源絕對路徑，兼容開發環境與 PyInstaller 打包環境 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

app = FastAPI()

# 開啟跨域支持
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
    db_name = "uploaded_data.db"
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
        
        # 欄位名稱清理
        df.columns = [str(c).strip().replace(' ', '_').replace('\n', '') for c in df.columns]
        
        conn = sqlite3.connect(db_name)
        df.to_sql('data_table', conn, if_exists='replace', index=False)
        conn.close()
        return {"status": "success", "db_path": db_name}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
    # 使用 resource_path 確保打包後能找到 html
    return FileResponse(resource_path("index.html"))

@app.get("/wechat_qr.jpg")
async def get_qr():
    # 使用 resource_path 確保打包後能找到圖片
    return FileResponse(resource_path("wechat_qr.jpg"))

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
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
    
    # 在 1.5 秒後自動開啟瀏覽器
    Timer(1.5, open_browser).start()
    
    # 監聽 0.0.0.0 以支持外部設備訪問
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_config=None)