# ==============================================================================
# Poetry Demo - FastAPI Application Docker Image  
# Python 3.10 기반, uv 패키지 매니저 사용
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder - 의존성 설치
# ------------------------------------------------------------------------------
FROM python:3.10-slim AS builder

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 파일 및 프로젝트 파일 복사 (README.md는 메타데이터 생성에 필요)
COPY pyproject.toml uv.lock README.md ./
COPY app/ ./app/

# uv sync를 사용하여 의존성 설치 (가상환경 자동 생성)
# --frozen: uv.lock 파일을 업데이트하지 않고 그대로 사용
# --no-dev: 개발용 의존성 제외
RUN uv sync --frozen --no-dev

# ------------------------------------------------------------------------------
# Stage 2: Production
# ------------------------------------------------------------------------------
FROM python:3.10-slim AS production

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"

# 비root 사용자 생성
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# 가상환경 복사
COPY --from=builder /app/.venv /app/.venv

# 애플리케이션 코드 복사
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup pyproject.toml ./

# 비root 사용자로 전환
USER appuser

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

# 포트 노출
EXPOSE 8001

# 애플리케이션 실행
CMD ["uvicorn", "app.router:app", "--host", "0.0.0.0", "--port", "8001"]
