from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
import logging

import aiohttp
from bs4 import BeautifulSoup

from .const import ADDRESSES_URL, CALENDAR_URL, COMMUNITIES_URL, FORM_URL

_LOGGER = logging.getLogger(__name__)

MONTHS_IT = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}


class SavnoApiError(Exception):
    """Error communicating with SAVNO."""


@dataclass(frozen=True, slots=True)
class SavnoPickup:
    day: date
    waste_types: tuple[str, ...]

    @property
    def summary(self) -> str:
        return " + ".join(self.waste_types)


class SavnoApiClient:
    """Small client for the public endpoints used by the SAVNO website."""

    def __init__(self) -> None:
        self._session = aiohttp.ClientSession(
            cookie_jar=aiohttp.CookieJar(),
            headers={
                "User-Agent": "Home Assistant SAVNO waste collection integration",
                "Accept": "application/json,text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.5",
            },
            timeout=aiohttp.ClientTimeout(total=25),
        )

    async def async_close(self) -> None:
        if not self._session.closed:
            await self._session.close()

    async def async_get_communities(self) -> list[dict[str, Any]]:
        data = await self._async_get_json(COMMUNITIES_URL)
        if not isinstance(data, list):
            raise SavnoApiError("Formato elenco comuni SAVNO non valido")
        return data

    async def async_get_addresses(self, comune_id: str) -> list[dict[str, Any]]:
        data = await self._async_get_json(ADDRESSES_URL, params={"comune": comune_id})
        if not isinstance(data, list):
            raise SavnoApiError("Formato elenco indirizzi SAVNO non valido")
        return data

    async def async_select_profile(
        self,
        *,
        comune_id: str,
        indirizzo_id: str = "",
        civico: str = "",
        utenza: str,
    ) -> None:
        try:
            async with self._session.get(
                FORM_URL,
                params={
                    "comune": comune_id,
                    "indirizzo": indirizzo_id,
                    "civico": civico,
                    "utenza": utenza,
                },
            ) as response:
                response.raise_for_status()
                result = (await response.text()).strip()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise SavnoApiError(f"Errore durante la selezione del profilo SAVNO: {err}") from err

        if result != "OK":
            raise SavnoApiError(f"SAVNO formv2 ha restituito {result!r} invece di 'OK'")

    async def async_get_pickups(self, today: date) -> list[SavnoPickup]:
        try:
            async with self._session.get(CALENDAR_URL) as response:
                response.raise_for_status()
                html = await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise SavnoApiError(f"Errore durante il download del calendario SAVNO: {err}") from err

        return parse_pickups(html, today)

    async def _async_get_json(
        self, url: str, params: dict[str, str] | None = None
    ) -> Any:
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise SavnoApiError(f"Errore API SAVNO: {err}") from err


def parse_pickups(html: str, today: date) -> list[SavnoPickup]:
    """Parse the server-rendered 'prossimi 7 giorni' calendar."""
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("div.row_box_calendario")
    if not rows:
        raise SavnoApiError(
            "Calendario SAVNO non trovato nella pagina; sessione non valida o struttura del sito modificata"
        )

    pickups: list[SavnoPickup] = []
    for row in rows:
        day_el = row.select_one(".calendario_numero")
        month_el = row.select_one(".calendario_mese")
        if day_el is None or month_el is None:
            continue

        try:
            day_num = int(day_el.get_text(strip=True))
            month_num = MONTHS_IT[month_el.get_text(strip=True).lower()]
        except (ValueError, KeyError):
            continue

        event_day = date(today.year, month_num, day_num)
        if event_day < today - timedelta(days=7):
            event_day = date(today.year + 1, month_num, day_num)

        waste_types: list[str] = []
        for image in row.select("img.icona_bidone"):
            parent = image.find_parent("p")
            if parent is None:
                continue
            text = " ".join(parent.stripped_strings)
            if text and text not in waste_types:
                waste_types.append(text)

        if waste_types:
            pickups.append(SavnoPickup(event_day, tuple(waste_types)))

    pickups.sort(key=lambda item: item.day)
    return pickups
