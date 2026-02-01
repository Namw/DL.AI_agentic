# M5_6UGL ✅

**概述**

M5_6UGL 包含一个市场调研到营销素材生成的流水线：调研智能体 → 平面设计（AI 图像）→ 文案 → 打包报告。代码组织成主流程、工具与多个智能体。

**主要文件/目录**

- `market_research_pipeline.py` — 调度示例：依次调用市场调研、图像生成、文案与打包智能体，演示完整流程。
- `tools.py` — 对外可用工具集合（供智能体调用）。
- `utils.py` — 日志、HTML 展示等共用工具。
- `inventory_utils.py` / `inventory_utils.py` — 库存/目录相关的工具（检查目录、匹配趋势）。
- `agents/` — 各智能体实现：
  - `agent_01_market_research.py`：市场调研智能体（调用 Tavily/内部目录）。
  - `agent_02_graphic_designer.py`：图像生成（使用图像生成 API），会把结果保存到 `agents/images/`。
  - `agent_03_copywriter.py`：图像 + 文案生成。
  - `agent_04_packaging.py`：将素材打包为 Markdown 报告。

**运行与使用**

1. 必需环境变量（示例）：
   - `DASHSCOPE_API_KEY`（用于 qwen / 图像接口）
   - 其它可能用到的模型/服务 key，例如 `DEEPSEEK_API_KEY` 等
2. 直接运行模拟管线：
   ```bash
   python M5_6UGL/market_research_pipeline.py
   ```
3. 图像将被保存在 `M5_6UGL/agents/images/`，打包结果如 `campaign_summary_*.md`。

**注意事项**

- 图像与多模态调用依赖外部 API，需配置好密钥并注意带宽/配额。
- 部分模块使用 LangChain 风格的模型绑定（bind_tools），请参考代码内注释以确保工具/模型兼容。