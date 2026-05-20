import gradio as gr
from agent import chat


def chat_with_ai(message, history):
    """和AI对话（查订单走本地模拟库，其它走大模型）"""
    try:
        return chat(message, user_id="gradio_user")
    except Exception as e:
        return f"出错了：{e}"


# ── 1. 使用 Soft 主题并自定义配色 ──────────────────
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="gray",
    neutral_hue="slate",
).set(
    body_background_fill="*neutral_50",
    block_background_fill="white",
    block_label_background_fill="*primary_100",
    button_primary_background_fill="*primary_600",
    button_primary_background_fill_hover="*primary_700",
    button_primary_text_color="white",
    border_color_primary="*primary_300",
)


# ── 2. 自定义 CSS 微调样式 ────────────────────────
css = """
.gradio-container {
    font-family: 'Segoe UI', system-ui, sans-serif;
}
#chatbot {
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    border: 1px solid #e2e8f0;
}
.example {
    border-radius: 20px !important;
    padding: 6px 16px !important;
    font-size: 0.875rem !important;
}
"""


# ── 3. 示例问题 ─────────────────────────────────
examples = [
    "查询订单 ABC12345678 的状态",
    "最近有哪些延迟的订单？",
    "帮我优化明天的配送路线",
    "如何处理客户投诉？",
]


# ── 4. 构建 ChatInterface（已去除版本敏感的按钮参数） ──
demo = gr.ChatInterface(
    fn=chat_with_ai,
    title="🚚 物流AI调度助手",
    description="智能物流助手 · 查订单、问延误、优化路线，随时问我吧！",
    theme=theme,
    css=css,
    examples=examples,
    chatbot=gr.Chatbot(
        height=520,
        placeholder="在下方输入您的问题…",
        avatar_images=(
            None,
            "https://img.icons8.com/fluency/48/chatbot.png",
        ),
        bubble_full_width=False,
        layout="bubble",
    ),
    textbox=gr.Textbox(
        placeholder="例如：查订单、问延误、优化路线…",
        container=False,
        scale=7,
    ),
    # 不再自定义按钮文案，使用 Gradio 默认的 Submit / Retry / Undo / Clear
)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1")