import asyncio
from typing import Any, Dict, List, Union
from unittest.mock import patch

from _decimal import Decimal
from dotmap import DotMap

from hummingbot.connector.gateway.clob_spot.data_sources.kujira.kujira_api_data_source import KujiraAPIDataSource
from hummingbot.connector.gateway.clob_spot.data_sources.kujira.kujira_helpers import (
    convert_market_name_to_hb_trading_pair,
)
from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder
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

        self.configure_asyncio_sleep()
        self.data_source._gateway = self.gateway_instance_mock
        self.configure_get_market()

    def tearDown(self) -> None:
        super().tearDown()

    def build_api_data_source(self, with_api_key: bool = True) -> Any:
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

    @staticmethod
    def configure_asyncio_sleep():
        async def sleep(*_args, **_kwargs):
            pass
        patch.object(asyncio, "sleep", new_callable=sleep)

    @patch("hummingbot.core.gateway.gateway_http_client.GatewayHttpClient.get_clob_markets")
    def configure_get_market(self, *_args):
        self.data_source._gateway.get_clob_markets.return_value = self.configure_get_market_response()

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

    def configure_batch_order_create_response(
        self,
        timestamp: float,
        transaction_hash: str,
        created_orders: List[GatewayInFlightOrder],
    ):
        super().configure_batch_order_create_response(
            timestamp=self.initial_timestamp,
            transaction_hash=self.expected_transaction_hash,
            created_orders=created_orders,
        )
        self.gateway_instance_mock.clob_batch_order_modify.return_value["ids"] = ["1", "2"]

    @patch("hummingbot.core.gateway.gateway_http_client.GatewayHttpClient.get_clob_order_status_updates")
    def configure_get_order_response(self, *_args):
        self.data_source._gateway.get_clob_order_status_updates.return_value = {
            "network": "mainnet",
            "timestamp": 1694619386793,
            "latency": 7.778,
            "orders": [
                {
                    "id": "1370335",
                    "orderHash": "",
                    "marketId": "kujira193dzcmy7lwuj4eda3zpwwt9ejal00xva0vawcvhgsyyp5cfh6jyq66wfrf", # noqa: mock
                    "active": "",
                    "subaccountId": "", # noqa: mock
                    "executionType": "",
                    "orderType": "LIMIT",
                    "price": "0.616",
                    "triggerPrice": "",
                    "quantity": "0.24777",
                    "filledQuantity": "",
                    "state": "FILLED",
                    "createdAt": "1694553828194861000",
                    "updatedAt": "",
                    "direction": "BUY"
                }
            ]
        }

    @property
    def expected_buy_client_order_id(self) -> str:
        return "03719e91d18db65ec3bf5554d678e5b4"

    @property
    def expected_sell_client_order_id(self) -> str:
        return "02719e91d18db65ec3bf5554d678e5b2"

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

    def exchange_symbol_for_tokens(
            self,
            base_token: str,
            quote_token: str
    ) -> str:
        return f"{base_token}/{quote_token}"

    def get_trading_pairs_info_response(self) -> List[Dict[str, Any]]:
        response = self.configure_get_market_response()

        market = response.markets[list(response.markets.keys())[0]]

        market_name = convert_market_name_to_hb_trading_pair(market.name)

        return [{"market_name": market_name, "market": market}]

    def get_order_status_response(
            self,
            timestamp: float,
            trading_pair: str,
            exchange_order_id: str,
            client_order_id: str,
            status: OrderState
    ) -> List[Dict[str, Any]]:
        orders = self.data_source._gateway.get_clob_order_status_updates.return_value
        return [{"exchange_order_id": orders.orders[0].id, "order": orders[0]}]

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

    def configure_get_market_response(self):
        return DotMap({
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
        }, _dynamic=False)

    def test_batch_order_cancel(self):
        super().test_batch_order_cancel()

    def test_batch_order_create(self):
        super().test_batch_order_create()

    def test_cancel_order(self):
        super().test_cancel_order()

    def test_cancel_order_transaction_fails(self):
        super().test_cancel_order_transaction_fails()

    def test_check_network_status(self):
        super().test_check_network_status()

    def test_delivers_balance_events(self):
        super().test_delivers_balance_events()

    def test_delivers_order_book_snapshot_events(self):
        super().test_delivers_order_book_snapshot_events()

    def test_get_account_balances(self):
        super().test_get_account_balances()

    def test_get_all_order_fills(self):
        super().test_get_all_order_fills()

    def test_get_all_order_fills_no_fills(self):
        super().test_get_all_order_fills_no_fills()

    def test_get_last_traded_price(self):
        super().test_get_last_traded_price()

    def test_get_order_book_snapshot(self):
        super().test_get_order_book_snapshot()

    def test_get_order_status_update(self):
        super().test_get_order_status_update()

    def test_get_symbol_map(self):
        super().test_get_symbol_map()

    def test_get_trading_fees(self):
        super().test_get_trading_fees()

    def test_get_trading_rules(self):
        super().test_get_trading_rules()

    def test_maximum_delay_between_requests_for_snapshot_events(self):
        super().test_maximum_delay_between_requests_for_snapshot_events()

    def test_minimum_delay_between_requests_for_snapshot_events(self):
        super().test_minimum_delay_between_requests_for_snapshot_events()

    def test_place_order(self):
        super().test_place_order()

    def test_place_order_transaction_fails(self):
        super().test_place_order_transaction_fails()
