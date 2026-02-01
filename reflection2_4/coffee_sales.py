import json

from utils import utils
import re
import pandas as pd
from utils.html_server import generate_html
import os

def generate_chart_code(instruction: str, model: str, out_path_v1: str) -> str:
    """生成使用 matplotlib 绘图的 Python 代码，并用标签包裹返回。"""

    prompt = f"""
    你是一位数据可视化专家。

    请*严格*按以下格式返回你的答案：

    <execute_python>
    # 在此填写有效的 Python 代码
    </execute_python>

    不要添加任何解释，仅包含上述标签与代码。

    代码需基于名为 'df' 的 DataFrame 生成可视化，其列包括：
    - date (M/D/YY)
    - time (HH:MM)
    - cash_type (card 或 cash)
    - card (string)
    - price (number)
    - coffee_name (string)
    - quarter (1-4)
    - month (1-12)
    - year (YYYY)

    用户指令：{instruction}

    代码要求：
    1. 假设 DataFrame 已加载为 'df'。
    2. 使用 matplotlib 进行绘图。
    3. 添加清晰的标题、坐标轴标签，并在需要时添加图例。
    4. 将图像以 '{out_path_v1}' 保存，dpi=300。
    5. 不要调用 plt.show()。
    6. 使用 plt.close() 关闭所有图。
    7. 补充所有必要的 import 语句。

    仅返回包含在 <execute_python> 标签中的代码。
    """

    response = utils.get_qwen_response(model, prompt)
    return response

# 生成初始代码

code_v1 = generate_chart_code(
    instruction="使用 coffee_sales.csv 中的数据，创建一张对比 2024 与 2025 年第一季度咖啡销售的图表。", 
    model="qwen-plus", 
    out_path_v1="chart_v1.png"
)

# 提取 <execute_python> 标签中的代码
match = re.search(r"<execute_python>([\s\S]*?)</execute_python>", code_v1)
if match:
    initial_code = match.group(1).strip()
    # 使用新的 generate_html 函数生成 HTML
    html_content = generate_html(initial_code, title="提取出的待执行代码")
    # 保存到文件
    with open("extracted_code.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("代码 HTML 已保存到: extracted_code.html")
    # 使用 utils.py 提供的函数将数据加载到 DataFrame
    df = utils.load_and_prepare_data('resource/coffee_sales.csv')
    exec_globals = {"df": df}
    exec(initial_code, exec_globals)

# 若代码运行成功，将生成文件 chart_v1.png
if os.path.exists("chart_v1.png"):
    # 使用新的 generate_html 函数生成图像 HTML
    html_content = generate_html("chart_v1.png", title="生成的图表（V1）", is_image=True)
    # 保存到文件
    with open("generated_chart.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("图表 HTML 已保存到: generated_chart.html")
else:
    print("警告: chart_v1.png 文件未生成")
