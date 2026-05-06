import urllib.parse

def normalize_link(raw_link):
    """
    [Transform Helper] 링크 정규화 (중복 방지 핵심 로직)
    사람인 채용공고의 링크는 매 검색 시마다 `search_uuid` 등 동적 쿼리 파라미터가 
    붙어서 동일한 공고도 늘 새로운 공고로 인식되는 문제(중복)를 유발합니다.
    따라서 고유 식별자인 `rec_idx`만 남기고 다 잘라내는 일관된 정규화가 필수입니다.
    """
    if not raw_link:
        return ""

    # 1. 기본 공백 라인/줄바꿈 제거
    link = raw_link.strip()

    # 2. 상대경로 보정
    if not link.startswith("http"):
        link = f"https://www.saramin.co.kr{link}"

    # 3. URL 파싱
    parsed = urllib.parse.urlparse(link)
    qs = urllib.parse.parse_qs(parsed.query)

    # 4. 필수 고유 ID 추출 및 재조립
    rec_idx = qs.get("rec_idx", [None])[0]
    
    if rec_idx:
        # 고유값이 존재하면 가장 깔끔한 URL로 재생성 (기타 불필요 param 모두 소거)
        return f"https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx={rec_idx}"
    else:
        # rec_idx가 없는 (외부) 링크인 경우 꼬리의 불필요한 문자만 제거
        return parsed.scheme + "://" + parsed.netloc + parsed.path.rstrip("/")

def transform_jobs(raw_jobs):
    """
    [Transform] 추출된 원본 데이터를 정제합니다.
    """
    print(f"🛠️ [Transform] 데이터 정제 시작... (입력: {len(raw_jobs)}건)")
    clean_jobs = []
    
    # 💡 [핵심] In-Memory 링크 중복 제거용 집합(set)
    seen_links = set()

    for job in raw_jobs:
        title = job.get("title", "").strip()
        company = job.get("company", "").strip()
        raw_link = job.get("link", "").strip()

        # [필터링 1] 결측치 무시
        if not title or not company or not raw_link:
            continue

        # [필터링 2] 링크 정규화
        link = normalize_link(raw_link)

        # [필터링 3] 이번 처리 사이클 내의 중복(In-Memory) 무시
        if link in seen_links:
            # print(f"  ↪ [생략] 메모리에 이미 존재하는 링크: {link}")
            continue

        # 유효한 새 데이터라면 기록
        seen_links.add(link)

        job_info = {
            "company": company,
            "title": title,
            "link": link
        }
        
        clean_jobs.append(job_info)

    print(f"✔️ [Transform] 정제 완료! 유효 데이터: {len(clean_jobs)}건")
    return clean_jobs