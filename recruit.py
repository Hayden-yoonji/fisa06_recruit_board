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
today_cmp = now.strftime("%Y%m%d")

# 오늘 기준 -10일 ~ +10일 (기간은 원하시는 대로 수정 가능)
start_api = (now - timedelta(days=10)).strftime("%Y-%m-%d")
end_api = (now + timedelta(days=10)).strftime("%Y-%m-%d")

# ==========================================
# 3. URL 직접 만들기 (핵심 수정!)
# ==========================================
# params 딕셔너리 대신 f-string으로 URL을 완성합니다.
# 주의: &resultType=json 을 꼭 넣어야 파이썬에서 처리하기 쉽습니다. (기본값은 XML일 수 있음)
request_url = f"{BASE_URL}?serviceKey={SERVICE_KEY}&resultType=json&pageNo=1&numOfRows=100&pbancBgngYmd={start_api}&pbancEndYmd={end_api}"

print(f"📡 요청 URL: {request_url}")

def get_job_data():
    try:
        # params 없이 URL만 넣어서 요청
        response = requests.get(request_url)
        
        # 에러 체크
        if response.status_code != 200:
            print(f"❌ 요청 실패: {response.status_code}")
            return "데이터 요청 실패", 0

        data = response.json()
        
        # 데이터가 있는지 확인
        if 'result' in data and len(data['result']) > 0:
            df = pd.DataFrame(data['result'])
            
            # 필터링
            if 'pbancEndYmd' in df.columns:
                df['end_date_clean'] = df['pbancEndYmd'].astype(str).str.replace('-', '')
                df = df[df['end_date_clean'] >= today_cmp]
                df = df.sort_values(by='end_date_clean')

            # 링크 생성
            # (만약 컬럼이 없다면 에러가 날 수 있으니 체크)
            if 'srcUrl' not in df.columns: df['srcUrl'] = ''
            if 'recrutPbancTtl' not in df.columns: df['recrutPbancTtl'] = '제목없음'
            
            df['공고명'] = df.apply(lambda x: f"[{x['recrutPbancTtl']}]({x['srcUrl']})", axis=1)
            
            # 필요한 컬럼만 뽑기
            target_cols = {
                "instNm": "기관명", "공고명": "공고제목", 
                "pbancBgngYmd": "시작일", "pbancEndYmd": "마감일", 
                "hireTypeNmLst": "고용형태", "recrutSeNm": "구분"
            }
            available_cols = [c for c in target_cols.keys() if c in df.columns]
            final_df = df[available_cols].rename(columns=target_cols)
            
            if len(final_df) > 0:
                header = "| " + " | ".join(final_df.columns) + " |"
                separator = "| " + " | ".join(["---"] * len(final_df.columns)) + " |"
                rows = [f"| {' | '.join(row.astype(str).tolist())} |" for _, row in final_df.iterrows()]
                return "\n".join([header, separator] + rows), len(final_df)
        
        else:
            print("⚠️ API 응답에 결과 데이터('result')가 없습니다.")
            # 디버깅용: 실제 응답이 뭔지 찍어보기
            # print(data) 

    except Exception as e:
        print(f"🚨 에러 발생: {e}")
    
    return "현재 지원 가능한 공고가 없습니다.", 0

def update_readme():
    table_str, count = get_job_data()
    update_time = now.strftime("%Y-%m-%d %H:%M:%S")

    readme_content = f"""# 📢 공공기관 채용 현황판

이 페이지는 **OpenAPI**를 사용하여 매일 자동으로 업데이트됩니다.
오늘({today_cmp}) 기준, 지원 가능한 공고는 총 **{count}건**입니다.

### 📋 채용 공고 목록
{table_str}

---
Updated at: {update_time} (Server Time)
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    print("🎉 README.md 업데이트 완료!")

if __name__ == "__main__":
    update_readme()