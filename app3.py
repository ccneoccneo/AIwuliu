import gradio as gr
from agent import chat

# ── 主题和 CSS 保持之前的美化设置 ──
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
).set(
    body_background_fill="*neutral_50",
    block_background_fill="white",
    block_label_background_fill="*primary_100",
    button_primary_background_fill="*primary_600",
    button_primary_background_fill_hover="*primary_700",
    button_primary_text_color="white",
    border_color_primary="*primary_200",
    input_background_fill="white",
)

css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
                 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif !important;
}

.gradio-container {
    background: linear-gradient(135deg, #f5f7fa 0%, #e9edf5 100%) !important;
}

.main-card {
    max-width: 880px;
    margin: 24px auto !important;
    border-radius: 24px !important;
    box-shadow: 0 12px 40px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04) !important;
    background: white !important;
    padding: 24px 28px !important;
}

#chatbot {
    border-radius: 16px !important;
    border: 1px solid #e8ecf1 !important;
    background: #fafbfc !important;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.02) !important;
}

.example {
    border-radius: 20px !important;
    padding: 6px 18px !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    background: #f0f4ff !important;
    border: 1px solid #d0dcff !important;
    color: #1e3a8a !important;
    transition: all 0.15s ease;
}
.example:hover {
    background: #e0e9ff !important;
    border-color: #b0c4ff !important;
    transform: translateY(-1px);
}

#input-box textarea {
    border-radius: 20px !important;
    padding: 12px 18px !important;
    border: 1px solid #dce1e8 !important;
    background: white !important;
    transition: border-color 0.15s ease;
}
#input-box textarea:focus {
    border-color: #4f8cff !important;
    box-shadow: 0 0 0 3px rgba(79,140,255,0.1) !important;
}

#send-btn {
    border-radius: 20px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    background: linear-gradient(135deg, #4f8cff 0%, #1e5ee0 100%) !important;
    border: none !important;
    box-shadow: 0 2px 6px rgba(79,140,255,0.3);
    transition: all 0.2s ease;
}
#send-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(79,140,255,0.4);
}

.app-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 4px;
}
.app-subtitle {
    font-size: 0.95rem;
    color: #6b7c93;
    text-align: center;
    margin-bottom: 20px;
    font-weight: 400;
}
"""

examples = [
    "查询订单 ORD202604130001",
    "最近有延误的订单吗？帮我分析原因",
    "我明天有个上海到北京的急件，怎么发最划算？",
    "如何降低20%的运输成本？",
]

# ── 核心修改：respond 函数返回元组格式历史 ──
def respond(message, history):
    history = history or []
    try:
        response = chat(message, user_id="gradio_user")
    except Exception as e:
        response = f"出错了：{e}"
    history.append((message, response))
    return "", history

# ── 构建 Blocks 界面 ──
with gr.Blocks(theme=theme, css=css, title="物流AI调度助手") as demo:
    gr.HTML("""
    <div class="app-title">🚚 物流AI调度助手</div>
    <div class="app-subtitle">查订单 · 问延误 · 优化路线 — 智能物流中枢</div>
    """)

    with gr.Column(elem_classes="main-card"):
        chatbot = gr.Chatbot(
            elem_id="chatbot",
            height=520,
            placeholder="在下方输入您的问题…",
            avatar_images=(
                None,
                "https://img.icons8.com/fluency/48/chatbot.png",
            ),
            bubble_full_width=False,
            layout="bubble",
        )

        with gr.Row():
            msg = gr.Textbox(
                show_label=False,
                placeholder="例如：查订单、问延误、优化路线…",
                container=False,
                scale=8,
                elem_id="input-box",
            )
            submit_btn = gr.Button("发送", variant="primary", elem_id="send-btn")

        gr.Examples(
            examples=examples,
            inputs=msg,
            label=None,
        )

        clear_btn = gr.Button("🗑️ 清空对话", variant="secondary", size="sm")

    # 事件绑定
    msg.submit(
        respond,
        [msg, chatbot],
        [msg, chatbot],
    )
    submit_btn.click(
        respond,
        [msg, chatbot],
        [msg, chatbot],
    )
    clear_btn.click(
        lambda: [],
        outputs=[chatbot],
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1")