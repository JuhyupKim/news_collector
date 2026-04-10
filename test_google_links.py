import sys
import io
sys.stdout.reconfigure(encoding='utf-8')

import google_news_crawler

urls = [
    "https://news.google.com/articles/CBMieEFVX3lxTE1LUFlRbFlZVElLTmthOGpRQ2d3QjhEcGVkLTZWNXJHRjZzWkN0UUdMdlRqUTF4ZzlrVTYxbHp2eEh0dEJBQUxReU9qWml1RjF2anVXYmpGeWRTeUQyQWh4WTcxVXkxakRfTHJVVmdhc3lHRTZFaXh6RtIBeEFVX3lxTE1LUFlRbFlZVElLTmthOGpRQ2d3QjhEcGVkLTZWNXJHRjZzWkN0UUdMdlRqUTF4ZzlrVTYxbHp2eEh0dEJBQUxReU9qWml1RjF2anVXYmpGeWRTeUQyQWh4WTcxVXkxakRfTHJVVmdhc3lHRTZFaXh6Rg?oc=5",
    "https://news.google.com/articles/CBMiVEFVX3lxTE9HSEtLRXJKNGlSMF9qbVdJZWdsUWhxNlk0Ump6eVVxcXlYVFpDRlJQX2xHQlRkNTRSVWJRLUxGdWpWVENja0Z1OVU1eGNtbDVLS1dkRQ?oc=5",
    "https://news.google.com/articles/CBMiaEFVX3lxTE52Y1JFVS1Ja2xZTDdwVzJhX1RpcXBRYkFNTjJ4LVNFb1c5NmtRMFk0ZkhHWXktZ19ZS1JiVC1UdEZZYU11MmJyenpobF9WZXAtRGNlSWdJaFBfTXJUZEVkcW9Gc04zNGtL?oc=5",
    "https://news.google.com/articles/CBMieEFVX3lxTE43TC1VOVhzSUFuVS1XSC1xQWUyNmk1QV81NFZZc2ozV191MWJHUXpnT2lLRDNhbmZjWnpMeUdPQnZSdjRBUUZKVUI1ZG1YVkh5b2h6UW5CMUFoR3NQbklDLUIzaGNHQnh5V2tyN3RHdk5BNElTNzFDRQ?oc=5"
]

for i, url in enumerate(urls, 1):
    print(f"\n--- URL {i} ---")
    try:
        content, summary = google_news_crawler.get_article_content(url)
        print(f"Content Length: {len(content)}")
        print(f"Summary preview: {summary[:100]}...")
    except Exception as e:
        print(f"Error: {e}")

