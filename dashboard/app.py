"""
=====================================================================
 📊 채용 데이터 대시보드 (dashboard/app.py)
 ---------------------------------------------------------------------
 이 파일은 MySQL에 저장된 채용 데이터를 시각적으로 보여주는
 Streamlit 대시보드입니다.

 실행 방법:
   pip install streamlit pymysql pandas
   streamlit run dashboard/app.py

 접속 주소: http://localhost:8501  (브라우저에서 자동으로 열립니다)
=====================================================================
"""

import streamlit as st
import pymysql
import pandas as pd


# ─────────────────────────────────────────────────────────────────────
# [설정 1] 페이지 기본 설정
# st.set_page_config()는 반드시 파일의 가장 위쪽에서 딱 한 번만 호출해야 합니다.
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="채용 데이터 대시보드",
    page_icon="📊",
    layout="wide",          # 화면을 좌우로 넓게 사용
)


import sys
import pathlib

# 상위 폴더(프로젝트 루트)를 경로에 추가하여 config 모듈 접근
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from config.database import DB_CONFIG


# ─────────────────────────────────────────────────────────────────────
# [함수 1] DB에서 전체 jobs 데이터를 DataFrame으로 불러오기
#
# @st.cache_data 는 Streamlit의 '캐시' 기능입니다.
# 화면을 새로고침할 때마다 DB에 접속하면 느려지므로,
# 한 번 가져온 데이터를 ttl=60초 동안 재사용합니다.
# ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    """
    MySQL jobs 테이블의 전체 데이터를 pandas DataFrame으로 반환합니다.
    연결 실패 시 빈 DataFrame을 반환하고 에러 메시지를 표시합니다.
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # created_at DESC: 최신 공고가 위에 오도록 정렬
            cursor.execute(
                "SELECT id, company, title, link, created_at "
                "FROM jobs ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
        conn.close()

        df = pd.DataFrame(rows)
        # created_at 컬럼을 날짜형으로 변환 (문자열로 오는 경우 대비)
        if not df.empty:
            df["created_at"] = pd.to_datetime(df["created_at"])
        return df

    except pymysql.MySQLError as e:
        st.error(f"❌ DB 연결 실패: {e}")
        st.info("💡 DB_CONFIG 안의 password와 database 값을 확인해주세요.")
        return pd.DataFrame()   # 빈 DataFrame 반환


# =====================================================================
# 📌 대시보드 레이아웃 시작
# =====================================================================

# ── 타이틀 영역 ──────────────────────────────────────────────────────
st.title("📊 채용 데이터 대시보드")
st.caption("사람인 크롤링 데이터 기반 · MySQL 직접 연결 · 최신 데이터 기준")
st.divider()


# ── 데이터 로드 ──────────────────────────────────────────────────────
df = load_data()

# 데이터가 없으면 안내 메시지를 보여주고 더 이상 실행하지 않음
if df.empty:
    st.warning("⚠️ 불러올 데이터가 없습니다. 먼저 crawler.py를 실행하여 데이터를 수집해주세요.")
    st.stop()   # 이 아래 코드는 실행되지 않음


# ─────────────────────────────────────────────────────────────────────
# [섹션 1] 핵심 지표 요약 (KPI 카드)
# st.columns()로 화면을 3칸으로 나눕니다.
# ─────────────────────────────────────────────────────────────────────
st.subheader("📌 핵심 지표")

col1, col2, col3 = st.columns(3)

with col1:
    # 전체 공고 수
    st.metric(
        label="📋 전체 공고 수",
        value=f"{len(df):,} 건"
    )

with col2:
    # 고유 회사 수 (nunique: 중복 제거 후 개수)
    st.metric(
        label="🏢 등록 회사 수",
        value=f"{df['company'].nunique():,} 개"
    )

with col3:
    # 가장 최근에 저장된 공고의 날짜
    latest_date = df["created_at"].max().strftime("%Y-%m-%d %H:%M")
    st.metric(
        label="🕐 가장 최근 수집",
        value=latest_date
    )

st.divider()


# ─────────────────────────────────────────────────────────────────────
# [섹션 2] 회사별 채용 공고 수 (막대 차트)
# ─────────────────────────────────────────────────────────────────────
st.subheader("🏢 회사별 채용 공고 수")

# value_counts(): 각 값이 몇 번 등장하는지 세어 내림차순으로 반환
# head(15): 상위 15개 회사만 표시 (너무 많으면 차트가 복잡해짐)
company_counts = (
    df["company"]
    .value_counts()
    .head(15)
    .reset_index()          # 인덱스를 컬럼으로 변환
)
company_counts.columns = ["회사명", "공고 수"]

# st.bar_chart(): Streamlit 내장 막대 차트
# x, y: 각 축에 사용할 컬럼 지정
st.bar_chart(company_counts, x="회사명", y="공고 수", use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────────────
# [섹션 3] 키워드 포함 공고 수 통계
#
# 공고 제목(title)에 특정 키워드가 얼마나 등장하는지 분석합니다.
# str.contains(): 문자열에 해당 키워드가 포함되어 있는지 True/False로 반환
# na=False: None(빈 값)이 있어도 에러 없이 False로 처리
# ─────────────────────────────────────────────────────────────────────
st.subheader("🔍 키워드별 공고 수")

# 분석할 키워드 목록 (추후 자유롭게 추가/수정 가능)
KEYWORDS = ["Python", "백엔드", "프론트엔드", "데이터", "AI", "클라우드", "Java", "DevOps"]

keyword_stats = {}
for kw in KEYWORDS:
    # 대소문자 구분 없이(case=False) 제목에 키워드가 포함된 공고 수 계산
    count = df["title"].str.contains(kw, case=False, na=False).sum()
    keyword_stats[kw] = int(count)

# 딕셔너리를 DataFrame으로 변환
keyword_df = (
    pd.DataFrame(list(keyword_stats.items()), columns=["키워드", "공고 수"])
    .sort_values("공고 수", ascending=False)  # 공고 수 내림차순 정렬
    .reset_index(drop=True)
)

# 차트와 숫자 표를 나란히 배치
kw_col1, kw_col2 = st.columns([2, 1])

with kw_col1:
    st.bar_chart(keyword_df, x="키워드", y="공고 수", use_container_width=True)

with kw_col2:
    # st.dataframe(): 스크롤 가능한 인터랙티브 표
    st.dataframe(keyword_df, use_container_width=True, hide_index=True)

st.divider()


# ─────────────────────────────────────────────────────────────────────
# [섹션 4] 최신 공고 목록
# ─────────────────────────────────────────────────────────────────────
st.subheader("🆕 최신 채용 공고")

# 사이드바에서 표시 개수를 조절하는 슬라이더
# st.sidebar: 화면 왼쪽에 고정 패널 영역
with st.sidebar:
    st.header("⚙️ 필터 설정")

    # 최신 공고 표시 개수 슬라이더
    top_n = st.slider(
        label="최신 공고 표시 개수",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
    )

    # 회사명 필터: 전체 회사 목록에서 선택 (multiselect)
    all_companies = sorted(df["company"].unique().tolist())
    selected_companies = st.multiselect(
        label="회사명 필터 (복수 선택 가능)",
        options=all_companies,
        default=[],
        placeholder="전체 회사 표시 중..."
    )

    # 키워드 검색창
    search_keyword = st.text_input(
        label="공고 제목 키워드 검색",
        placeholder="예: 백엔드, Python ..."
    )

# 필터 적용
filtered_df = df.copy()

# 회사명 필터: 선택된 회사가 있을 때만 적용
if selected_companies:
    filtered_df = filtered_df[filtered_df["company"].isin(selected_companies)]

# 키워드 필터: 입력이 있을 때만 적용
if search_keyword:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_keyword, case=False, na=False)
    ]

