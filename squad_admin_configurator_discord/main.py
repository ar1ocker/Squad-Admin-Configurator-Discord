import logging
import sys
from pathlib import Path
from typing import Any

import checks
import cogs
import filters
import jinja2
import toml
from bot import Bot

BASE_PATH: Path = Path(__file__).resolve().parent
sys.path.append(BASE_PATH)  # type: ignore


def main() -> None:
    logging.basicConfig(format="%(asctime)s - %(name)s - %(message)s", level=logging.INFO)

    config: dict[str, Any] = toml.load(BASE_PATH / "config.toml")

    jinja_templates_path = Path(config["TEMPLATES"]["DIR"])

    if not jinja_templates_path.is_absolute():
        jinja_templates_path = BASE_PATH / jinja_templates_path

    jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(BASE_PATH / config["TEMPLATES"]["DIR"]),
        autoescape=jinja2.select_autoescape(),
        auto_reload=config["TEMPLATES"]["AUTO_RELOAD"],
        trim_blocks=True,
        lstrip_blocks=True,
        enable_async=True,
    )
    jinja_environment.filters["escape_markdown"] = filters.escape_markdown
    jinja_environment.filters["format_datetime"] = filters.format_datetime

    bot = Bot()
    bot.add_check(checks.only_this_guilds(config["DISCORD"]["GUILDS"]))

    cogs.privileges.setup_cog(bot, config, jinja_environment)

    bot.run(config["DISCORD"]["TOKEN"])


if __name__ == "__main__":
    main()
