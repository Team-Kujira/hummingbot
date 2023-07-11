import asyncio
import unittest
from contextlib import ExitStack
from decimal import Decimal
from os.path import join, realpath
from test.mock.http_recorder import HttpPlayer
from typing import Any, Dict
from unittest.mock import patch

from aiohttp import ClientSession
from aiounittest import async_test

from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder
from hummingbot.core.data_type.common import OrderType
from hummingbot.core.event.events import TradeType
from hummingbot.core.gateway.gateway_http_client import GatewayHttpClient

ev_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()


class GatewayHttpClientUnitTest(unittest.TestCase):
    _db_path: str
    _http_player: HttpPlayer
    _patch_stack: ExitStack

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._db_path = realpath(join(__file__, "../../../fixtures/gateway_http_client_clob_fixture.db"))
        cls._http_player = HttpPlayer(cls._db_path)
        cls._patch_stack = ExitStack()
        cls._patch_stack.enter_context(cls._http_player.patch_aiohttp_client())
        cls._patch_stack.enter_context(
            patch(
                "hummingbot.core.gateway.gateway_http_client.GatewayHttpClient._http_client",
                return_value=ClientSession(),
            )
        )
        GatewayHttpClient.get_instance().base_url = "https://localhost:15888"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._patch_stack.close()

    @async_test(loop=ev_loop)
    async def test_kujira_place_order(self):
        request = {
            "connector": "kujira",
            "chain": "kujira",
            "network": "testnet",
            "trading_pair": "KUJI-DEMO",
            "address": "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7", # noqa: mock
            "trade_type": TradeType.BUY,
            "order_type": OrderType.LIMIT,
            "price": Decimal("0.001"),
            "size": Decimal("1.0"),
        }

        result: Dict[str, Any] = await GatewayHttpClient.get_instance().clob_place_order(**request)

        self.assertEqual("testnet", result["network"])
        self.assertEqual(1647066435595, result["timestamp"])
        self.assertEqual(2, result["latency"])
        self.assertEqual("D5C9B4FBD06482C1B40CEA3B1D10E445049F1F19CA5531265FC523973CC65EF9", result["txHash"])  # noqa: mock

    @async_test(loop=ev_loop)
    async def test_kujira_cancel_order(self):
        request = {
            "connector": "kujira",
            "chain": "kujira",
            "network": "testnet",
            "trading_pair": "KUJI-DEMO",
            "address": "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7", # noqa: mock
            "exchange_order_id": "198462",
        }

        result = await GatewayHttpClient.get_instance().clob_cancel_order(**request)

        self.assertEqual("testnet", result["network"])
        self.assertEqual(1647066436595, result["timestamp"])
        self.assertEqual(2, result["latency"])
        self.assertEqual("D5C9B4FBD06482C1B40CEA3B1D10E445049F1F19CA5531265FC523973CC65EF9", result["txHash"])  # noqa: mock

    @async_test(loop=ev_loop)
    async def test_kujira_get_order_status_update(self):
        request = {
            "trading_pair": "KUJI-DEMO",
            "chain": "kujira",
            "network": "testnet",
            "connector": "kujira",
            "address": "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7",  # noqa: mock
        }

        result = await GatewayHttpClient.get_instance().get_clob_order_status_updates(**request)

        self.assertEqual(2, len(result["orders"]))
        self.assertEqual("198462", result["orders"][0]["id"])
        self.assertEqual("198463", result["orders"][1]["id"])

    @async_test(loop=ev_loop)
    async def test_kujira_get_market(self):
        request = {
            "connector": "kujira",
            "chain": "kujira",
            "network": "testnet",
        }

        result = await GatewayHttpClient.get_instance().get_clob_markets(**request)

        self.assertEqual(2, len(result["markets"]))
        self.assertEqual("KUJI/DEMO", result["markets"][1]["name"])

    @async_test(loop=ev_loop)
    async def test_kujira_get_orderbook(self):
        request = {
            "trading_pair": "KUJI-DEMO",
            "connector": "kujira",
            "chain": "kujira",
            "network": "testnet"
        }

        result = await GatewayHttpClient.get_instance().get_clob_orderbook_snapshot(**request)

        expected_orderbook = {
            "bids": [[1, 2], [3, 4]],
            "asks": [[5, 6]],
        }
        self.assertEqual(expected_orderbook, result["orderbook"])

    @async_test(loop=ev_loop)
    async def test_kujira_get_ticker(self):
        request = {
            "connector": "kujira",
            "chain": "kujira",
            "network": "testnet"
        }

        result = await GatewayHttpClient.get_instance().get_clob_ticker(**request)

        expected_markets = [
            {
                "pair": "KUJI-DEMO",
                "lastPrice": 9,
            },
            {
                "pair": "DEMO-USK",
                "lastPrice": 10,
            }
        ]

        self.assertEqual(expected_markets, result["markets"])

    @async_test(loop=ev_loop)
    async def test_clob_batch_order_update(self):
        trading_pair = "KUJI-DEMO"
        order_to_create = GatewayInFlightOrder(
            client_order_id="someOrderIDCreate",
            trading_pair=trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            creation_timestamp=123123123,
            amount=Decimal("10"),
            price=Decimal("100"),
        )
        order_to_cancel = GatewayInFlightOrder(
            client_order_id="someOrderIDCancel",
            trading_pair=trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.SELL,
            creation_timestamp=123123123,
            price=Decimal("90"),
            amount=Decimal("9"),
            exchange_order_id="someExchangeOrderID",
        )
        result: Dict[str, Any] = await GatewayHttpClient.get_instance().clob_batch_order_modify(
            connector="kujira",
            chain="kujira",
            network="testnet",
            address="kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7",  # noqa: mock
            orders_to_create=[order_to_create],
            orders_to_cancel=[order_to_cancel],
        )

        self.assertEqual("testnet", result["network"])
        self.assertEqual(1647066456595, result["timestamp"])
        self.assertEqual(3, result["latency"])
        self.assertEqual("D5C9B4FBD06482C1B40CEA3B1D10E445049F1F19CA5531265FC523973CC65EF9", result["txHash"])  # noqa: mock
