import asyncio
from typing import Any, Dict, List, Union
from unittest.mock import AsyncMock, patch

from _decimal import Decimal

from hummingbot.connector.gateway.clob_spot.data_sources.kujira.kujira_api_data_source import KujiraAPIDataSource
from hummingbot.connector.test_support.gateway_clob_api_data_source_test import AbstractGatewayCLOBAPIDataSourceTests
from hummingbot.connector.utils import combine_to_hb_trading_pair
from hummingbot.core.data_type.common import TradeType
from hummingbot.core.data_type.in_flight_order import OrderState
from hummingbot.core.data_type.trade_fee import TradeFeeBase
from hummingbot.core.network_iterator import NetworkStatus


class KujiraAPIDataSourceTest(AbstractGatewayCLOBAPIDataSourceTests.GatewayCLOBAPIDataSourceTests):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.chain = "kujira"  # noqa: mock
        cls.network = "mainnet"
        cls.base = "KUJI"  # noqa: mock
        cls.quote = "USK"
        cls.trading_pair = combine_to_hb_trading_pair(base=cls.base, quote=cls.quote)
        cls.owner_address = "kujira1yrensec9gzl7y3t3duz44efzgwj2qv6gwayrn7"  # noqa: mock

    def setUp(self) -> None:
        super().setUp()

        self.data_source._gateway = self.gateway_instance_mock
        self.configure_get_market()
        # asyncio.sleep = AsyncMock()

    def tearDown(self) -> None:
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

        return data_source

    @patch("hummingbot.core.gateway.gateway_http_client.GatewayHttpClient.ping_gateway")
    def test_gateway_ping_gateway(self, *_args):
        self.data_source._gateway.ping_gateway.return_value = True

        result = self.async_run_with_timeout(
            coro=self.data_source._gateway_ping_gateway()
        )

        expected = True

        self.assertEqual(expected, result)

    @patch("hummingbot.core.gateway.gateway_http_client.GatewayHttpClient.ping_gateway")
    def test_check_network_status_with_gateway_connected(self, *_args):
        self.data_source._gateway.ping_gateway.return_value = True

        result = self.async_run_with_timeout(
            coro=self.data_source.check_network_status()
        )

        expected = NetworkStatus.CONNECTED

        self.assertEqual(expected, result)

    @patch("hummingbot.core.gateway.gateway_http_client.GatewayHttpClient.ping_gateway")
    def test_check_network_status_with_gateway_not_connected(self, *_args):
        self.data_source._gateway.ping_gateway.return_value = False

        result = self.async_run_with_timeout(
            coro=self.data_source.check_network_status()
        )

        expected = NetworkStatus.NOT_CONNECTED

        self.assertEqual(expected, result)

    @patch("hummingbot.core.gateway.gateway_http_client.GatewayHttpClient.ping_gateway")
    def test_check_network_status_with_gateway_exception(self, *_args):
        self.data_source._gateway.ping_gateway.side_effect = RuntimeError("Unknown error")

        result = self.async_run_with_timeout(
            coro=self.data_source.check_network_status()
        )

        expected = NetworkStatus.NOT_CONNECTED

        self.assertEqual(expected, result)

    @patch("hummingbot.core.gateway.gateway_http_client.GatewayHttpClient.get_clob_markets")
    def configure_get_market(self, *_args):
        self.data_source._gateway.get_clob_markets.return_value = \
            {
                "network": "mainnet",
                "timestamp": 1694561843115,
                "latency": 0.001,
                "markets": {
                    "KUJI-USK": {
                        "id": "kujira193dzcmy7lwuj4eda3zpwwt9ejal00xva0vawcvhgsyyp5cfh6jyq66wfrf",
                        "name": "KUJI/USK",
                        "baseToken": {
                            "id": "ukuji",
                            "name": "KUJI",
                            "symbol": "KUJI",
                            "decimals": 6
                        },
                        "quoteToken": {
                            "id": "factory/kujira1qk00h5atutpsv900x202pxx42npjr9thg58dnqpa72f2p7m2luase444a7/uusk",
                            "name": "USK",
                            "symbol": "USK",
                            "decimals": 6
                        },
                        "precision": 3,
                        "minimumOrderSize": "0.001",
                        "minimumPriceIncrement": "0.001",
                        "minimumBaseAmountIncrement": "0.001",
                        "minimumQuoteAmountIncrement": "0.001",
                        "fees": {
                            "maker": "0.075",
                            "taker": "0.15",
                            "serviceProvider": "0"
                        },
                        "deprecated": False,
                        "connectorMarket": {
                            "address": "kujira193dzcmy7lwuj4eda3zpwwt9ejal00xva0vawcvhgsyyp5cfh6jyq66wfrf",
                            "denoms": [
                                {
                                    "reference": "ukuji",
                                    "decimals": 6,
                                    "symbol": "KUJI"
                                },
                                {
                                    "reference": "factory/kujira1qk00h5atutpsv900x202pxx42npjr9thg58dnqpa72f2p7m2luase444a7/uusk",
                                    "decimals": 6,
                                    "symbol": "USK"
                                }
                            ],
                            "precision": {
                                "decimal_places": 3
                            },
                            "decimalDelta": 0,
                            "multiswap": True,
                            "pool": "kujira1g9xcvvh48jlckgzw8ajl6dkvhsuqgsx2g8u3v0a6fx69h7f8hffqaqu36t",
                            "calc": "kujira1e6fjnq7q20sh9cca76wdkfg69esha5zn53jjewrtjgm4nktk824stzyysu"
                        }
                    }
                }
            }

    def configure_place_order_response(
        self,
        timestamp: float,
        transaction_hash: str,
        exchange_order_id: str,
        trade_type: TradeType,
        price: Decimal,
        size: Decimal,
    ):
        super().configure_place_order_response(
            timestamp,
            transaction_hash,
            exchange_order_id,
            trade_type,
            price,
            size,
        )
        self.gateway_instance_mock.clob_place_order.return_value["id"] = "1"

    @property
    def expected_buy_exchange_order_id(self) -> str:
        return "1"

    @property
    def expected_sell_exchange_order_id(self) -> str:
        return "2"

    @property
    def exchange_base(self) -> str:
        return self.base

    @property
    def exchange_quote(self) -> str:
        return self.quote

    @property
    def expected_quote_decimals(self) -> int:
        return 6

    @property
    def expected_base_decimals(self) -> int:
        return 6

    def exchange_symbol_for_tokens(self, base_token: str, quote_token: str) -> str:
        return f"{base_token}/{quote_token}"

    def get_trading_pairs_info_response(self) -> List[Dict[str, Any]]:
        pass

    def get_order_status_response(self, timestamp: float, trading_pair: str, exchange_order_id: str,
                                  client_order_id: str, status: OrderState) -> List[Dict[str, Any]]:
        pass

    def get_clob_ticker_response(self, trading_pair: str, last_traded_price: Decimal) -> List[Dict[str, Any]]:
        pass

    def configure_account_balances_response(self, base_total_balance: Decimal, base_available_balance: Decimal,
                                            quote_total_balance: Decimal, quote_available_balance: Decimal):
        pass

    def configure_empty_order_fills_response(self):
        pass

    def configure_trade_fill_response(self, timestamp: float, exchange_order_id: str, price: Decimal, size: Decimal,
                                      fee: TradeFeeBase, trade_id: Union[str, int], is_taker: bool):
        pass
