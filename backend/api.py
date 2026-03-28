from fastapi import FastAPI, Query
import pymysql

# =====================================================================
# FastAPI 채용공고 조회 API
# ---------------------------------------------------------------------
# 실행 방법:
#   1. 패키지 설치: pip install fastapi uvicorn
#   2. 서버 시작:   uvicorn api:app --reload
#   3. 브라우저에서 확인:
#      - 전체 조회:        http://127.0.0.1:8000/jobs
#      - 키워드 필터 조회: http://127.0.0.1:8000/jobs?keyword=백엔드
#      - API 자동 문서:    http://127.0.0.1:8000/docs   ← 여기서 직접 테스트 가능!
# =====================================================================

# FastAPI 앱 인스턴스를 생성합니다.
# title, description은 /docs 페이지에서 표시되는 API 설명입니다.
app = FastAPI(
    title="채용공고 API",
    description="사람인에서 크롤링한 채용공고를 조회하는 API입니다.",
    version="1.0.0"
)

# DB 접속 정보 (crawler.py와 동일하게 맞춰주세요)
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'yes050278!!',       # 본인의 MySQL 비밀번호
    'database': 'job_data_platform', # 사용할 데이터베이스 이름
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor  # 결과를 딕셔너리로 받기
}


def get_connection():
    """DB 연결통로를 열어서 반환하는 함수.
    API 요청이 들어올 때마다 새로운 연결을 열고, 작업이 끝나면 닫습니다.
    """
    return pymysql.connect(**DB_CONFIG)


# =====================================================================
# API 엔드포인트 1: GET /jobs
# - 전체 채용공고를 조회하거나,
# - ?keyword=검색어 를 붙이면 제목/회사명에서 필터링하여 조회합니다.
# =====================================================================
@app.get("/jobs")
def get_jobs(keyword: str = Query(default=None, description="제목 또는 회사명으로 검색 (예: 백엔드, 카카오)")):
    """
    채용공고 목록을 조회합니다.

    - **keyword 없이 호출** → 전체 공고 반환
    - **keyword=검색어** → 제목 또는 회사명에 해당 단어가 포함된 공고만 반환
    """
    # 1. DB 연결
    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            if keyword:
                # [필터 기능] keyword가 있을 때:
                # LIKE '%검색어%' 는 SQL에서 '검색어'가 포함된 모든 것을 찾는 문법입니다.
                # title(공고명) 또는 company(회사명) 중 하나라도 일치하면 결과에 포함합니다.
                sql = """
                    SELECT id, company, title, link, created_at
                    FROM jobs
                    WHERE title LIKE %s OR company LIKE %s
                    ORDER BY id DESC
                """
                # %s 자리에 넣을 값. 앞뒤로 %를 붙여야 '포함' 검색이 됩니다.
                like_keyword = f"%{keyword}%"
                cursor.execute(sql, (like_keyword, like_keyword))
            else:
                # [전체 조회] keyword가 없을 때: 모든 공고를 최신순으로 가져옵니다.
                sql = """
                    SELECT id, company, title, link, created_at
                    FROM jobs
                    ORDER BY id DESC
                """
                cursor.execute(sql)

            # 조회된 모든 행(row)을 파이썬 리스트로 가져옵니다.
            results = cursor.fetchall()

        # 2. 결과를 JSON 형태로 응답
        # FastAPI는 파이썬 딕셔너리/리스트를 자동으로 JSON으로 변환해줍니다.
        return {
            "total": len(results),       # 총 공고 수
            "keyword": keyword,          # 사용된 필터 키워드 (없으면 null)
            "jobs": results              # 공고 목록
        }

    finally:
        # 예외가 발생해도 반드시 연결을 닫아서 자원 낭비를 방지합니다.
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
