import logging
from typing import Any

import discord
import jinja2
from yarl import URL

import api
from bot import Bot


class PrivilegesCog(discord.Cog):
    privileges_group = discord.SlashCommandGroup("privileges", "Привилегированные пользователи")

    def __init__(self, bot: Bot, config: dict[str, Any], template_env: jinja2.Environment) -> None:
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.api_url = URL(self.config["PRIVILEGES"]["API"])
        self.template_env = template_env
        self.authorization_header = {"Authorization": self.config["PRIVILEGES"]["TOKEN"]}

    def get_permissions(self, context: discord.ApplicationContext, action: str):
        action_map: dict[str, Any] = self.config["DISCORD"]["ACTION_ROLES_MAP"][str(context.guild_id)][action]

        roles: list[discord.Role] = context.user.roles  # type: ignore

        all_actions_permissions = set()
        for role in roles:
            role_permission = action_map.get(str(role.id))

            if role_permission == self.config["ALL_INDICATOR"]:
                return self.config["ALL_INDICATOR"]

            if role_permission:
                all_actions_permissions.update(role_permission)

        return (
            all_actions_permissions
            or self.config["DISCORD"]["ACTION_ROLES_MAP"][str(context.guild_id)][action]["others"]
        )

    @privileges_group.command()
    async def get(self, context: discord.ApplicationContext, steam_id: str, hide: bool = True) -> None:
        # discord не поддерживает огромные int, которыми по факту являются steam_id 64
        try:
            int(steam_id)
        except ValueError:
            await context.send_response("Неправильный steam_id", ephemeral=True)
            return

        permissions = self.get_permissions(context, "READ")

        if permissions == self.config["NONE_INDICATOR"]:
            await context.send_response("У вас нет прав для запроса", ephemeral=True)
            self.logger.info(f"{context.user.id} Запросил {steam_id} без прав")
            return

        message: discord.Interaction = await context.send_response("Иду запрашивать", ephemeral=hide)

        roles_params = []
        if permissions != self.config["ALL_INDICATOR"]:
            roles_params.extend([("roles", self.config["PRIVILEGES"]["ROLES_ID"][role]) for role in permissions])

        async with api.ConfiguratorSession(self.api_url, headers=self.authorization_header) as session:
            try:
                user = await session.get_privileged(steam_id, [("fields!", "servers_roles")])
                if user is None:
                    await message.edit_original_response(content="Такой пользователь не найден")
                    return

                servers_roles = await session.get_servers_roles(user["id"], roles_params)
                if not servers_roles:
                    await message.edit_original_response(content="Такой пользователь не найден")
                    return
            except api.BaseApiError:
                await message.edit_original_response(content="На текущий момент сервис недоступен")
                return

        template = self.template_env.get_template("privileged_get.md.j2")
        resp: str = await template.render_async(user=user, servers_roles=servers_roles)
        await message.edit_original_response(content=resp)

    @privileges_group.command()
    async def set(
        self,
        context: discord.ApplicationContext,
        steam_id: str,
        name: str,
        role: str,
        duration: int = None,
        hide: bool = True,
    ) -> None:
        try:
            int(steam_id)
        except ValueError:
            await context.send_response("Неправильный steam_id", ephemeral=True)

        permissions = self.get_permissions(context, "WRITE")

        if (
            permissions == self.config["NONE_INDICATOR"]
            or permissions != self.config["ALL_INDICATOR"]
            and role not in permissions
        ):
            await context.send_response("У вас нет прав для запроса", ephemeral=True)
            self.logger.info(f"{context.user.id} Запросил добавление {role} без прав")
            return

        message: discord.Interaction = await context.send_response("Иду добавлять", ephemeral=hide)

        try:
            role_config = self.config["PRIVILEGES"]["ROLE_WEBHOOK"][role]
        except KeyError:
            await message.edit_original_response(
                content="Вебхук для данной роли не найден, проверьте название роли или конфигурацию бота"
            )
            return

        url_postfix: str = role_config["url_postfix"]
        hmac_key: str = role_config["hmac_key"]
        hmac_header: str = role_config["hmac_header"]
        hmac_hash: str = role_config["hmac_hash"]

        comment = f"Добавил {context.user.global_name} {context.user.id}"

        async with api.ConfiguratorSession(self.api_url) as session:
            try:
                await session.call_role_webhook(
                    url_postfix, steam_id, name, comment, duration, hmac_key, hmac_hash, hmac_header
                )
            except api.BaseApiError:
                await message.edit_original_response(content="На текущий момент сервис недоступен")
                return

        template = self.template_env.get_template("privileged_set.md.j2")
        resp: str = await template.render_async(steam_id=steam_id, role=role)

        await message.edit_original_response(content=resp)


def setup_cog(bot: Bot, config: dict[str, Any], template_env: jinja2.Environment) -> None:
    bot.add_cog(PrivilegesCog(bot, config, template_env))
