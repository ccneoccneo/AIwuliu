# 物流AI调度助手

## 功能
- ✅ 意图识别（查订单/问延误/要调度）
- ✅ 多轮对话记忆（记住你说过的话）
- ✅ 高并发优化（线程池+TTL缓存）
- ✅ 网页界面（Gradio）

## 运行方法
1. 安装依赖：`pip install -r requirements.txt`
2. 创建 `.env` 文件，填入：`DEEPSEEK_API_KEY=你的密钥`
3. 运行：`python main.py` 或 `python web_app.py`

## 技术栈
- Python
- DeepSeek API
- cachetools（缓存）
- gradio（网页界面）

## 项目结构
- agent.py - 核心逻辑
- main.py - 命令行入口
- web_app.py - 网页入口
