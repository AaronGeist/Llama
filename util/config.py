import os
import json


class Config:
    CONFIG_FILE = "../config/config.json"

    settings = None

    @classmethod
    def initialize(cls):
        if cls.settings is None:
            location = os.path.join(os.path.dirname("__file__"), cls.CONFIG_FILE)
            with open(location, "r") as f:
                cls.settings = json.load(f)

    @classmethod
    def get(cls, attr):
        if cls.settings is None:
            cls.initialize()
        return cls.settings[attr]


if __name__ == "__main__":
    print(Config.get("cookie_location"))
