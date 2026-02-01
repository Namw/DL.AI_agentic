"""
HTTP 服务器模块，用于通过 Web 界面展示 print_html 函数的结果
"""
import http.server
import socketserver
import threading
import json
import base64
import mimetypes
from pathlib import Path
from typing import Any, Optional
import pandas as pd
from html import escape


def generate_html(content: Any, title: Optional[str] = None, is_image: bool = False) -> str:
    """
    生成 HTML 字符串，不依赖 IPython.display
    这是 print_html 函数的非交互式版本
    
    Args:
        content: 要显示的内容
        title: 可选的标题
        is_image: 是否将内容视为图像路径
        
    Returns:
        HTML 字符串
    """
    def image_to_base64(image_path: str) -> str:
        """将图像文件转换为 base64 字符串"""
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

    # 渲染内容
    if is_image and isinstance(content, str):
        try:
            b64 = image_to_base64(content)
            rendered = f'<img src="data:image/png;base64,{b64}" alt="Image" style="max-width:100%; height:auto; border-radius:8px;">'
        except Exception as e:
            rendered = f'<div style="color: red;">无法加载图像: {escape(str(e))}</div>'
    elif isinstance(content, pd.DataFrame):
        rendered = content.to_html(classes="pretty-table", index=False, border=0, escape=False)
    elif isinstance(content, pd.Series):
        rendered = content.to_frame().to_html(classes="pretty-table", border=0, escape=False)
    elif isinstance(content, str):
        rendered = f"<pre><code>{escape(content)}</code></pre>"
    else:
        rendered = f"<pre><code>{escape(str(content))}</code></pre>"

    css = """
    <style>
    body {
        font-family: ui-sans-serif, system-ui;
        background: #f8fafc;
        margin: 0;
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 100vh;
    }
    .container {
        max-width: 1200px;
        width: 100%;
    }
    .pretty-card{
      font-family: ui-sans-serif, system-ui;
      border: 2px solid transparent;
      border-radius: 14px;
      padding: 14px 16px;
      margin: 10px 0;
      background: linear-gradient(#fff, #fff) padding-box,
                  linear-gradient(135deg, #3b82f6, #9333ea) border-box;
      color: #111;
      box-shadow: 0 4px 12px rgba(0,0,0,.08);
    }
    .pretty-title{
      font-weight:700;
      margin-bottom:8px;
      font-size:14px;
      color:#111;
    }
    /* 🔒 Only affects INSIDE the card */
    .pretty-card pre, 
    .pretty-card code {
      background: #f3f4f6;
      color: #111;
      padding: 8px;
      border-radius: 8px;
      display: block;
      overflow-x: auto;
      font-size: 13px;
      white-space: pre-wrap;
    }
    .pretty-card img { max-width: 100%; height: auto; border-radius: 8px; }
    .pretty-card table.pretty-table {
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
      color: #111;
    }
    .pretty-card table.pretty-table th, 
    .pretty-card table.pretty-table td {
      border: 1px solid #e5e7eb;
      padding: 6px 8px;
      text-align: left;
    }
    .pretty-card table.pretty-table th { background: #f9fafb; font-weight: 600; }
    
    .controls {
        background: white;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .control-group {
        margin-bottom: 15px;
    }
    
    label {
        display: block;
        margin-bottom: 5px;
        font-weight: 600;
        color: #374151;
    }
    
    input, textarea, select {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        font-size: 14px;
        box-sizing: border-box;
    }
    
    textarea {
        min-height: 100px;
        resize: vertical;
        font-family: monospace;
    }
    
    button {
        background: linear-gradient(135deg, #3b82f6, #9333ea);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: opacity 0.2s;
    }
    
    button:hover {
        opacity: 0.9;
    }
    
    .examples {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    
    .example-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .example-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    
    .example-title {
        font-weight: 600;
        margin-bottom: 8px;
        color: #111;
    }
    
    .example-desc {
        font-size: 13px;
        color: #6b7280;
    }
    </style>
    """

    title_html = f'<div class="pretty-title">{title}</div>' if title else ""
    card = f'<div class="pretty-card">{title_html}{rendered}</div>'
    
    return css + card


class HTMLRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义 HTTP 请求处理器"""
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/':
            # 返回主页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # 生成示例页面
            html_content = self.generate_main_page()
            self.wfile.write(html_content.encode('utf-8'))
            
        elif self.path == '/api/examples':
            # 返回示例数据
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            examples = self.get_examples()
            self.wfile.write(json.dumps(examples).encode('utf-8'))
            
        elif self.path.startswith('/api/generate'):
            # 处理生成 HTML 的请求
            self.handle_generate_request()
            
        else:
            # 其他请求返回 404
            self.send_response(404)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>404 Not Found</h1>')
    
    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/api/generate':
            self.handle_generate_request()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_generate_request(self):
        """处理生成 HTML 的请求"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            content = data.get('content', '')
            title = data.get('title', '')
            content_type = data.get('type', 'text')  # text, dataframe, image
            
            # 根据类型处理内容
            if content_type == 'dataframe':
                # 尝试解析为 DataFrame
                import pandas as pd
                import io
                df = pd.read_csv(io.StringIO(content))
                html_result = generate_html(df, title if title else "DataFrame 预览")
            elif content_type == 'image':
                # 图像路径
                html_result = generate_html(content, title if title else "图像预览", is_image=True)
            else:
                # 文本内容
                html_result = generate_html(content, title if title else "文本内容")
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_result.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                'error': str(e),
                'message': '处理请求时发生错误'
            })
            self.wfile.write(error_response.encode('utf-8'))
    
    def generate_main_page(self) -> str:
        """生成主页面 HTML"""
        examples = self.get_examples()
        
        examples_html = ""
        for example in examples:
            examples_html += f"""
            <div class="example-card" onclick="loadExample('{example['id']}')">
                <div class="example-title">{example['title']}</div>
                <div class="example-desc">{example['description']}</div>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>print_html Web 界面</title>
            {generate_html("", "", False).split('</style>')[0] + '</style>'}
        </head>
        <body>
            <div class="container">
                <h1 style="color: #111; margin-bottom: 10px;">print_html Web 界面</h1>
                <p style="color: #6b7280; margin-bottom: 30px;">
                    通过 HTTP 服务展示 print_html 函数的结果，无需 Jupyter/IPython 环境
                </p>
                
                <div class="controls">
                    <div class="control-group">
                        <label for="contentType">内容类型</label>
                        <select id="contentType" onchange="updateInputField()">
                            <option value="text">文本/代码</option>
                            <option value="dataframe">CSV 数据 (DataFrame)</option>
                            <option value="image">图像文件路径</option>
                        </select>
                    </div>
                    
                    <div class="control-group">
                        <label for="title">标题 (可选)</label>
                        <input type="text" id="title" placeholder="输入标题...">
                    </div>
                    
                    <div class="control-group">
                        <label for="content">内容</label>
                        <textarea id="content" placeholder="输入要显示的内容..."></textarea>
                    </div>
                    
                    <button onclick="generateHTML()">生成 HTML 预览</button>
                </div>
                
                <div id="resultContainer" style="display: none;">
                    <h2 style="color: #111; margin-bottom: 15px;">预览结果</h2>
                    <div id="previewResult"></div>
                </div>
                
                <h2 style="color: #111; margin-top: 40px; margin-bottom: 15px;">示例</h2>
                <div class="examples">
                    {examples_html}
                </div>
            </div>
            
            <script>
            function updateInputField() {{
                const type = document.getElementById('contentType').value;
                const contentField = document.getElementById('content');
                
                if (type === 'text') {{
                    contentField.placeholder = '输入文本或代码...';
                }} else if (type === 'dataframe') {{
                    contentField.placeholder = '输入 CSV 数据...\\n例如: name,age,score\\nAlice,25,95\\nBob,30,88\\nCharlie,28,92';
                }} else if (type === 'image') {{
                    contentField.placeholder = '输入图像文件路径...\\n例如: /path/to/image.png';
                }}
            }}
            
            function generateHTML() {{
                const contentType = document.getElementById('contentType').value;
                const title = document.getElementById('title').value;
                const content = document.getElementById('content').value;
                
                if (!content) {{
                    alert('请输入内容');
                    return;
                }}
                
                fetch('/api/generate', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        type: contentType,
                        title: title,
                        content: content
                    }})
                }})
                .then(response => response.text())
                .then(html => {{
                    document.getElementById('previewResult').innerHTML = html;
                    document.getElementById('resultContainer').style.display = 'block';
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    alert('生成 HTML 时发生错误: ' + error);
                }});
            }}
            
            function loadExample(exampleId) {{
                const examples = {json.dumps(examples)};
                const example = examples.find(e => e.id === exampleId);
                
                if (example) {{
                    document.getElementById('contentType').value = example.type;
                    document.getElementById('title').value = example.title || '';
                    document.getElementById('content').value = example.content;
                    updateInputField();
                    
                    // 自动生成预览
                    setTimeout(() => generateHTML(), 100);
                }}
            }}
            
            // 初始化
            updateInputField();
            </script>
        </body>
        </html>
        """
    
    def get_examples(self) -> list:
        """获取示例数据"""
        import pandas as pd
        import numpy as np
        
        # 创建示例 DataFrame
        df_example = pd.DataFrame({
            '姓名': ['张三', '李四', '王五', '赵六'],
            '年龄': [25, 30, 28, 35],
            '分数': [95, 88, 92, 78],
            '城市': ['北京', '上海', '广州', '深圳']
        })
        
        # 转换为 CSV 字符串
        df_csv = df_example.to_csv(index=False)
        
        return [
            {
                'id': 'text_example',
                'title': '文本示例',
                'description': '显示格式化文本和代码',
                'type': 'text',
                'content': '这是一个示例文本内容。\n\nprint("Hello, World!")\n\nfor i in range(10):\n    print(f"Number: {i}")'
            },
            {
                'id': 'dataframe_example',
                'title': 'DataFrame 示例',
                'description': '显示 CSV 数据表格',
                'type': 'dataframe',
                'content': df_csv
            },
            {
                'id': 'image_example',
                'title': '图像示例',
                'description': '显示图像文件（需要有效路径）',
                'type': 'image',
                'content': 'resource/coffee_sales.csv'  # 注意：这实际上不是图像，仅作示例
            }
        ]


def start_server(port: int = 8080, host: str = "localhost"):
    """
    启动 HTTP 服务器
    
    Args:
        port: 端口号，默认为 8080
        host: 主机地址，默认为 localhost
    """
    handler = HTMLRequestHandler
    httpd = socketserver.TCPServer((host, port), handler)
    
    print(f"服务器启动在 http://{host}:{port}")
    print("按 Ctrl+C 停止服务器")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    finally:
        httpd.server_close()


def start_server_in_background(port: int = 8080, host: str = "localhost") -> threading.Thread:
    """
    在后台启动 HTTP 服务器
    
    Args:
        port: 端口号
        host: 主机地址
        
    Returns:
        服务器线程
    """
    server_thread = threading.Thread(
        target=start_server,
        args=(port, host),
        daemon=True
    )
    server_thread.start()
    return server_thread


if __name__ == "__main__":
    # 直接运行此文件时启动服务器
    start_server()
