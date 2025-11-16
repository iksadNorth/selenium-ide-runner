FROM python:3.11-slim

# Node.js 설치 (selenium-side-runner를 위해 필요)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install uv

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치 (uv 사용)
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# selenium-side-runner 및 드라이버 설치
RUN npm install -g selenium-side-runner chromedriver geckodriver

# 애플리케이션 코드 복사
COPY main.py .
COPY src/* ./src/

# 디렉토리 생성
RUN mkdir -p scenarios reports

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

