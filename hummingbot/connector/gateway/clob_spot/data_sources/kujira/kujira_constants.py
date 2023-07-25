from dotmap import DotMap

KUJIRA_NATIVE_TOKEN = DotMap({
    "id": "ukuji",
    "name": "Kuji",
    "symbol": "KUJI",
    "decimals": "6",
}, _dynamic=False)

CONNECTOR = "kujira"

MARKETS_UPDATE_INTERVAL = 8 * 60 * 60

NUMBER_OF_RETRIES = 3
DELAY_BETWEEN_RETRIES = 3
TIMEOUT = 60
