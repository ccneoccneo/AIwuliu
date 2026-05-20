from cachetools import TTLCache
import time
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from dotenv import load_dotenv
import os
import sys

# ====== 真实订单（模拟库） ======
from order_db import extract_order_query, format_order_result, query_orders

# ====== 加载密钥 ======
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ====== 配置DeepSeek API ======
client = OpenAI(
    api_key="sk-19eedce8378e40208c39847a5a365c43",
    base_url="https://api.deepseek.com"
)
# ====== 系统提示词 ======
SYSTEM_PROMPT = """
你是专业的物流AI调度指挥官，精通快递配送全链路优化。
用户输入物流相关问题，你必须：
1.先精准识别用户意图（查订单、问延误、要调度、其他）
2.给出专业、可落地的分析和解决方案
3.语言简洁，分点输出，符合物流行业规范
禁止闲聊，只输出专业内容。"""


# ====== 意图识别 ======
def recognize_intent(user_input):
    """识别用户意图，拆解任务"""
    if "订单" in user_input or "查" in user_input:
        return "query_order", "订单查询任务"
    elif "迟到" in user_input or "延误" in user_input:
        return "analyze_delay", "延误原因分析任务"
    elif "优化" in user_input or "调度" in user_input:
        return "optimize_schedule", "配送调度优化任务"
    else:
        return "general_query", "通用物流咨询任务"


# ====== 缓存和线程池 ======
cache = TTLCache(maxsize=100, ttl=300)
executor = ThreadPoolExecutor(max_workers=8)

from datetime import datetime

# 用来存每个人的对话历史
conversation_history = {}


def call_llm(prompt, user_input, user_id="default"):
    """调用大模型，支持多轮对话记忆"""

    # 获取这个用户的对话历史
    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": prompt}
        ]

    # 把用户的新问题加进去
    conversation_history[user_id].append({"role": "user", "content": user_input})

    # 只保留最近10轮（防止太长）
    if len(conversation_history[user_id]) > 21:  # 10轮对话 = 20条 + 1条system
        conversation_history[user_id] = [conversation_history[user_id][0]] + conversation_history[user_id][-20:]

    # 调用大模型
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=conversation_history[user_id],  # 传入完整历史
            temperature=0.7,
            max_tokens=2000
        )

        result = response.choices[0].message.content

        # 把AI的回答也存进历史
        conversation_history[user_id].append({"role": "assistant", "content": result})

        return result

    except Exception as e:
        print(f"API调用失败: {e}")
        return f"系统繁忙: {e}"


def handle_query_order(user_input: str) -> str:
    """
    “查询真实订单”能力：
    - 优先从用户输入提取：订单号 / 手机号 / 姓名
    - 命中则返回订单详情（不依赖大模型）
    - 未命中则引导用户补全关键信息
    """
    q = extract_order_query(user_input)
    order_id, phone, customer_name = q.get("order_id"), q.get("phone"), q.get("customer_name")

    if not any([order_id, phone, customer_name]):
        return (
            "【订单查询】\n"
            "- 请提供任意一个信息以查询真实订单：订单号 / 手机号（11位）/ 收件人姓名\n"
            "- 例如：查订单 ORD202604130001 或 手机 13800138000"
        )

    results = query_orders(order_id=order_id, phone=phone, customer_name=customer_name)

    if not results:
        provided = "、".join([x for x in [order_id, phone, customer_name] if x])
        return (
            "【订单查询未命中】\n"
            f"- 已按你提供的信息查询：{provided}\n"
            "- 建议你补充：完整订单号 或 绑定手机号（11位）"
        )

    if len(results) == 1:
        return format_order_result(results[0])

    # 多条匹配，返回列表让用户确认
    lines = ["【订单查询结果（多条匹配）】", "- 请回复你要查询的订单号："]
    for o in results[:10]:
        lines.append(
            f"  - {o.get('order_id')}｜{o.get('customer_name')}｜手机尾号{str(o.get('phone',''))[-4:]}｜{o.get('status')}"
        )
    return "\n".join(lines)


def chat(user_input: str, user_id: str = "user1") -> str:
    """统一对外的对话入口：先走工具能力，再走大模型。"""
    intent, _task = recognize_intent(user_input)
    if intent == "query_order":
        return handle_query_order(user_input)
    return call_llm(SYSTEM_PROMPT, user_input, user_id=user_id)

# ====== 主对话循环 ======
def chat_loop():
    # Windows 控制台下尽量避免中文乱码（不影响 Web/Gradio）
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("====================================")
    print("   物流AI调度助手 v2.0 (真·AI版)")
    print("   输入问题，AI会智能回答")
    print("   输入exit退出")
    print("====================================")

    while True:
        user_input = input("\n请输入您的问题：")
        if user_input.lower() == "exit":
            print("感谢使用物流AI调度助手！")
            break

        # 意图识别
        intent, task = recognize_intent(user_input)
        print(f"\n【任务拆解】：{task}")
        print("【AI思考中...】")

        # 异步调用（查订单走本地库，其它走大模型）
        future = executor.submit(chat, user_input, "user1")
        result = future.result()

        # 输出结果
        print("\n【AI调度分析结果】")
        print(result)
