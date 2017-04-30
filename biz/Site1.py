from core.crawler import BaseCrawler


class Site1(BaseCrawler):
    navigation_url = "http://www.kuaidaili.com/free/inha/" + BaseCrawler.PAGE_NUM_PLACEHOLDER + "/"

    line_css_selector = "#container #list table tbody tr"
    ip_css_selector = "td:nth-of-type(1)"
    port_css_selector = "td:nth-of-type(2)"
