# 📊 Chat2Data Pro - AI 數據深度分析助理

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-v0.128-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/AI-DeepSeek/OpenAI-red.svg" alt="AI Engine">
</p>

**Chat2Data Pro** 是一款專為非技術人員設計的輕量級數據分析工具。只需「上傳表格」並「輸入問題」，AI 就會自動為你編寫 SQL 指令並解析數據內容。

---

## 🌟 核心特性

- 📁 **多格式支持**：流暢解析 `.xlsx`, `.xls`, `.csv` 數據文件。
- 🔍 **精準連結保護**：特別優化網盤連結、提取碼的識別，確保數據細節不被 AI 縮減。
- 🌍 **局域網訪問**：一鍵啟動後，同 Wi-Fi 下的手機或其他電腦可直接通過 IP 訪問。
- 🎨 **現代化界面**：簡潔的聊天氣泡設計，支持 Markdown 渲染（表格、清單、粗體）。
- 🔗 **便捷聯繫**：內嵌開發者微信二維碼，支持點擊號碼自動複製。

---

## 🛠️ 技術架構



- **Frontend**: HTML5, CSS3 (Modern Flexbox), JavaScript (Fetch API)
- **Backend**: Python, FastAPI, Uvicorn
- **Database**: SQLite3 (Dynamic temporary database)
- **AI Agent**: Custom SQL-Auto-Agent logic

---

## 🚀 快速開始

1. 克隆倉庫

git clone [https://github.com/aizgz/Chat2Data-Pro.git](https://github.com/aizgz/Chat2Data-Pro.git)
cd Chat2Data-Pro

2. 安裝依賴
python -m venv venv
source venv/bin/activate  # Windows 使用: venv\Scripts\activate
pip install -r requirements.txt

3. 啟動程序
python main.py

程序啟動後，瀏覽器將自動打開 http://127.0.0.1:8000。

💡 使用說明
配置 API：在網頁頂部輸入您的 OpenAI 或 DeepSeek 的 API Key 與 Base URL。

上傳數據：點擊上傳區域選擇您的數據文件。

對話分析：在輸入框輸入如「幫我找出所有網盤連結並列出對應的提取碼」即可。

👨‍💻 聯絡開發者
如果您有任何建議或合作意向，歡迎通過微信與我聯繫：

WeChat ID: 252500112


📄 開源協議
本项目基於 MIT License 協議開源。