from fastapi import FastAPI, Query
import pymysql

# =====================================================================
# FastAPI 채용공고 조회 API
# ---------------------------------------------------------------------
# 실행 방법:
#   1. 패키지 설치: pip install fastapi uvicorn pymysql
#   2. 서버 시작:   uvicorn api:app --reload
#   3. 브라우저에서 확인:
#      - 전체 조회:        http://127.0.0.1:8000/jobs
#      - 키워드 필터 조회: http://127.0.0.1:8000/jobs?keyword=백엔드
#      - 회사명 필터 조회: http://127.0.0.1:8000/jobs?company=카카오
#      - 복합 필터 조회:   http://127.0.0.1:8000/jobs?keyword=백엔드&company=카카오
#      - API 자동 문서:    http://127.0.0.1:8000/docs   ← 여기서 직접 테스트 가능!
#
# [v1.1 변경사항] 최신순 정렬 추가
#   - ORDER BY created_at DESC : 실제 공고 등록 시각 기준 최신순 정렬
#
# [v1.2 변경사항] company 필터 추가 + 동적 WHERE 절 방식 도입
#   - /jobs?company=카카오         → 회사명 완전 일치(LIKE 포함) 필터
#   - /jobs?keyword=백엔드&company=카카오 → 두 조건을 AND로 동시 적용
#
#   ★ 동적 WHERE 절이란?
#     - 쿼리 조건을 실행 시점에 동적으로 조립하는 기법입니다.
#     - 예를 들어 keyword만 있으면 WHERE keyword 조건만,
#       company만 있으면 WHERE company 조건만,
#       둘 다 있으면 WHERE keyword AND company 조건이 만들어집니다.
#     - if/else 분기를 여러 개 쓰지 않아도 되므로 코드가 훨씬 간결해집니다.
#
#   ★ company 필터가 서비스성 향상에 도움이 되는 이유:
#     - 사용자가 관심 있는 특정 기업(예: 카카오, 네이버)의 공고만 골라 볼 수 있습니다.
#     - '기업 탐색 → 공고 필터 → 지원' 흐름을 자연스럽게 지원합니다.
#     - keyword와 조합하면 '카카오의 백엔드 공고'처럼 정밀 검색이 가능해져
#       사용자가 원하는 정보를 더 빠르게 찾을 수 있습니다.
# =====================================================================

# FastAPI 앱 인스턴스를 생성합니다.
# title, description은 /docs 페이지에서 표시되는 API 설명입니다.
app = FastAPI(
    title="채용공고 API",
    description="사람인에서 크롤링한 채용공고를 조회하는 API입니다.",
    version="1.2.0"
)

import sys
import pathlib

# 상위 폴더(프로젝트 루트)를 경로에 추가하여 config 모듈 접근
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from config.database import get_connection


