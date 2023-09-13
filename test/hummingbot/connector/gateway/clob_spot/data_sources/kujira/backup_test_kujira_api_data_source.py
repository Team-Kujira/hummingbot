# import asyncio
# import math
# import re
from decimal import Decimal
from typing import Any, Dict

# from typing import Any, Dict, List, Union
from unittest.mock import AsyncMock, MagicMock, Mock, patch

#
# import pandas as pd
from aioresponses import aioresponses

from hummingbot.client.config.config_crypt import ETHKeyFileSecretManger, store_password_verification, validate_password
from hummingbot.client.config.security import Security

#
# from hummingbot.connector.gateway.clob_spot.data_sources.dexalot import dexalot_constants as CONSTANTS
from hummingbot.connector.gateway.clob_spot.data_sources.kujira.kujira_api_data_source import KujiraAPIDataSource

# import time
# import unittest
# from decimal import Decimal
# from unittest.mock import AsyncMock
#
# from hummingbot.client.config.client_config_map import ClientConfigMap
# from hummingbot.client.config.config_helpers import ClientConfigAdapter
# from hummingbot.connector.connector_base import ConnectorBase
# from hummingbot.connector.gateway.clob_spot.data_sources.kujira.kujira_api_data_source import KujiraAPIDataSource
from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder

# from hummingbot.connector.gateway.clob_spot.data_sources.dexalot.dexalot_constants import HB_TO_DEXALOT_STATUS_MAP
# from hummingbot.connector.gateway.common_types import PlaceOrderResult
# from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder
from hummingbot.connector.test_support.gateway_clob_api_data_source_test import AbstractGatewayCLOBAPIDataSourceTests
from hummingbot.connector.test_support.network_mocking_assistant import NetworkMockingAssistant

# from hummingbot.connector.gateway.gateway_order_tracker import GatewayOrderTracker
from hummingbot.connector.utils import combine_to_hb_trading_pair

# from hummingbot.connector.utils import split_hb_trading_pair
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.network_iterator import NetworkStatus

# from hummingbot.core.data_type.in_flight_order import OrderState, OrderUpdate
# from hummingbot.core.data_type.order_book_message import OrderBookMessage
# from hummingbot.core.data_type.trade_fee import TradeFeeBase
# from hummingbot.core.event.event_logger import EventLogger



# from hummingbot.core.data_type.common import OrderType, TradeType
#
#
# class MockConnector(ConnectorBase):
#     pass
#
#
# class KujiraAPIDataSourceTest(unittest.TestCase):
#     chain: str
#     network: str
#     trading_pair: str
#     base: str
#     quote: str
#     trading_pair: str
#     owner_address: str
#
#     @classmethod
#     def setUpClass(cls) -> None:
#         super().setUpClass()
#         cls.chain = "kujira" # noqa: mock
#         cls.network = "mainnet"
#         cls.base = "KUJI" # noqa: mock
#         cls.quote = "USK"
#         cls.trading_pair = combine_to_hb_trading_pair(base=cls.base, quote=cls.quote)
#         cls.owner_address = "kujira1ga9qk68ne00wfflv7y2v92epaajt59e554uulc" # noqa: mock
#
#     async def setUp(self) -> None:
#         super().setUp()
#         client_config_map = ClientConfigAdapter(hb_config=ClientConfigMap())
#         self.initial_timestamp = time.time()
#
#         self.connector = MockConnector(client_config_map=ClientConfigAdapter(ClientConfigMap()))
#         self.tracker = GatewayOrderTracker(connector=self.connector)
#         connector_spec = {
#             "chain": self.chain,
#             "network": self.network,
#             "wallet_address": self.owner_address
#         }
#
#         self.data_source = KujiraAPIDataSource(
#             trading_pairs=[self.trading_pair],
#             connector_spec=connector_spec,
#             client_config_map=client_config_map,
#         )
#
#         self.data_source.gateway_order_tracker = self.tracker
#
#         await self.data_source.start()
#
#     async def test_place_order(self):
#         expected_exchange_order_id = "1365802"
#         expected_transaction_hash = "9981D7CB9F0542F9B6778149E6501EF9625C848A165D42CA94A4CC8788379562"  # noqa: mock
#
#         order = GatewayInFlightOrder(
#             client_order_id="ClientOrderID",
#             trading_pair=self.trading_pair,
#             order_type=OrderType.LIMIT,
#             trade_type=TradeType.BUY,
#             creation_timestamp=self.initial_timestamp,
#             price=Decimal(0.64),
#             amount=Decimal(1.0),
#             exchange_order_id=expected_exchange_order_id,
#             creation_transaction_hash=expected_transaction_hash,
#         )
#
#         self.data_source.place_order = syncMock(return_value=order)
#
#         request = GatewayInFlightOrder(
#             client_order_id="ClientOrderID",
#             trading_pair=self.trading_pair,
#             order_type=OrderType.LIMIT,
#             trade_type=TradeType.BUY,
#             creation_timestamp=self.initial_timestamp,
#             price=Decimal(0.6115),
#             amount=Decimal(1),
#         )
#
#         # result = await self.data_source.place_order(request)
#
#         exchange_order_id, misc_updates = await self.data_source.place_order(order=request)
#
#         self.assertEqual(expected_exchange_order_id, exchange_order_id)
#         self.assertEqual({"creation_transaction_hash": expected_transaction_hash}, misc_updates)

