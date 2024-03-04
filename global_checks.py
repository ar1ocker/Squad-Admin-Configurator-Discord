from discord.ext import commands


async def block_direct_message(context: commands.Context) -> bool:
    return context.guild is not None


def register_global_checks(bot: commands.Bot) -> None:
    bot.add_check(block_direct_message)
