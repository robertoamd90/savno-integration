from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import SavnoApiClient, SavnoApiError, SavnoPickup
from .const import (
    CONF_CIVICO,
    CONF_COMUNE_ID,
    CONF_INDIRIZZO_ID,
    CONF_UTENZA,
    DOMAIN,
    UPDATE_INTERVAL_HOURS,
)

_LOGGER = logging.getLogger(__name__)


class SavnoCoordinator(DataUpdateCoordinator[list[SavnoPickup]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )
        self.entry = entry
        self.client = SavnoApiClient()
        self._unsub_midnight = async_track_time_change(
            hass,
            self._handle_midnight,
            hour=0,
            minute=0,
            second=0,
        )

    async def async_close(self) -> None:
        self._unsub_midnight()
        await self.client.async_close()

    @callback
    def _handle_midnight(self, _now: datetime) -> None:
        """Refresh date-dependent entity state without calling SAVNO."""
        self.async_update_listeners()

    async def _async_update_data(self) -> list[SavnoPickup]:
        try:
            # formv2 stores the selected profile in the session cookie. We run it
            # on every refresh so the integration self-heals if SAVNO expires it.
            await self.client.async_select_profile(
                comune_id=self.entry.data[CONF_COMUNE_ID],
                indirizzo_id=self.entry.data.get(CONF_INDIRIZZO_ID, ""),
                civico=self.entry.data.get(CONF_CIVICO, ""),
                utenza=self.entry.data[CONF_UTENZA],
            )
            return await self.client.async_get_pickups(dt_util.now().date())
        except SavnoApiError as err:
            raise UpdateFailed(str(err)) from err
