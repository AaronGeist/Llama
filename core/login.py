from util.utils import HttpUtils


class Login:
    # login status cache
    isLogin = False

    @classmethod
    def login(cls, site):
        if not cls.isLogin and site.login_needed and not cls.check_login(site):
            res = HttpUtils.post(site.login_page, data=cls.build_post_data(site),
                           headers=site.login_headers, returnRaw=True)

            cls.isLogin = cls.check_login(site)
            return cls.isLogin
        else:
            cls.isLogin = True
            return True

    @classmethod
    def build_post_data(cls, site):
        data = dict()
        data['username'] = site.login_username
        data['password'] = site.login_password
        data['checkcode'] = "XxXx"

        return data

    @classmethod
    def check_login(cls, site):
        content = HttpUtils.get_content(HttpUtils.get(site.home_page, headers=site.login_headers),
                                        site.login_verify_css_selector)
        return content is not None and content == site.login_verify_str
