import json
import argparse
import os

def extract_failed_tests(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    failed_results = []

    for test_result in data.get("testResults", []):
        for assertion in test_result.get("assertionResults", []):
            if assertion.get("status") != "failed": continue
            
            text = assertion.get("title")
            failureMessages = [
                msg.encode("utf-8").decode("unicode_escape")
                for msg in assertion.get("failureMessages", [])
            ]
            
            failed_results.append({
                "title": text,
                "failureMessages": failureMessages
            })

    return failed_results


def main():
    parser = argparse.ArgumentParser(
        description="Selenium-side-runner JSON 리포트에서 실패한 테스트만 추출"
    )
    parser.add_argument(
        "json_file",
        type=str,
        help="selenium-side-runner가 생성한 JSON 리포트 파일 경로"
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON 출력 들여쓰기 (기본값=2)"
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="실패 메시지를 평문으로 출력 (줄바꿈 포함)"
    )

    args = parser.parse_args()

    try:
        failed = extract_failed_tests(args.json_file)

        if args.plain:
            # 평문 출력
            for test in failed:
                print(f"=== {test['title']} ===")
                for msg in test["failureMessages"]:
                    print(msg)  # 이미 줄바꿈 적용됨
                print("\n")
        else:
            # JSON 출력
            print(json.dumps(failed, indent=args.indent, ensure_ascii=False))
        
    except Exception as e:
        print(f"[오류] {e}")


if __name__ == "__main__":
    main()
