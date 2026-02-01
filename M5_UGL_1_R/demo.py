# ==== 导入 ====
from __future__ import annotations
import json
from dotenv import load_dotenv
import os
import requests
# from openai import OpenAI
import re, io, sys, traceback, json
from typing import Any, Dict, Optional
from tinydb import Query, where

# 工具模块
import utils      # 用于提示/打印的助手函数
import inv_utils  # 用于库存、交易、模式构建和 TinyDB 数据填充的函数

load_dotenv()

PROMPT = """你是一名高级数据助手。通过编写安全、稳健的 TinyDB PYTHON 代码来制定计划。

数据库模式和示例 (只读):
{schema_block}

执行环境 (已导入/已提供):
- 变量: db, inventory_tbl, transactions_tbl  # TinyDB 表对象
- 助手函数: get_current_balance(tbl) -> float, next_transaction_id(tbl, prefix="TXN") -> str
- 自然语言: user_request: str  # 原始用户消息

!!! Python 编码安全规范 (最高优先级 - 必须遵守) !!!
由于代码将在受限的 exec() 沙盒中运行，局部变量无法传递给生成器或 Lambda。你必须严格模仿下面的【正确】写法：

1. 【检测关键词】
   [❌ 错误]: is_hit = any(w in text for w in keywords)
   [✅ 正确]: 
   is_hit = False
   for w in keywords:
       if w in text:
           is_hit = True
           break

2. 【查找/过滤数据】
   [❌ 错误]: results = [x for x in data if check(x)]
   [✅ 正确]: 
   results = []
   for x in data:
       if check(x):
           results.append(x)

3. 【防御性读取】
   [❌ 错误]: val = item['name'].lower()
   [✅ 正确]: val = (item.get('name') or "").lower()

规划规则:
- 数据获取策略: 不要尝试构建复杂的 TinyDB 查询对象。
  1. 直接使用 `data = inventory_tbl.all()` 获取所有数据。
  2. 使用显式的 `for` 循环 (参考上述规范) 遍历 `data`。
- 参数提取: 从 user_request 派生过滤器。不要硬编码假设值。
- 保持保守: 如果意图不明确，仅执行只读操作。

交易政策 (硬性规定):
- 不要创建聚合的多项目交易。
- 如果请求包含多个项目，则为每个项目创建单独的交易行。
- 对于每个项目：
  - 计算其自己的单行总计 (unit_price * qty),
  - 插入一笔该金额的交易,
  - 按顺序更新余额 (balance += line_total),
  - 更新该项目的库存。
- 如果任何请求的项目库存不足，不要更改任何数据；回复 STATUS="insufficient_stock"。

人类可读响应要求 (硬性规定):
- 必须设置变量 `answer_text` (str)，内容为简短、客户友好的句子 (1-2 行)。这是唯一面向用户的消息。
- 如果没有匹配项，礼貌地说明情况，并提供一个相近的替代方案 (最接近的款式/价格) 或下一步建议。

行动政策:
- 如果请求明确要求改变状态 (购买/采购/退货/补货/调整):
    ACTION="mutate"; SHOULD_MUTATE=True; 执行更改并写入匹配的交易行。
  否则:
    ACTION="read"; SHOULD_MUTATE=False; 模拟并作为演习 (dry run) 简要说明 (仅在日志中)。

状态与边缘情况处理:
- 始终设置 `answer_text` 和 `STATUS`。
- `STATUS` 可选值: "success", "no_match", "insufficient_stock", "invalid_request", "unsupported_intent"。
- invalid_request: 无法解析基本信息 (如数量) → 简洁询问缺失部分。
- unsupported_intent: 超出商店能力 → 提供替代方案。

输出契约:
- 仅在这些标签之间返回可执行的 Python (没有额外文本):
  <execute_python>
  # 你的 python 代码
  </execute_python>

代码编写核对清单:
1) 解析 user_request (使用显式循环检查关键词)。
2) `all_items = inventory_tbl.all()`。
3) 使用显式 `for` 循环遍历 `all_items` 查找匹配项 (注意处理 None 值)。
4) 根据逻辑设置 ACTION 和 SHOULD_MUTATE。
5) 如果是 mutate，执行库存更新和交易插入。
6) 设置 `answer_text` 和 `STATUS`，并打印日志 "LOG: ..."。

用户请求:
{question}
"""

