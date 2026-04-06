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
    company: str = Query(default=None, description="회사명으로 필터링 (예: 카카오, 네이버)"),
    limit: int = Query(default=20, ge=1, le=100, description="한 번에 가져올 공고 수 (최대 100)"),
    offset: int = Query(default=0, ge=0, description="건너뛸 공고 수 (페이징용)")
):
    """
    채용공고 목록을 페이징 처리하여 조회합니다.

    - **keyword** : 공고 제목 또는 회사명에 해당 단어가 포함된 공고를 반환
    - **company** : 입력한 회사명과 일치하는 회사의 공고만 반환
    - **limit** : 한 번에 가져올 공고 수 (조회 제한량, 기본 20)
    - **offset** : 맨 앞에서부터 건너뛸 공고 수 (조회 시작점, 기본 0)
    """
    # ── 1. DB 연결 ──────────────────────────────────────────────────────
    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            # [동적 WHERE 절 구성]
            conditions = []
            params = []

            if keyword:
                conditions.append("(title LIKE %s OR company LIKE %s)")
                like_keyword = f"%{keyword}%"
                params.extend([like_keyword, like_keyword])

            if company:
                conditions.append("company LIKE %s")
                params.append(f"%{company}%")

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)

            # ── [신규 추가] 전체 데이터 건수 추산 (COUNT) ────────────────
            # 데이터를 일부만 꺼내기 전에(LIMIT 적용 전), 전체 조건에 부합하는 데이터가 
            # 몇 개인지 미리 조회해야 정확한 전체 페이징 숫자를 알 수 있습니다.
            count_sql = f"SELECT COUNT(*) as cnt FROM jobs{where_clause}"
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['cnt']

            # ── 2. 데이터 조회 (LIMIT, OFFSET 적용) ──────────────────────
            # 기존 쿼리에 내림차순 정렬을 유지하고, 끝에 LIMIT과 OFFSET을 붙입니다.
            sql = f"SELECT id, company, title, link, created_at FROM jobs{where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s"
            
            # 파이썬 리스트 더하기 연산을 이용해, WHERE절 파라미터 뒤에 페이징 변수를 넣습니다.
            final_params = params + [limit, offset]
            
            cursor.execute(sql, final_params)
            results = cursor.fetchall()

        # ── 3. 실무형 JSON 응답 반환 (메타데이터/데이터 분리) ─────────
        # 프론트엔드 연동과 파이프라인 확인을 돕기 위해 응답 구조를 명확히 나눕니다.
        return {
            "meta": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "keyword": keyword,
                "company": company
            },
            "data": results
        }

    finally:
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
