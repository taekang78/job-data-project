""\"
⚠️ [Deprecated Module]
기존 crawler.py는 파이프라인 구조 분리(ETL) 작업으로 인해 더 이상 메인 로직을 포함하지 않습니다.

하위 호환성을 위해 이 파일을 실행하면 새로운 run_pipeline.py가 구동됩니다.
앞으로는 `python data_pipeline/run_pipeline.py` 를 실행해주세요.
""\"

from data_pipeline.run_pipeline import run

if __name__ == "__main__":
    print("\n⚠️ [경고] crawler.py는 향후 삭제될 예정입니다.")
    print("⚠️ [안내] 대신 data_pipeline/run_pipeline.py 를 직접 실행해 주세요.\n")
    
    # 레거시 래퍼 역할: 새로운 파이프라인을 호출
    run()
