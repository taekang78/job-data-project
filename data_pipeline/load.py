import csv
import sys
import pathlib
import pymysql

# 프로젝트 루트 경로를 sys.path에 추가하여 config 모듈 접근
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from config.database import get_connection, DB_CONFIG

def save_jobs_to_csv(jobs_list):
    """
    [Load] 파이프라인 정제 결과를 로컬 CSV 파일로 저장합니다.
    """
    if not jobs_list:
        print("⚠️ [Load] CSV로 저장할 데이터가 없습니다.")
        return

    # 경로 통일 보장: 항상 루트 디렉토리 산하의 data 폴더만 이용
    csv_path = ROOT_DIR / "data" / "jobs.csv"
    
    # data 폴더가 없으면 에러가 나므로 생성해줍니다.
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["company", "title", "link"])
        writer.writeheader()
        for data in jobs_list:
            writer.writerow(data)
    
    print(f"💾 [Load] CSV 임시 저장 완료: {csv_path}")


def save_jobs_to_db(jobs_list):
    """
    [Load] 최종 데이터를 MySQL 데이터베이스에 적재합니다.
    """
    if not jobs_list:
        print("⚠️ [Load] DB에 저장할 데이터가 없습니다.")
        return

    # 어떤 데이터베이스를 바라보고 있는지 확인하기 위한 로깅
    print(f"🚀 [Load] DB 적재를 시작합니다... (Target DB: {DB_CONFIG['database']} @ {DB_CONFIG['host']})")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 테이블이 없다면 생성 (방어 로직)
            create_sql = """
            CREATE TABLE IF NOT EXISTS jobs (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                company     VARCHAR(255)  NOT NULL,
                title       VARCHAR(500)  NOT NULL,
                link        VARCHAR(1000) NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_link (link)
            )
            """
            cursor.execute(create_sql)

            # 2. INSERT IGNORE를 사용한 최종 데이터 적재 (중복 방어)
            insert_sql = "INSERT IGNORE INTO jobs (company, title, link) VALUES (%s, %s, %s)"
            
            saved_count = 0
            for job in jobs_list:
                cursor.execute(insert_sql, (job['company'], job['title'], job['link']))
                saved_count += cursor.rowcount  # rowcount가 1이면 새로 저장, 0이면 중복 통과
        
        conn.commit()
        skipped_count = len(jobs_list) - saved_count
        print(f"✅ [Load] DB 적재 완료! 신규: {saved_count}건 / 중복 제외: {skipped_count}건")

    except pymysql.MySQLError as e:
        print(f"❌ [Load] DB 저장 중 에러 발생: {e}")
    finally:
        conn.close()
