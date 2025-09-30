import os, json, time, random, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote

# ===== API 설정 =====
client_id = ""
client_secret = ""
NEWS_JSON = "hanssem_news_trend.json"

# ===== 필터링 키워드 =====
INCLUDE_KEYWORDS = ["가구", "인테리어", "리모델링", "주방", "거실", "수납", "트렌드", "리빙"]
EXCLUDE_KEYWORDS = ["주가", "영업이익", "매출", "실적", "증권", "재무"]

def fetch_news_links(query="한샘", display=50):
    url = "https://openapi.naver.com/v1/search/news.json"
    params = {"query": query, "display": display, "sort": "date"}  # dict 그대로!
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    res = requests.get(url, headers=headers, params=params)  # requests가 자동 인코딩
    data = res.json()
    return [(item["title"], item["link"]) for item in data["items"]]

# ===== 드라이버 설정 =====
options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/120.0.0.0 Safari/537.36")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

def human_pause(a=0.8, b=1.5):
    time.sleep(random.uniform(a, b))

# ===== 본문 크롤링 =====
def scrape_article(url):
    driver.get(url)
    human_pause()
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # 본문 영역
    content = soup.select_one("div#dic_area") or soup.select_one("div.article_body")
    return content.get_text("\n", strip=True) if content else ""

# ===== 필터링 함수 =====
def is_relevant(title, text):
    content = title + " " + text
    if any(kw in content for kw in INCLUDE_KEYWORDS):
        if not any(bad in content for bad in EXCLUDE_KEYWORDS):
            return True
    return False

# ===== 실행 =====
links = fetch_news_links("한샘", display=50)
results = []

for i, (title, url) in enumerate(links, 1):
    try:
        text = scrape_article(url)
        if is_relevant(title, text):
            results.append({"url": url, "title": title, "text": text})
            print(f"{i}/{len(links)} 저장됨 ✅: {title[:40]}")
        else:
            print(f"{i}/{len(links)} 제외 ❌: {title[:40]}")
    except Exception as e:
        print("에러:", e)

driver.quit()

# ===== 저장 =====
with open(NEWS_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ 최종 저장 완료: {len(results)}개 → {NEWS_JSON}")