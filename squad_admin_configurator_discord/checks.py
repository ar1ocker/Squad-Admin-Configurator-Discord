import discord


class BaseChecksError(discord.ApplicationCommandError):
    pass


class WrongGuildError(BaseChecksError):
    pass


def only_this_guilds(guild_ids: list[int]):
    async def wrapper(context: discord.ApplicationContext):
        if context.guild_id not in guild_ids:
            await context.respond("Мы тут не работаем", ephemeral=True)
            raise WrongGuildError()

        return True

    return wrapper
