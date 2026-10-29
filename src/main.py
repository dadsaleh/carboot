from config import *


def main():
    print("init: attempting to load configuration file")
    try:
        if (config := init_config()) != None:
            print("init: configuration loaded from path")
            for key, value in config.items():
                print(key, "=", value)
    except ConfigError as err:
        print(f"ERROR={err}")


if __name__ == "__main__":
    main()
