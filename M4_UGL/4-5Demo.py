# =========================
# 导入
# =========================

# --- 标准库 
from datetime import datetime
import json
import os
import re
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- 第三方 ---
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

# --- 本地 / 项目 ---
import research_tools
import utils

_ = load_dotenv()
# 加载各平台 API keys
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
qwen_api_key = os.getenv("DASHSCOPE_API_KEY")
glm_api_key = os.getenv("ZHIPUAI_API_KEY")
doubao_api_key = os.getenv("ARK_API_KEY")

def init_client(model_type: str = "auto"):
    """根据可用的 API key 初始化客户端"""
    
    try:
        if model_type in ["auto", "deepseek"] and deepseek_api_key:
            logger.info("正在初始化 Deepseek 模型...")
            client = ChatOpenAI(
                model="deepseek-coder",
                api_key=deepseek_api_key,
                base_url="https://api.deepseek.com/v1",
                temperature=0.7
            )
            logger.info("✓ Deepseek 模型初始化完成")
            return client, "deepseek"
        
        if model_type in ["auto", "qwen"] and qwen_api_key:
            logger.info("正在初始化阿里千问模型...")
            client = ChatOpenAI(
                model="qwen-plus",
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                temperature=0.7
            )
            logger.info("✓ 阿里千问模型初始化完成")
            return client, "qwen"
        
        if model_type in ["auto", "glm"] and glm_api_key:
            logger.info("正在初始化智普GLM模型...")
            from langchain_community.chat_models import ChatZhipuAI
            client = ChatZhipuAI(
                model="glm-4.5",
                zhipuai_api_key=glm_api_key,
                temperature=0.7
            )
            logger.info("✓ 智普GLM模型初始化完成")
            return client, "glm"
        
        if model_type in ["auto", "doubao"] and doubao_api_key:
            logger.info("正在初始化字节豆包模型...")
            client = ChatOpenAI(
                model="doubao-1.5-pro-32k-250115",
                api_key=doubao_api_key,
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                temperature=0.7
            )
            logger.info("✓ 字节豆包模型初始化完成")
            return client, "doubao"
        
    except ImportError as e:
        logger.warning(f"导入错误: {e}")
    except Exception as e:
        logger.error(f"初始化错误: {e}")
    
    raise ValueError(
        "未配置任何 API key\n"
        "需要以下任一配置:\n"
        "  - DEEPSEEK_API_KEY (Deepseek)\n"
        "  - DASHSCOPE_API_KEY (阿里千问)\n"
        "  - ZHIPU_API_KEY (智普GLM)\n"
        "  - ARK_API_KEY (字节豆包)"
    )

def find_references(task: str, model: str = "deepseek", return_messages: bool = False):
    """使用外部工具（arxiv、tavily、wikipedia）执行研究任务。"""
    logger.info(f"开始研究任务: {task}")

    prompt = f"""
    你是一个研究函数，可以访问：
    - arxiv_search_tool：学术论文
    - tavily_search_tool：通用网页搜索（需要时返回 JSON）
    - wikipedia_search_tool：百科式摘要

    任务：
    {task}

    今天是 {datetime.now().strftime('%Y-%m-%d')}。
    """.strip()

    # 创建工具集合
    tools = [
        research_tools.arxiv_search_tool,
        research_tools.tavily_search_tool,
        research_tools.wikipedia_search_tool,
    ]
    
    # 将客户端绑定到工具
    client, _ = init_client(model_type=model)
    model_with_tools = client.bind_tools(tools)
    logger.info(f"已绑定 {len(tools)} 个研究工具")
    
    messages = [HumanMessage(content=prompt)]

    try:
        # 执行多轮对话（最多1轮）
        for turn in range(1):
            logger.info(f"=== 对话轮次 {turn + 1}/5 ===")
            logger.info(f"正在调用模型...")
            response = model_with_tools.invoke(messages)
            messages.append(response)
            logger.info(f"模型响应已收到")
            
            # 检查是否有工具调用
            if not response.tool_calls:
                # 没有工具调用，返回最终结果
                logger.info(f"模型未调用工具，返回最终结果")
                content = response.content
                return (content, messages) if return_messages else content
            
            # 处理工具调用
            logger.info(f"模型调用了 {len(response.tool_calls)} 个工具")
            for i, tool_call in enumerate(response.tool_calls, 1):
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                logger.info(f"  [{i}] 调用工具: {tool_name}，参数: {tool_args}")
                
                # 调用相应的工具
                if tool_name == "arxiv_search_tool":
                    logger.info(f"      正在搜索 arXiv...")
                    tool_result = research_tools.arxiv_search_tool(**tool_args)
                elif tool_name == "tavily_search_tool":
                    logger.info(f"      正在进行网页搜索...")
                    tool_result = research_tools.tavily_search_tool(**tool_args)
                elif tool_name == "wikipedia_search_tool":
                    logger.info(f"      正在搜索 Wikipedia...")
                    tool_result = research_tools.wikipedia_search_tool(**tool_args)
                else:
                    tool_result = {"error": f"Unknown tool: {tool_name}"}
                    logger.error(f"      未知工具: {tool_name}")
                
                logger.info(f"      工具执行完成，获得 {len(tool_result) if isinstance(tool_result, list) else 1} 个结果")
                # 添加工具结果消息
                messages.append(ToolMessage(
                    content=json.dumps(tool_result),
                    tool_call_id=tool_call["id"]
                ))
        
        # 达到最大轮次，返回最后的内容
        logger.warning(f"达到最大对话轮次 (1轮)")
        if messages and hasattr(messages[-1], 'content'):
            content = messages[-1].content
        else:
            content = "[达到最大对话轮次]"
        logger.info(f"研究任务完成")
        return (content, messages) if return_messages else content
        
    except Exception as e:
        logger.error(f"执行出错: {e}", exc_info=True)
        return f"[模型错误: {e}]"
