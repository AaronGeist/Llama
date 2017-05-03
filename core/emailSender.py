# -*- coding:utf-8 -*-  

import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

from model.email import Email
from util.config import Config


class EmailSender:
    @classmethod
    def format_addr(cls, s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    @classmethod
    def build_msg(cls, email):
        msg = MIMEText(email.body, 'plain', 'utf-8')
        msg['From'] = cls.format_addr(u'自己 <%s>' % email.from_addr)
        msg['To'] = cls.format_addr(u'自己 <%s>' % email.to_addr)
        msg['Subject'] = Header(email.title, 'utf-8').encode()

        return msg

    @classmethod
    def generate_email(cls, title, content):
        email = Email()
        email.from_addr = Config.get("email_from_addr")
        email.to_addr = Config.get("email_to_addr")
        email.password = Config.get("email_password")
        email.stmp_server = Config.get("email_stmp_server")
        email.stmp_port = Config.get("email_stmp_port")
        email.is_ssl = Config.get("email_is_ssl")
        email.title = title
        email.body = content
        return email

    @classmethod
    def send(cls, title, content):
        email = cls.generate_email(title, content)
        msg = cls.build_msg(email)
        if email.is_ssl:
            server = smtplib.SMTP_SSL(email.stmp_server, email.stmp_port)
        else:
            server = smtplib.SMTP(email.stmp_server, email.stmp_port)
        server.set_debuglevel(1)
        server.login(email.from_addr, email.password)
        server.sendmail(email.from_addr, email.to_addr, msg.as_string())
        server.quit()

if __name__ == "__main__":
    EmailSender.send("test", "test")
