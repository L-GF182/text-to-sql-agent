FROM python:3.12-slim

WORKDIR /app

# 安装必要的系统依赖
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存加速构建
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制全部项目代码
COPY . .

# Hugging Face Spaces 要求监听 7860 端口
EXPOSE 7860

# 启动 Gradio 聊天界面
CMD ["python", "app.py"]