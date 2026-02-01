import os
import re
import json
import utils 
import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

def copywriter_agent(image_path: str, trend_summary: str) -> dict:

    """
    使用 aisuite（仅 OpenAI）发送图像与趋势摘要并返回活动短句。

    参数：
        image_path (str)：待分析图像的路径。
        trend_summary (str)：来自调研智能体的文本。

    返回：
        dict: {
            "quote": "...",
            "justification": "...",
            "image_path": "..."
        }
    """

    utils.log_agent_title_html("文案智能体", "✍️")

    # 步骤 1: 加载本地图像并编码为 base64
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    b64_img = base64.b64encode(img_bytes).decode("utf-8")

    # 步骤 2: 构建兼容 OpenAI 的多模态消息
    user_prompt = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64_img}"}
        },
        {
            "type": "text",
            "text": f"""
以下为一个视觉营销图像与趋势分析：

趋势摘要：
\"\"\"{trend_summary}\"\"\"

请返回如下 JSON 对象：
{{
  "quote": "简短、优雅的活动短句（最多 12 个词）",
  "justification": "为何该短句契合该图像与趋势"
}}"""
        }
    ]
    messages = [
        SystemMessage(content=("你是一名文案撰写者，基于图像与市场趋势摘要创作优雅的活动短句。")),
        HumanMessage(content=user_prompt)
    ]

    # 创建ChatOpenAI实例，配置阿里云参数
    chat = ChatOpenAI(
        model="qwen3-vl-plus",
        openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    response = chat.invoke(messages)

    # 步骤 4: 解析 JSON 响应
    content = response.content.strip()

    utils.log_final_summary_html(content)

    try:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        parsed = json.loads(match.group(0)) if match else {"error": "No valid JSON returned"}
    except Exception as e:
        parsed = {"error": f"Failed to parse: {e}", "raw": content}


    parsed["image_path"] = image_path
    return parsed