# ---------- 1) 代码生成 ----------
def generate_llm_code(
    dashscope_api_key: str,
    prompt: str,
    *,
    inventory_tbl,
    transactions_tbl,
    temperature: float = 0.2,
) -> str:
    """
    请求 LLM 生成一个“带代码的计划”响应。
    返回完整的助手内容 (包括周围的文本和标签)。
    实际的代码提取稍后在 execute_generated_code 中进行。
    """
    schema_block = inv_utils.build_schema_block(inventory_tbl, transactions_tbl)
    prompt = PROMPT.format(schema_block=schema_block, question=prompt)

    # Use DashScope (阿里云百炼) qwen-plus via the OpenAI-compatible endpoint
    if not dashscope_api_key:
      raise ValueError("DASHSCOPE_API_KEY 未设置。请在环境中添加 DASHSCOPE_API_KEY。")

    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    url = f"{base_url}/chat/completions"
    headers = {
      "Authorization": f"Bearer {dashscope_api_key}",
      "Content-Type": "application/json",
    }
    payload = {
      "model": "qwen-plus",
      "temperature": temperature,
      "messages": [
        {"role": "system", "content": "你编写安全、注释良好的 TinyDB 代码来处理数据问题和更新。"},
        {"role": "user", "content": prompt},
      ],
    }

    try:
      r = requests.post(url, headers=headers, json=payload, timeout=60)
      r.raise_for_status()
      j = r.json()
      content = ""
      # Compatible with OpenAI style response
      if isinstance(j, dict):
        choices = j.get("choices") or j.get("result")
        if choices and isinstance(choices, list):
          first = choices[0]
          if isinstance(first, dict):
            msg = first.get("message") or first
            if isinstance(msg, dict):
              content = msg.get("content") or msg.get("text") or ""
            else:
              content = first.get("text") or ""
      return content
    except Exception as e:
      raise RuntimeError(f"DashScope 请求失败: {e}")