# =====================================================================
# API 엔드포인트 1: GET /jobs
# - 전체 채용공고를 조회하거나,
# - ?keyword=검색어            → 제목/회사명 통합 검색
# - ?company=회사명            → 특정 회사의 공고만 필터
# - ?keyword=검색어&company=회사명 → 두 조건을 동시에 적용 (AND)
# =====================================================================
@app.get("/jobs")
def get_jobs(
    keyword: str = Query(default=None, description="제목 또는 회사명으로 검색 (예: 백엔드, 카카오)"),
    company: str = Query(default=None, description="회사명으로 필터링 (예: 카카오, 네이버)")
):
    """
    채용공고 목록을 조회합니다.

    - **keyword** : 공고 제목 또는 회사명에 해당 단어가 포함된 공고를 반환
    - **company** : 입력한 회사명과 일치하는 회사의 공고만 반환
    - **두 파라미터 동시 사용** → AND 조건으로 교집합 결과 반환
    - **파라미터 없음** → 전체 공고를 최신순으로 반환
    """
    # ── 1. DB 연결 ──────────────────────────────────────────────────────
    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            # ──────────────────────────────────────────────────────────
            # [동적 WHERE 절 구성 방법]
            #
            # 아이디어:
            #   조건을 고정된 if/else 분기로 처리하면, 필터가 늘어날수록
            #   경우의 수(keyword만/company만/둘 다/둘 다 없음)가 기하급수적으로 늘어납니다.
            #
            #   대신, 파이썬 리스트 2개를 준비합니다.
            #   - conditions : SQL WHERE 절에 붙일 조건 문자열(예: "title LIKE %s")
            #   - params     : 위 조건의 %s 자리에 채울 실제 값
            #
            #   파라미터가 있을 때마다 조건과 값을 리스트에 추가하고,
            #   마지막에 ' AND '.join(conditions) 으로 한 번에 연결합니다.
            #
            # 장점:
            #   새 필터(예: location, salary)가 생겨도 if 블록 하나만 추가하면 됩니다.
            # ──────────────────────────────────────────────────────────

            conditions = []  # WHERE 절에 들어갈 조건 목록
            params     = []  # 각 조건의 %s에 대응하는 값 목록

            # ── keyword 조건 추가 ────────────────────────────────────
            # keyword가 있으면 제목(title) 또는 회사명(company) 중 하나라도
            # 검색어를 포함하는 행을 조건으로 추가합니다.
            # 괄호로 감싸야 OR 연산자가 다른 AND 조건과 섞이지 않습니다.
            if keyword:
                conditions.append("(title LIKE %s OR company LIKE %s)")
                like_keyword = f"%{keyword}%"   # '%검색어%' 형태로 LIKE 검색
                params.extend([like_keyword, like_keyword])  # OR 이므로 값이 2개

            # ── company 조건 추가 ────────────────────────────────────
            # company가 있으면 company 컬럼이 입력값을 포함하는 행만 필터합니다.
            # 완전 일치가 아닌 LIKE를 사용하므로 '카카오'를 입력하면
            # '카카오뱅크', '카카오페이' 등도 함께 조회됩니다.
            if company:
                conditions.append("company LIKE %s")
                params.append(f"%{company}%")  # '%회사명%' 형태

            # ── SQL 조립 ─────────────────────────────────────────────
            # 기본 SELECT 절 (공통)
            sql = "SELECT id, company, title, link, created_at FROM jobs"

            # conditions 리스트에 값이 있을 때만 WHERE 절을 붙입니다.
            # ' AND '.join([...]) : 조건들을 AND로 연결
            #   예시)
            #   conditions = ["(title LIKE %s OR company LIKE %s)", "company LIKE %s"]
            #   → WHERE (title LIKE %s OR company LIKE %s) AND company LIKE %s
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            # 정렬: created_at DESC → 최신 등록 공고가 항상 가장 위에
            sql += " ORDER BY created_at DESC"

            # 완성된 SQL 실행 (params가 빈 리스트면 WHERE 없이 전체 조회)
            cursor.execute(sql, params)

            # 조회된 모든 행을 파이썬 리스트로 가져옵니다.
            results = cursor.fetchall()

        # ── 2. JSON 응답 반환 ─────────────────────────────────────────
        # 적용된 필터 정보도 함께 반환하여 클라이언트가 어떤 조건으로
        # 조회했는지 확인할 수 있게 합니다.
        return {
            "total"  : len(results),  # 조회된 총 공고 수
            "keyword": keyword,       # 사용된 keyword 필터 (없으면 null)
            "company": company,       # 사용된 company 필터 (없으면 null)
            "jobs"   : results        # 공고 목록
        }

    finally:
        # 예외가 발생해도 반드시 연결을 닫아 자원 낭비를 방지합니다.
        conn.close()


# =====================================================================
# API 엔드포인트 2: GET /jobs/{job_id}
# - id 값으로 특정 공고 하나만 조회합니다.
# - 예: http://127.0.0.1:8000/jobs/5
# =====================================================================
@app.get("/jobs/{job_id}")
def get_job_by_id(job_id: int):
    """
    특정 id의 채용공고 1건을 조회합니다.
    """
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, company, title, link, created_at FROM jobs WHERE id = %s"
            cursor.execute(sql, (job_id,))
            result = cursor.fetchone()  # fetchone: 딱 1건만 가져옵니다.

        if result is None:
            # 해당 id의 데이터가 없으면 404 상태 코드와 메시지를 반환합니다.
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"id={job_id} 에 해당하는 공고가 없습니다.")

        return result

    finally:
        conn.close()


# =====================================================================
# API 엔드포인트 3: GET /
# - 서버가 정상 작동 중인지 확인하는 간단한 헬스체크 엔드포인트입니다.
# =====================================================================
@app.get("/")
def root():
    return {"message": "채용공고 API 서버가 정상 작동 중입니다! /docs 에서 API를 테스트해 보세요."}
