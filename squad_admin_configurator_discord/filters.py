import re

from dateutil.parser import isoparse


def escape_markdown(value: str) -> str:
    return re.sub(r"([_*~`>|\[\]])", r"\\\1", value)


def format_datetime(value: str) -> str:
    date = isoparse(value)
    return date.strftime(r"%d.%m.%Y %H:%M")
