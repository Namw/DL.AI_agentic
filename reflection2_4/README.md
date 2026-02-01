# reflection2_4 ✅

**概述**

reflection2_4 侧重于数据可视化的生成与“反思”机制：基于自动生成的 matplotlib 代码绘图、评审图像并用 LLM 给出改进建议，还包括一个轻量的 `print_html` HTTP 展示服务。

**主要文件**

- `coffee_sales.py` / `coffee_salesv2.py` — 演示：自动生成绘图代码、执行并保存图表，v2 支持对图像与原始代码的反思与改进。
- `run_html_server.py` — 启动 `print_html` 的 HTTP 服务器 (8080 默认)。
- `utils/html_server.py` — 实现 HTML 渲染与 HTTP handler，用于生成可交互的预览页面。
- `utils/utils.py` — 辅助函数（数据加载、编码、调用 LLM 的封装等）。

**运行与使用**

- 启动 web 服务器：
  ```bash
  python reflection2_4/run_html_server.py -p 8080
  ```
- 可用 `coffee_sales.py` 自动生成图表、将结果导出为 HTML 预览。

**注意事项**

- `coffee_sales` 模块假设 `resource/coffee_sales.csv` 可用并且格式符合预期（说明见 `resource/README.md`）。
- 若使用 Qwen 等多模态模型，需要配置相应环境变量（例如 `DASHSCOPE_API_KEY`）。