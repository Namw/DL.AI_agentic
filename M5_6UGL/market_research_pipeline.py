import os
from datetime import datetime
from pathlib import Path  # 推荐使用Pathlib，更现代

from agents.agent_01_market_research import market_research_agent
from agents.agent_02_graphic_designer import graphic_designer_agent
from agents.agent_03_copywriter import copywriter_agent
from agents.agent_04_packaging import packaging_agent

market_research_result = market_research_agent()
# market_research_result = """
# ### 2026夏季太阳镜市场趋势分析报告
# **日期：2026年1月11日**
#
# ---
#
# #### **主要时尚趋势发现（2–3项）**
#
# 1. **金属框架回归（Metal Frames Revival）**
#    2026年夏季，轻盈且富有现代感的金属框架太阳镜成为主流。尤其以细框设计、高光泽金属材质为主，强调“精致摩登”（polished modernity）的审美。这类眼镜不仅提升整体造型质感，还兼具轻便舒适的特点，适合日常与度假佩戴。
#
# 2. **超大廓形与蝴蝶框（Oversized & Butterfly Silhouettes）**
#    蝴蝶框和超大尺寸太阳镜强势回归，融合浪漫女性化线条与未来主义轮廓。这类设计具有强烈的视觉冲击力，是打造“吸睛造型”的关键单品，深受时尚达人和明星青睐。
#
# 3. **复古元素与多功能技术结合（Retro Aesthetics with Smart Features）**
#    尽管经典款式如飞行员、猫眼、方形框持续流行，但消费者更偏好融合现代科技的设计，例如偏光镜片、变色镜片（photochromic）等，实现风格与功能的双重满足。
#
# ---
# """
print("✅ 市场调研完成")

save_dir = Path(os.path.dirname(os.path.abspath(__file__)) + "/images")
graphic_designer_agent_result = graphic_designer_agent(trend_insights=market_research_result, save_dir=save_dir)
# graphic_designer_agent_result = {"image_path": "/Users/wangchunyang/PycharmProjects/deeplearningAgent01/M5_6UGL/agents/images/0fd3d79e-f202-4658-8370-24ff3ab96bc84076764017.png"}
print("🖼️ 图像已生成")

copywriter_agent_result = copywriter_agent(
   image_path=graphic_designer_agent_result["image_path"],
   trend_summary=market_research_result,
)
# copywriter_agent_result = {'quote': '金属蝶翼，耀目未来', 'justification': '短句精准呼应图像中女性佩戴的金属蝴蝶框太阳镜，同时‘耀目’体现其视觉冲击力与时尚吸睛属性，‘未来’则暗合趋势中科技感与现代摩登的融合，简洁有力地传达2026夏季核心趋势。', 'image_path': '/Users/wangchunyang/PycharmProjects/deeplearningAgent01/M5_6UGL/agents/images/0fd3d79e-f202-4658-8370-24ff3ab96bc84076764017.png'}
print("💬 短句已生成")

packaging_agent_result = packaging_agent(
    trend_summary=market_research_result,
    image_url=graphic_designer_agent_result["image_path"],
    quote=copywriter_agent_result["quote"],
    justification=copywriter_agent_result["justification"],
    output_path=f"campaign_summary_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"
)
print(f"📦 报告已生成：{packaging_agent_result}")
