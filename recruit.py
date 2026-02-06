import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. 설정
# ==========================================
SERVICE_KEY = os.getenv("SERVICE_KEY")
BASE_URL = "https://apis.data.go.kr/1051000/recruitment/list"

# ==========================================
# 2. 날짜 계산 (자동화)
# ==========================================
now = datetime.now()
today_dt = pd.to_datetime(now.date())

# 오늘 기준 -10일 ~ +10일
start_api = (now - timedelta(days=10)).strftime("%Y-%m-%d")
end_api = (now + timedelta(days=10)).strftime("%Y-%m-%d")

# ==========================================
# 3. 요청 파라미터
# ==========================================
params = {
    "serviceKey": SERVICE_KEY,
    "pageNo": 1,
    "pbancBgngYmd": start_api,
    "pbancEndYmd": end_api
}

# ==========================================
# 4. 데이터 수집
# ==========================================
def get_job_data():
    try:
        response = requests.get(BASE_URL, params=params)
        print("📡 요청 URL:", response.url)
        print("📡 상태 코드:", response.status_code)

        if response.status_code != 200:
            print("❌ 요청 실패")
            print(response.text)
            return "데이터 요청 실패", 0

        # JSON 변환
        try:
            data = response.json()
        except Exception:
            print("❌ JSON 변환 실패")
            print(response.text)
            return "데이터 요청 실패", 0

        print("📦 응답 데이터:", data)

        # 결과 데이터 확인
        if "result" not in data or len(data["result"]) == 0:
            print("⚠️ 결과 데이터가 없습니다.")
            return "현재 지원 가능한 공고가 없습니다.", 0

        df = pd.DataFrame(data["result"])

        # 마감일 기준 필터링
        if "pbancEndYmd" in df.columns:
            df["end_date_clean"] = (
                df["pbancEndYmd"]
                .astype(str)
                .str.replace("-", "")
            )
            df = df[df["end_date_clean"] >= today_cmp]
            df = df.sort_values(by="end_date_clean")

        if len(df) == 0:
            return "현재 지원 가능한 공고가 없습니다.", 0

        # 컬럼 보정
        if "srcUrl" not in df.columns:
            df["srcUrl"] = ""
        if "recrutPbancTtl" not in df.columns:
            df["recrutPbancTtl"] = "제목없음"

        # 마크다운 링크 생성
        df["공고명"] = df.apply(
            lambda x: f"[{x['recrutPbancTtl']}]({x['srcUrl']})",
            axis=1
        )

        # 필요한 컬럼만 추출
        target_cols = {
            "instNm": "기관명",
            "공고명": "공고제목",
            "pbancBgngYmd": "시작일",
            "pbancEndYmd": "마감일",
            "hireTypeNmLst": "고용형태",
            "recrutSeNm": "구분"
        }

        available_cols = [
            col for col in target_cols.keys()
            if col in df.columns
        ]

        final_df = df[available_cols].rename(columns=target_cols)

        # 마크다운 테이블 생성
        header = "| " + " | ".join(final_df.columns) + " |"
        separator = "| " + " | ".join(["---"] * len(final_df.columns)) + " |"
        rows = [
            "| " + " | ".join(row.astype(str)) + " |"
            for _, row in final_df.iterrows()
        ]

        table_md = "\n".join([header, separator] + rows)

        return table_md, len(final_df)

    except Exception as e:
        print("🚨 예외 발생:", e)
        return "데이터 요청 실패", 0

# ==========================================
# 5. README 업데이트
# ==========================================
def update_readme():
    table_str, count = get_job_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    readme_content = f"""# 📢 공공기관 채용 현황판

이 페이지는 **공공데이터 OpenAPI**를 사용하여 자동으로 업데이트됩니다.  
오늘({today_cmp}) 기준, 지원 가능한 공고는 총 **{count}건**입니다.

### 📋 채용 공고 목록
{table_str}

---
Updated at: {update_time} (Server Time)
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("🎉 README.md 업데이트 완료!")

# ==========================================
# 6. 실행
# ==========================================
if __name__ == "__main__":
    update_readme()