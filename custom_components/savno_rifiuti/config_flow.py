from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.util import dt as dt_util

from .api import SavnoApiClient, SavnoApiError
from .const import (
    CONF_CIVICO,
    CONF_COMUNE_ID,
    CONF_COMUNE_NAME,
    CONF_HAS_ADDRESSES,
    CONF_INDIRIZZO_ID,
    CONF_INDIRIZZO_NAME,
    CONF_UTENZA,
    DOMAIN,
    UTENZA_AZIENDA,
    UTENZA_DOMESTICA,
)


class SavnoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._client: SavnoApiClient | None = None
        self._communities: dict[str, dict[str, Any]] = {}
        self._addresses: dict[str, dict[str, Any]] = {}
        self._selected_address: dict[str, Any] | None = None
        self._data: dict[str, Any] = {}

    async def _get_client(self) -> SavnoApiClient:
        if self._client is None:
            self._client = SavnoApiClient()
        return self._client

    async def _close_client(self) -> None:
        if self._client is not None:
            await self._client.async_close()
            self._client = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if not self._communities:
            try:
                communities = await (await self._get_client()).async_get_communities()
                self._communities = {item["id"]: item for item in communities if item.get("id")}
            except SavnoApiError:
                errors["base"] = "cannot_connect"

        if user_input is not None and not errors:
            comune_id = user_input[CONF_COMUNE_ID]
            comune = self._communities[comune_id]
            self._data.update(
                {
                    CONF_COMUNE_ID: comune_id,
                    CONF_COMUNE_NAME: comune.get("nome_formattato") or comune.get("nome") or comune_id,
                    CONF_HAS_ADDRESSES: bool(comune.get("has_raccolte_addresses")),
                }
            )
            if self._data[CONF_HAS_ADDRESSES]:
                return await self.async_step_address()
            return await self.async_step_user_type()

        options = {
            item_id: item.get("nome_formattato") or item.get("nome") or item_id
            for item_id, item in sorted(
                self._communities.items(),
                key=lambda kv: (kv[1].get("nome_formattato") or kv[1].get("nome") or "").casefold(),
            )
        }
        schema = vol.Schema({vol.Required(CONF_COMUNE_ID): vol.In(options)})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_address(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if not self._addresses:
            try:
                addresses = await (await self._get_client()).async_get_addresses(
                    self._data[CONF_COMUNE_ID]
                )
                self._addresses = {item["id"]: item for item in addresses if item.get("id")}
            except SavnoApiError:
                errors["base"] = "cannot_connect"

        # Some SAVNO municipalities are flagged for addresses but currently
        # return an empty list. The website itself permits proceeding in this case.
        if not errors and not self._addresses:
            self._data[CONF_INDIRIZZO_ID] = ""
            self._data[CONF_INDIRIZZO_NAME] = ""
            self._data[CONF_CIVICO] = ""
            return await self.async_step_user_type()

        if user_input is not None and not errors:
            address_id = user_input[CONF_INDIRIZZO_ID]
            self._selected_address = self._addresses[address_id]
            self._data[CONF_INDIRIZZO_ID] = address_id
            self._data[CONF_INDIRIZZO_NAME] = self._selected_address.get("street", address_id)
            return await self.async_step_house_number()

        options = {
            item_id: item.get("street") or item_id
            for item_id, item in sorted(
                self._addresses.items(), key=lambda kv: (kv[1].get("street") or "").casefold()
            )
        }
        return self.async_show_form(
            step_id="address",
            data_schema=vol.Schema({vol.Required(CONF_INDIRIZZO_ID): vol.In(options)}),
            errors=errors,
        )

    async def async_step_house_number(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        assert self._selected_address is not None
        numbers = [
            str(item.get("number"))
            for item in self._selected_address.get("numbers", [])
            if item.get("number") is not None
        ]

        if not numbers:
            self._data[CONF_CIVICO] = ""
            return await self.async_step_user_type()

        if user_input is not None:
            self._data[CONF_CIVICO] = user_input[CONF_CIVICO]
            return await self.async_step_user_type()

        options = {number: number for number in sorted(numbers, key=str.casefold)}
        return self.async_show_form(
            step_id="house_number",
            data_schema=vol.Schema({vol.Required(CONF_CIVICO): vol.In(options)}),
        )

    async def async_step_user_type(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data[CONF_UTENZA] = user_input[CONF_UTENZA]
            unique = ":".join(
                [
                    self._data[CONF_COMUNE_ID],
                    self._data.get(CONF_INDIRIZZO_ID, ""),
                    self._data.get(CONF_CIVICO, ""),
                    self._data[CONF_UTENZA],
                ]
            )
            await self.async_set_unique_id(unique)
            self._abort_if_unique_id_configured()

            try:
                client = await self._get_client()
                await client.async_select_profile(
                    comune_id=self._data[CONF_COMUNE_ID],
                    indirizzo_id=self._data.get(CONF_INDIRIZZO_ID, ""),
                    civico=self._data.get(CONF_CIVICO, ""),
                    utenza=self._data[CONF_UTENZA],
                )
                # Validate that the selected profile actually produces a calendar.
                await client.async_get_pickups(dt_util.now().date())
            except SavnoApiError:
                errors["base"] = "cannot_connect"
            else:
                await self._close_client()
                title = self._data[CONF_COMUNE_NAME]
                if self._data.get(CONF_INDIRIZZO_NAME):
                    title += f" - {self._data[CONF_INDIRIZZO_NAME]}"
                return self.async_create_entry(title=f"SAVNO {title}", data=self._data)

        return self.async_show_form(
            step_id="user_type",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UTENZA, default=UTENZA_DOMESTICA): vol.In(
                        {
                            UTENZA_DOMESTICA: "Domestica",
                            UTENZA_AZIENDA: "Aziendale",
                        }
                    )
                }
            ),
            errors=errors,
        )
