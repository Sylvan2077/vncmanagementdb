# 基于 Python 3.10-base 基础镜像
FROM python:3.10-base

# 设置工作目录
ENV SERVICE_HOME=/service

# 设置镜像的工作目录，程序代码放在该目录中
WORKDIR $SERVICE_HOME

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    libmagic1 libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建目录
RUN mkdir $SERVICE_HOME -p

# 复制程序代码文件到服务运行目录
COPY . $SERVICE_HOME

# 复制项目文件到工作目录
COPY . /app

COPY user_management-0.1.0-py3-none-any.whl .
COPY vnc_session_client-0.1.0-py3-none-any.whl .

# 运行 pip 命令安装依赖项
# 安装依赖（确保用当前环境的 pip）
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --no-cache-dir \
    -r /$SERVICE_HOME/requirements.txt \
    ./user_management-0.1.0-py3-none-any.whl \
    ./vnc_session_client-0.1.0-py3-none-any.whl

# 开放应用程序的端口
EXPOSE 10086

# 启动 Django 项目
CMD ["python3", "manage.py", "runserver", "0.0.0.0:10086"]

# 镜像维护者
MAINTAINER qa-team