# 필터 결과 건수 표시
st.caption(f"조회 결과: {len(filtered_df):,} 건 (상위 {top_n}건 표시)")

# 최신 공고 N건만 잘라서 표시
display_df = filtered_df.head(top_n).copy()

# link 컬럼을 클릭 가능한 하이퍼링크로 변환
# column_config으로 각 컬럼의 표시 방식을 세부 설정합니다
st.dataframe(
    display_df[["company", "title", "link", "created_at"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "company"   : st.column_config.TextColumn("회사명", width="medium"),
        "title"     : st.column_config.TextColumn("공고 제목", width="large"),
        "link"      : st.column_config.LinkColumn("공고 링크", width="medium"),
        "created_at": st.column_config.DatetimeColumn("수집 일시", format="YYYY-MM-DD HH:mm"),
    }
)


# ─────────────────────────────────────────────────────────────────────
# [섹션 5] 날짜별 수집량 추이 (시계열 차트)
# ─────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📅 날짜별 공고 수집량")

# created_at에서 날짜만 추출하여 날짜별 집계
daily_counts = (
    df.set_index("created_at")
    .resample("D")          # D: 일(Day) 단위로 리샘플링 (집계)
    .size()                 # 각 날짜의 행 수 계산
    .reset_index()
)
daily_counts.columns = ["날짜", "수집 건수"]

if len(daily_counts) > 1:
    # 날짜 데이터가 2일 이상일 때만 라인 차트 표시
    st.line_chart(daily_counts, x="날짜", y="수집 건수", use_container_width=True)
else:
    st.info("📌 날짜별 추이 차트는 2일 이상의 데이터가 있을 때 표시됩니다.")


# ─────────────────────────────────────────────────────────────────────
# [푸터]
# ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("데이터 소스: 사람인 크롤링 | 새로고침 주기: 60초 캐시 | 프로젝트: job-data-platform")
