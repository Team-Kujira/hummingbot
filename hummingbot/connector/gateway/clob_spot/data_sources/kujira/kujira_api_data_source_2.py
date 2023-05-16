import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from _decimal import Decimal
from dotmap import DotMap

from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.connector.gateway.clob_spot.data_sources.clob_api_data_source_base import CLOBAPIDataSourceBase
from hummingbot.connector.gateway.common_types import CancelOrderResult, PlaceOrderResult
from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.core.data_type.common import OrderType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.order_book_message import OrderBookMessage
from hummingbot.core.data_type.trade_fee import MakerTakerExchangeFeeRates
from hummingbot.core.gateway.gateway_http_client import GatewayHttpClient
from hummingbot.core.network_iterator import NetworkStatus

from .kujira_constants import CONNECTOR
from .kujira_helpers import generate_hash
from .kujira_types import OrderSide as KujiraOrderSide, OrderType as KujiraOrderType


class KujiraAPIDataSource(CLOBAPIDataSourceBase):

    def __init__(
        self,
        trading_pairs: List[str],
        connector_spec: Dict[str, Any],
        client_config_map: ClientConfigAdapter,
    ):
        super().__init__(
            trading_pairs=trading_pairs,
            connector_spec=connector_spec,
            client_config_map=client_config_map
        )

        self._chain = connector_spec["chain"]
        self._network = connector_spec["network"]
        self._connector = CONNECTOR
        self._owner_address = connector_spec["wallet_address"]
        self._payer_address = self._owner_address
        self._markets = DotMap({}, _dynamic=False)
        self._market = DotMap({}, _dynamic=False)

        self._tasks = DotMap({
            "get_markets"
        }, _dynamic=False)
        self._locks = DotMap({
            "place_order": asyncio.Lock(),
            "place_orders": asyncio.Lock(),
        }, _dynamic=False)

        self._gateway = GatewayHttpClient.get_instance(self._client_config)

    @property
    def real_time_balance_update(self) -> bool:
        return False

    @property
    def events_are_streamed(self) -> bool:
        return False

    @staticmethod
    def supported_stream_events() -> List[Enum]:
        return []

    def get_supported_order_types(self) -> List[OrderType]:
        return [OrderType.LIMIT]

    async def start(self):
        pass

    async def stop(self):
        pass

    async def place_order(self, order: GatewayInFlightOrder, **kwargs) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        order.client_id = generate_hash(order)

        async with self._locks.place_order:
            try:
                response = await self._gateway.kujira_post_orders({
                    "chain": self._chain,
                    "network": self._network,
                    "connector": self._connector,
                    "orders": [{
                        "clientId": order.client_id,
                        "marketId": self._market.id,
                        "marketName": self._market.name,
                        "ownerAddress": self._owner_address,
                        "side": KujiraOrderSide.from_hummingbot(order.trade_type).value[0],
                        "price": str(order.price),
                        "amount": str(order.amount),
                        "type": KujiraOrderType.from_hummingbot(order.order_type).value[0],
                        "payerAddress": self._payer_address,
                        "replaceIfExists": True,
                        "waitUntilIncludedInBlock": True
                    }]
                })

                placed_orders = response.values()
                placed_order = DotMap(placed_orders[0], _dynamic=False)

                self.logger().debug(
                    f"""Order "{order.client_id}" successfully placed. Exchange id: {placed_order.id}. Transaction hash: {placed_order.hashes.creation}"""
                )
            except Exception as exception:
                self.logger().debug(
                    f"""Order "{order.client_id}" failed."""
                )

                raise exception

            transaction_hash = placed_order.hashes.creation

            if transaction_hash in (None, ""):
                raise Exception(
                    f"""Order "{order.client_id}" failed. Invalid transaction hash: "{transaction_hash}"."""
                )

        misc_updates = DotMap({
            "creation_transaction_hash": transaction_hash,
        }, _dynamic=False)

        return placed_order.client_id, misc_updates

    async def batch_order_create(self, orders_to_create: List[InFlightOrder]) -> List[PlaceOrderResult]:
        orders = []
        clients_ids = []
        for order_to_create in orders_to_create:
            order_to_create.client_id = generate_hash(order_to_create)
            clients_ids.append(order_to_create.client_id)

            order = {
                "clientId": order_to_create.client_id,
                "marketId": self._market.id,
                "marketName": self._market.name,
                "ownerAddress": self._owner_address,
                "side": KujiraOrderSide.from_hummingbot(order_to_create.trade_type).value[0],
                "price": str(order_to_create.price),
                "amount": str(order_to_create.amount),
                "type": KujiraOrderType.from_hummingbot(order_to_create.order_type).value[0],
                "payerAddress": self._payer_address,
                "replaceIfExists": True,
                "waitUntilIncludedInBlock": True
            }

            orders.append(order)

        async with self._locks.place_orders:
            try:
                response = await self._gateway.kujira_post_orders({
                    "chain": self._chain,
                    "network": self._network,
                    "connector": self._connector,
                    "orders": orders
                })

                placed_orders = DotMap(response.values(), _dynamic=False)

                ids = [order["id"] for order in orders]

                hashes = set([order["hashes"]["creation"] for order in placed_orders])

                self.logger().debug(
                    f"""Orders "{clients_ids}" successfully placed. Exchange id: {ids}. Transaction hash(es): {hashes}"""
                )
            except Exception as exception:
                self.logger().debug(
                    f"""Orders "{clients_ids}" failed."""
                )

                raise exception

            transaction_hash = "".join(hashes)

            if transaction_hash in (None, ""):
                raise Exception(
                    f"""Orders "{clients_ids}" failed. Invalid transaction hash: "{transaction_hash}"."""
                )

        place_order_results = [
            # PlaceOrderResult(
            #     update_timestamp=time.time(),
            #     client_order_id=order.client_order_id,
            #     exchange_order_id=order_hash,
            #     trading_pair=order.trading_pair,
            #     misc_updates={
            #         "creation_transaction_hash": transaction_hash,
            #     },
            #     exception=exception,
            # ) for order, order_hash in zip(orders_to_create, order_hashes.spot)
        ]

        return place_order_results

    async def cancel_order(self, order: GatewayInFlightOrder) -> Tuple[bool, Optional[Dict[str, Any]]]:
        pass

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

    @property
    def is_cancel_request_in_exchange_synchronous(self) -> bool:
        return True

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
