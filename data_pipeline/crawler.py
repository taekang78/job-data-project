import requests
from bs4 import BeautifulSoup
import csv
import pymysql  # MySQL 데이터베이스 연결을 위한 모듈

def scrape_saramin_jobs():
    """사람인(Saramin)에서 'python' 검색 결과 채용공고를 크롤링하는 함수"""
    
    url = "https://www.saramin.co.kr/zf_user/search/recruit?searchword=python"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🚀 [사람인] 웹 크롤링을 시작합니다...\n")
    response = requests.get(url, headers=headers)
    jobs_list = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        job_items = soup.find_all("div", class_="item_recruit")
        
        for job in job_items:
            try:
                # [기능 1: 공백 제거]
                # .strip() 함수를 사용하여 앞뒤의 불필요한 줄바꿈이나 띄어쓰기를 깔끔하게 제거합니다.
                title = job.find("h2", class_="job_tit").find("a").text.strip()
                company = job.find("strong", class_="corp_name").find("a").text.strip()
                link = "https://www.saramin.co.kr" + job.find("h2", class_="job_tit").find("a")['href']
                
                # [기능 3: 값이 없는 데이터 제거]
                # 크롤링을 하다 보면 빈 데이터가 섞여 들어올 수 있습니다.
                # 제목이나 회사명이 아예 비어있는(빈 문자열인) 쓰레기 데이터라면 리스트에 넣지 않고 건너뜁니다.
                if not title or not company:
                    continue  # continue를 만나면 아래 코드를 실행하지 않고 다음 공고로 넘어갑니다.
                
                # 추출한 데이터를 딕셔너리로 묶습니다.
                job_info = {
                    "company": company,
                    "title": title,
                    "link": link
                }
                
                # [기능 2: 중복 제거]
                # 똑같은 공고가 2번 이상 리스트에 들어가는 것을 방지합니다.
                # 리스트 안에 현재 추출한 정보(job_info)가 이미 있는지 검사해서 없을 때만 추가합니다.
                if job_info not in jobs_list:
                    jobs_list.append(job_info)
                
            except AttributeError:
                # 구조가 달라서 에러가 나면 그냥 무시하고 다음 공고로 넘어갑니다.
                pass
                
    else:
        print(f"❌ 접속에 실패했습니다. (응답 코드: {response.status_code})")

    return jobs_list


# =====================================================================
# 2. 데이터베이스 파트
# 💡 API 확장 팁: 이 함수들을 그대로 FastAPI나 Flask 같은 웹 프레임워크에서
#    불러다 쓰면 바로 API로 확장할 수 있습니다!
# =====================================================================

# DB 접속 정보를 딕셔너리로 한 곳에 모아둡니다.
# 🚨 본인의 MySQL 환경에 맞게 password와 database 값을 반드시 수정해주세요!
DB_CONFIG = {
    'host': '127.0.0.1',       # DB 서버 주소 (내 컴퓨터면 127.0.0.1 또는 localhost)
    'user': 'root',            # MySQL 아이디
    'password': 'yes050278!!',  # 🚨 본인의 MySQL 비밀번호로 변경!
    'database': 'job_data_platform',      # 사용할 데이터베이스 이름 (미리 MySQL에서 만들어두어야 합니다)
    'charset': 'utf8mb4',      # 한글/이모지 깨짐 방지
    'cursorclass': pymysql.cursors.DictCursor  # 조회 결과를 딕셔너리 형태로 받기
}


def get_connection():
    """DB와의 연결통로(connection)를 열어서 반환하는 함수.
    나중에 API 서버(FastAPI, Flask 등)를 만들 때도 이 함수 하나만 import하면 됩니다.
    """
    return pymysql.connect(**DB_CONFIG)


def create_jobs_table(conn):
    """(1) DB에 jobs 테이블이 없으면 새로 생성하는 함수.

    [중복 방지 핵심 포인트]
    link 컬럼에 UNIQUE 제약(UNIQUE KEY)을 설정합니다.
    UNIQUE 제약이란? → 같은 값을 가진 행(row)이 2개 이상 존재할 수 없도록
    DB 자체가 강제로 막아주는 규칙입니다.
    덕분에 파이썬 코드가 아닌 DB 레벨에서 중복을 원천 차단할 수 있습니다.
    """
    with conn.cursor() as cursor:
        sql = """
        CREATE TABLE IF NOT EXISTS jobs (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            company     VARCHAR(255)  NOT NULL,
            title       VARCHAR(500)  NOT NULL,
            link        VARCHAR(1000) NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- ✅ [중복 방지] link 값이 동일한 행이 2개 이상 저장되는 것을 DB가 직접 막습니다.
            -- 이미 테이블이 존재하면 이 SQL 자체가 실행되지 않으므로,
            -- 기존 테이블에 적용하려면 아래 주석의 ALTER TABLE 명령을 MySQL에서 한 번 실행하세요:
            -- ALTER TABLE jobs ADD UNIQUE KEY uq_link (link);
            UNIQUE KEY uq_link (link)
        )
        """
        cursor.execute(sql)
    conn.commit()
    print("✅ [DB] jobs 테이블 준비 완료! (link 컬럼 UNIQUE 제약 적용)")


