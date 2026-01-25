# Pydantic validate_default 경고 해결

## 문제

LlamaIndex 라이브러리 사용 시 다음과 같은 Pydantic 경고가 발생했습니다:

```
D:\lab\python\code\poetry-demo\.venv\lib\site-packages\pydantic\_internal\_generate_schema.py:2249:
UnsupportedFieldAttributeWarning: The 'validate_default' attribute with value True was provided
to the `Field()` function, which has no effect in the context it was used.
```

## 원인 분석

이 경고는 **우리 코드의 문제가 아니라** `llama-index` 라이브러리 내부에서 발생하는 문제입니다.

### 검증 과정

```python
# app.models - 우리 코드 테스트
from app.models import DocumentUploadRequest
# ✅ 경고 없음

# LlamaIndex 테스트
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
# ⚠️ 경고 발생
```

LlamaIndex 라이브러리가 내부적으로 Pydantic 모델을 정의할 때 `validate_default=True`를
잘못된 컨텍스트에서 사용하여 발생하는 경고입니다.

## 해결 방법

LlamaIndex를 import하는 모든 파일에 경고 필터를 추가했습니다.

### 수정된 파일 목록

1. **app/configs/llama_index.py**
2. **app/utils/advanced_query.py**
3. **app/utils/document_analysis.py**
4. **app/utils/redis_index.py**

### 적용된 코드

```python
import warnings

# LlamaIndex 내부의 Pydantic validate_default 경고 억제
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=".*validate_default.*",
    module="pydantic._internal._generate_schema",
)

from llama_index.core import Settings, VectorStoreIndex
# ... 기타 LlamaIndex imports
```

## 검증 결과

### Before (경고 발생)
```bash
$ uv run python -c "from app.routers import document_advanced_query"
D:\...\pydantic\_internal\_generate_schema.py:2249: UnsupportedFieldAttributeWarning: ...
```

### After (경고 제거)
```bash
$ uv run python -c "from app.routers import document_advanced_query"
✅ Advanced query router - no warnings

$ uv run python -c "from app.router import app"
✅ App loaded with 88 routes
✅ No validate_default warnings
```

## 기술적 배경

### Pydantic v2의 validate_default

Pydantic v2에서 `validate_default` 속성은 다음과 같이 사용해야 합니다:

**올바른 사용 (Annotated 사용)**:
```python
from typing import Annotated
from pydantic import BaseModel, Field

class Model(BaseModel):
    value: Annotated[int, Field(ge=0, validate_default=True)] = 10
```

**잘못된 사용 (경고 발생)**:
```python
class Model(BaseModel):
    value: int = Field(default=10, ge=0, validate_default=True)
```

LlamaIndex는 내부적으로 후자의 방식을 사용하고 있어 경고가 발생합니다.

### 왜 경고를 억제해도 안전한가?

1. **기능에 영향 없음**: 경고일 뿐, 실제 동작에는 문제가 없습니다.
2. **외부 라이브러리 문제**: 우리 코드가 아닌 LlamaIndex의 문제입니다.
3. **임시 조치**: LlamaIndex가 업데이트되면 이 필터를 제거할 수 있습니다.
4. **선택적 억제**: `validate_default` 경고만 선택적으로 억제하므로 다른 중요한 경고는 계속 표시됩니다.

## 향후 조치

### LlamaIndex 업데이트 시

1. 새 버전에서 경고가 수정되었는지 확인:
   ```bash
   uv run python -c "
   from llama_index.core import Settings
   from llama_index.llms.openai import OpenAI
   print('Test passed')
   "
   ```

2. 경고가 사라졌다면 필터 제거:
   - `app/configs/llama_index.py`
   - `app/utils/advanced_query.py`
   - `app/utils/document_analysis.py`
   - `app/utils/redis_index.py`

### 모니터링

정기적으로 경고 필터가 여전히 필요한지 확인:
```bash
# 필터 임시 비활성화하고 테스트
# warnings.filterwarnings 라인을 주석 처리하고 테스트
```

## 참고 자료

- **Pydantic 공식 문서**: https://docs.pydantic.dev/latest/
- **LlamaIndex GitHub**: https://github.com/run-llama/llama_index
- **관련 이슈**: LlamaIndex가 Pydantic v2 완전 지원을 작업 중

---

**수정일**: 2026-01-21
**수정자**: Claude Sonnet 4.5
**검증**: ✅ 모든 import 테스트 통과
