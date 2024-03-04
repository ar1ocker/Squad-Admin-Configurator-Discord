import json
import logging
from typing import Any, Iterable

import aiohttp

logger = logging.getLogger(__name__)


class BaseApiError(Exception):
    pass


class StatusCodeApiError(BaseApiError):
    pass


class ParsingJsonApiError(json.JSONDecodeError, BaseApiError):
    pass


class ConnectionError(BaseApiError):
    pass


class ConfiguratorSession:
    def __init__(self, api_url, headers=None):
        self.session = aiohttp.ClientSession(api_url, headers=headers)

    async def __aenter__(self) -> "ConfiguratorSession":
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.session.close()

    def __repr__(self) -> str:
        return self.session.__repr__()

    def __str__(self) -> str:
        return self.session.__str__()

    def _parse_response(
        self, response: aiohttp.ClientResponse, data: str, valid_status_code=200
    ) -> list[dict[str, str]]:
        if response.status != valid_status_code:
            logger.error(f"Ответ конфигуратора не 200, {response}, {data}")
            raise StatusCodeApiError("Ответ конфигуратора не 200")

        try:
            json_data: list[dict[str, str]] = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при парсинге json {e}")
            raise ParsingJsonApiError(e.msg, e.doc, e.pos)

        return json_data

    async def get_privileged(
        self, steam_id: int, params: Iterable[tuple[str, str | int]] | None = None
    ) -> dict[str, Any] | None:
        _params: list[tuple[str, str | int]] = [("steam_id", steam_id)]

        if params:
            _params.extend(params)
        try:
            resp: aiohttp.ClientResponse = await self.session.get("/v1/api/privileged/privileges/", params=_params)
            data: str = await resp.text()
        except aiohttp.ClientError:
            raise ConnectionError("Ошибка подключения")

        parsed_data = self._parse_response(resp, data)

        if parsed_data:
            return self._parse_response(resp, data)[0]
        else:
            return None

    async def get_servers_roles(
        self, user_id: int | str, params: Iterable[tuple[str, str | int]] | None = None
    ) -> list[dict[str, Any]]:
        _params: list[tuple[str, str | int]] = [("privileged", user_id)]

        if params:
            _params.extend(params)

        try:
            resp: aiohttp.ClientResponse = await self.session.get(
                "/v1/api/privileged/servers_privileges/", params=_params
            )
            data: str = await resp.text()
        except aiohttp.ClientError:
            raise ConnectionError("Ошибка подключения")

        return self._parse_response(resp, data)
