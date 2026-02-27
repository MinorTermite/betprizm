import requests
from bs4 import BeautifulSoup

url = "https://www.marathonbet.ru/su/betting/Tennis/ATP/Masters%2B1000%2B-%2B88884"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
html = resp.text
soup = BeautifulSoup(html, 'lxml')
rows = soup.select('div.coupon-row')
if rows:
    row = rows[0]
    print("Row text:")
    import re
    cleaned_text = re.sub(r'\s+', ' ', row.text)
    print(cleaned_text[:1000])
    print("All buttons/links:")
    for a in row.find_all(['a', 'button', 'div']):
        if 'data-selection-key' in a.attrs or 'data-selection-price' in a.attrs:
            print("  FOUND:", a.name, a.get('class'), a.text.strip())
    print(html[:1000])
