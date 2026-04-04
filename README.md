# 📊 채용 데이터 수집 및 분석 플랫폼

> 채용 공고를 자동으로 수집하고, 정제하고, API로 제공하는 ETL 기반 데이터 파이프라인 프로젝트입니다.

<br>

## 🗂️ 목차

1. [프로젝트 개요](#-프로젝트-개요)
2. [프로젝트 목표](#-프로젝트-목표)
3. [왜 ETL 기반으로 설계했는가](#-왜-etl-기반으로-설계했는가)
4. [기술 스택](#-기술-스택)
5. [현재 구현 기능](#-현재-구현-기능)
6. [폴더 구조](#-폴더-구조)
7. [실행 방법](#-실행-방법)
8. [API 사용 예시](#-api-사용-예시)
9. [향후 확장 방향](#-향후-확장-방향)

---

## 🔍 프로젝트 개요

채용 플랫폼(사람인)의 공고 데이터를 크롤링하여 정제한 뒤, MySQL 데이터베이스에 저장하고 FastAPI를 통해 외부에 조회 API 형태로 제공하는 프로젝트입니다.

단순한 데이터 수집 스크립트가 아니라, **데이터를 수집(Extract) → 정제(Transform) → 저장(Load)** 하는 ETL 파이프라인 구조 위에 **백엔드 API 서비스**까지 얹은 형태를 목표로 합니다.

---

## 🎯 프로젝트 목표

- 실제 채용 데이터를 직접 수집하고 다루는 경험을 쌓는다
- ETL 파이프라인의 흐름을 코드 수준에서 직접 구현해본다
- 수집한 데이터를 단순 파일이 아닌 **데이터베이스 + REST API**로 서비스화한다
- 추후 Airflow, Spark, 대시보드로 확장 가능한 구조를 미리 잡아둔다

---

## 🤔 왜 ETL 기반으로 설계했는가

일반적인 크롤링 프로젝트는 "수집 → CSV 저장" 에서 끝나는 경우가 많습니다.  
하지만 이 프로젝트는 아래와 같은 이유로 ETL 구조를 선택했습니다.

| 이유 | 설명 |
|------|------|
| **확장성** | 수집 → 정제 → 저장 단계가 분리되어 있어, 각 단계를 독립적으로 교체하거나 고도화할 수 있습니다 |
| **중복 방지** | DB 레벨의 `UNIQUE KEY` + `INSERT IGNORE` 조합으로 크롤러를 여러 번 실행해도 데이터가 중복 저장되지 않습니다 |
| **서비스화** | CSV에만 저장하면 데이터를 꺼내 쓰기 불편하지만, DB + API 구조로 만들면 누구나 HTTP 요청 한 번으로 조회할 수 있습니다 |
| **파이프라인 학습** | 실무에서 쓰는 Airflow, Spark 같은 도구의 개념적 기반이 바로 ETL이기 때문에, 직접 구현해보는 것이 중요합니다 |

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| **언어** | Python 3.x |
| **크롤링** | `requests`, `BeautifulSoup4` |
| **데이터 저장** | `CSV`, `MySQL` |
| **DB 연결** | `pymysql` |
| **API 서버** | `FastAPI`, `uvicorn` |
| **데이터베이스** | MySQL 8.x |

---

## ✅ 현재 구현 기능

### 1️⃣ 데이터 수집 (Extract)

- 사람인에서 `python` 검색 결과 채용공고 크롤링
- 수집 항목: 공고 제목(`title`), 회사명(`company`), 공고 링크(`link`)

### 2️⃣ 데이터 정제 (Transform)

- `.strip()`으로 앞뒤 공백 제거
- 빈 값(제목 또는 회사명이 없는 데이터) 필터링
- 파이썬 리스트 수준의 중복 제거

### 3️⃣ 데이터 저장 (Load)

- **CSV 저장**: `data/jobs.csv`로 매 실행마다 최신 데이터로 갱신
- **MySQL 저장**:
  - `jobs` 테이블 자동 생성 (`CREATE TABLE IF NOT EXISTS`)
  - `link` 컬럼에 `UNIQUE KEY` 제약 → DB 레벨 중복 원천 차단
  - `INSERT IGNORE`로 중복 공고는 조용히 스킵
  - `created_at` 컬럼: 공고 저장 시각 자동 기록 (`TIMESTAMP DEFAULT CURRENT_TIMESTAMP`)

### 4️⃣ API 서비스 (FastAPI)

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/` | GET | 서버 헬스체크 |
| `/jobs` | GET | 전체 공고 조회 (최신순 정렬) |
| `/jobs?keyword=검색어` | GET | 제목 또는 회사명에 키워드 포함 공고 필터 |
| `/jobs?company=회사명` | GET | 특정 회사명 공고 필터 |
| `/jobs?keyword=백엔드&company=카카오` | GET | keyword + company 동시 적용 (AND 조건) |
| `/jobs/{id}` | GET | 특정 id의 공고 단건 조회 |
| `/docs` | GET | Swagger UI 자동 문서 |

**응답 예시** (`/jobs?company=카카오`):
```json
{
  "total": 3,
  "keyword": null,
  "company": "카카오",
  "jobs": [
    {
      "id": 42,
      "company": "카카오페이",
      "title": "백엔드 개발자 (Python)",
      "link": "https://www.saramin.co.kr/...",
      "created_at": "2026-04-04T22:30:00"
    }
  ]
}
```

---

## 📁 폴더 구조

```
job-data-platform/
│
├── backend/
│   └── api.py              # FastAPI 엔드포인트 (v1.2.0)
│                           #   - /jobs, /jobs/{id}
│                           #   - keyword / company 필터
│                           #   - created_at DESC 최신순 정렬
│                           #   - 동적 WHERE 절 방식
│
├── dashboard/
│   └── app.py              # Streamlit 대시보드 (v1.3.0)
│                           #   - 회사별 공고 수 막대 차트
│                           #   - 키워드별 공고 통계
│                           #   - 최신 공고 목록 + 인터랙티브 필터
│                           #   - 날짜별 수집량 시계열 차트
│
├── data_pipeline/
│   └── crawler.py          # ETL 파이프라인 실행 스크립트
│                           #   - 사람인 크롤링
│                           #   - 데이터 정제 (공백제거, 중복제거)
│                           #   - CSV 저장
│                           #   - MySQL 저장 (UNIQUE KEY + INSERT IGNORE)
│
├── data/
│   └── jobs.csv            # 크롤링 결과 CSV (실행마다 갱신)
│
├── database/
│   └── schema.sql          # DB 스키마 정의 (테이블 생성 SQL)
│
├── .gitignore
└── README.md
```

---

## 🚀 실행 방법

### 사전 준비

```bash
# 1. 패키지 설치
pip install requests beautifulsoup4 pymysql fastapi uvicorn streamlit pandas

# 2. MySQL에서 데이터베이스 생성 (최초 1회)
CREATE DATABASE job_data_platform CHARACTER SET utf8mb4;
```

> `crawler.py`, `api.py`, `dashboard/app.py`의 `DB_CONFIG` 안에 있는 `password` 값을 본인의 MySQL 비밀번호로 수정해주세요.


---

### Step 1. 데이터 수집 및 저장 (ETL 파이프라인 실행)

```bash
python data_pipeline/crawler.py
```

실행 시 다음 순서로 자동 처리됩니다:
1. 사람인에서 채용공고 크롤링
2. 데이터 정제 (공백·중복 제거)
3. `data/jobs.csv` 저장
4. MySQL `jobs` 테이블 생성 (없을 때만)
5. 중복 없이 DB에 저장
6. 최신 5건 조회 결과 출력

---

### Step 2. API 서버 실행

```bash
uvicorn backend.api:app --reload
```

서버가 시작되면 아래 주소에서 확인할 수 있습니다:

| 주소 | 설명 |
|------|------|
| `http://127.0.0.1:8000/jobs` | 전체 공고 조회 |
| `http://127.0.0.1:8000/jobs?keyword=백엔드` | 키워드 필터 |
| `http://127.0.0.1:8000/jobs?company=카카오` | 회사명 필터 |
| `http://127.0.0.1:8000/docs` | Swagger 자동 문서 |

---

## 📡 API 사용 예시

```bash
# 전체 공고 조회
GET /jobs

# 키워드 검색
GET /jobs?keyword=백엔드

# 회사명 필터
GET /jobs?company=카카오

# 복합 필터 (카카오의 백엔드 공고)
GET /jobs?keyword=백엔드&company=카카오

# 단건 조회
GET /jobs/5
```

---

## 🔭 향후 확장 방향

이 프로젝트는 다음 단계로 점진적으로 확장할 예정입니다.

| 단계 | 기술 | 설명 |
|------|------|------|
| **스케줄링 자동화** | Apache Airflow | 크롤러를 매일 정해진 시간에 자동 실행하는 DAG 구성 |
| **대용량 처리** | Apache Spark | 수십만 건 이상의 공고 데이터를 분산 처리 |
| **데이터 시각화** | Streamlit / Grafana | 기술 스택별 채용 트렌드, 회사별 공고 수 등 대시보드 구현 |
| **검색 고도화** | Elasticsearch | 형태소 분석 기반 한국어 전문 검색 지원 |
| **다중 소스** | 잡코리아, 원티드 등 | 크롤러를 복수의 채용 플랫폼으로 확장 |
| **페이지네이션** | FastAPI | `/jobs?page=1&size=20` 형태의 페이지 단위 응답 |

---

## 📝 변경 이력

| 버전 | 주요 변경사항 |
|------|--------------|
| v1.0.0 | 크롤링, CSV/MySQL 저장, FastAPI `/jobs` 기본 조회 |
| v1.1.0 | `created_at DESC` 기준 최신순 정렬 추가 |
| v1.2.0 | `company` 필터 추가, 동적 WHERE 절 방식 도입, 복합 필터 지원 |
| v1.3.0 | Streamlit 대시보드 추가 (회사별/키워드 통계, 최신 공고, 시계열) |

---

<div align="center">
  <sub>Built with ☕ and Python</sub>
</div>
