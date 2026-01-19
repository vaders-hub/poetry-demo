# Claude 임시 파일 정리 가이드

## ✅ Claude 임시 파일이란?

Claude Code가 작업 중 생성하는 임시 파일 및 디렉토리입니다.

### 1. tmpclaude-* 디렉토리
세션별로 생성되는 임시 작업 디렉토리 (예: `tmpclaude-47ea-cwd`)

**특징**:
- 각 세션마다 새로운 디렉토리 생성
- 작업 컨텍스트 및 캐시 저장
- 세션 종료 후에도 남아있음
- 삭제해도 안전함 (다시 생성됨)
- 현재 프로젝트: **55개** 존재, 총 **57KB**

### 2. *.cwd 파일
작업 디렉토리 상태를 저장하는 파일

**특징**:
- 세션별 작업 상태 저장
- 자동 생성되는 캐시 파일
- Git에 커밋할 필요 없음
- 삭제해도 안전함 (다시 생성됨)

---

## 🗑️ Claude 임시 파일 정리 방법

### 방법 1: Git에서 무시하기 (권장)

`.gitignore`에 추가되어 있습니다:

```gitignore
# Claude temporary directories
tmpclaude-*

# Claude Code working files
*.cwd
```

이제 Claude 임시 파일들은 Git에서 자동으로 무시됩니다.

---

### 방법 2: 수동으로 삭제

#### tmpclaude-* 디렉토리 삭제

**Windows (PowerShell)**
```powershell
# 프로젝트 루트에서 실행
Remove-Item -Path "tmpclaude-*" -Recurse -Force

# 확인
Get-ChildItem -Path . -Filter "tmpclaude-*" -Directory
```

**Windows (CMD)**
```cmd
# 프로젝트 루트에서 실행
for /d %i in (tmpclaude-*) do @rd /s /q "%i"

# 확인
dir /b /ad tmpclaude-*
```

**Linux/Mac**
```bash
# 프로젝트 루트에서 실행
rm -rf tmpclaude-*

# 확인
ls -d tmpclaude-* 2>/dev/null
```

---

### 방법 3: .cwd 파일 삭제

#### Windows (PowerShell)
```powershell
# 프로젝트 루트에서 실행
Get-ChildItem -Path . -Filter "*.cwd" -Recurse | Remove-Item -Force

# 확인
Get-ChildItem -Path . -Filter "*.cwd" -Recurse
```

#### Windows (CMD)
```cmd
# 프로젝트 루트에서 실행
del /s /q *.cwd

# 확인
dir /s /b *.cwd
```

#### Linux/Mac
```bash
# 프로젝트 루트에서 실행
find . -name "*.cwd" -type f -delete

# 확인
find . -name "*.cwd" -type f
```

---

### 방법 3: Python 스크립트로 정리

프로젝트에 정리 스크립트를 추가할 수 있습니다:

```python
# scripts/cleanup_cwd.py
import os
from pathlib import Path

def cleanup_cwd_files(root_dir="."):
    """
    .cwd 파일 정리
    """
    root = Path(root_dir)
    cwd_files = list(root.rglob("*.cwd"))

    if not cwd_files:
        print("✅ .cwd 파일이 없습니다.")
        return

    print(f"🗑️  {len(cwd_files)}개의 .cwd 파일 발견")

    for file in cwd_files:
        try:
            file.unlink()
            print(f"  삭제: {file}")
        except Exception as e:
            print(f"  ❌ 삭제 실패: {file} - {e}")

    print(f"\n✅ 정리 완료: {len(cwd_files)}개 파일 삭제")

if __name__ == "__main__":
    cleanup_cwd_files()
```

**실행**:
```bash
poetry run python scripts/cleanup_cwd.py
```

---

## 📋 관련 파일들도 정리하기

### 다른 임시/캐시 파일들

```bash
# Python 캐시
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# pytest 캐시
rm -rf .pytest_cache

# mypy 캐시
rm -rf .mypy_cache

# 로그 파일
find . -name "*.log" -delete

# 임시 파일
find . -name "*.tmp" -delete
find . -name "*~" -delete
```

---

## 🔧 자동화 스크립트

### Makefile 추가

`Makefile`을 프로젝트 루트에 생성:

```makefile
.PHONY: clean clean-cwd clean-pyc clean-claude clean-all

# .cwd 파일만 정리
clean-cwd:
	@echo "🗑️  Cleaning .cwd files..."
	@find . -name "*.cwd" -type f -delete
	@echo "✅ Done"

# Python 캐시 정리
clean-pyc:
	@echo "🗑️  Cleaning Python cache..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@rm -rf .pytest_cache .mypy_cache
	@echo "✅ Done"

# Claude 임시 디렉토리 정리
clean-claude:
	@echo "🗑️  Cleaning Claude temp directories..."
	@rm -rf tmpclaude-*
	@find . -name "*.cwd" -type f -delete
	@echo "✅ Done"

# 전체 정리
clean-all: clean-cwd clean-pyc clean-claude
	@echo "🗑️  Cleaning all temporary files..."
	@find . -name "*.log" -delete
	@find . -name "*.tmp" -delete
	@find . -name "*~" -delete
	@echo "✅ All cleaned!"

# 기본 clean (pyc만)
clean: clean-pyc
```

