from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import SavnoCoordinator

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR]
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)
_FRONTEND_URL = "/api/savno_rifiuti/frontend/savno-prossimi-ritiri-card.js?v=0.5.5"
_FRONTEND_REGISTERED = f"{DOMAIN}_frontend_registered"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Expose and load the SAVNO dashboard card once per HA runtime."""
    if hass.data.get(_FRONTEND_REGISTERED):
        return

    frontend_path = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                "/api/savno_rifiuti/frontend",
                str(frontend_path),
                False,
            )
        ]
    )

    # Register the JS only after the HTTP route exists. Doing this from
    # async_setup() makes the route available before individual config entries
    # perform network I/O / their first coordinator refresh.
    add_extra_js_url(hass, _FRONTEND_URL)
    hass.data[_FRONTEND_REGISTERED] = True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration-wide resources as early as possible."""
    await _async_register_frontend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a SAVNO config entry."""
    coordinator = SavnoCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: SavnoCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_close()
    return unload_ok
