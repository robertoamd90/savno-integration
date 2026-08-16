DOMAIN = "savno_rifiuti"
BASE_URL = "https://www.savnoservizi.it"
COMMUNITIES_URL = f"{BASE_URL}/admin/api_front_end/selectV2/comune"
ADDRESSES_URL = f"{BASE_URL}/admin/api_front_end/selectV2/indirizzo/"
FORM_URL = f"{BASE_URL}/it/formv2"
CALENDAR_URL = f"{BASE_URL}/it/servizi/servizi-per-le-utenze/raccolta-porta-a-porta"

CONF_COMUNE_ID = "comune_id"
CONF_COMUNE_NAME = "comune_name"
CONF_HAS_ADDRESSES = "has_raccolte_addresses"
CONF_INDIRIZZO_ID = "indirizzo_id"
CONF_INDIRIZZO_NAME = "indirizzo_name"
CONF_CIVICO = "civico"
CONF_UTENZA = "utenza"

UTENZA_DOMESTICA = "1"
UTENZA_AZIENDA = "2"

UPDATE_INTERVAL_HOURS = 3
