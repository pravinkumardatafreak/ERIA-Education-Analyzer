import requests

url = "https://www.ugc.gov.in/pdfnews/0696290_PMIS_Guidelines.pdf"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

try:
    response = requests.get(url, headers=headers, timeout=15)
    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("Length:", len(response.content))
except Exception as e:
    print(f"Error fetching URL: {e}")
