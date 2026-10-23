"""Configuration Wrapper"""

import json
import sys


class ConfigError(Exception):
    pass


DEFAULT_PATH = "/config.json"  # ESP32 constraint: no actual "fs"

"""
    Init the config, this function will either return None, or a dict, set a optinal "fail_open" flag if you want to continue dispite an
    exception being raised, an unexpected error will always result in a exit, regardless of the condtion

    path: defaults to "DEFAULT_PATH", must pass "path" as a string
"""


def init_config(path=DEFAULT_PATH, *, fail_open=False) -> dict | None:

    try:
        if type(path) is str:
            with open(path) as f:
                config = json.load(f)
                if (t := type(config)) == dict:
                    print(f"init: found valid configuration at {path}")
                    return config
                else:
                    if __continue(fail_open):
                        return None
                # Else, type is nor a dict, nor nfig raise instead of calling sys.exit(), and let main.py decide whether to exit. The config function shouldn't be the one deciding to kill the whole program.can we fail open, so raise the final case and exit
                raise ConfigError(f"error=expected a dict, got={t}")
        raise ConfigError(f"error=path is not a string path={path}, type={type(path)}")

    except OSError:
        print(f"error=could not find configuration file. path={path}")
        if __continue(fail_open):
            return None
    except ValueError as err:
        print(f"error=invalid json configuration, err={err}")
        if __continue(fail_open):
            return None
    except ConfigError as err:
        print(err)
        if __continue(fail_open):
            return None
    except Exception as err:  # noqa BLE001
        print(f"unexpected_error={err}")
        sys.exit()


# Simply exit if failed, or return true
def __continue(v):
    if v == True:
        return True
    else:
        sys.exit()


if __name__ == "__main__":
    init_config()