def insert_jobs(conn, jobs_list):
    """(3) 크롤링한 공고 목록을 jobs 테이블에 INSERT 하는 함수.

    [중복 방지 핵심 포인트]
    INSERT IGNORE 를 사용합니다.
    - 일반 INSERT: 이미 같은 link가 있으면 에러가 발생하고 프로그램이 중단됩니다.
    - INSERT IGNORE: 이미 같은 link가 있으면 '조용히 건너뜁니다.' 에러 없이 계속 진행합니다.
    → UNIQUE 제약 + INSERT IGNORE 조합이 중복 방지의 정석 패턴입니다!
    """
    if not jobs_list:
        print("저장할 데이터가 없습니다.")
        return

    total = len(jobs_list)
    saved_count = 0  # 실제로 DB에 새로 저장된 건수

    with conn.cursor() as cursor:
        # ✅ INSERT IGNORE: link가 이미 존재하는 행은 오류 없이 조용히 건너뜁니다.
        # 즉, 크롤러를 10번 실행해도 같은 공고는 딱 1번만 저장됩니다.
        sql = "INSERT IGNORE INTO jobs (company, title, link) VALUES (%s, %s, %s)"

        for job in jobs_list:
            cursor.execute(sql, (job['company'], job['title'], job['link']))
            # cursor.rowcount: 직전 SQL이 실제로 영향을 준 행 수입니다.
            # INSERT IGNORE에서 중복으로 건너뛴 경우 rowcount = 0, 저장 성공 시 = 1 이 됩니다.
            saved_count += cursor.rowcount

    conn.commit()

    skipped_count = total - saved_count  # 중복으로 인해 건너뛴 건수
    print(f"✅ [DB] 처리 완료! → 새로 저장: {saved_count}건 / 중복 스킵: {skipped_count}건 / 전체 시도: {total}건")


def select_all_jobs(conn):
    """(4) jobs 테이블의 모든 데이터를 SELECT 해서 반환하는 함수.
    API에서 GET /jobs 엔드포인트를 만들 때 이 함수를 그대로 활용할 수 있습니다.
    """
    with conn.cursor() as cursor:
        # 최신 데이터부터 보이도록 id 기준 내림차순(DESC) 정렬합니다.
        sql = "SELECT id, company, title, link, created_at FROM jobs ORDER BY id DESC"
        cursor.execute(sql)
        results = cursor.fetchall()  # 조회된 모든 행(row)을 리스트로 가져옵니다.
    return results


# =====================================================================
# 3. 메인 실행 파트 (크롤링 → CSV 저장 → DB 저장 → DB 조회)
# =====================================================================
if __name__ == "__main__":
    import pathlib

    # [Step 1] 크롤링 실행
    scraped_data = scrape_saramin_jobs()
    print(f"🎉 총 {len(scraped_data)}개의 정제된 채용공고를 수집했습니다!\n")

    # [Step 2] CSV 파일 저장
    # pathlib.Path(__file__): 현재 실행 중인 파일(crawler.py)의 절대 경로를 가져옵니다.
    # .parent: 그 파일이 들어있는 폴더(data_pipeline)를 의미합니다.
    # .parent.parent: 한 단계 더 위(프로젝트 루트)로 올라갑니다.
    # 이렇게 하면 어떤 위치에서 실행해도 항상 data/jobs.csv에 저장됩니다.
    csv_path = pathlib.Path(__file__).parent.parent / "data" / "jobs.csv"

    # mode="w" 는 파일을 매번 새로 덮어쓰는(overwrite) 모드입니다.
    # 실행할 때마다 최신 데이터로 교체되므로, CSV 파일은 항상 딱 1개만 유지됩니다.
    with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["company", "title", "link"])
        writer.writeheader()
        for data in scraped_data:
            writer.writerow(data)
    print(f"💾 CSV 저장 완료! → {csv_path}\n")

    # [Step 3] MySQL DB 저장 및 조회
    # 🚨 실행 전 확인 사항:
    #   1. MySQL 서버가 실행 중인지 확인 (XAMPP, MySQL Workbench 등)
    #   2. 위 DB_CONFIG의 password와 database가 본인 환경과 일치하는지 확인
    #   3. job_db 데이터베이스가 없다면 MySQL에서 먼저 생성:
    #      > CREATE DATABASE job_db CHARACTER SET utf8mb4;
    print("🚀 [DB 연동 시작]")
    try:
        conn = get_connection()      # DB 연결
        create_jobs_table(conn)      # 테이블 생성 (없을 때만)
        insert_jobs(conn, scraped_data)  # 크롤링 데이터 저장

        # 저장된 데이터 중 최신 5건만 조회해서 확인
        all_jobs = select_all_jobs(conn)
        print(f"\n🔍 DB 저장 확인 (최신 5건 / 전체 {len(all_jobs)}건):")
        print("-" * 60)
        for job in all_jobs[:5]:
            print(f"  [{job['id']}] {job['company']} | {job['title']}")
            print(f"       저장시각: {job['created_at']}")
        print("-" * 60)

    except pymysql.MySQLError as e:
        # DB 연결 실패 또는 SQL 오류 시 에러 내용을 친절하게 알려줍니다.
        print("\n❌ 데이터베이스 오류가 발생했습니다:")
        print(f"   {e}")
        print("💡 해결 팁: DB_CONFIG의 password/database 값과 MySQL 서버 상태를 확인해주세요.")

    finally:
        # 성공하든 실패하든 마지막에는 반드시 연결을 닫아야 자원이 낭비되지 않습니다.
        if 'conn' in locals() and conn.open:
            conn.close()
            print("\n🔌 DB 연결이 안전하게 종료되었습니다.")
