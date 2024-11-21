# 首个阶段，使用构建基础镜像
FROM python:3.10-slim-bullseye AS builder

ENV PYTHONIOENCODING=utf-8

WORKDIR /app

# 安装build依赖，包括 Rust 和 Cargo，并保持清洁，尽可能小的构建环境
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y build-essential curl libssl-dev pkg-config \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && apt-get clean \
    && rm -rf /var/lib/apt-get/lists/*

# 确保 Cargo 在 PATH 中
ENV PATH="/root/.cargo/bin:${PATH}"

# 复制需求文件，并且安装Python依赖
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 第二阶段, 构建最终小镜像
FROM python:3.10-slim-bullseye

ENV PYTHONIOENCODING=utf-8

WORKDIR /app

# 复制构建阶段产物
COPY --from=builder /root/.cache /root/.cache
COPY --from=builder /usr/local /usr/local
COPY --from=builder /usr/lib /usr/lib

# 设置时区
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    rm -rf /var/lib/apt-get/lists/*

# 从构建阶段复制已经下载好的依赖包
COPY . .

# 预下载或执行可能会生成大的临时文件的步骤
RUN python3 _download_web.py || (echo "Failed to download web file" && exit 1)

EXPOSE 13200

VOLUME ["/app/result", "/app/cache"]

CMD ["python3", "_httpserver_test.py"]