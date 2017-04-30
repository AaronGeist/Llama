from core.crawler import BaseCrawler


class Site2(BaseCrawler):
    navigation_url = "http://www.xicidaili.com/nn/" + BaseCrawler.PAGE_NUM_PLACEHOLDER

    line_css_selector = "#ip_list tr"
    ip_css_selector = "td:nth-of-type(2)"
    port_css_selector = "td:nth-of-type(3)"

    skip_first_line = True


if __name__ == "__main__":
    site = Site2()
    proxyInfos = site.parse()
    print(len(proxyInfos))