**사용**:
```bash
# .cwd 파일만 삭제
make clean-cwd

# Python 캐시 삭제
make clean-pyc

# Claude 임시 디렉토리 삭제 (tmpclaude-* + *.cwd)
make clean-claude

# 전체 정리
make clean-all
```

---

### Poetry 스크립트 추가

`pyproject.toml`에 추가:

```toml
[tool.poetry.scripts]
clean-cwd = "scripts.cleanup_cwd:cleanup_cwd_files"
clean-pyc = "scripts.cleanup_pyc:cleanup_python_cache"
clean-all = "scripts.cleanup_all:cleanup_all_temp_files"
```

**사용**:
```bash
poetry run clean-cwd
poetry run clean-pyc
poetry run clean-all
```

---

## 🚫 .gitignore 전체 권장 설정

```gitignore
# Environment
.env
.env.local
.env.*.local
.Config.ini

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Testing
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
.nox/
.hypothesis/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
.pytype/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~
.project
.pydevproject
.settings/

# Claude Code
.claude/
tmpclaude-*
*.cwd

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
```

---

## 📊 .cwd 파일 분석

### 파일 크기 확인

```bash
# 전체 .cwd 파일 크기
find . -name "*.cwd" -type f -exec du -ch {} + | grep total

# 개별 파일 크기
find . -name "*.cwd" -type f -exec ls -lh {} \;
```

### 파일 개수 확인

```bash
# .cwd 파일 개수
find . -name "*.cwd" -type f | wc -l

# 디렉토리별 개수
find . -name "*.cwd" -type f | xargs dirname | sort | uniq -c
```

---

## ⚠️ 주의사항

### 삭제해도 안전한 파일들
- ✅ `*.cwd` - 다시 생성됨
- ✅ `__pycache__/` - 자동 생성됨
- ✅ `.pytest_cache/` - 테스트 시 생성됨
- ✅ `*.pyc` - 컴파일 시 생성됨
- ✅ `*.log` - 로그 파일

### 삭제하면 안 되는 파일들
- ❌ `.env` - 환경 설정 (이미 .gitignore에 있음)
- ❌ `poetry.lock` - 의존성 잠금 파일
- ❌ `pyproject.toml` - 프로젝트 설정
- ❌ 소스 코드 (`.py`, `.md` 등)

---

## 🔄 CI/CD에서 정리

### GitHub Actions 예시

`.github/workflows/cleanup.yml`:

```yaml
name: Cleanup Temp Files

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check for .cwd files
        run: |
          if find . -name "*.cwd" -type f | grep -q .; then
            echo "❌ .cwd files found - please add to .gitignore"
            find . -name "*.cwd" -type f
            exit 1
          else
            echo "✅ No .cwd files"
          fi
```

---

## 📝 체크리스트

정리 전 확인사항:

- [ ] `.gitignore`에 `tmpclaude-*` 추가됨 (✅ 이미 적용)
- [ ] `.gitignore`에 `*.cwd` 추가됨 (✅ 이미 적용)
- [ ] 현재 작업 중인 파일 저장됨
- [ ] Git 커밋 상태 확인

정리 방법 선택:

- [ ] `.gitignore`만 유지 (권장 - 이미 적용됨)
- [ ] tmpclaude-* 디렉토리 삭제 (55개, 57KB)
- [ ] .cwd 파일 삭제
- [ ] Makefile 추가하여 자동화

---

## 🎯 권장 워크플로우

### 1. 현재 상태 (이미 완료됨)
```bash
# .gitignore 이미 설정됨 ✅
# tmpclaude-* 와 *.cwd 모두 무시됨
```

### 2. tmpclaude-* 디렉토리 정리 (선택사항)
```bash
# 현재 55개 디렉토리 (57KB) 존재
# 원하면 정리 가능:
rm -rf tmpclaude-*

# 또는 Makefile 사용:
make clean-claude
```

### 3. 정기적 정리 (선택사항)
```bash
# 주간 정리 - 모든 임시 파일
make clean-all

# 또는 Claude 임시 파일만
make clean-claude
```

### 4. PR 전 체크
```bash
# 임시 파일 확인
git status --ignored

# Claude 임시 파일은 자동으로 무시됨 ✅
```

---

## 📚 관련 문서

- [.gitignore 패턴](https://git-scm.com/docs/gitignore)
- [Python 캐시 파일 관리](https://docs.python.org/3/tutorial/modules.html#compiled-python-files)
- [프로젝트 구조 가이드](README.md)

---

**작성일**: 2026-01-15
**버전**: 1.0.0
**적용 상태**: ✅ .gitignore 업데이트 완료
