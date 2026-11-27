"""Offline regression tests for the SAVNO calendar parser.

Run from repository root: python -m unittest discover -s tests
Requires aiohttp, but not Home Assistant or an internet connection.
"""
import importlib
import sys
import types
import unittest
from datetime import date
from pathlib import Path

# Import the API without running the integration's Home Assistant bootstrap.
package_name = "_savno_parser_test"
package = types.ModuleType(package_name)
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "savno_rifiuti")]
sys.modules[package_name] = package
api = importlib.import_module(f"{package_name}.api")
parse_pickups = api.parse_pickups
SavnoPickup = api.SavnoPickup
SavnoApiError = api.SavnoApiError


def row(day, month, body):
    return (f'<div class="row row_box_calendario">'
            f'<div class="calendario_numero">{day}</div>'
            f'<div class="calendario_mese">{month}</div>{body}</div>')


class ParserTests(unittest.TestCase):
    def test_multiple_pickups_sorted_and_deduplicated(self):
        html = row(30, "novembre", '<p><img class="icona_bidone"/>Vetro</p>') + row(
            28, " Novembre ", '<p><img class="icon icona_bidone" src="x">Carta <b>e cartone</b></p>'
            '<p><img class="icona_bidone">Umido</p><p><img class="icona_bidone">Umido</p>'
            '<img class="icona_bidone">')
        self.assertEqual(parse_pickups(html, date(2026, 11, 27)), [
            SavnoPickup(date(2026, 11, 28), ("Carta e cartone", "Umido")),
            SavnoPickup(date(2026, 11, 30), ("Vetro",)),
        ])

    def test_year_rollover(self):
        html = row(2, "gennaio", '<p><img class="icona_bidone">Plastica &amp; lattine</p>')
        self.assertEqual(parse_pickups(html, date(2026, 12, 30)), [
            SavnoPickup(date(2027, 1, 2), ("Plastica & lattine",)),
        ])

    def test_empty_and_invalid_rows(self):
        html = row(30, "febbraio", '<p><img class="icona_bidone">Carta</p>') + row(28, "novembre", '<p>Nessun ritiro</p>')
        self.assertEqual(parse_pickups(html, date(2026, 11, 27)), [])

    def test_missing_calendar(self):
        with self.assertRaises(SavnoApiError):
            parse_pickups('<html><form></form></html>', date(2026, 11, 27))
