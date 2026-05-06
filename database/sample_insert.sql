-- =====================================================================
-- 샘플 데이터 INSERT - 기능 테스트용 더미 데이터
-- ---------------------------------------------------------------------
-- 주의: 이 파일의 데이터는 API 키 발급 전 기능 테스트를 위한
--       더미 데이터이며, 실제 채용공고가 아닙니다.
--
-- 실행 방법 (PowerShell):
--   Get-Content ".\database\sample_insert.sql" |
--     & "C:\Program Files\MySQL\MySQL Server 9.4\bin\mysql.exe"
--       --default-character-set=utf8mb4 -u root -p job_data_platform
--
-- 실행 전 확인:
--   jobs 테이블이 database/schema.sql 기준으로 먼저 생성되어 있어야 합니다.
--   중복 실행 시 UNIQUE KEY(link) 제약으로 자동 스킵됩니다.
-- =====================================================================

USE job_data_platform;
SET NAMES utf8mb4;

-- 1. KB국민은행 - 데이터
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    'KB국민은행',
    '데이터 분석 담당자',
    'https://sample.dummy/jobs/001',
    '서울',
    '경력 3년 이상',
    '대졸이상',
    '2026-06-30',
    'sample_data',
    '금융 데이터',
    '데이터',
    'KB국민은행'
);

-- 2. 신한은행 - IT
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '신한은행',
    '금융 IT 시스템 개발자',
    'https://sample.dummy/jobs/002',
    '서울',
    '경력 2년 이상',
    '대졸이상',
    '2026-07-15',
    'sample_data',
    '금융 IT',
    'IT',
    '신한은행'
);

-- 3. 하나은행 - 디지털
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '하나은행',
    '디지털 전환 기획 담당자',
    'https://sample.dummy/jobs/003',
    '서울',
    '경력 5년 이상',
    '대졸이상',
    '2026-06-20',
    'sample_data',
    '은행 디지털',
    '디지털',
    '하나은행'
);

-- 4. 우리은행 - 데이터
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '우리은행',
    'AI 모델 개발 엔지니어',
    'https://sample.dummy/jobs/004',
    '서울',
    '경력 3년 이상',
    '석사이상',
    '2026-07-31',
    'sample_data',
    '금융 데이터',
    '데이터',
    '우리은행'
);

-- 5. 카카오뱅크 - IT
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '카카오뱅크',
    '백엔드 개발자',
    'https://sample.dummy/jobs/005',
    '경기',
    '경력 2년 이상',
    '대졸이상',
    '2026-08-01',
    'sample_data',
    '핀테크',
    'IT',
    '카카오뱅크'
);

-- 6. 토스뱅크 - 데이터
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '토스뱅크',
    '데이터 엔지니어',
    'https://sample.dummy/jobs/006',
    '서울',
    '경력 3년 이상',
    '대졸이상',
    '채용시',
    'sample_data',
    '데이터분석',
    '데이터',
    '토스뱅크'
);

-- 7. 케이뱅크 - IT
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '케이뱅크',
    '클라우드 인프라 엔지니어',
    'https://sample.dummy/jobs/007',
    '서울',
    '경력 4년 이상',
    '대졸이상',
    '2026-07-20',
    'sample_data',
    '디지털',
    'IT',
    '케이뱅크'
);

-- 8. 부산은행 - 디지털
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '부산은행',
    '디지털 금융 서비스 기획자',
    'https://sample.dummy/jobs/008',
    '부산',
    '경력 3년 이상',
    '대졸이상',
    '2026-06-25',
    'sample_data',
    '은행 디지털',
    '디지털',
    '부산은행'
);

-- 9. 대구은행 - IT
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '대구은행',
    '전산 시스템 운영 담당자',
    'https://sample.dummy/jobs/009',
    '대구',
    '신입 경력',
    '대졸이상',
    '2026-07-10',
    'sample_data',
    '금융 IT',
    'IT',
    '대구은행'
);

-- 10. 신한카드 - 데이터
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '신한카드',
    '마케팅 데이터 분석가',
    'https://sample.dummy/jobs/010',
    '서울',
    '경력 2년 이상',
    '대졸이상',
    '2026-06-30',
    'sample_data',
    '데이터분석',
    '데이터',
    '신한카드'
);

-- 11. 현대카드 - 디지털
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '현대카드',
    '디지털 프로덕트 매니저',
    'https://sample.dummy/jobs/011',
    '서울',
    '경력 4년 이상',
    '대졸이상',
    '2026-07-05',
    'sample_data',
    '디지털',
    '디지털',
    '현대카드'
);

-- 12. 삼성카드 - 기타
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '삼성카드',
    '정보보안 담당자',
    'https://sample.dummy/jobs/012',
    '서울',
    '경력 3년 이상',
    '대졸이상',
    '2026-07-31',
    'sample_data',
    'IT',
    '기타',
    '삼성카드'
);

-- 13. 삼성증권 - 데이터
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '삼성증권',
    '퀀트 데이터 분석가',
    'https://sample.dummy/jobs/013',
    '서울',
    '경력 5년 이상',
    '석사이상',
    '2026-06-28',
    'sample_data',
    '금융 데이터',
    '데이터',
    '삼성증권'
);

-- 14. NH투자증권 - IT
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    'NH투자증권',
    '프론트엔드 개발자',
    'https://sample.dummy/jobs/014',
    '서울',
    '경력 2년 이상',
    '대졸이상',
    '2026-07-25',
    'sample_data',
    '금융 IT',
    'IT',
    'NH투자증권'
);

-- 15. 한국투자증권 - 기타
INSERT IGNORE INTO jobs (
    company, title, link, location, experience, education,
    deadline, source, search_keyword, category, bank_name
) VALUES (
    '한국투자증권',
    'DB 관리자',
    'https://sample.dummy/jobs/015',
    '경기',
    '경력 3년 이상',
    '대졸이상',
    '2026-08-10',
    'sample_data',
    '금융 IT',
    '기타',
    '한국투자증권'
);

-- 적재 결과 확인
SELECT COUNT(*) AS total FROM jobs WHERE source = 'sample_data';
