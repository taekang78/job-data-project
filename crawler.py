import requests
from bs4 import BeautifulSoup
import csv  # CSV 저장을 위한 모듈 추가

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


if __name__ == "__main__":
    # 1. 크롤링부터 데이터 정제까지 포함된 위 함수를 실행합니다.
    scraped_data = scrape_saramin_jobs()

    # 2. 터미널(화면)에 결과 출력하기
    print(f"🎉 성공적으로 총 {len(scraped_data)}개의 정제된 채용공고를 수집했습니다!\n")
    for i, data in enumerate(scraped_data, 1):
        print(f"[{i}번 공고]")
        print(f"🏢 회사명: {data['company']}")
        print(f"📝 공고명: {data['title']}")
        print(f"🔗 링크:   {data['link']}")
        print("-" * 50)

    # 3. [기능 4: CSV 파일로 저장하기]
    # 모아둔 데이터를 엑셀에서 열 수 있도록 csv 파일로 저장합니다. 
    # 한글 깨짐 현상을 막기 위해 인코딩을 반드시 'utf-8-sig' 로 설정해야 합니다. (조건 1)
    # newline='' 는 윈도우 환경에서 엔터가 두 번씩 쳐져 엑셀에 한 줄씩 빈 공간이 생기는 것을 막아줍니다.
    with open("jobs.csv", mode="w", encoding="utf-8-sig", newline="") as file:
        # csv에 글을 한 줄씩 쓸 수 있는 'DictWriter' 도구를 가져옵니다.
        # fieldnames는 엑셀의 열 제목(머리글)이 됩니다. 딕셔너리의 키 이름과 동일해야 합니다.
        fieldnames = ["company", "title", "link"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # 엑셀의 최상단 1번째 줄에 열 제목(company, title, link)을 적어줍니다.
        writer.writeheader()
        
        # 수집한 데이터 리스트를 for문으로 하나씩 꺼내 엑셀의 행(row)에 작성합니다.
        for data in scraped_data:
            writer.writerow(data)

    print("💾 데이터 정제 및 'jobs.csv' 파일 저장이 성공적으로 완료되었습니다!")
