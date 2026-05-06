import sys
import pathlib

# [Import 경로 이슈 방지] 프로젝트의 루트 디렉토리를 path에 등록
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from data_pipeline.extract import extract_jobs
from data_pipeline.transform import transform_jobs
from data_pipeline.load import save_jobs_to_csv, save_jobs_to_db

def run():
    """
    데이터 엔지니어링 파이프라인을 관장하는 Orchestrator 함수입니다.
    E -> T -> L 순서대로 제어합니다.
    """
    print("\n" + "="*50)
    print(" 🚀 Job Data ETL Pipeline 시작")
    print("="*50 + "\n")

    # 1. Extract (데이터 추출)
    raw_data = extract_jobs()

    # 2. Transform (데이터 정제)
    clean_data = transform_jobs(raw_data)

    # 3. Load (데이터 적재)
    save_jobs_to_csv(clean_data)
    save_jobs_to_db(clean_data)

    print("\n" + "="*50)
    print(" ✨ 파이프라인 전체 프로세스가 정상 종료되었습니다.")
    print("="*50 + "\n")

if __name__ == "__main__":
    run()
