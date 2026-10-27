from config import init_config


def main():
    print("init: attempting to load configuration file")
    # First, load the configuration
    if (config := init_config()) != None:
        print("init: configuration loaded from path")
        for key, value in config:
            print(key, "=", value)
    else:
        print(
            "init: failed to load configuration file"
        )  # If here, that means fail_open is set to true


if __name__ == "__main__":
    main()
