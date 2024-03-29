from util.utils import HttpUtils
import abc


class Login:
    # login status cache
    isLogin = False

    def login(self, site):
        if not self.isLogin and site.login_needed and not self.check_login(site):
            if site.need_captcha:
                site.login_captcha_value = self.parse_captcha(site)

            # trigger login action
            HttpUtils.post(site.login_page, data=self.build_post_data(site),
                           headers=site.login_headers, returnRaw=True)

            self.isLogin = self.check_login(site)
            return self.isLogin
        else:
            self.isLogin = True
            return True

    @abc.abstractmethod
    def build_post_data(self, site):
        pass

    @abc.abstractmethod
    def parse_captcha(self, site):
        pass

    def check_login(self, site):
        HttpUtils.create_session_if_absent()
        HttpUtils.load_cookie()

        soup_obj = HttpUtils.get(site.home_page, headers=site.login_headers)
        content = HttpUtils.get_content(soup_obj, site.login_verify_css_selector)
        print("Current user is " + str(content))
        result = content is not None and content == site.login_verify_str

        if result:
            HttpUtils.save_cookie()
        else:
            HttpUtils.clear_cookie()

        return result
