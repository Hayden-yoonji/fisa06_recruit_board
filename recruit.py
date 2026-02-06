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
URL = "https://apis.data.go.kr/1051000/recruitment/list"

# ==========================================
# 2. 날짜 및 데이터 준비
# ==========================================
now = datetime.now()
today_cmp = now.strftime("%Y%m%d")
start_api = (now - timedelta(days=10)).strftime("%Y-%m-%d")
end_api = (now + timedelta(days=10)).strftime("%Y-%m-%d")

params = {
    'serviceKey': SERVICE_KEY,
    'resultType': 'json',
    'pageNo': '1',
    'numOfRows': '100',
    'pbancBgngYmd': start_api,
    'pbancEndYmd': end_api
}



def get_job_data():
    """API 데이터를 가져와서 마크다운 표 문자열을 리턴하는 함수"""
    try:
        response = requests.get(URL, params=params)
        data = response.json()
        
        if 'result' in data and len(data['result']) > 0:
            df = pd.DataFrame(data['result'])
            
            # (1) 마감일 기준 필터링
            if 'pbancEndYmd' in df.columns:
                df['end_date_clean'] = df['pbancEndYmd'].astype(str).str.replace('-', '')
                df = df[df['end_date_clean'] >= today_cmp]
                df = df.sort_values(by='end_date_clean')

            # (2) 링크 만들기
            # 데이터에 srcUrl과 recrutPbancTtl이 무조건 있다고 가정
            df['공고명'] = df.apply(lambda x: f"[{x['recrutPbancTtl']}]({x['srcUrl']})", axis=1)
            
            # (3) 필요한 컬럼만 선택 및 이름 변경
            target_cols = {
                "instNm": "기관명", 
                "공고명": "공고제목", 
                "pbancBgngYmd": "시작일", 
                "pbancEndYmd": "마감일", 
                "hireTypeNmLst": "고용형태", 
                "recrutSeNm": "구분"
            }
            
            # 실제 데이터프레임에 있는 컬럼만 가져오기
            available_cols = [c for c in target_cols.keys() if c in df.columns]
            final_df = df[available_cols].rename(columns=target_cols)
            
            if len(final_df) > 0:
                # 마크다운 표 생성
                header = "| " + " | ".join(final_df.columns) + " |"
                separator = "| " + " | ".join(["---"] * len(final_df.columns)) + " |"
                # 행 데이터 생성
                rows = [f"| {' | '.join(row.astype(str).tolist())} |" for _, row in final_df.iterrows()]
                
                return "\n".join([header, separator] + rows), len(final_df)

    except Exception as e:
        print(f"데이터 가져오기 실패: {e}")
    
    return "현재 지원 가능한 공고가 없습니다.", 0

# ==========================================
# 3. README 전체 덮어쓰기
# ==========================================
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