import time, random, csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

SEARCH_KEYWORD = "실내 디자인"
START_PAGE = 11
END_PAGE = 30
OUT_FILE = f"riss_metadata_{START_PAGE}_{END_PAGE}.csv"

START_URL = (
    "https://www.riss.kr/search/Search.do?"
    f"query={SEARCH_KEYWORD}&pageNumber={START_PAGE}&iStartCount={(START_PAGE-1)*10}&pageScale=10&isTab=Y&"
    "icate=re_a_kor&colName=re_a_kor"
)

MIN_DELAY, MAX_DELAY = 3.0, 6.0

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 12)

def human_delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

def extract_detail_fields():
    try:
        detail = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".infoDetailL")))
    except:
        return {"authors": "", "publisher": "", "journal": "", "issue": "", "year": ""}

    def get_field(field_name):
        try:
            el = detail.find_element(By.XPATH, f".//span[text()='{field_name}']/following-sibling::div//p")
            return el.text.strip()
        except:
            return ""

    return {
        "authors": get_field("저자"),
        "publisher": get_field("발행기관"),
        "journal": get_field("학술지명"),
        "issue": get_field("권호사항"),
        "year": get_field("발행연도")
    }

def main():
    # ===== 기존 CSV 불러오기 =====
    done_links = set()
    try:
        df = pd.read_csv(OUT_FILE)
        done_links = set(df["link"].dropna())
        print(f"이미 수집된 논문 {len(done_links)}건 → 중복 스킵 예정")
    except FileNotFoundError:
        print("기존 CSV 없음 → 새로 생성 시작")

    driver.get(START_URL)
    human_delay()

    current_block_start = START_PAGE
    csv_fields = ["database", "keyword", "title", "authors", "publisher", "journal", "issue", "year", "link"]

    with open(OUT_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        if f.tell() == 0:
            writer.writeheader()  # 새 파일이면 헤더 추가

        while current_block_start <= END_PAGE:
            block_end = min(current_block_start + 9, END_PAGE)

            for page_num in range(current_block_start, block_end + 1):
                print(f"\n=== 📄 페이지 {page_num} ===")
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".srchResultListW > ul > li")))

                items = driver.find_elements(By.CSS_SELECTOR, ".srchResultListW > ul > li > div.cont.ml60 > p.title > a")
                for i, a in enumerate(items, start=1):
                    title, href = a.text.strip(), a.get_attribute("href")

                    if href in done_links:
                        print(f"[SKIP] 이미 수집됨: {title}")
                        continue

                    print(f"[{page_num}-{i}] {title}")

                    driver.execute_script("window.open(arguments[0]);", href)
                    driver.switch_to.window(driver.window_handles[-1])

                    fields = extract_detail_fields()
                    fields.update({
                        "title": title,
                        "link": href,
                        "database": "RISS",
                        "keyword": SEARCH_KEYWORD
                    })

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                    writer.writerow(fields)   # 한 건씩 CSV append 저장
                    done_links.add(href)

                    human_delay()

                # 페이지 이동
                if page_num < block_end:
                    nth = (page_num - current_block_start) + 4
                    selector = f"#divContent > div > div.rightContent.wd756 > div > div.paging > a:nth-child({nth})"
                    driver.find_element(By.CSS_SELECTOR, selector).click()
                    human_delay()

            # 블록 끝 → next 버튼 눌러서 다음 블록 이동
            if block_end < END_PAGE:
                next_btn = driver.find_element(By.CSS_SELECTOR, "#divContent > div > div.rightContent.wd756 > div > div.paging > a.next1")
                next_btn.click()
                human_delay()

            current_block_start += 10

    driver.quit()
    print(f"\n✅ 크롤링 완료 (총 {len(done_links)}건 저장됨)")

if __name__ == "__main__":
    main()