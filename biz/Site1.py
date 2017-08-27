from core.crawler import BaseCrawler


class Site1(BaseCrawler):
    navigation_url = "http://www.kuaidaili.com/free/intr/" + BaseCrawler.PAGE_NUM_PLACEHOLDER + "/"

    line_css_selector = "#list table tbody tr"
    ip_css_selector = "td:nth-of-type(1)"
    port_css_selector = "td:nth-of-type(2)"
    headers = {
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    interval = 5