# Tavily 结果的首选域名列表
TOP_DOMAINS = {
    # 通用参考 / 机构 / 出版方
    "wikipedia.org", "nature.com", "science.org", "sciencemag.org", "cell.com",
    "mit.edu", "stanford.edu", "harvard.edu", "nasa.gov", "noaa.gov", "europa.eu",

    # 计算机科学 / 人工智能领域会议与索引
    "arxiv.org", "acm.org", "ieee.org", "neurips.cc", "icml.cc", "openreview.net",

    # 其他权威出版源
    "elifesciences.org", "pnas.org", "jmlr.org", "springer.com", "sciencedirect.com",

    # 额外域名（针对特定情况）
    "pbs.org", "nova.edu", "nvcc.edu", "cccco.edu",

    # 知名编程网站
    "codecademy.com", "datacamp.com"
}

def evaluate_tavily_results(TOP_DOMAINS, raw: str, min_ratio=0.4):
    """
    评估纯文本研究结果是否主要来自首选域名。

    Args:
        TOP_DOMAINS (set[str]): 首选域名集合（例如 'arxiv.org', 'nature.com'）。
        raw (str): 包含 URL 的纯文本或 Markdown。
        min_ratio (float): 通过评估所需的最小首选比例（例如 0.4 = 40%）。

    Returns:
        tuple[bool, str]: (flag, markdown_report)
            flag -> True 表示通过，False 表示未通过
            markdown_report -> Markdown 格式的评估摘要
    """

    # 从文本中提取 URL
    url_pattern = re.compile(r'https?://[^\s\]\)>\}]+', flags=re.IGNORECASE)
    urls = url_pattern.findall(raw)

    if not urls:
        return False, """### Evaluation — Tavily Preferred Domains
未检测到任何 URL。
请在研究结果中包含链接。
"""

    # 统计首选域名与总数
    total = len(urls)
    preferred_count = 0
    details = []

    for url in urls:
        domain = url.split("/")[2]
        preferred = any(td in domain for td in TOP_DOMAINS)
        if preferred:
            preferred_count += 1
        details.append(f"- {url} → {'✅ 首选域名' if preferred else '❌ 非首选域名'}")

    ratio = preferred_count / total if total > 0 else 0.0
    flag = ratio >= min_ratio

    # 生成 Markdown 格式的评估报告
    report = f"""
### 评估结果 — Tavily 首选域名
- 总链接数: {total}
- 首选链接数: {preferred_count}
- 比例: {ratio:.2%}
- 阈值: {min_ratio:.0%}
- 状态: {"✅ 通过" if flag else "❌ 未通过"}

**详细结果：**
{chr(10).join(details)}
"""
    return flag, report


if __name__ == "__main__":
    research_task = "查找 2 篇关于黑洞科学最新进展的近期论文"
    research_result = find_references(research_task, model="deepseek")
    flag, report = evaluate_tavily_results(TOP_DOMAINS, research_result)
    print(flag, report)