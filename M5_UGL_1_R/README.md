# M5_UGL_1_R ✅

**概述**

M5_UGL_1_R 包含用于模拟店铺库存与交易的工具与示例（TinyDB 存储演示），以及用于生成演示数据的脚本。

**主要文件**

- `demo.py` — 演示脚本，调用 agents / utils 展示工作流。
- `inv_utils.py` — TinyDB 的库存与事务种子、schema 辅助函数（`create_inventory`, `seed_db`, `build_schema_block` 等）。
- `utils.py` — 可视化与 HTML 打印（与其他模块共享样式）。
- `store_db.json` — 示例 TinyDB 存储文件。

**运行与使用**

- 在交互式环境或脚本中调用 `inv_utils.seed_db()` 来创建示例数据。
- `build_schema_block()` 帮助生成供 LLM 使用的架构说明块（便于自动化 SQL/查询生成）。

**注意事项**

- TinyDB 是轻量 JSON 存储，适合演示和测试；生产系统请选用更可靠的数据库。