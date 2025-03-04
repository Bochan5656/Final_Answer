from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import re

# WebDriverのセットアップ
driver = webdriver.Chrome()
# データフレーム
df = pd.DataFrame(columns=['店舗名', '電話番号', 'メールアドレス', '都道府県', '市区町村', '番地', '建物名', 'URL', 'SSL'])
urls = []
elements = 50
base_url = 'https://r.gnavi.co.jp/eki/0005953/rs/?r=1000'

# Webサイトにアクセス
driver.get(base_url)
driver.set_page_load_timeout(60)  # ページの読み込みタイムアウト
while len(urls) < elements * 2:
    time.sleep(3)
    # 店舗のURLリストを取得
    url_elements = driver.find_elements(By.CLASS_NAME, 'style_titleLink__oiHVJ')
    new_urls = [element.get_attribute('href') for element in url_elements]
    urls.extend(new_urls)
    try:
        next_page = driver.find_element(By.CLASS_NAME, 'style_nextIcon__M_Me_')
        # imgタグの親タグ(aタグ)取得してクリック
        next_page_url = next_page.find_element(By.XPATH, '..')
        next_page_url.click()
        # ページ遷移のための待機
        driver.set_page_load_timeout(60)
    except NoSuchElementException:
        print("次ページのURLが取得できませんでした")
        break
    print("取得したURL数:", len(urls))

# 情報の取得
for url in urls:
    try:
        driver.get(url)
        # ページの読み込み完了を待つ
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print(f'{url} ：取得成功')
    except TimeoutException:
        print(f"タイムアウト: {url}")
        continue  # 次のURLへスキップ
    
    # 店舗名
    try:
        store_name = driver.find_element(By.ID, 'info-name').text
    except NoSuchElementException:
        store_name = None
    
    # 電話番号
    try:
        phone_number = driver.find_element(By.CLASS_NAME, 'number').text
    except NoSuchElementException:
        phone_number = None

    # メールアドレス
    try:
        mail_element = driver.find_element(By.LINK_TEXT, 'お店に直接メールする')
        mail_address = mail_element.get_attribute('href')
    except NoSuchElementException:
        mail_address = None

    # 住所
    try:
        address = driver.find_element(By.CLASS_NAME, 'region').text
    except NoSuchElementException:
        address = None

    # 都道府県、市区町村、番地に分割
    if address:
        address_pattern = r'([^\d]+?(?:都|道|府|県))([^\d]+?[市区町村])(.+)'
        match = re.search(address_pattern, address)
        if match:
            prefecture = match.group(1).strip()
            city = match.group(2).strip()
            street = match.group(3).strip()
        else:
            prefecture, city, street = None, None, None
    else:
        prefecture, city, street = None, None, None

    # 建物名
    try:
        building_name = driver.find_element(By.CLASS_NAME, 'locality').text
    except NoSuchElementException:
        building_name = None

    # 店舗URL
    try:
        store_url = driver.find_element(By.CSS_SELECTOR, '.url.go-off').get_attribute('href')
    except NoSuchElementException:
        store_url = None
    
    # SSLの有無を判定
    ssl_status = 'False' if store_url and 'http' in store_url else 'True'

    # データをデータフレームに追加
    new_row = {
        '店舗名': store_name, 
        '電話番号': phone_number, 
        'メールアドレス': mail_address,
        '都道府県': prefecture, 
        '市区町村': city, 
        '番地': street, 
        '建物名': building_name, 
        'URL': store_url,
        'SSL': ssl_status
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    print(f"現在のデータ件数: {len(df)}")
    # 終了条件
    if len(df) == elements:
        break

# 終了処理
driver.quit()
print(df)

# CSVに書き込みß
df.to_csv('./Python/ex1_web-scraping/1-2.csv', encoding='utf-8-sig', index=False)