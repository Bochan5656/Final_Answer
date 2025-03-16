from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import re
import ssl
from urllib.parse import urlparse
import socket

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
    except Exception:
        store_name = None
    
    # 電話番号
    try:
        phone_number = driver.find_element(By.CLASS_NAME, 'number').text
    except Exception:
        phone_number = None

    # メールアドレス
    try:
        mail_element = driver.find_element(By.LINK_TEXT, 'お店に直接メールする')
        mail_address = mail_element.get_attribute('href')
    except Exception:
        mail_address = None

    # 住所
    try:
        address = driver.find_element(By.CLASS_NAME, 'region').text
    except Exception:
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
    except Exception:
        building_name = None

    # 店舗URL
    try:
        original_tab = driver.current_window_handle  # 元のタブを記憶
        official_page = driver.find_element(By.CLASS_NAME, 'sv-of')
        # オフィシャルページへ遷移
        official_page.click()
        driver.set_page_load_timeout(60)

        driver.switch_to.window(driver.window_handles[-1])
        store_url = driver.current_url  # オフィシャルページのurlを取得
        host = urlparse(store_url).hostname  # ホスト名を取得
        
        # タブを閉じる
        driver.close()
        driver.switch_to.window(original_tab)
    except Exception:
        print('オフィシャルページなし')
        store_url = None
        host = None
    
    # SSL証明書の有無を判定
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                ssl_status = 'True'
    except Exception:
        ssl_status = 'False'

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

# CSVに書き込み
df.to_csv('./Python/ex1_web-scraping/1-2.csv', encoding='utf-8-sig', index=False)