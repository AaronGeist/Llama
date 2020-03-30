from util.utils import HttpUtils


class FlyerWatchDog:
    @classmethod
    def check_and_notify(cls):
        url = "https://www.flyertea.com/forum.php?mod=forumdisplay&orderby=dateline&sum=226&fid=226&mobile=2"
        soup_obj = HttpUtils.get(url, return_raw=False)
        titles = list(map(lambda title: title.strip(), HttpUtils.get_contents(soup_obj, "div.n5sq_htmk p.n5_htnrbt")))
        readers = list(map(lambda x: int(x), HttpUtils.get_contents(soup_obj, "div.n5sq_htmk div.n5_hthfcs")))
        flowers = list(
            map(lambda x: int(x) if x else 0, HttpUtils.get_contents(soup_obj, "div.n5sq_htmk div.n5_htdzcs")))

        print(titles)
        print(readers)
        print(flowers)


if __name__ == "__main__":
    FlyerWatchDog.check_and_notify()
