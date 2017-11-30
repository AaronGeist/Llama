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
    sticky = False
    discount = 100
    discount_ttl = ""
    since = ""

    def __str__(self):
        msg = list()
        msg.append(str(self.id))
        if self.free:
            msg.append("Y")
        else:
            msg.append("N")
        if self.sticky:
            msg.append("Y")
        else:
            msg.append("N")

        msg.append(str(self.discount))
        msg.append(str(self.upload_num))
        msg.append(str(self.download_num))
        msg.append(self.title[0: 25])
        msg.append(self.since)
        msg.append(str(int(self.size / 1024)))

        return "|".join(msg)


class TransmissionSeed:
    id = ""
    done = 0
    size = 0
    ETA = None
    up = 0
    down = 0
    ratio = 0
    status = None
    name = ""
    since = 0
    done_size = 0
    location = ""
    file = ""

    def __str__(self):
        msg = list()
        msg.append(self.id)
        msg.append(str(self.done))
        msg.append(str(self.size))
        msg.append(str(self.ETA))
        msg.append(str(self.up))
        msg.append(str(self.down))
        msg.append(str(self.ratio))
        msg.append(str(self.status))
        msg.append(str(self.name))
        msg.append(str(self.since))
        msg.append(str(self.done_size))
        msg.append(str(self.location))
        msg.append(str(self.file))

        return "|".join(msg)


if __name__ == "__main__":
    l = []
    seed = TransmissionSeed()
    seed.size = 1
    seed.up = 2
    seed.ETA = ""
    seed.status = ""
    l.append(seed)

    seed = TransmissionSeed()
    seed.size = 2
    seed.up = 2
    seed.ETA = ""
    seed.status = ""
    l.append(seed)

    seed = TransmissionSeed()
    seed.size = 3
    seed.up = 1
    seed.ETA = ""
    seed.status = ""
    l.append(seed)

    seed = TransmissionSeed()
    seed.size = 3
    seed.up = 100
    seed.ETA = ""
    seed.status = ""
    l.append(seed)

    l.sort(key=lambda x: round(x.size / x.up), reverse=True)
    for i in l:
        print(i)
