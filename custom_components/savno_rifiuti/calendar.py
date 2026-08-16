from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import SavnoPickup
from .const import CONF_COMUNE_NAME, CONF_INDIRIZZO_NAME, DOMAIN
from .coordinator import SavnoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: SavnoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SavnoCalendar(coordinator, entry)])


class SavnoCalendar(CoordinatorEntity[SavnoCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "Raccolta rifiuti"
    _attr_icon = "mdi:trash-can-outline"

    def __init__(self, coordinator: SavnoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        comune = entry.data[CONF_COMUNE_NAME]
        address = entry.data.get(CONF_INDIRIZZO_NAME, "")
        self._location = f"{address}, {comune}" if address else comune
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"SAVNO {comune}",
            "manufacturer": "SAVNO",
            "model": "Raccolta porta a porta",
        }

    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().date()
        for pickup in self.coordinator.data or []:
            if pickup.day >= today:
                return self._to_event(pickup)
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        start_day = start_date.date()
        end_day = end_date.date()
        return [
            self._to_event(pickup)
            for pickup in (self.coordinator.data or [])
            if pickup.day < end_day and pickup.day + timedelta(days=1) > start_day
        ]

    def _to_event(self, pickup: SavnoPickup) -> CalendarEvent:
        return CalendarEvent(
            start=pickup.day,
            end=pickup.day + timedelta(days=1),
            summary=pickup.summary,
            description="Raccolta porta a porta SAVNO",
            location=self._location,
        )
