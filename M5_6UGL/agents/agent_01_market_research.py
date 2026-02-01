import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

# 假设这是你的工具模块，保持你的用法
import utils
import tools 

def market_research_agent(return_messages: bool = False):
    
    utils.log_agent_title_html("Market Research Agent", "🕵️‍♂️")

    # 1. 保持原来的提示词
    system_prompt_content = f"""
你是一名时尚市场调研代理，负责为夏季太阳镜活动准备趋势分析。

目标：
1. 使用网页搜索探索与太阳镜相关的当前时尚趋势。
2. 查看内部产品目录，识别与这些趋势相契合的商品。
3. 从目录中推荐一个或多个最符合新兴趋势的产品。
4. 如需注明，今天的日期是 {datetime.now().strftime("%Y-%m-%d")}。

可调用以下工具：
- tavily_search_tool：发现外部网络趋势。
- product_catalog_tool：检查内部太阳镜目录。

完成分析后，请总结：
- 你发现的 2–3 个主要趋势。
- 与这些趋势匹配的目录产品。
- 为何它们适合夏季活动的理由说明。
"""
    human_trigger = "请开始执行市场调研任务，并按要求输出报告。"
    # --- 初始化 LangChain 模型 ---
    qwen_api_key = os.getenv("DASHSCOPE_API_KEY")
    llm = ChatOpenAI(
        model="qwen-plus",
        api_key=qwen_api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.2
    )

    # 2. 获取工具 (保持你的逻辑)
    # 注意：这里假设 tools.get_available_tools() 返回的是 LangChain Tool 对象列表
    # 如果返回的是 OpenAI JSON Schema，bind_tools 通常也能兼容
    tools_ = tools.get_available_tools()
    
    # 关键步骤：在 LangChain 中，需先将工具绑定到模型
    llm_with_tools = llm.bind_tools(tools_)

    # 初始化消息列表，使用 LangChain 的 HumanMessage
    messages = [
        SystemMessage(content=system_prompt_content),
        HumanMessage(content=human_trigger)
    ]

    # 3. 使用 while True 循环
    while True:
        # 4. 调用模型 (invoke 替代 chat.completions.create)
        # response 是一个 AIMessage 对象
        response = llm_with_tools.invoke(messages)

        # 5. 检查是否返回内容 (终止条件)
        # 逻辑：如果有文本内容且没有工具调用，说明是最终回复
        # 注意：有时候模型会同时返回“思考过程(content)”和“工具调用”，
        # 所以这里的判断优先级要根据你的业务需求。这里严格照搬你的逻辑：有 content 就结束。
        if response.content and not response.tool_calls:
            utils.log_final_summary_html(response.content)
            
            # 这里的 messages 已经是 LangChain 对象列表，如果外部需要 Dict，可能需要转换
            return (response.content, messages) if return_messages else response.content

        # 6. 检查是否需要调用工具
        if response.tool_calls:
            # 将 AI 的这一轮回复（包含工具调用请求）加入历史
            messages.append(response)

            for tool_call in response.tool_calls:
                # 兼容你的 utils 日志
                # LangChain 的 tool_call 结构通常包含 'name', 'args', 'id'
                utils.log_tool_call_html(tool_call["name"], tool_call["args"])
                
                # --- 执行工具 ---
                # 这里调用你的 tools.handle_tool_call
                # 注意：LangChain 的 tool_call["args"] 已经是解析好的字典，
                # 如果你的 handle_tool_call 需要 json 字符串，请留意这里
                result = tools.handle_tool_call(tool_call)
                
                utils.log_tool_result_html(result)

                # --- 构造 ToolMessage 并加入历史 ---
                # 这一步对应原本的 messages.append(tools.create_tool_response_message(...))
                # LangChain 必须显式使用 ToolMessage
                tool_msg = ToolMessage(
                    tool_call_id=tool_call["id"], 
                    content=str(result) # 确保内容是字符串
                )
                messages.append(tool_msg)
        
        else:
            # 既没有 content 也没有 tool_calls (异常情况)
            utils.log_unexpected_html()
            err_msg = "[⚠️ Unexpected: No tool_calls or content returned]"
            return (err_msg, messages) if return_messages else err_msg