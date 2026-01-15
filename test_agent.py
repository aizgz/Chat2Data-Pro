import sqlite3
from openai import OpenAI

class SQLAutoAgent:
    def __init__(self, api_key, base_url, model_name, db_path):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        self.db_path = db_path

    def run_sql(self, sql):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            return {"columns": columns, "data": rows}
        except Exception as e:
            return {"error": str(e), "sql": sql}

    def get_schema(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        schema = cursor.fetchall()
        conn.close()
        return schema

    def run(self, question):
        schema = self.get_schema()
        
        # 1. 生成 SQL
        sql_prompt = f"""你是一個 SQLite 專家。表名 'data_table'，結構：{schema}
        要求：必須包含網址(URL)或連結的列。只輸出 SQL，不准有 Markdown 標籤。問題：{question}"""
        
        sql_res = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": sql_prompt}],
            temperature=0
        )
        sql = sql_res.choices[0].message.content.strip().replace('```sql', '').replace('```', '').split(';')[0]

        # 2. 獲取數據
        db_data = self.run_sql(sql)
        
        # 3. 深度分析並強制保留連結
        analysis_prompt = f"""
        你是一個資深數據分析師。
        數據庫結果：{db_data}
        用戶問題：{question}
        
        要求：
        1. 數據中如果包含百度網盤連結(pan.baidu.com)或提取碼，必須【完整展示】，嚴禁省略。
        2. 嚴禁提及技術細節。
        
        Markdown 格式：
        - 📊 **核心結論**
        - 🔍 **數據詳情（含完整連結）**
        - 💡 **專業洞察**
        - ⚠️ **建議**
        """
        
        final_res = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3
        )
        return final_res.choices[0].message.content