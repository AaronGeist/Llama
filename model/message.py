class Message:
    id = ""
    read = False
    title = ""
    body = ""
    from_user = ""
    to_user = ""
    since = ""

    def __str__(self):
        msg = list()
        msg.append(str(self.id))
        msg.append(str(self.read))
        msg.append(str(self.title))
        msg.append(str(self.body))
        msg.append(str(self.from_user))
        msg.append(str(self.to_user))
        msg.append(str(self.since))

        return "|".join(msg)
