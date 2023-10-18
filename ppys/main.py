import os
from dotenv import load_dotenv
import utils

APP_NAME = "ppys"
lg = utils.init_logger(APP_NAME)


def load_environment():
    load_dotenv()
    global PASSWORD
    PASSWORD = os.getenv("PASSWORD")
    print(f"{PASSWORD=}")

def main():
    lg.info("hello world")
    load_environment()
    pass


if __name__ == "__main__":
    main()
