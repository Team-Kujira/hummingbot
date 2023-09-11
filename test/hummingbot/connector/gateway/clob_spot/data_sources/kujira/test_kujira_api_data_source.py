import time
import unittest
from decimal import Decimal
from unittest.mock import AsyncMock

from hummingbot.client.config.client_config_map import ClientConfigMap
from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.connector.gateway.clob_spot.data_sources.kujira.kujira_api_data_source import KujiraAPIDataSource
from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder
from hummingbot.connector.gateway.gateway_order_tracker import GatewayOrderTracker
from hummingbot.connector.utils import combine_to_hb_trading_pair
from hummingbot.core.data_type.common import OrderType, TradeType


class MockConnector(ConnectorBase):
    pass


class KujiraAPIDataSourceTest(unittest.TestCase):
    chain: str
    network: str
    trading_pair: str
    base: str
    quote: str
    trading_pair: str
    owner_address: str

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.chain = "kujira" # noqa: mock
        cls.network = "mainnet"
        cls.base = "KUJI" # noqa: mock
        cls.quote = "USK"
        cls.trading_pair = combine_to_hb_trading_pair(base=cls.base, quote=cls.quote)
        cls.owner_address = "kujira1ga9qk68ne00wfflv7y2v92epaajt59e554uulc" # noqa: mock

    async def setUp(self) -> None:
        super().setUp()
        client_config_map = ClientConfigAdapter(hb_config=ClientConfigMap())
        self.initial_timestamp = time.time()

        self.connector = MockConnector(client_config_map=ClientConfigAdapter(ClientConfigMap()))
        self.tracker = GatewayOrderTracker(connector=self.connector)
        connector_spec = {
            "chain": self.chain,
            "network": self.network,
            "wallet_address": self.owner_address
        }

        self.data_source = KujiraAPIDataSource(
            trading_pairs=[self.trading_pair],
            connector_spec=connector_spec,
            client_config_map=client_config_map,
        )

        self.data_source.gateway_order_tracker = self.tracker

        await self.data_source.start()

    async def test_place_order(self):
        expected_exchange_order_id = "1365802"
        expected_transaction_hash = "9981D7CB9F0542F9B6778149E6501EF9625C848A165D42CA94A4CC8788379562"  # noqa: mock

        order = GatewayInFlightOrder(
            client_order_id="ClientOrderID",
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            creation_timestamp=self.initial_timestamp,
            price=Decimal(0.64),
            amount=Decimal(1.0),
            exchange_order_id=expected_exchange_order_id,
            creation_transaction_hash=expected_transaction_hash,
        )

        self.data_source.place_order = AsyncMock(return_value=order)

        request = GatewayInFlightOrder(
            client_order_id="ClientOrderID",
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            creation_timestamp=self.initial_timestamp,
            price=Decimal(0.6115),
            amount=Decimal(1),
        )

        # result = await self.data_source.place_order(request)

        exchange_order_id, misc_updates = await self.data_source.place_order(order=request)

        self.assertEqual(expected_exchange_order_id, exchange_order_id)
        self.assertEqual({"creation_transaction_hash": expected_transaction_hash}, misc_updates)
