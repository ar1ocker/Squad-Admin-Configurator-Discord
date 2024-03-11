import discord

import checks


class Bot(discord.Bot):
    async def on_application_command_error(
        self, context: discord.ApplicationContext, exception: discord.DiscordException
    ):
        # Замалчиваем базовые ошибки
        if isinstance(exception, checks.BaseChecksError):
            return

        await super().on_application_command_error(context, exception)
