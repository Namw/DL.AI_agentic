import json
import os
import utils
import pandas as pd
from dotenv import load_dotenv
import aisuite as ai

_ = load_dotenv()
# dashscope_api_key = os.getenv("DEEPSEEK_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
client = ai.Client(provider_configs={"google": {"api_key": gemini_api_key}})
# utils.create_transactions_db()
# res = utils.get_schema('products.db')
# print(res)

def generate_sql(question: str, schema: str, model: str) -> str:
    prompt = f"""
    你是一名 SQL 助理。根据给定的数据库架构与用户问题，编写适用于 SQLite 的 SQL 查询。

    架构：
    {schema}

    用户问题：
    {question}

    不要增加这个条件：AND qty_delta > 0
    仅返回 SQL 语句。
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content.strip()

# 我们将架构以字符串形式提供
schema = """
表名: transactions
id (INTEGER)
product_id (INTEGER)
product_name (TEXT)
brand (TEXT)
category (TEXT)
color (TEXT)
action (TEXT)
qty_delta (INTEGER)
unit_price (REAL)
notes (TEXT)
ts (DATETIME)
"""

def refine_sql_external_feedback(
    question: str,
    sql_query: str,
    df_feedback: pd.DataFrame,
    schema: str,
    schema_dec: str,
    model: str,
) -> tuple[str, str]:
    """
    评估 SQL 结果是否回答用户问题；如有必要，提出改进版查询。
    返回 (feedback, refined_sql)。
    """
    prompt = f"""
    你是一位 SQL 审查与优化专家。

    用户问题：
    {question}

    原始 SQL：
    {sql_query}

    SQL 输出：
    {df_feedback.to_markdown(index=False)}

    表架构：
    {schema}

    表架构的字段描述：
    {schema_dec}

    步骤 1：简要评估该 SQL 输出是否回答了用户问题。
    步骤 2：若可改进，请提供优化后的 SQL 查询。
    若原始 SQL 已正确，请保持不变返回。

    请严格返回仅包含以下两个字段的 JSON 对象：
    - "feedback": 简短评估与建议
    - "refined_sql": 需要执行的最终 SQL
    """

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )

    print(f"\n prompt: {prompt} \n")
    content = response.choices[0].message.content
    content = content.strip('```json\n').strip('\n```')
    try:
        obj = json.loads(content)
        feedback = str(obj.get("feedback", "")).strip()
        refined_sql = str(obj.get("refined_sql", sql_query)).strip()
        if not refined_sql:
            refined_sql = sql_query
    except Exception:
        # 若模型未返回有效 JSON 的回退处理：
        # 使用原始内容作为反馈并保留原始 SQL
        feedback = content.strip()
        refined_sql = sql_query

    return feedback, refined_sql

question = "哪种颜色的产品总销售额最高？"
# model="deepseek:deepseek-chat"
model="google:gemini-1.5-flash"
# --- V1 ---
# 我们用自然语言提出关于数据的问题
sql_V1 = generate_sql(question, schema, model)
df_sql_V1 = utils.execute_sql(sql_V1, db_path='products.db')
print("\nV1 版本SQL:")
print(sql_V1)
print("\nV1 数据:")
print(df_sql_V1.to_markdown(index=False))

# --- 反馈与 V2 ---
# 使用外部反馈进行评估与改进
schema_dec = """
• id → 事件的唯一 ID（自增）。
• product_id、product_name、brand、category、color → 用于标识产品。
• action → 事件类型（insert、restock、sale、price_update）。
• qty_delta → 库存变化（插入/补货为 +，销售为 –，价格更新为 0）。
• unit_price → 当时价格（补货为 NULL）。
• notes → 事件的可选描述。
• ts → 记录事件时的时间戳。
"""
feedback, sql_V2 = refine_sql_external_feedback(
    question=question,
    sql_query=sql_V1,   # V1 查询
    df_feedback=df_sql_V1,    # V1 的输出
    schema=schema,
    schema_dec=schema_dec,
    model=model
)
df_sql_V2 = utils.execute_sql(sql_V2, db_path='products.db')
print(f"feedback: {feedback}")
print("\nV2 版本SQL:")
print(sql_V2)
print("\nV2 数据:")
print(df_sql_V2.to_markdown(index=False))
