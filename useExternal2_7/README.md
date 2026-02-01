# useExternal2_7 ✅

**概述**

useExternal2_7 提供基于事件溯源（`transactions` 表）的 SQLite 示例数据库生成、以及基于外部 LLM 的 SQL 生成与优化示例（通过 `improvSql.py`）。

**主要文件**

- `utils.py` — 提供 `create_transactions_db()`、`execute_sql()`、`get_schema()` 等工具，用于构建和查询示例 `products.db`（事件溯源风格）。
- `improvSql.py` — 演示：用 LLM（例：Gemini / aisuite）生成 SQL，再根据查询结果用 LLM 提出改进建议。
- `products.db` — 示例 SQLite 数据库（可由 `create_transactions_db()` 生成）。

**运行与使用**

1. 生成数据库：
   ```python
   from useExternal2_7 import utils
   utils.create_transactions_db(db_name='products.db', n_products=100, n_txns_per_product=50)
   ```
2. 使用 `improvSql.py` 演示 LLM 生成 SQL 的完整回路（需配置 `GEMINI_API_KEY` 或其它模型密钥）。

**注意事项**

- `execute_sql()` 仅执行 `SELECT` 查询以避免破坏性操作。
- LLM 调用需要外部模型 API key（示例中使用 `GEMINI_API_KEY` / aisuite）。