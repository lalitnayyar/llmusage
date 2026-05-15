from db import config_get, config_set


def logging_enabled() -> bool:
    return config_get("logging", "off").lower() == "on"


def set_logging(enabled: bool) -> None:
    config_set("logging", "on" if enabled else "off")
