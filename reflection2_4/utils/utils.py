# === Standard Library ===
import os
import re
import mimetypes
import base64

# === Third-Party ===
import pandas as pd
from dotenv import load_dotenv
import dashscope
from dashscope import Generation
from dashscope import MultiModalConversation
from dotenv import load_dotenv

# === Env & Clients ===
load_dotenv()
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")

# Initialize clients lazily or with dummy values to avoid immediate errors
openai_client = None
anthropic_client = None

# === Data Loading ===
def load_and_prepare_data(csv_path: str) -> pd.DataFrame:
    """Load CSV and derive date parts commonly used in charts."""
    df = pd.read_csv(csv_path)
    # Be tolerant if 'date' exists
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["quarter"] = df["date"].dt.quarter
        df["month"] = df["date"].dt.month
        df["year"] = df["date"].dt.year
    return df

def ensure_execute_python_tags(text: str) -> str:
    """Normalize code to be wrapped in <execute_python>...</execute_python>."""
    text = text.strip()
    # Strip ```python fences if present
    text = re.sub(r"^```(?:python)?\s*|\s*```$", "", text).strip()
    if "<execute_python>" not in text:
        text = f"<execute_python>\n{text}\n</execute_python>"
    return text

def encode_image_b64(path: str) -> tuple[str, str]:
    """Return (media_type, base64_str) for an image file path."""
    mime, _ = mimetypes.guess_type(path)
    media_type = mime or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return media_type, b64

def get_qwen_response(model: str, prompt: str) -> str:
    """调用阿里千问模型获取响应"""       
    try:
        response = Generation.call(
            model=model,
            prompt=prompt,
            api_key=dashscope_api_key
        )
        
        if response.status_code == 200:
            return response.output.text
        else:
            return f"错误: 千问 API 调用失败，状态码: {response.status_code}, 错误: {response.message}"
    except Exception as e:
        return f"错误: 调用千问模型时发生异常: {str(e)}"

def image_ali_call_qwen_vl(model_name: str, prompt: str, media_type: str, b64: str) -> str:
    """
    阿里百炼 qwen-vl-plus 版本
    使用DashScope原生SDK
    """
    # 构建Data URL
    data_url = f"data:{media_type};base64,{b64}"
    
    # 构建消息
    messages = [
        {
            "role": "user",
            "content": [
                {"image": data_url},  # 直接使用data URL
                {"text": prompt}
            ]
        }
    ]
    
    try:
        # 调用模型
        response = MultiModalConversation.call(
            model=model_name,  # 例如: 'qwen-vl-plus'
            messages=messages,
            api_key=dashscope_api_key,
            max_tokens=2048,  # 可选参数
            temperature=0.7   # 可选参数
        )
        
        # 检查响应状态
        if response.status_code == 200:
            # return response.output.choices[0].message.content.strip()
            return response.output.choices[0].message.content[0]["text"]
        else:
            return f"Error: {response.code} - {response.message}"
            
    except Exception as e:
        return f"API调用失败: {str(e)}"