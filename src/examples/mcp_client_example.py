"""
MCP Client Example

간단한 MCP 클라이언트 예제입니다.
FastAPI 서버의 MCP 엔드포인트를 호출하는 방법을 보여줍니다.
"""

import requests
import json


BASE_URL = "http://localhost:8001/mcp"


def print_response(response):
    """응답을 보기 좋게 출력합니다."""
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("\n" + "="*70 + "\n")


def get_mcp_info():
    """MCP 서버 정보를 가져옵니다."""
    print("📋 MCP 서버 정보 조회")
    print("-" * 70)
    response = requests.get(f"{BASE_URL}/info")
    print_response(response)


def list_tools():
    """사용 가능한 도구 목록을 가져옵니다."""
    print("🔧 사용 가능한 도구 목록")
    print("-" * 70)
    response = requests.get(f"{BASE_URL}/tools")
    print_response(response)


def test_calculate():
    """계산 도구를 테스트합니다."""
    print("🧮 계산 도구 테스트")
    print("-" * 70)

    # 덧셈
    print("덧셈: 10 + 20")
    response = requests.post(
        f"{BASE_URL}/calculate",
        json={"operation": "add", "a": 10, "b": 20}
    )
    print_response(response)

    # 곱셈
    print("곱셈: 15 * 3")
    response = requests.post(
        f"{BASE_URL}/calculate",
        json={"operation": "multiply", "a": 15, "b": 3}
    )
    print_response(response)

    # 나눗셈
    print("나눗셈: 100 / 4")
    response = requests.post(
        f"{BASE_URL}/calculate",
        json={"operation": "divide", "a": 100, "b": 4}
    )
    print_response(response)


def test_text_stats():
    """텍스트 통계 도구를 테스트합니다."""
    print("📊 텍스트 통계 도구 테스트")
    print("-" * 70)

    # 영문 텍스트
    print("영문 텍스트 분석:")
    response = requests.post(
        f"{BASE_URL}/text-stats",
        json={"text": "The quick brown fox jumps over the lazy dog"}
    )
    print_response(response)

    # 한글 텍스트
    print("한글 텍스트 분석:")
    response = requests.post(
        f"{BASE_URL}/text-stats",
        json={"text": "안녕하세요! MCP 서버 테스트입니다."}
    )
    print_response(response)


def test_health_check():
    """헬스 체크를 수행합니다."""
    print("❤️ 헬스 체크")
    print("-" * 70)
    response = requests.get(f"{BASE_URL}/health")
    print_response(response)


def main():
    """메인 함수"""
    print("\n" + "="*70)
    print("🚀 MCP Client Example - FastAPI 서버 테스트")
    print("="*70 + "\n")

    try:
        # 1. 서버 정보 조회
        get_mcp_info()

        # 2. 도구 목록 조회
        list_tools()

        # 3. 계산 도구 테스트
        test_calculate()

        # 4. 텍스트 통계 도구 테스트
        test_text_stats()

        # 5. 헬스 체크
        test_health_check()

        print("✅ 모든 테스트가 성공적으로 완료되었습니다!")

    except requests.exceptions.ConnectionError:
        print("❌ 오류: 서버에 연결할 수 없습니다.")
        print("FastAPI 서버가 실행 중인지 확인하세요:")
        print("  python -m src.main")
        print("  또는")
        print("  poetry run start")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()