# --- 辅助函数：提取 <execute_python>...</execute_python> 之间的代码 ---
def _extract_execute_block(text: str) -> str:
    """
    返回 <execute_python>...</execute_python> 标签内的 Python 代码。
    如果未找到标签，则假定 'text' 已经是原始 Python 代码。
    """
    if not text:
        raise RuntimeError("空内容被传递给代码执行器。")
    m = re.search(r"<execute_python>(.*?)</execute_python>", text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else text.strip()

# ---------- 2) 代码执行 ----------
def execute_generated_code(
    code_or_content: str,
    *,
    db,
    inventory_tbl,
    transactions_tbl,
    user_request: Optional[str] = None,
) -> Dict[str, Any]:
    """
    在受控的命名空间中执行代码。
    接受原始 Python 代码 或 包含 <execute_python> 标签的完整内容。
    返回最小化的产物：stdout、error 和提取的答案。
    """
    # 在此处提取代码 (现在是集中处理)
    code = _extract_execute_block(code_or_content)

    SAFE_GLOBALS = {
        "Query": Query,
        "get_current_balance": inv_utils.get_current_balance,
        "next_transaction_id": inv_utils.next_transaction_id,
        "user_request": user_request or "",
    }
    SAFE_LOCALS = {
        "db": db,
        "inventory_tbl": inventory_tbl,
        "transactions_tbl": transactions_tbl,
    }

    # 捕获从被执行代码产生的 stdout
    _stdout_buf, _old_stdout = io.StringIO(), sys.stdout
    sys.stdout = _stdout_buf
    err_text = None
    try:
        exec(code, SAFE_GLOBALS, SAFE_LOCALS)
    except Exception:
        err_text = traceback.format_exc()
    finally:
        sys.stdout = _old_stdout
    printed = _stdout_buf.getvalue().strip()

    # 提取由生成代码设置的可能答案
    answer = (
        SAFE_LOCALS.get("answer_text")
        or SAFE_LOCALS.get("answer_rows")
        or SAFE_LOCALS.get("answer_json")
    )

    return {
        "code": code,           # <- 已经没有标签了
        "stdout": printed,
        "error": err_text,
        "answer": answer,
        "transactions_tbl": transactions_tbl.all(), # 供检查
        "inventory_tbl": inventory_tbl.all(),     # 供检查
    }

dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
db, inventory_tbl, transactions_tbl = inv_utils.seed_db()

def ask_stok():
    # 讲座中的 Andrew 示例提示
    prompt_round = "你们是否有库存中的圆形太阳镜，且价格低于 100 美元？"
    # 生成以代码为计划的响应（完整内容；可能包含 <execute_python> 标签）
    # 搜索库存表，查找描述(description)或名称(name)
    # 包含单词 "round" (不区分大小写) 的文档。检查是内联完成的：
    # - (v or "") 确保我们通过将 None 转换为空字符串来处理它
    # - .lower() 规范化大小写
    # - " round " 强制执行一个粗略的单词边界 (不会匹配 "wraparound")
    # round_sunglasses = inventory_tbl.search(
    #     (Item.description.test(lambda v: " round " in ((v or "").lower()))) |
    #     (Item.name.test(lambda v: " round " in ((v or "").lower())))
    # )
    full_content_round = generate_llm_code(
        dashscope_api_key,
        prompt_round,
        inventory_tbl=inventory_tbl,
        transactions_tbl=transactions_tbl,
        temperature=1.0,
    )
    # 针对圆形太阳镜问题执行生成的计划
    result = execute_generated_code(
        full_content_round,          # 先前生成的完整 LLM 响应
        db=db,
        inventory_tbl=inventory_tbl,
        transactions_tbl=transactions_tbl,
        user_request=prompt_round,   # 例如："你们是否有库存中的圆形太阳镜，且价格低于 100 美元？"
    )

    # 查看计划实际执行的 Python 所提取的答案
    print(result["answer"])

def return_googds():
    Item = Query()  # 创建一个 Query 对象来引用字段 (例如 Item.name, Item.description)
    aviators = inventory_tbl.search(
        (Item.name == "Aviator")
    )
    # 检查符合的数据
    print("=" * 60)
    print("Aviator库存情况：")
    print(json.dumps(aviators, indent=2))
    print("=" * 60)
    print("退货表情况：")
    print(json.dumps(transactions_tbl.all(), indent=2))
    print("=" * 60)
    print("模型生成的代码：")
    # 生成以代码为计划的响应（完整内容；可能包含 <execute_python> 标签）
    prompt_aviator = "退回我上周购买的 2 副 Aviator 太阳镜。"
    full_content_aviator = generate_llm_code(
            dashscope_api_key,
            prompt_aviator,
            inventory_tbl=inventory_tbl,
            transactions_tbl=transactions_tbl,
            temperature=1.0,
        )
    # 查看 LLM 的计划与代码（此处不执行）
    print(full_content_aviator)
    print("=" * 60)
    print("代码的执行结果：")
    # 执行针对 Aviator 太阳镜退货的生成计划
    result = execute_generated_code(
        full_content_aviator,          # 先前生成的完整 LLM 响应
        db=db,
        inventory_tbl=inventory_tbl,
        transactions_tbl=transactions_tbl,
        user_request=prompt_aviator,   # 例如："退回我上周购买的 2 副 Aviator 太阳镜。"
    )
    # 查看计划实际执行的 Python 所提取的答案
    print(result["answer"])
    print("=" * 60)
    print(json.dumps(transactions_tbl.all(), indent=2))
    
def customer_service_agent(
    question: str,
    *,
    db,
    inventory_tbl,
    transactions_tbl,
    temperature: float = 1.0,
    reseed: bool = False,
) -> dict:
    """
    端到端助手：
      1) (可选) 重新填充库存和交易数据
      2) 根据 `question` 生成“代码即计划”
      3) 在受控的命名空间中执行
      4) 渲染执行前后的快照并返回产物

    Returns:
      {
        "full_content": <原始 LLM 响应 (可能包含 <execute_python> 标签)>,
        "exec": {
            "code": <提取出的 python 代码>,
            "stdout": <计划日志>,
            "error": <回溯信息或 None>,
            "answer": <答案文本/行/json>,
            "inventory_after": [...],
            "transactions_after": [...]
        }
      }
    """
    # 0) 可选的重新填充数据
    if reseed:
        inv_utils.create_inventory()
        inv_utils.create_transactions()

    # 1) 显示问题
    print("=" * 80)
    print(f"用户问题:{question}")

    # 2) 生成“代码即计划”(完整内容)
    full_content = generate_llm_code(
        dashscope_api_key,
        question,
        inventory_tbl=inventory_tbl,
        transactions_tbl=transactions_tbl,
        temperature=temperature,
    )
    print("=" * 80)
    print(f"生成的完整内容（以代码为计划）：{full_content}")

    # 3) 执行前的快照
    print("=" * 80)
    print(f"库存表 · 之前：{json.dumps(inventory_tbl.all(), indent=2)}")
    print(f"交易表 · 之前：{json.dumps(transactions_tbl.all(), indent=2)}")

    # 4) 执行
    exec_res = execute_generated_code(
        full_content,          # 先前生成的完整 LLM 响应
        db=db,
        inventory_tbl=inventory_tbl,
        transactions_tbl=transactions_tbl,
        user_request=question,   # 例如："你们是否有库存中的圆形太阳镜，且价格低于 100 美元？"
    )

    # 5) 执行后的快照 + 最终答案
    print("=" * 80)
    print(f"计划执行 · 提取的答案：{exec_res["answer"]}")
    print(f"库存表 · 之后：{json.dumps(inventory_tbl.all(), indent=2)}")
    print(f"交易表 · 之后：{json.dumps(transactions_tbl.all(), indent=2)}")

    # 6) 返回产物
    return {
        "full_content": full_content,
        "exec": {
            "code": exec_res["code"],
            "stdout": exec_res["stdout"],
            "error": exec_res["error"],
            "answer": exec_res["answer"],
            "inventory_after": inventory_tbl.all(),
            "transactions_after": transactions_tbl.all(),
        },
    }

prompt = "我想购买 3 副 Classic 太阳镜和 1 副 Aviator 太阳镜。"
out = customer_service_agent(
    prompt,
    db=db,
    inventory_tbl=inventory_tbl,
    transactions_tbl=transactions_tbl,
    temperature=1.0,
    reseed=True,   # 设为 False 以保留当前库存与交易状态
)