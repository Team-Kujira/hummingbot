from dotmap import DotMap

KUJIRA_NATIVE_TOKEN = DotMap({
    "id": "ukuji",
    "name": "Kuji",
    "symbol": "KUJI",
    "decimals": "6",
}, _dynamic=False)

CONNECTOR = "kujira"

MARKETS_UPDATE_INTERVAL = 8 * 60 * 60
