from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.connector.gateway.clob_spot.data_sources.clob_api_data_source_base import CLOBAPIDataSourceBase
from hummingbot.connector.gateway.clob_spot.data_sources.kujira.kujira_constants import CONNECTOR_NAME
from hummingbot.connector.gateway.common_types import CancelOrderResult, PlaceOrderResult
from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.core.data_type.common import OrderType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.order_book import OrderBookMessage
from hummingbot.core.data_type.trade_fee import MakerTakerExchangeFeeRates
from hummingbot.core.gateway.gateway_http_client import GatewayHttpClient
from hummingbot.core.network_iterator import NetworkStatus


class KujiraAPIDataSource(CLOBAPIDataSourceBase):

    def __init__(
            self,
            trading_pairs: List[str],
            connector_spec: Dict[str, Any],
            client_config_map: ClientConfigAdapter,
    ):
        super().__init__(
            trading_pairs=trading_pairs, connector_spec=connector_spec, client_config_map=client_config_map
        )
        self._connector_name = CONNECTOR_NAME
        self._chain = connector_spec["chain"]
        self._network = connector_spec["network"]
        self._account_address: str = connector_spec["wallet_address"]

    @property
    def real_time_balance_update(self) -> bool:
        return True

    @property
    def events_are_streamed(self) -> bool:
        return True

    @staticmethod
    def supported_stream_events() -> List[Enum]:
        pass

    def get_supported_order_types(self) -> List[OrderType]:
        pass

    async def start(self):
        pass

    async def stop(self):
        pass

    async def place_order(self, order: GatewayInFlightOrder, **kwargs) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:

        payload = {
            "connector": self._connector_name,
            "chain": self._chain,
            "network": self._network,
            "trading_pair": order.trading_pair,
            "address": self._account_address,
            "trade_type": order.trade_type,
            "order_type": order.order_type,
            "price": order.price,
            "size": order.amount
        }

        result: Dict[str, Any] = await self._get_gateway_instance().clob_place_order(**payload)

        return "", result

    async def batch_order_create(self, orders_to_create: List[InFlightOrder]) -> List[PlaceOrderResult]:
        pass

    async def cancel_order(self, order: GatewayInFlightOrder) -> Tuple[bool, Optional[Dict[str, Any]]]:

        payload = {
            "connector": self._connector_name,
            "chain": self._chain,
            "network": self._network,
            "address": self._account_address,
            "market": order.trading_pair,
            "orderId": order.exchange_order_id,
        }
        result = await self._get_gateway_instance().clob_place_order(**payload)

        return True, result

    async def batch_order_cancel(self, orders_to_cancel: List[InFlightOrder]) -> List[CancelOrderResult]:
        pass

    async def get_last_traded_price(self, trading_pair: str) -> Decimal:
        pass

    async def get_order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        pass

    async def get_account_balances(self) -> Dict[str, Dict[str, Decimal]]:
        pass

    async def get_order_status_update(self, in_flight_order: InFlightOrder) -> OrderUpdate:
        pass

    async def get_all_order_fills(self, in_flight_order: InFlightOrder) -> List[TradeUpdate]:
        pass

    def is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        pass

    def is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        pass

    async def check_network_status(self) -> NetworkStatus:
        pass

    def _check_markets_initialized(self) -> bool:
        pass

    async def _update_markets(self):
        pass

    def _parse_trading_rule(self, trading_pair: str, market_info: Any) -> TradingRule:
        pass

    def _get_exchange_trading_pair_from_market_info(self, market_info: Any) -> str:
        pass

    def _get_maker_taker_exchange_fee_rates_from_market_info(self, market_info: Any) -> MakerTakerExchangeFeeRates:
        pass

    def _get_gateway_instance(self) -> GatewayHttpClient:
        gateway_instance = GatewayHttpClient.get_instance(self._client_config)
        return gateway_instance
