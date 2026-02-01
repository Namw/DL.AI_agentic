import requests
import os
import json
from dotenv import load_dotenv
from tavily import TavilyClient
import pandas as pd

from inventory_utils import create_inventory_dataframe

# Session setup (optional)
session = requests.Session()
session.headers.update({
    "User-Agent": "LF-ADP-Agent/1.0 (mailto:your.email@example.com)"
})

load_dotenv()

# 🔧 TOOL IMPLEMENTATIONS

def tavily_search_tool(query: str, max_results: int = 5, include_images: bool = False) -> list[dict[str, str]]:
    
    params = {}
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables.")
    params['api_key'] = api_key

    #client = TavilyClient(api_key)

    api_base_url = os.getenv("DLAI_TAVILY_BASE_URL")
    if api_base_url:
        params['api_base_url'] = api_base_url

    client = TavilyClient(api_key=api_key, api_base_url=api_base_url)

    try:
        response = client.search(
            query=query,
            max_results=max_results,
            include_images=include_images
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "url": r.get("url", "")
            })

        if include_images:
            for img_url in response.get("images", []):
                results.append({"image_url": img_url})

        return results

    except Exception as e:
        return [{"error": str(e)}]
    

def product_catalog_tool(max_items: int = 10) -> list[dict[str, str]]:
    inventory_df = create_inventory_dataframe()
    return inventory_df.head(max_items).to_dict(orient="records")


# 🧠 TOOL METADATA FOR LLM

def get_available_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "tavily_search_tool",
                "description": "Perform web search for sunglasses trends using Tavily.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 5},
                        "include_images": {"type": "boolean", "default": False}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "product_catalog_tool",
                "description": "Get sunglasses products from internal inventory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "max_items": {"type": "integer", "default": 10}
                    }
                }
            }
        }
    ]


# 🔁 TOOL CALL DISPATCHER
def handle_tool_call(tool_call):
    # 1. 初始化变量
    function_name = ""
    arguments = {}

    # 2. 判断输入类型
    if isinstance(tool_call, dict):
        # === 针对 LangChain (字典模式) ===
        function_name = tool_call.get("name")
        # LangChain 通常已经把 args 解析为字典了，不需要 json.loads
        # 但为了保险，检查一下类型
        args_raw = tool_call.get("args", {})
        if isinstance(args_raw, str):
            arguments = json.loads(args_raw)
        else:
            arguments = args_raw
            
    else:
        # === 针对 OpenAI SDK (对象模式) ===
        # 也就是你原来的代码逻辑
        if hasattr(tool_call, 'function'):
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
        else:
            raise ValueError(f"Unknown tool_call format: {type(tool_call)}")

    # ... 下面保持你原有的逻辑不变 ...
    
    print(f"Executing {function_name} with {arguments}") # Debug 用
    
    if function_name == "tavily_search_tool":
        return tavily_search_tool(**arguments)
    elif function_name == "product_catalog_tool":
        return product_catalog_tool(**arguments)
    else:
        return f"Error: Tool {function_name} not found."

def create_tool_response_message(tool_call, tool_result):
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": tool_call.function.name,
        "content": json.dumps(tool_result)
    }