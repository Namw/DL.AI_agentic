import json
from typing import Any, List, Dict, Union

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.rule import Rule
from rich.align import Align
from rich.text import Text

# 初始化全局 Console 实例
console = Console()

def render_pretty_table(df: pd.DataFrame, title: str = "Data Table") -> None:
    """
    在终端渲染漂亮的 Pandas 表格
    """
    table = Table(title=title, show_header=True, header_style="bold white on #007acc", expand=True)

    # 添加列
    for column in df.columns:
        table.add_column(str(column), style="cyan")

    # 添加行 (将所有数据转为字符串以确保兼容性)
    for _, row in df.iterrows():
        table.add_row(*[str(item) for item in row])

    console.print(table)
    console.print("\n")


def format_logs_as_pretty_console(logs: List[Dict[str, Any]]) -> None:
    """
    渲染日志流摘要 (替代原有的 format_logs_as_pretty_html)
    """
    # 状态对应的颜色风格
    status_styles = {
        "success": "bold green",
        "fixed": "bold yellow",
        "error": "bold red",
    }
    
    console.print(Rule("Customer Return Workflow Summary", style="bold blue"))
    
    for log in logs:
        status = log.get("status", "success")
        style = status_styles.get(status, "white")
        step = log.get("step", "?")
        desc = log.get("description", "")
        
        # 构建内容
        content = f"[bold]Description:[/bold] {desc}\n[bold]Status:[/bold] [{style}]{status}[/{style}]"
        
        # 渲染单个卡片
        console.print(Panel(
            content,
            title=f"Step {step}",
            border_style=style,
            expand=False,
            padding=(1, 2)
        ))
    console.print("\n")


def render_image_with_quote(image_url: str, quote: str) -> None:
    """
    终端无法原生显示图片，改为显示图片路径和引用语
    """
    # 构建居中的引用语
    quote_text = Text(f'“{quote}”', justify="center", style="italic bold cyan on black")
    
    # 构建图片占位符信息
    image_info = f"[🖼️ Image Reference]: {image_url}"
    
    panel = Panel(
        Align.center(quote_text),
        title=image_info,
        subtitle="Image cannot be rendered in CLI",
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(panel)


def log_tool_call(tool_name: str, arguments: Any) -> None:
    """
    记录工具调用 (蓝色主题)
    """
    # 尝试格式化 JSON 参数，使其更易读
    if isinstance(arguments, (dict, list)):
        args_str = json.dumps(arguments, indent=2, ensure_ascii=False)
        # 使用 Syntax 高亮 JSON
        renderable_args = Syntax(args_str, "json", theme="ansi_dark", word_wrap=True)
    else:
        renderable_args = str(arguments)

    console.print(Panel(
        renderable_args,
        title=f"📞 Tool Call: [bold blue]{tool_name}[/bold blue]",
        border_style="blue",
        style="white",
        padding=(1, 2)
    ))


def log_tool_result(result: Any) -> None:
    """
    记录工具结果 (绿色主题)
    """
    # 如果结果很长或者是复杂结构，尝试美化
    content_str = str(result)
    
    console.print(Panel(
        content_str,
        title="✅ Tool Result",
        border_style="green",
        style="green",
        padding=(1, 2)
    ))


def log_final_summary(content: str) -> None:
    """
    记录最终摘要 (深绿色主题)
    """
    console.print(Panel(
        Markdown(content), # 支持 Markdown 渲染
        title="📝 Final Summary",
        border_style="bold green",
        padding=(1, 2)
    ))


def log_unexpected() -> None:
    """
    记录异常情况 (橙色/红色主题)
    """
    console.print(Panel(
        "No tool_calls or content returned.",
        title="⚠️ Unexpected",
        border_style="bold orange1",
        style="bold red",
        padding=(1, 2)
    ))


def log_agent_title(title: str, icon: str = "🕵️‍♂️") -> None:
    """
    打印 Agent 标题
    """
    console.print("\n")
    console.print(Rule(f"{icon} {title}", style="bold cyan"))
    console.print("\n")


def print_pretty(content: Any, title: Union[str, None] = None, is_image: bool = False) -> None:
    """
    通用漂亮打印函数 (替代 print_html)
    """
    # 1. 处理图片 (终端降级处理)
    if is_image and isinstance(content, str):
        console.print(Panel(
            f"[yellow]Image Path:[/yellow] {content}", 
            title=title or "Image", 
            border_style="magenta"
        ))
        return

    # 2. 处理 DataFrame
    if isinstance(content, pd.DataFrame):
        render_pretty_table(content, title=title or "DataFrame")
        return

    # 3. 处理 Series
    if isinstance(content, pd.Series):
        render_pretty_table(content.to_frame(), title=title or "Series")
        return

    # 4. 处理普通文本/代码
    content_str = str(content)
    # 如果看起来像代码或JSON，可以用 Syntax 高亮 (这里简单处理为普通文本，或尝试 Markdown)
    console.print(Panel(
        content_str,
        title=title or "Output",
        border_style="blue",
        padding=(1, 2)
    ))

# =========================================================================
# 为了兼容你之前的调用代码，这里做一些别名映射 (Alias)
# 这样你原本代码里的 utils.log_tool_result_html(...) 不用改也能跑
# =========================================================================

log_tool_result_html = log_tool_result
log_tool_call_html = log_tool_call
log_final_summary_html = log_final_summary
log_unexpected_html = log_unexpected
log_agent_title_html = log_agent_title
render_pretty_table_html = render_pretty_table
render_image_with_quote_html = render_image_with_quote
print_html = print_pretty
format_logs_as_pretty_html = format_logs_as_pretty_console