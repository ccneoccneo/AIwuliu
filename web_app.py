import gradio as gr
from agent import chat

def chat_with_ai(message, history):
    """和AI对话（查订单走本地模拟库，其它走大模型）"""
    try:
        # Gradio未提供稳定的用户ID，这里用一个固定ID维持多轮记忆
        return chat(message, user_id="gradio_user")
    except Exception as e:
        return f"出错了：{e}"

# 创建网页界面
gr.ChatInterface(
    fn=chat_with_ai,
    title="物流AI调度助手",
    description="问我任何物流问题：查订单、问延误、优化路线..."
).launch()
