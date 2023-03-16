from typing import Any, Dict, List, Mapping, Optional, Tuple

from _decimal import Decimal
from bidict import bidict

from hummingbot.connector.gateway.clob_spot.data_sources.gateway_clob_api_data_source_base import (
    CancelOrderResult,
    GatewayCLOBAPIDataSourceBase,
    PlaceOrderResult,
)
from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.core.data_type.common import OrderType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.order_book_message import OrderBookMessage
from hummingbot.core.data_type.trade_fee import MakerTakerExchangeFeeRates
from hummingbot.core.network_iterator import NetworkStatus


class KujiraAPIDataSource(GatewayCLOBAPIDataSourceBase):
    def get_supported_order_types(self) -> List[OrderType]:
        pass

    async def start(self):
        pass

    async def stop(self):
        pass

    async def place_order(self, order: GatewayInFlightOrder, **kwargs) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        pass

    async def batch_order_create(self, orders_to_create: List[InFlightOrder]) -> List[PlaceOrderResult]:
        pass

    async def cancel_order(self, order: GatewayInFlightOrder) -> Tuple[bool, Optional[Dict[str, Any]]]:
        pass

    async def batch_order_cancel(self, orders_to_cancel: List[InFlightOrder]) -> List[CancelOrderResult]:
        pass

    async def get_trading_rules(self) -> Dict[str, TradingRule]:
        pass

    async def get_symbol_map(self) -> bidict[str, str]:
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

    async def check_network_status(self) -> NetworkStatus:
        pass

    async def get_trading_fees(self) -> Mapping[str, MakerTakerExchangeFeeRates]:
        pass

    def is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        pass

    def is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        pass
