from util.utils import HttpUtils
import abc


class Login:
    # login status cache
    isLogin = False

    def login(self, site):
        if not self.isLogin and site.login_needed and not self.check_login(site):
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

    def check_login(self, site):
        HttpUtils.create_session_if_absent()
        HttpUtils.load_cookie()

        content = HttpUtils.get_content(HttpUtils.get(site.home_page, headers=site.login_headers),
                                        site.login_verify_css_selector)
        print("Find user name: " + str(content))
        result = content is not None and content == site.login_verify_str

        if result:
            HttpUtils.save_cookie()
        else:
            HttpUtils.clear_cookie()

        return result
