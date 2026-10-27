"""Configuration Wrapper"""

import json
import sys

import machine

import sys_cntl


class ConfigError(Exception):
    pass


DEFAULT_PATH = "/config.json"  # ESP32 constraint: no actual "fs"

"""
    Init the config, this function will either return None, or a dict, set the optional "fail_open" flag to continue despite an
    exception being raised. An unexpected error always results in an exit, regardless of the condition.

    path: defaults to DEFAULT_PATH, must be a string
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
                # Not a dict and we cannot fail open, so raise
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
        platform = sys_cntl.get_platform()
        if platform == sys_cntl.LINUX:
            sys.exit(1)
        elif platform == sys_cntl.ESP32:
            machine.deepsleep()
        else:
            sys.exit()  # Unknown platform, so try to exit


"""
    Rationale for this module:
    Configuration is the one thing that must be fully loaded and valid before doing anything else
    machine wise. Callers that access the configuration are expected to validate their own inputs.
"""

if __name__ == "__main__":
    init_config()
