import json

from utils import utils
import re
import pandas as pd
from utils.html_server import generate_html
import os

def reflect_on_image_and_regenerate(
    chart_path: str,
    instruction: str,
    model_name: str,
    out_path_v2: str,
    code_v1: str,  
) -> tuple[str, str]:
    """
    根据给定指令评审图表图像与原始代码，
    然后返回改进后的 matplotlib 代码。
    返回值：(feedback, refined_code_with_tags)。
    支持 阿里千问。
    """
    media_type, b64 = utils.encode_image_b64(chart_path)


    prompt = f"""
    你是一位数据可视化专家。
    你的任务：依据给定指令评审附件中的图表与原始代码，
    并返回改进后的 matplotlib 代码。

    原始代码（用于提供上下文）：
    {code_v1}

    输出格式（严格遵守！）：
    1) 第一行：仅包含 "feedback" 字段的有效 JSON 对象。
    示例：{{"feedback": "图例不清晰，且坐标轴标签存在重叠。"}}

    2) 换行后，仅输出用如下标签包裹的改进版 Python 代码：
    <execute_python>
    ...
    </execute_python>

    3) 在代码中导入所有必要的库。不要依赖原始代码中的 import。

    强约束：
    - 除上述两部分外，不要包含 Markdown、反引号或任何额外说明文字。
    - 仅使用 pandas/matplotlib（不使用 seaborn）。
    - 假设 df 已存在；不要从文件读取。
    - 保存到 '{out_path_v2}'，dpi=300。
    - 结尾始终调用 plt.close()（不要使用 plt.show()）。
    - 包含所有必要的 import 语句。

    架构（df 中可用的列）：
    - date (M/D/YY)
    - time (HH:MM)
    - cash_type (card 或 cash)
    - card (string)
    - price (number)
    - coffee_name (string)
    - quarter (1-4)
    - month (1-12)
    - year (YYYY)

    指令：
    {instruction}
    """

    content = utils.image_ali_call_qwen_vl(model_name=model_name, prompt=prompt, media_type=media_type, b64=b64)
    # --- 仅解析第一行 JSON（feedback） ---
    lines = content.strip().splitlines()
    json_line = lines[0].strip() if lines else ""

    try:
        obj = json.loads(json_line)
    except Exception as e:
        # 回退：尝试在完整内容中捕获第一个 {...}
        m_json = re.search(r"\{.*?\}", content, flags=re.DOTALL)
        if m_json:
            try:
                obj = json.loads(m_json.group(0))
            except Exception as e2:
                obj = {"feedback": f"Failed to parse JSON: {e2}", "refined_code": ""}
        else:
            obj = {"feedback": f"Failed to find JSON: {e}", "refined_code": ""}

    # --- 从 <execute_python>...</execute_python> 中提取改进代码 ---
    m_code = re.search(r"<execute_python>([\s\S]*?)</execute_python>", content)
    refined_code_body = m_code.group(1).strip() if m_code else ""
    refined_code = utils.ensure_execute_python_tags(refined_code_body)

    feedback = str(obj.get("feedback", "")).strip()
    return feedback, refined_code

# 生成反馈并返回反思后的代码
code_v1 = """
import pandas as pd
import matplotlib.pyplot as plt

# Filter data for Q1 of 2024 and 2025
df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y')

df_q1_2024 = df[(df['quarter'] == 1) & (df['year'] == 2024)]
df_q1_2025 = df[(df['quarter'] == 1) & (df['year'] == 2025)]

# Group by coffee_name and sum the prices
sales_2024 = df_q1_2024.groupby('coffee_name')['price'].sum()
sales_2025 = df_q1_2025.groupby('coffee_name')['price'].sum()

# Combine both years for comparison
comparison_df = pd.DataFrame({'2024': sales_2024, '2025': sales_2025}).fillna(0)

# Create bar chart
fig, ax = plt.subplots(figsize=(10, 6))
comparison_df.plot(kind='bar', ax=ax)
ax.set_title("Comparison of Q1 Coffee Sales: 2024 vs 2025")
ax.set_xlabel("Coffee Name")
ax.set_ylabel("Total Sales ($)")
plt.xticks(rotation=45)
plt.tight_layout()

# Save the figure
plt.savefig('chart_v1.png', dpi=300)
plt.close()
"""
feedback, code_v2 = reflect_on_image_and_regenerate(
    chart_path="chart_v1.png",            
    instruction="使用 coffee_sales.csv 中的数据，创建一张对比 2024 与 2025 年第一季度咖啡销售的图表。", 
    model_name="qwen3-vl-flash",
    out_path_v2="chart_v2.png",
    code_v1=code_v1,   # 传入原始代码作为上下文        
)

print(f"feedback:{feedback}")
print(f"重新生成的代码输出（V2）:{code_v2}")

# 提取 <execute_python> 标签中的代码
match = re.search(r"<execute_python>([\s\S]*?)</execute_python>", code_v2)
if match:
    initial_code = match.group(1).strip()
    df = utils.load_and_prepare_data('resource/coffee_sales.csv')
    exec_globals = {"df": df}
    exec(initial_code, exec_globals)