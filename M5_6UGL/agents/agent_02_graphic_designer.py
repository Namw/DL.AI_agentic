import os
import re
import json
import utils 
import requests
from pathlib import Path  # 推荐使用Pathlib，更现代
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
from http import HTTPStatus
from dashscope import ImageSynthesis
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

def graphic_designer_agent(trend_insights: str, save_dir: Path, caption_style: str = "short punchy", size: str = "1024x1024") -> dict:

    """
    使用 aisuite 生成营销提示/文案，并直接使用 OpenAI 生成图像。

    参数：
        trend_insights (str)：来自调研智能体的趋势摘要。
        caption_style (str)：文案的可选风格提示。
        size (str)：图像分辨率（例如 '1024x1024'）。

    返回：
        dict：包含 image_url、prompt 与 caption 的字典。
    """

    utils.log_agent_title_html("平面设计智能体", "🎨")

    # 步骤 1: 使用 aisuite 生成提示和文案
    system_message = (
        "你是一名视觉营销助理。根据输入的趋势洞见，"
        "为 AI 图像生成模型编写一个中文版本的有创意的视觉提示，并生成一段简短文案。"
    )

    user_prompt = f"""
趋势洞见：
{trend_insights}

请输出：
1. 一段生动、具描述性的提示，用于引导图像生成。
2. 一句营销文案，风格：{caption_style}。

按如下格式回应：
{{"prompt": "...", "caption": "..."}}
"""
    # --- 初始化 LangChain 模型 ---
    qwen_api_key = os.getenv("DASHSCOPE_API_KEY")
    llm = ChatOpenAI(
        model="qwen-plus",
        api_key=qwen_api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.2
    )
    # 初始化消息列表，使用 LangChain 的 HumanMessage
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_prompt)
    ]
    
    # 使用 LangChain 的 llm.invoke() 替代旧的 client.chat 接口
    response = llm.invoke(messages)

    # 提取文本内容并解析出 JSON
    content = response.content.strip() if hasattr(response, "content") else str(response).strip()
    match = re.search(r'\{.*\}', content, re.DOTALL)
    parsed = json.loads(match.group(0)) if match else {"error": "No JSON returned", "raw": content}

    prompt = parsed["prompt"]
    caption = parsed["caption"]
    # 记录结果
    utils.log_final_summary_html(f"""
        <h3>文案模型生成给图片模型的提示词：</h3>
        <p><strong>提示：</strong> {prompt}</p>
    """)

    image_response = ImageSynthesis.call(
        api_key=qwen_api_key,
        model="qwen-image-plus",
        prompt=prompt,
        negative_prompt=" ",
        n=1,
        size='1024*1024',
        prompt_extend=True,
        watermark=False
    )

    print(f'response: {image_response}')
    if image_response.status_code == HTTPStatus.OK:
        # 创建保存目录
        save_dir.mkdir(parents=True, exist_ok=True)  # exist_ok=True 确保不重复创建时报错
        image_url = image_response.output.results[0].url
        file_name = PurePosixPath(unquote(urlparse(image_url).path)).parts[-1]
        save_path = save_dir / file_name
        print("=" * 120)
        print(f"图片地址：{image_url}")

        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()  # 检查HTTP错误
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"图片已保存: {save_path}")
        except Exception as e:
            print(f"下载失败: {e}")
    else:
        print(f'同步调用失败, status_code: {image_response.status_code}, code: {image_response.code}, message: {image_response.message}')

    return {
        "image_url": image_url,
        "prompt": prompt,
        "caption": caption,
        "image_path": str(save_path)
    }