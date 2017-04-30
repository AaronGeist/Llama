class Proxy:
    ip = None
    port = None
    protocol = []

    def __str__(self):
        return "%s://%s:%s" % (self.protocol, self.ip, str(self.port))
