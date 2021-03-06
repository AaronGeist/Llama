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
    sticky = 0
    discount = 100
    discount_ttl = ""
    since = ""
    done = ""
    working = False

    def __str__(self):
        msg = list()
        msg.append("{:>6}".format(self.id))
        if self.free:
            msg.append("free")
        else:
            msg.append("----")
        if self.sticky == 1:
            msg.append("sticky")
        elif self.sticky == 2:
            msg.append("double")
        else:
            msg.append("------")

        msg.append("{:>3}%".format(self.discount))
        msg.append("{:>3}".format(self.upload_num))
        msg.append("{:>3}".format(self.download_num))
        msg.append("{:>3}".format(self.since))
        msg.append("{:>3}GB".format(int(self.size / 1024)))
        msg.append("{:->4}".format(self.done))
        if self.working:
            msg.append("working")
        else:
            msg.append("-------")
        msg.append(self.title[0: 25])

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
        msg.append("{:>3}".format(self.id))
        msg.append("{:>5}%".format(self.done))
        msg.append("{:>4}GB".format(round(self.size / 1024, 1)))
        msg.append("{:>5}KB".format(round(self.up)))
        msg.append("{:>5}KB".format(round(self.down)))
        msg.append("{:>3}".format(self.ratio))
        msg.append("{:<9}".format(self.status))
        msg.append("{:>3}min".format(round(self.since / 60)))
        msg.append("{:<40}".format(self.location[0: 40]))
        msg.append("{:<20}".format(self.name[0: 20]))

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
