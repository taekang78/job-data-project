import os
import sys
import time
import pathlib
import requests
from dotenv import load_dotenv

# ─── 프로젝트 루트 경로 설정 및 .env 로드 ──────────────────────────────────
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# ─── 사람인 API 설정 ────────────────────────────────────────────────────────
SARAMIN_API_URL   = "https://oapi.saramin.co.kr/job-search"

# 사람인 API 문서 기준 검색어 파라미터 이름.
# 공식 문서는 "keywords" 이나 일부 예제에서 "keyword"로 표기되기도 함.
# 실제 동작하지 않을 경우 아래 상수만 변경하면 모든 호출에 반영됩니다.
SEARCH_PARAM_NAME = "keywords"

# ─── 수집 대상 키워드 목록 ──────────────────────────────────────────────────
KEYWORDS = [
    "은행 디지털",
    "금융 IT",
    "금융 데이터",
    "데이터분석",
    "핀테크",
    "디지털",
    "IT",
]

# 페이지당 최대 공고 수 (사람인 API 최대 110)
COUNT_PER_PAGE = 110

# 키워드 사이 호출 대기 시간 (초) – 과도한 요청 방지
SLEEP_SECONDS = 1.0


def _get_access_key() -> str:
    """
    .env에서 SARAMIN_ACCESS_KEY를 읽어 반환합니다.
    키가 없으면 안내 메시지를 출력하고 프로세스를 종료합니다.
    """
    key = os.environ.get("SARAMIN_ACCESS_KEY", "").strip()
    if not key:
        print("\n" + "=" * 60)
        print("❌ [Extract] SARAMIN_ACCESS_KEY 가 설정되지 않았습니다.")
        print()
        print("  1. https://oapi.saramin.co.kr 에서 API 키를 발급받으세요.")
        print("  2. 프로젝트 루트의 .env 파일에 아래 내용을 추가하세요:")
        print()
        print("       SARAMIN_ACCESS_KEY=발급받은_사람인_API_KEY")
        print()
        print("  3. 이후 다시 python data_pipeline/run_pipeline.py 를 실행하세요.")
        print("=" * 60 + "\n")
        sys.exit(1)
    return key


def _fetch_jobs_for_keyword(access_key: str, keyword: str) -> list[dict]:
    """
    단일 키워드에 대해 사람인 채용정보 API를 호출하고,
    원본(raw) 공고 딕셔너리 리스트를 반환합니다.

    Parameters
    ----------
    access_key : str
        사람인 API access-key
    keyword : str
        검색 키워드

    Returns
    -------
    list[dict]
        파싱된 원본 공고 목록
    """
    params = {
        "access-key":       access_key,
        SEARCH_PARAM_NAME:  keyword,
        "count":            COUNT_PER_PAGE,
        "fields":           "expiration-date,posting-date",
    }
    headers = {
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            SARAMIN_API_URL,
            params=params,
            headers=headers,
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"  ❌ [Extract] 네트워크 오류 (키워드: '{keyword}'): {e}")
        return []

    if response.status_code != 200:
        print(
            f"  ❌ [Extract] API 응답 오류 (키워드: '{keyword}') "
            f"→ HTTP {response.status_code}"
        )
        return []

    try:
        data = response.json()
    except ValueError:
        print(f"  ❌ [Extract] JSON 파싱 실패 (키워드: '{keyword}')")
        return []

    # ── 응답 구조 안전 탐색 ────────────────────────────────────────────────
    # 사람인 API 응답: { "job-search": { "jobs": { "job": [...], "total": N } } }
    job_search = data.get("job-search", {})
    jobs_obj   = job_search.get("jobs", {})
    job_list   = jobs_obj.get("job", [])

    if not isinstance(job_list, list):
        # total == 1 이면 사람인이 리스트 대신 단일 dict로 반환하는 경우 있음
        job_list = [job_list] if job_list else []

    if not job_list:
        print(f"  ℹ️  [Extract] 검색 결과 없음 (키워드: '{keyword}')")
        return []

    # ── 필드 추출 ────────────────────────────────────────────────────────────
    raw_jobs = []
    for job in job_list:
        try:
            company  = job.get("company",  {}).get("name",  {}).get("$", "")
            title    = job.get("position", {}).get("title", "")
            link     = job.get("url",      "")

            location   = (
                job.get("position", {})
                   .get("location", {})
                   .get("name",     "")
            )
            experience = (
                job.get("position", {})
                   .get("experience-level", {})
                   .get("name", "")
            )
            education  = (
                job.get("position", {})
                   .get("required-education-level", {})
                   .get("name", "")
            )
            deadline   = job.get("expiration-date", "")

            raw_jobs.append({
                "company":        company,
                "title":          title,
                "link":           link,
                "location":       location,
                "experience":     experience,
                "education":      education,
                "deadline":       deadline,
                "source":         "saramin_api",
                "search_keyword": keyword,
            })

        except (AttributeError, TypeError):
            # 개별 공고 파싱 실패 시 해당 건만 건너뜀
            continue

    return raw_jobs


def extract_jobs() -> list[dict]:
    """
    [Extract] 사람인 공식 채용정보 API를 사용해 다중 키워드로 채용공고를 수집합니다.

    - SARAMIN_ACCESS_KEY (.env) 가 없으면 안내 메시지 출력 후 종료
    - 키워드별 API 호출 후 결과를 단일 리스트로 병합하여 반환
    - 호출 간 SLEEP_SECONDS 대기 (과도한 요청 방지)

    Returns
    -------
    list[dict]
        수집된 원본 공고 딕셔너리 리스트
    """
    access_key = _get_access_key()

    print("\n" + "=" * 60)
    print(" 📡 [Extract] 사람인 공식 API 수집을 시작합니다.")
    print(f"    검색 키워드 ({len(KEYWORDS)}개): {KEYWORDS}")
    print("=" * 60)

    all_raw_jobs: list[dict] = []

    for idx, keyword in enumerate(KEYWORDS, start=1):
        print(f"\n  🔍 [{idx}/{len(KEYWORDS)}] 키워드: '{keyword}' 수집 중...")

        jobs = _fetch_jobs_for_keyword(access_key, keyword)
        all_raw_jobs.extend(jobs)
        print(f"  ✔️  수집: {len(jobs)}건 (누적: {len(all_raw_jobs)}건)")

        # 마지막 키워드 이후에는 sleep 생략
        if idx < len(KEYWORDS):
            time.sleep(SLEEP_SECONDS)

    print(f"\n✅ [Extract] 전체 수집 완료 → 총 {len(all_raw_jobs)}건\n")
    return all_raw_jobs
