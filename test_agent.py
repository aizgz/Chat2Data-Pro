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
        # 修改点：去掉了“必须包含网址”这种无法满足的硬性要求，改为“如果存在则包含”
        # 修改点：增加 max_tokens 防止截断
        sql_prompt = f"""你是一个SQLite专家。表名 'data_table'，结构：{schema}
        要求：
        1. 如果表中包含网址(URL)或链接的列，请一并查询出来，如果不存在则忽略，严禁捏造。
        2. 只输出 SQL，不准有 Markdown 标签，不要输出任何思考过程或解释。
        问题：{question}"""
        
        sql_res = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": sql_prompt}],
            temperature=0,
            max_tokens=2000  # 修复截断
        )
        # 清理 AI 返回的多余字符
        sql = sql_res.choices[0].message.content.strip().replace('```sql', '').replace('```', '').split(';')[0]

        # 2. 获取数据
        db_data = self.run_sql(sql)
        
        # 3. 深度分析
        # 修改点：明确禁止输出思考过程，直接输出最终报告
        analysis_prompt = f"""
        你是一位资深数据分析师。
        数据库查询结果：{db_data}
        用户问题：{question}
        
        要求：
        1. 严禁输出你的思考过程、严禁提及"嗯，我现在需要..."等废话。直接给出最终结果！
        2. 数据中如果包含百度网盘链接(pan.baidu.com)或提取码，必须【完整展示】，严禁省略。
        3. 严禁提及任何技术细节。
        
        请严格按照以下 Markdown 格式输出：
        - 📊 **核心结论**
        - 🔍 **数据详情（含完整链接）**
        - 💡 **专业洞察**
        - ⚠️ **建议**
        """
        
        final_res = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3,
            max_tokens=4000  # 修复截断，给最终报告留足空间
        )
        return final_res.choices[0].message.content
