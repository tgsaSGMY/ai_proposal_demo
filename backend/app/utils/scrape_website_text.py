import requests
from bs4 import BeautifulSoup

def scrape_website_text(url: str) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # 如果是 4xx 或 5xx 錯誤，會拋出異常 
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 移除 script 和 style 標籤
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        # 獲取文本並清理
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # 截斷以避免過長
        return text[:8000]

    except requests.RequestException as e:
        logger.error(f"Failed to scrape URL {url}: {e}")
        raise HTTPException(status_code=400, detail=f"無法抓取該網址: {e}")