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
        payload = {
            "connector": "kujira",
            "chain": "kujira",
            "network": "testnet",
            "marketId": "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh",
            "ownerAddress": "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7",
            "side": TradeType.BUY.name,
            "price": 0.001,
            "amount": 1.0,
            "type": OrderType.LIMIT.name,
            "payerAddress": "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7"
        }

        result: Dict[str, Any] = await GatewayHttpClient.get_instance().kujira_post_order(payload=payload)

        self.assertGreater(Decimal(result["id"]), 0)
        self.assertEqual(result["marketName"], "KUJI/DEMO")
        self.assertEquals(result["marketId"], "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh")
        self.assertEqual(result["ownerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["payerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["price"], "0.001")
        self.assertEqual(result["amount"], "100")
        self.assertEqual(result["side"], TradeType.BUY.name)
        self.assertEqual(result["status"], "OPEN")
        self.assertEqual(result["type"], OrderType.LIMIT.name)
        self.assertGreater(Decimal(result["fee"]), 0)
        self.assertEqual(len(result["hashes"]["creation"]), 64)

    @async_test(loop=ev_loop)
    async def test_kujira_cancel_order(self):
        payload = {
            "connector": "kujira",
            "chain": "kujira",
            "network": "testnet",
            "id": "198462",
            "ownerAddress": "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7",
            "marketId": "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh"
        }

        result = await GatewayHttpClient.get_instance().kujira_delete_order(payload=payload)

        self.assertGreater(len(result["id"]), 0)
        self.assertEqual(result["market"]["name"], "KUJI/DEMO")
        self.assertEquals(result["marketId"], "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh")
        self.assertEqual(result["ownerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["payerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["status"], "CANCELLED")
        self.assertEqual(result["type"], OrderType.LIMIT.name)
        self.assertGreater(Decimal(result["fee"]), 0)
        self.assertEqual(len(result["hashes"]["cancellation"]), 64)

    @async_test(loop=ev_loop)
    async def test_kujira_get_order_status_update(self):
        payload = {
            "connector": "kujira",
            "chain": "kujira",
            "network": "testnet",
            "id": "198462",
            "ownerAddress": "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7"
        }

        result = await GatewayHttpClient.get_instance().kujira_get_order(payload=payload)

        self.assertGreater(len(result["id"]), 0)
        self.assertEqual(result["market"]["name"], "KUJI/DEMO")
        self.assertEquals(result["marketId"], "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh")
        self.assertEqual(result["ownerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["payerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["status"], "OPEN")
        self.assertEqual(result["type"], OrderType.LIMIT.name)
        self.assertGreater(result["creationTimestamp"], 0)
        self.assertEqual(result["connectorOrder"]["original_offer_amount"], "100000000")

    @async_test(loop=ev_loop)
    async def test_kujira_get_market(self):
        payload = {
            "chain": "kujira",
            "network": "testnet",
            "id": "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh",
        }

        result = await GatewayHttpClient.get_instance().kujira_get_market(payload=payload)

        self.assertEqual(result["id"], "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh")
        self.assertEqual(result["name"], "KUJI/DEMO")
        self.assertEqual(result["baseToken"], {"id": "ukuji", "name": "KUJI", "symbol": "KUJI", "decimals": 6})
        self.assertEqual(result["quoteToken"],
                         {"id": "factory/kujira1ltvwg69sw3c5z99c6rr08hal7v0kdzfxz07yj5/demo", "name": "DEMO",
                          "symbol": "DEMO", "decimals": 6})
        self.assertEqual(result["minimumOrderSize"], "0.001")
        self.assertEqual(result["minimumPriceIncrement"], "0.001")
        self.assertEqual(result["minimumBaseAmountIncrement"], "0.001")
        self.assertEqual(result["minimumQuoteAmountIncrement"], "0.001")
        self.assertEqual(result["fees"], {"maker": "0.075", "taker": "0.15", "serviceProvider": "0"})

    @async_test(loop=ev_loop)
    async def test_kujira_get_orderbook(self):
        payload = {
            "chain": "kujira",
            "network": "testnet",
            "marketId": "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh",
        }

        result = await GatewayHttpClient.get_instance().kujira_get_order_book(payload=payload)

        self.assertEqual(result["market"]["id"], "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh")
        self.assertEqual(len(result["bids"]), 3)
        self.assertEqual(len(result["asks"]), 3)
        self.assertGreater(Decimal(result["bestBid"]["price"]), 0)
        self.assertGreater(Decimal(result["bestAsk"]["price"]), 0)
        self.assertEqual(len(result["connectorOrderBook"]["base"]), 3)
        self.assertEqual(len(result["connectorOrderBook"]["quote"]), 3)

    @async_test(loop=ev_loop)
    async def test_kujira_get_ticker(self):
        payload = {
            "chain": "kujira",
            "network": "testnet",
            "marketId": "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh",
        }

        result = await GatewayHttpClient.get_instance().kujira_get_ticker(payload=payload)

        self.assertEqual(result["market"]["id"], "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh")
        self.assertEqual(result["market"]["name"], "KUJI/DEMO")
        self.assertGreater(Decimal(result["price"]), 0)
        self.assertIsNot(result["timestamp"], 0)
        self.assertGreater(Decimal(result["price"]), 0)
        self.assertEqual(Decimal(result["ticker"]["price"]), Decimal(result["price"]))

    @async_test(loop=ev_loop)
    async def test_kujira_batch_order_update(self):
        payload = {
            "chain": "kujira",
            "network": "testnet",
            "ids": ["5680", "5681"],
            "ownerAddress": "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7",
            "status": "OPEN"
        }

        result = await GatewayHttpClient.get_instance().kujira_get_orders(payload=payload)

        self.assertEqual(len(result), 2)

        self.assertIsNotNone(result.get("5680"))
        self.assertEqual(result["5680"]["marketName"], "KUJI/DEMO")
        self.assertEqual(result["5680"]["ownerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["5680"]["side"], TradeType.BUY.name)
        self.assertEqual(result["5680"]["type"], OrderType.LIMIT.name)
        self.assertEqual(result["5680"]["status"], "OPEN")
        self.assertEqual(result["5680"]["creationTimestamp"], 1685739617894166000)

        self.assertIsNotNone(result.get("5681"))
        self.assertEqual(result["5681"]["marketName"], "KUJI/DEMO")
        self.assertEqual(result["5681"]["ownerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["5681"]["side"], TradeType.SELL.name)
        self.assertEqual(result["5681"]["type"], OrderType.LIMIT.name)
        self.assertEqual(result["5681"]["status"], "OPEN")
        self.assertEqual(result["5681"]["creationTimestamp"], 1685739617894166000)

    @async_test(loop=ev_loop)
    async def test_kujira_cancel_orders(self):
        payload = {
            "chain": "kujira",
            "network": "testnet",
            "ids": ["5680", "5681"],
            "marketId": "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh",
            "ownerAddress": "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7"
        }

        result = await GatewayHttpClient.get_instance().kujira_delete_orders(payload=payload)

        self.assertEqual(len(result), 2)

        self.assertIsNotNone(result.get("5680"))
        self.assertEqual(result["5680"]["marketName"], "KUJI/DEMO")
        self.assertEqual(result["5680"]["ownerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["5680"]["status"], "CANCELLED")
        self.assertEqual(result["5680"]["type"], OrderType.LIMIT.name)
        self.assertEqual(len(result["5680"]["hashes"]['cancellation']), 64)

        self.assertIsNotNone(result.get("5681"))
        self.assertEqual(result["5681"]["marketName"], "KUJI/DEMO")
        self.assertEqual(result["5681"]["ownerAddress"], "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7")
        self.assertEqual(result["5681"]["status"], "CANCELLED")
        self.assertEqual(result["5681"]["type"], OrderType.LIMIT.name)
        self.assertEqual(len(result["5681"]["hashes"]['cancellation']), 64)

    @async_test(loop=ev_loop)
    async def test_kujira_get_all_markets(self):
        payload = {
            "chain": "kujira",
            "network": "testnet"
        }

        result = await GatewayHttpClient.get_instance().kujira_get_markets_all(payload=payload)

        self.assertEqual(len(result), 3)

        self.assertIsNotNone(result.get("kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh"))
        self.assertEqual(
            result.get("kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh")["name"],
            "KUJI/DEMO"
        )

        self.assertIsNotNone(result.get("kujira1wl003xxwqltxpg5pkre0rl605e406ktmq5gnv0ngyjamq69mc2kqm06ey6"))
        self.assertEqual(
            result.get("kujira1wl003xxwqltxpg5pkre0rl605e406ktmq5gnv0ngyjamq69mc2kqm06ey6")["name"],
            "KUJI/USK"
        )

        self.assertIsNotNone(result.get("kujira14sa4u42n2a8kmlvj3qcergjhy6g9ps06rzeth94f2y6grlat6u6ssqzgtg"))
        self.assertEqual(
            result.get("kujira14sa4u42n2a8kmlvj3qcergjhy6g9ps06rzeth94f2y6grlat6u6ssqzgtg")["name"],
            "DEMO/USK"
        )