class KujiraAPIDataSourceTest(AbstractGatewayCLOBAPIDataSourceTests.GatewayCLOBAPIDataSourceTests):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.chain = "kujira" # noqa: mock
        cls.network = "mainnet"
        cls.base = "KUJI" # noqa: mock
        cls.quote = "USK"
        cls.trading_pair = combine_to_hb_trading_pair(base=cls.base, quote=cls.quote)
        cls.owner_address = "kujira1ga9qk68ne00wfflv7y2v92epaajt59e554uulc" # noqa: mock

        # If removed, an error occurs
        password = "asdf"
        secrets_manager = ETHKeyFileSecretManger(password)
        store_password_verification(secrets_manager)

        Security.login(secrets_manager)

    def setUp(self) -> None:
        self.mock_api = aioresponses()
        self.mock_api.start()
        # self.mocking_assistant = NetworkMockingAssistant()
        # self.ws_connect_patch = patch("aiohttp.ClientSession.ws_connect", new_callable=AsyncMock)
        # self.ws_connect_mock = self.ws_connect_patch.start()
        super().setUp()

    def tearDown(self) -> None:
        self.mock_api.stop()
        # self.ws_connect_patch.stop()
        super().tearDown()

    def build_api_data_source(self, with_api_key: bool = True) -> KujiraAPIDataSource:
        connector_spec = {
            "chain": self.chain,
            "network": self.network,
            "wallet_address": self.owner_address,
        }
        data_source = KujiraAPIDataSource(
            trading_pairs=[self.trading_pair],
            connector_spec=connector_spec,
            client_config_map=self.client_config_map,
        )
        # self.async_run_with_timeout(coro=data_source.start())
        return data_source

    def exchange_symbol_for_tokens(self, base_token: str, quote_token: str) -> str:
        exchange_trading_pair = f"{base_token}/{quote_token}"
        return exchange_trading_pair

    def configure_place_order_response(
            self,
            timestamp: float,
            transaction_hash: str,
            exchange_order_id: str,
            trade_type: TradeType,
            price: Decimal,
            size: Decimal,
    ):
        super().configure_batch_order_create_response(
            timestamp=timestamp,
            transaction_hash=transaction_hash,
            created_orders=[
                GatewayInFlightOrder(
                    client_order_id=self.expected_buy_client_order_id,
                    trading_pair=self.trading_pair,
                    order_type=OrderType.LIMIT,
                    trade_type=trade_type,
                    creation_timestamp=timestamp,
                    price=price,
                    amount=size,
                    exchange_order_id=exchange_order_id,
                    creation_transaction_hash=transaction_hash,
                )
            ]
        )

    def configure_update_markets(self):
        response = {
            "teste": "teste",
        }
        self.gateway_instance_mock.get_clob_markets.return_value = response

    @patch("hummingbot.core.gateway.gateway_http_client.GatewayHttpClient.ping_gateway")
    def test_check_network_status(self, *args):
        self.data_source._gateway.ping_gateway.return_value = "Aloha"
        self.data_source._gateway.update_config.return_value = "Ihuu"

        output = self.async_run_with_timeout(
            coro=self.data_source._gateway_ping_gateway()
        )

        self.assertEqual(output, "Aloha")

    @patch(
        "hummingbot.connector.gateway.clob_spot.data_sources.gateway_clob_api_data_source_base"
        ".GatewayCLOBAPIDataSourceBase._sleep",
        new_callable=AsyncMock,
    )
    def test_place_order(self, sleep_mock: AsyncMock):
        def sleep_mock_side_effect(delay):
            raise Exception

        sleep_mock.side_effect = sleep_mock_side_effect

        self.configure_place_order_response(
            timestamp=self.initial_timestamp,
            transaction_hash=self.expected_transaction_hash,
            exchange_order_id=self.expected_buy_exchange_order_id,
            trade_type=TradeType.BUY,
            price=self.expected_buy_order_price,
            size=self.expected_buy_order_size,
        )
        self.configure_update_markets()
        order = GatewayInFlightOrder(
            client_order_id=self.expected_buy_client_order_id,
            trading_pair=self.exchange_symbol_for_tokens(self.base, self.quote),
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            creation_timestamp=self.initial_timestamp,
            price=self.expected_buy_order_price,
            amount=self.expected_buy_order_size,
        )
        exchange_order_id, misc_updates = self.async_run_with_timeout(
            coro=self.data_source.place_order(order=order)
        )

        self.assertEqual({"creation_transaction_hash": self.expected_transaction_hash}, misc_updates)

    def test_get_last_traded_price(self):
        pass
    def configure_account_balances_response(self):
        pass

    def configure_empty_order_fills_response(self):
        pass

    def configure_trade_fill_response(self):
        pass

    def exchange_base(self):
        pass

    def exchange_quote(self):
        pass

    def expected_buy_exchange_order_id(self):
        pass

    def expected_sell_exchange_order_id(self):
        pass

    def get_clob_ticker_response(self):
        pass

    def get_order_status_response(self):
        pass

    def get_trading_pairs_info_response(self):
        pass
