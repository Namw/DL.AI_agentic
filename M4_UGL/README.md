# M4_UGL ✅

**概述**

M4_UGL 包含研究相关的工具与示例，侧重于学术检索与网页检索的“工具式”封装（arXiv、Tavily、Wikipedia）。

**主要文件**

- `4-5Demo.py` — 演示脚本（示例入口）。
- `research_tools.py` — 提供：`arxiv_search_tool`, `tavily_search_tool`, `wikipedia_search_tool`，适配为 LLM 工具（返回 JSON/列表）。
- `utils.py` — 链接提取、域名评估、结果评估等实用函数（如 `evaluate_tavily_results`、`extract_urls`、`evaluate_anytext_against_domains` 等）。
- `store_db.json` — 示例存储文件（演示用）。
- `images/` — 存放演示生成的图片。

**运行与使用**

1. 准备环境变量（如需使用 Tavily/其他 API）：
   - `TAVILY_API_KEY`、`DLAI_TAVILY_BASE_URL`（若使用自定义 base_url）。
2. 调用示例（交互式/脚本）：
   - 直接运行演示脚本：
     ```bash
     python M4_UGL/4-5Demo.py
     ```
3. `research_tools.py` 中的函数可直接被 LLM 绑定使用（已提供 tool 定义字典）。

**注意事项**

- 调用外部 API 时请确保设置好对应的环境变量。
- `utils.py` 中包含若干评估与清洗函数，可用于对 LLM 返回结果做可靠性检查。