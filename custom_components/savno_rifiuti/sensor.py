from __future__ import annotations

from datetime import date, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_COMUNE_NAME, DOMAIN
from .coordinator import SavnoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: SavnoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SavnoTomorrowSensor(coordinator, entry),
            SavnoUpcomingPickupsSensor(coordinator, entry),
        ]
    )


class _SavnoBaseSensor(CoordinatorEntity[SavnoCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SavnoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"SAVNO {entry.data[CONF_COMUNE_NAME]}",
            "manufacturer": "SAVNO",
            "model": "Raccolta porta a porta",
        }


class SavnoTomorrowSensor(_SavnoBaseSensor):
    _attr_name = "Ritiro domani"
    _attr_icon = "mdi:trash-can-clock-outline"

    def __init__(self, coordinator: SavnoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_tomorrow"

    @property
    def native_value(self) -> str:
        tomorrow = dt_util.now().date() + timedelta(days=1)
        waste_types = _waste_for_day(self.coordinator.data or [], tomorrow)
        return " + ".join(waste_types) if waste_types else "Nessun ritiro"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        tomorrow = dt_util.now().date() + timedelta(days=1)
        waste_types = _waste_for_day(self.coordinator.data or [], tomorrow)
        return {
            "data": tomorrow.isoformat(),
            "rifiuti": waste_types,
            "comune": self._entry.data[CONF_COMUNE_NAME],
        }


class SavnoUpcomingPickupsSensor(_SavnoBaseSensor):
    """Expose all pickup rows returned by SAVNO for easy Lovelace tables."""

    _attr_name = "Prossimi ritiri"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: SavnoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_upcoming"

    @property
    def native_value(self) -> str:
        pickups = self.coordinator.data or []
        if not pickups:
            return "Nessun ritiro"
        first = pickups[0]
        return f"{_friendly_day(first.day)} · {first.summary}"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        pickups = self.coordinator.data or []
        rows = [
            {
                "giorno_settimana": _weekday_it(pickup.day),
                "quando": _friendly_day(pickup.day),
                "data": pickup.day.isoformat(),
                "giorni_mancanti": (pickup.day - dt_util.now().date()).days,
                "cosa": pickup.summary,
                "rifiuti": list(pickup.waste_types),
            }
            for pickup in pickups
        ]
        return {
            "ritiri": rows,
            "numero_ritiri": len(rows),
            "comune": self._entry.data[CONF_COMUNE_NAME],
        }


def _waste_for_day(pickups, target_day: date) -> list[str]:
    waste_types: list[str] = []
    for pickup in pickups:
        if pickup.day == target_day:
            for waste in pickup.waste_types:
                if waste not in waste_types:
                    waste_types.append(waste)
    return waste_types


def _friendly_day(day: date) -> str:
    today = dt_util.now().date()
    if day == today:
        return "Oggi"
    if day == today + timedelta(days=1):
        return "Domani"
    return day.strftime("%d/%m")


def _weekday_it(day: date) -> str:
    """Return the weekday name in Italian without relying on OS locale."""
    weekdays = (
        "Lunedì",
        "Martedì",
        "Mercoledì",
        "Giovedì",
        "Venerdì",
        "Sabato",
        "Domenica",
    )
    return weekdays[day.weekday()]
