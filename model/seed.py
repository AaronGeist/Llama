class SeedInfo:
    id = ""
    title = ""
    url = ""
    size = 0
    download_num = 0
    upload_num = 0
    finish_num = 0
    hot = False
    free = False
    discount = 0
    discount_ttl = ""
    since = ""

    def __str__(self):
        msg = []
        if self.free:
            msg.append("Y")
        else:
            msg.append("N")

        msg.append(str(self.upload_num))
        msg.append(str(self.download_num))
        msg.append(self.since)
        msg.append(str(int(self.size / 1024)))

        return ("|".join(msg) + '\n').encode("utf-8")
