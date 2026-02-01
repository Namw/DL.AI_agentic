# deeplearningAgent01 🧠✨

**项目概述**

这是一个以“研究工具 + 数据分析/可视化 + 市场活动自动化” 为主题的示例工程。主要功能模块包括：

- 研究工具（arXiv / 网页 / Wikipedia）用于支持学术或市场研究；
- 自动化数据可视化与“反思”流程（生成 matplotlib 代码、评审并改进）；
- 市场活动流水线（市场调研 → AI 图像 → 文案 → 打包报告）；
- 多个演示脚本与示例数据（SQLite、TinyDB、CSV）。

---

## 目录结构（要点）

- `M4_UGL/` — 研究工具与 demo
- `M5_6UGL/` — 市场调研与营销资产生成流水线（含 `agents/`）
- `M5_UGL_1_R/` — 库存/店铺演示（TinyDB）
- `reflection2_4/` — 可视化 + print_html HTTP 服务
- `useExternal2_7/` — 示例 SQLite 事件溯源 DB 与 LLM 驱动的 SQL 生成
- `resource/` — 示例 CSV 数据（`coffee_sales.csv`）

（各子模块均包含单独的 `README.md`，请查看相应目录了解详细说明）

---

## 快速开始 ⚡

1. 克隆并进入项目目录

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 设置必要的环境变量（视功能而定）：
   - `DASHSCOPE_API_KEY` (qwen / 图像)
   - `TAVILY_API_KEY` (网页搜索)
   - `DEEPSEEK_API_KEY` / `GEMINI_API_KEY` / `ZHIPUAI_API_KEY` / `ARK_API_KEY`（视模块需要）

4. 运行示例：
   - 市场流水线（演示 agents）：
     ```bash
     python M5_6UGL/market_research_pipeline.py
     ```
   - 启动 print_html HTTP 服务器：
     ```bash
     python reflection2_4/run_html_server.py -p 8080
     ```
   - 生成示例 SQLite 数据库：
     ```python
     from useExternal2_7 import utils
     utils.create_transactions_db(db_name='products.db')
     ```

---

## 贡献与说明

- 代码以教学/示例为主；若用于生产请注意安全、配额与密钥管理。
- 许多流程依赖外部模型/服务（请确保配置好密钥并查看相应文件内的注释）。

---

若需要，我可以：
- 为每个模块添加更详细的用例或运行脚本；
- 增加 CI 测试或简单的自动化任务（例如 `make` / `tox`）。

感谢！
