import os
import utils 
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

def packaging_agent(trend_summary: str, image_url: str, quote: str, justification: str, output_path: str = "campaign_summary.md") -> str:

    """
    将活动资产打包为精美的 Markdown 报告，供高管审阅。

    Args:
        trend_summary (str)：市场趋势摘要。
        image_url (str)：活动图像的 URL。
        quote (str)：需叠加的营销短句。
        justification (str)：短句的理由说明。
        output_path (str)：保存 Markdown 报告的路径。

    Returns:
        str：已保存的 Markdown 文件路径。
    """

    utils.log_agent_title_html("打包智能体", "📦")

    qwen_api_key = os.getenv("DASHSCOPE_API_KEY")
    llm = ChatOpenAI(
        model="qwen-plus",
        api_key=qwen_api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.2
    )
    human_trigger = (f"""
请将以下趋势摘要改写为清晰、专业且适合 CEO 受众的表达：

\"\"\"{trend_summary.strip()}\"\"\"
""")
    messages = [
        SystemMessage(content=("你是一名市场传播专家，为高管撰写优雅的活动总结。")),
        HumanMessage(content=human_trigger)
    ]
    response = llm.invoke(messages)

    beautified_summary = response.content.strip()

    utils.log_tool_result_html(beautified_summary)

    # 我们在 <img> 的 src 中使用此路径
    styled_image_html = f"""
    ![打开生成的文件查看]({image_url})
        """

    # 将所有部分合并为 markdown
    markdown_content = f"""# 🕶️ 夏季太阳镜活动 – 高管摘要

## 📊 精炼的趋势洞见
{beautified_summary}

## 🎯 活动视觉
{styled_image_html}

## ✍️ 活动短句
{quote.strip()}

## ✅ 原因说明
{justification.strip()}

---

*报告生成日期 {datetime.now().strftime('%Y-%m-%d')}*
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return output_path