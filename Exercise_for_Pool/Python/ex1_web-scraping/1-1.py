from urllib import request
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

base_url = 'https://r.gnavi.co.jp/eki/0002846/rs/'
urls = []
elements = 50  # URLの数

while len(urls) < elements and base_url:
    time.sleep(3)
    response = request.urlopen(base_url)
    soup = BeautifulSoup(response, 'html.parser')
    response.close()
    # urlの取得
    new_urls = [link.get('href') for link in soup.find_all('a', class_='style_titleLink__oiHVJ') if link.get('href')]
    urls.extend(new_urls)
    if len(urls) >= elements:
        break
    # クローリング
    next_page = soup.find('img', class_='style_nextIcon__M_Me_')
    if next_page:
        next_page_url = next_page.find_parent('a').get('href')
        base_url = f"https://r.gnavi.co.jp{next_page_url}"
    else:
        break
# データフレーム
df = pd.DataFrame(columns=['店舗名', '電話番号', 'メールアドレス', '都道府県', '市区町村', '番地', '建物名', 'URL', 'SSL'])

for url in urls[:elements]:
    response = request.urlopen(url)
    soup = BeautifulSoup(response, 'html.parser')
    response.close()

    # 店舗名
    store_name = soup.find('p', id='info-name').text.strip() if soup.find('p', id='info-name') else None
    
    # 電話番号
    phone_number = soup.find('span', class_='number').text.strip() if soup.find('span', class_='number') else None
    
    # メールアドレス
    mail_tag = soup.find('a', string='お店に直接メールする')
    mail_address = mail_tag.get('href') if mail_tag else None
    
    # 住所の取得
    address = soup.find('span', class_='region').text.strip() if soup.find('span', class_='region') else None
    address_pattern = r'([^¥d]+?都|道|府|県)([^¥d]+?[市区町村])(.+)'
    match = re.search(address_pattern, address) if address else None
    
    # 都道府県・市区町村・番地
    prefecture, city, street = (match.group(1), match.group(2), match.group(3)) if match else (None, None, None)
    
    # 建物名
    building = soup.find('span', class_='locality')
    building_name = building.text.strip() if building else None
    
    # SSLの有無
    store_url = soup.find('a', class_='url go-off').get('href') if soup.find('a', class_='url go-off') else None
    ssl_status = 'True' if store_url and 'https://' in store_url else 'False'
    
    # データフレームに追加
    new_row = pd.DataFrame([{
        '店舗名': store_name, 
        '電話番号': phone_number, 
        'メールアドレス': mail_address, 
        '都道府県': prefecture, 
        '市区町村': city, 
        '番地': street, 
        '建物名': building_name, 
        'URL': None, 
        'SSL': ssl_status
    }])
    df = pd.concat([df, new_row], ignore_index=True)

print(df)
# csvに書き込み
df.to_csv('./Python/ex1_web-scraping/1-1.csv', encoding='utf-8-sig', index=False)
