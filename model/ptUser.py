class User:
    id = 0
    name = ""
    rank = ""
    ratio = 0
    up = 0
    down = 0
    last_time = ""
    create_time = ""
    warn_time = ""
    mp = 0
    is_ban = False
    is_secret = False

    def __str__(self):
        data = list()
        data.append(str(self.id))
        data.append(self.name)
        data.append(self.rank)
        data.append(str(self.ratio))
        data.append(str(self.up).replace(",", ""))
        data.append(str(self.down).replace(",", ""))
        data.append(self.last_time)
        data.append(self.create_time)
        data.append(self.warn_time)
        data.append(str(self.mp).replace(",", ""))
        data.append(str(self.is_ban))
        data.append(str(self.is_secret))

        return "|".join(data)

    @classmethod
    def parse(cls, line):
        data = str(line).strip().split("|")
        if len(data) < 11:
            print("cannot parse: " + line)
            return None

        user = User()
        user.id = data[0]
        user.name = data[1]
        user.rank = data[2]
        user.ratio = float(data[3].replace(",", ""))
        user.up = float(data[4])
        user.down = float(data[5])
        user.last_time = data[6]
        user.create_time = data[7]
        user.warn_time = data[8]
        user.mp = float(data[9])
        user.is_ban = data[10] == "True"
        user.is_secret = data[11] == "True"

        return user



