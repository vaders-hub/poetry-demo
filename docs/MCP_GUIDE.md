# MCP (Model Context Protocol) 통합 가이드

이 프로젝트는 **MCP (Model Context Protocol)** 서버를 통합하여 LLM 애플리케이션에서 도구를 사용할 수 있도록 합니다.

## 📋 목차

1. [MCP란?](#mcp란)
2. [설치 방법](#설치-방법)
3. [MCP 서버 실행](#mcp-서버-실행)
4. [사용 가능한 도구](#사용-가능한-도구)
5. [API 엔드포인트](#api-엔드포인트)
6. [사용 예제](#사용-예제)
7. [Claude Desktop 연동](#claude-desktop-연동)

---

## MCP란?

**Model Context Protocol (MCP)**는 LLM 애플리케이션이 외부 도구 및 데이터 소스와 통신할 수 있도록 하는 표준 프로토콜입니다.

### 주요 특징:
- ✅ 표준화된 도구 호출 인터페이스
- ✅ LLM과 외부 시스템 간의 안전한 통신
- ✅ 재사용 가능한 도구 컴포넌트
- ✅ Claude Desktop 및 기타 MCP 클라이언트와 호환

---

## 설치 방법

### 1. 의존성 설치

```bash
pip install mcp
```

또는 poetry를 사용하는 경우:

```bash
poetry add mcp
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 필요한 설정을 추가합니다:

```bash
# Database Configuration
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=1521
DB_SERVICE_NAME=your_service_name

# OpenAI API Key
OPENAI_API_KEY=your_api_key_here
```

---

## MCP 서버 실행

### 독립 실행형 MCP 서버

MCP 서버를 독립적으로 실행하려면:

```bash
python src/mcp_server.py
```

이 서버는 stdio를 통해 통신하며, Claude Desktop 또는 다른 MCP 클라이언트와 연동할 수 있습니다.

### FastAPI와 함께 실행

FastAPI 애플리케이션을 실행하면 MCP 도구가 REST API 엔드포인트로도 제공됩니다:

```bash
python -m src.main
# 또는
poetry run start
```

서버가 `http://localhost:8001`에서 실행됩니다.

---

## 사용 가능한 도구

### 1. **get_all_customers**
데이터베이스에서 모든 고객 정보를 조회합니다.

**입력 파라미터:** 없음

**출력:**
```
Customers:
- ID: uuid-1234, Name: John Doe, Address: 123 Main St, Website: https://example.com, Credit Limit: 10000
...
```

### 2. **get_customer_by_id**
특정 고객의 상세 정보를 조회합니다.

**입력 파라미터:**
- `customer_id` (string, required): 고객 고유 ID

**출력:**
```
Customer Details:
ID: uuid-1234
Name: John Doe
Address: 123 Main St
Website: https://example.com
Credit Limit: 10000
```

### 3. **calculate**
기본 산술 연산을 수행합니다.

**입력 파라미터:**
- `operation` (string, required): 연산 종류 (`add`, `subtract`, `multiply`, `divide`)
- `a` (number, required): 첫 번째 숫자
- `b` (number, required): 두 번째 숫자

**출력:**
```
10 add 20 = 30
```

### 4. **text_stats**
텍스트 문자열의 통계를 계산합니다.

**입력 파라미터:**
- `text` (string, required): 분석할 텍스트

**출력:**
```
Text Statistics:
Characters: 28
Words: 5
Lines: 1

Most common characters:
  'e': 3
  'l': 3
  'o': 2
  ...
```

---

## API 엔드포인트

FastAPI 서버를 통해 다음 엔드포인트에 접근할 수 있습니다:

### GET `/mcp/tools`
사용 가능한 모든 MCP 도구 목록을 반환합니다.

**응답 예제:**
```json
{
  "success": true,
  "message": "Available MCP tools",
  "tools": [...]
}
```

### GET `/mcp/info`
MCP 서버 정보를 반환합니다.

**응답 예제:**
```json
{
  "success": true,
  "mcp_server": {
    "name": "poetry-demo-mcp-server",
    "version": "1.0.0",
    "protocol": "Model Context Protocol (MCP)"
  }
}
```

### POST `/mcp/calculate`
산술 계산을 수행합니다.

**요청 예제:**
```json
{
  "operation": "add",
  "a": 10,
  "b": 20
}
```

**응답 예제:**
```json
{
  "success": true,
  "tool": "calculate",
  "operation": "add",
  "operands": {"a": 10, "b": 20},
  "result": 30
}
```

### POST `/mcp/text-stats`
텍스트 통계를 계산합니다.

**요청 예제:**
```json
{
  "text": "Hello World! This is a test."
}
```

**응답 예제:**
```json
{
  "success": true,
  "tool": "text_stats",
  "statistics": {
    "character_count": 28,
    "word_count": 5,
    "line_count": 1,
    "most_common_characters": {
      "l": 3,
      "o": 2,
      ...
    }
  }
}
```

### GET `/mcp/health`
MCP 서버의 상태를 확인합니다.

---

## 사용 예제

### cURL을 사용한 예제

#### 1. 도구 목록 조회
```bash
curl http://localhost:8001/mcp/tools
```

#### 2. 계산 수행
```bash
curl -X POST http://localhost:8001/mcp/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "multiply",
    "a": 15,
    "b": 3
  }'
```

#### 3. 텍스트 분석
```bash
curl -X POST http://localhost:8001/mcp/text-stats \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog"
  }'
```

### Python 클라이언트 예제

```python
import requests

# 계산 수행
response = requests.post(
    "http://localhost:8001/mcp/calculate",
    json={
        "operation": "divide",
        "a": 100,
        "b": 4
    }
)
print(response.json())
# 출력: {"success": true, "tool": "calculate", "result": 25.0}

# 텍스트 통계
response = requests.post(
    "http://localhost:8001/mcp/text-stats",
    json={"text": "Hello, World!"}
)
print(response.json())
```

---

## Claude Desktop 연동

### 1. MCP 서버 설정 파일 생성

Claude Desktop에서 MCP 서버를 사용하려면 설정 파일을 추가합니다.

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

### 2. 설정 예제

```json
{
  "mcpServers": {
    "poetry-demo": {
      "command": "python",
      "args": [
        "D:\\lab\\python\\code\\poetry-demo\\src\\mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "D:\\lab\\python\\code\\poetry-demo"
      }
    }
  }
}
```

### 3. Claude Desktop 재시작

설정을 저장한 후 Claude Desktop을 재시작하면 MCP 도구를 사용할 수 있습니다.

### 4. Claude에서 사용하기

Claude Desktop에서 다음과 같이 요청할 수 있습니다:

```
"10과 20을 더해줘"
→ calculate 도구 사용

"이 텍스트를 분석해줘: Hello World"
→ text_stats 도구 사용

"모든 고객 정보를 보여줘"
→ get_all_customers 도구 사용
```

---

## 🔧 문제 해결

### MCP 서버가 시작되지 않음
- Python 경로가 올바른지 확인
- 필요한 의존성이 모두 설치되었는지 확인: `pip install mcp`
- 환경 변수가 올바르게 설정되었는지 확인

### 데이터베이스 연결 오류
- `.env` 파일의 데이터베이스 자격증명 확인
- 데이터베이스 서버가 실행 중인지 확인

### Claude Desktop에서 도구가 보이지 않음
- `claude_desktop_config.json` 파일 경로 확인
- JSON 형식이 올바른지 확인
- Claude Desktop 재시작

---

## 📚 추가 리소스

- [MCP 공식 문서](https://modelcontextprotocol.io)
- [Claude Desktop MCP 가이드](https://docs.anthropic.com/claude/docs/mcp)
- [FastAPI 문서](https://fastapi.tiangolo.com)

---

## 🤝 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해 주세요.
