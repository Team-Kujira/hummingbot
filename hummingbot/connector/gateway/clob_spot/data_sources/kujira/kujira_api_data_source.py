import asyncio
from enum import Enum
from time import time
from typing import Any, Dict, List, Optional, Tuple

from _decimal import Decimal
from dotmap import DotMap

from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.connector.gateway.clob_spot.data_sources.clob_api_data_source_base import CLOBAPIDataSourceBase
from hummingbot.connector.gateway.common_types import CancelOrderResult, PlaceOrderResult
from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.core.data_type.common import OrderType
from hummingbot.core.data_type.in_flight_order import OrderUpdate, TradeUpdate
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
from hummingbot.core.data_type.trade_fee import MakerTakerExchangeFeeRates, TokenAmount, TradeFeeBase, TradeFeeSchema
from hummingbot.core.event.events import AccountEvent, MarketEvent, OrderBookDataSourceEvent
from hummingbot.core.gateway.gateway_http_client import GatewayHttpClient
from hummingbot.core.network_iterator import NetworkStatus
from hummingbot.core.utils.async_utils import safe_ensure_future, safe_gather

from .kujira_constants import CONNECTOR, MARKETS_UPDATE_INTERVAL
from .kujira_helpers import generate_hash
from .kujira_types import OrderSide as KujiraOrderSide, OrderStatus as KujiraOrderStatus, OrderType as KujiraOrderType


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

        self._trading_pair = None
        if self._trading_pairs:
            self._trading_pair = self._trading_pairs[0]

        self._markets_names = [trading_pair.replace("-", "/") for trading_pair in trading_pairs]

        self._market_name = None
        if self._markets_names:
            self._market_name = self._markets_names[0]

        self._markets_name_id_map = None

        self._markets = None
        self._market = None

        self._user_balances = None

        self._tasks = DotMap({
            "update_markets": None,
        }, _dynamic=False)

        self._locks = DotMap({
            "place_order": asyncio.Lock(),
            "place_orders": asyncio.Lock(),
            "cancel_order": asyncio.Lock(),
            "cancel_orders": asyncio.Lock(),
            "settle_market_funds": asyncio.Lock(),
            "settle_markets_funds": asyncio.Lock(),
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
        return [
            MarketEvent.TradeUpdate,
            MarketEvent.OrderUpdate,
            AccountEvent.BalanceEvent,
            OrderBookDataSourceEvent.TRADE_EVENT,
            OrderBookDataSourceEvent.DIFF_EVENT,
            OrderBookDataSourceEvent.SNAPSHOT_EVENT,
        ]

    def get_supported_order_types(self) -> List[OrderType]:
        return [OrderType.LIMIT]

    async def start(self):
        self._tasks.update_markets = self._tasks.update_markets or safe_ensure_future(
            coro=self._update_markets_loop()
        )

    async def stop(self):
        self._tasks.update_markets and self._tasks.update_markets.cancel()
        self._tasks.update_markets = None

    async def place_order(self, order: GatewayInFlightOrder, **kwargs) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        order.client_order_id = generate_hash(order)

        async with self._locks.place_order:
            try:
                response = await self._gateway.kujira_post_orders({
                    "chain": self._chain,
                    "network": self._network,
                    "connector": self._connector,
                    "orders": [{
                        "clientId": order.client_order_id,
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
                    f"""Order "{order.client_order_id}" / "{placed_order.id}" successfully placed. Transaction hash: "{placed_order.hashes.creation}"."""
                )
            except Exception as exception:
                self.logger().debug(
                    f"""Placement of order "{order.client_order_id}" failed."""
                )

                raise exception

            transaction_hash = placed_order.hashes.creation

            if transaction_hash in (None, ""):
                raise Exception(
                    f"""Placement of order "{order.client_order_id}" failed. Invalid transaction hash: "{transaction_hash}"."""
                )

        order.exchange_order_id = placed_order.id

        misc_updates = DotMap({
            "creation_transaction_hash": transaction_hash,
        }, _dynamic=False)

        return placed_order.client_id, misc_updates

    async def batch_order_create(self, orders_to_create: List[GatewayInFlightOrder]) -> List[PlaceOrderResult]:
        candidate_orders = []
        client_ids = []
        for order_to_create in orders_to_create:
            order_to_create.client_order_id = generate_hash(order_to_create)
            client_ids.append(order_to_create.client_order_id)

            candidate_order = {
                "clientId": order_to_create.client_order_id,
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

            candidate_orders.append(candidate_order)

        async with self._locks.place_orders:
            try:
                response = await self._gateway.kujira_post_orders({
                    "chain": self._chain,
                    "network": self._network,
                    "connector": self._connector,
                    "orders": candidate_orders
                })

                placed_orders = DotMap(response.values(), _dynamic=False)

                ids = [order.id for order in placed_orders]

                hashes = set([order.hashes.creation for order in placed_orders])

                self.logger().debug(
                    f"""Orders "{client_ids}" / "{ids}" successfully placed. Transaction hash(es): {hashes}."""
                )
            except Exception as exception:
                self.logger().debug(
                    f"""Placement of orders "{client_ids}" failed."""
                )

                raise exception

            transaction_hash = "".join(hashes)

            if transaction_hash in (None, ""):
                raise RuntimeError(
                    f"""Placement of orders "{client_ids}" / "{ids}" failed. Invalid transaction hash: "{transaction_hash}"."""
                )

        place_order_results = []
        for order_to_create, placed_order in zip(orders_to_create, placed_orders):
            order_to_create.exchange_order_id = placed_order.id

            place_order_results.append(PlaceOrderResult(
                update_timestamp=time(),
                client_order_id=order_to_create.client_order_id,
                exchange_order_id=placed_order.id,
                trading_pair=order_to_create.trading_pair,
                misc_updates={
                    "creation_transaction_hash": transaction_hash,
                },
                exception=None,
            ))

        return place_order_results

    async def cancel_order(self, order: GatewayInFlightOrder) -> Tuple[bool, Optional[Dict[str, Any]]]:
        await order.get_exchange_order_id()

        async with self._locks.cancel_order:
            try:
                response = await self._gateway.kujira_delete_orders({
                    "chain": self._chain,
                    "network": self._network,
                    "connector": self._connector,
                    "ids": [order.exchange_order_id],
                    "marketId": self._market.id,
                    "ownerAddress": self._owner_address,
                })

                cancelled_orders = response.values()
                cancelled_order = DotMap(cancelled_orders[0], _dynamic=False)

                self.logger().debug(
                    f"""Order "{order.client_order_id}" / "{cancelled_order.id}" successfully cancelled. Transaction hash: "{cancelled_order.hashes.cancelation}"."""
                )
            except Exception as exception:
                self.logger().debug(
                    f"""Cancellation of order "{order.client_order_id}" / "{cancelled_order.id}" failed."""
                )

                raise exception

            transaction_hash = cancelled_order.hashes.creation

            if transaction_hash in (None, ""):
                raise Exception(
                    f"""Cancellation of order "{order.client_order_id}" / "{cancelled_order.id}" failed. Invalid transaction hash: "{transaction_hash}"."""
                )

        misc_updates = DotMap({
            "cancelation_transaction_hash": transaction_hash,
        }, _dynamic=False)

        return True, misc_updates

    async def batch_order_cancel(self, orders_to_cancel: List[GatewayInFlightOrder]) -> List[CancelOrderResult]:
        client_ids = [order.client_order_id for order in orders_to_cancel]

        in_flight_orders_to_cancel = [
            self._gateway_order_tracker.fetch_tracked_order(client_order_id=order.client_order_id)
            for order in orders_to_cancel
        ]
        exchange_order_ids_to_cancel = await safe_gather(
            *[order.get_exchange_order_id() for order in in_flight_orders_to_cancel],
            return_exceptions=True,
        )
        found_orders_to_cancel = [
            order
            for order, result in zip(orders_to_cancel, exchange_order_ids_to_cancel)
            if not isinstance(result, asyncio.TimeoutError)
        ]

        ids = [order.exchange_order_id for order in found_orders_to_cancel]

        async with self._locks.cancel_orders:
            try:
                response = await self._gateway.kujira_delete_orders({
                    "chain": self._chain,
                    "network": self._network,
                    "connector": self._connector,
                    "ids": ids,
                    "marketId": self._market.id,
                    "ownerAddress": self._owner_address,
                })

                cancelled_orders = DotMap(response.values(), _dynamic=False)

                hashes = set([order.hashes.cancellation for order in cancelled_orders])

                self.logger().debug(
                    f"""Orders "{client_ids}" / "{ids}" successfully cancelled. Transaction hash(es): "{hashes}"."""
                )
            except Exception as exception:
                self.logger().debug(
                    f"""Cancellation of orders "{client_ids}" / "{ids}" failed."""
                )

                raise exception

            transaction_hash = "".join(hashes)

            if transaction_hash in (None, ""):
                raise RuntimeError(
                    f"""Placement of orders "{client_ids}" / "{ids}" failed. Invalid transaction hash: "{transaction_hash}"."""
                )

        cancel_order_results = []
        for order_to_cancel, cancelled_order in zip(orders_to_cancel, cancelled_orders):
            cancel_order_results.append(CancelOrderResult(
                client_order_id=order_to_cancel.client_order_id,
                trading_pair=order_to_cancel.trading_pair,
                misc_updates={
                    "cancelation_transaction_hash": transaction_hash
                },
                exception=None,
            ))

        return cancel_order_results

    async def get_last_traded_price(self, trading_pair: str) -> Decimal:
        response = await self._gateway.kujira_get_ticker({
            "chain": self._chain,
            "network": self._network,
            "connector": self._connector,
            "marketId": self._market.id,
        })

        ticker = DotMap(response, _dynamic=False)

        return Decimal(ticker.price)

    async def get_order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        response = await self._gateway.kujira_get_order_book({
            "chain": self._chain,
            "network": self._network,
            "connector": self._connector,
            "marketId": self._market.id,
        })

        order_book = DotMap(response, _dynamic=False)

        price_scale = 1
        size_scale = 1

        timestamp = time()

        bids = []
        asks = []
        for bid in order_book.bids.values():
            bids.append((Decimal(bid.price) * price_scale, Decimal(bid.amount) * size_scale))

        for ask in order_book.asks.values():
            asks.append((Decimal(ask.price) * price_scale, Decimal(ask.amount) * size_scale))

        snapshot = OrderBookMessage(
            message_type=OrderBookMessageType.SNAPSHOT,
            content={
                "trading_pair": trading_pair,
                "update_id": timestamp,
                "bids": bids,
                "asks": asks,
            },
            timestamp=timestamp
        )

        return snapshot

    async def get_account_balances(self) -> Dict[str, Dict[str, Decimal]]:
        response = await self._gateway.kujira_get_balances_all({
            "chain": self._chain,
            "network": self._network,
            "connector": self._connector,
            "ownerAddress": self._owner_address,
        })

        balances = DotMap(response, _dynamic=False)

        balances.total.free = Decimal(balances.total.free)
        balances.total.lockedInOrders = Decimal(balances.total.lockedInOrders)
        balances.total.unsettled = Decimal(balances.total.unsettled)

        hb_balances = {}
        for balance in balances.tokens.values():
            balance.free = Decimal(balance.free)
            balance.lockedInOrders = Decimal(balance.lockedInOrders)
            balance.unsettled = Decimal(balance.unsettled)
            hb_balances[balance.token.symbol] = DotMap({}, _dynamic=False)
            hb_balances[balance.token.symbol]["total_balance"] = Decimal(balance.free + balance.lockedInOrders + balance.unsettled)
            hb_balances[balance.token.symbol]["available_balance"] = Decimal(balance.free)

        self._user_balances = balances

        return hb_balances

    async def get_order_status_update(self, in_flight_order: GatewayInFlightOrder) -> OrderUpdate:
        default: Optional[OrderUpdate] = None

        await in_flight_order.get_exchange_order_id()

        response = await self._gateway.kujira_get_order({
            "chain": self._chain,
            "network": self._network,
            "connector": self._connector,
            "id": in_flight_order.exchange_order_id,
            "marketId": self._market.id,
            "ownerAddress": self._owner_address,
        })

        order = DotMap(response, _dynamic=False)

        if order:
            order_status = KujiraOrderStatus.to_hummingbot(order.status)

            if in_flight_order.current_state != order_status:
                timestamp = time()

                open_update = OrderUpdate(
                    trading_pair=in_flight_order.trading_pair,
                    update_timestamp=timestamp,
                    new_state=order_status,
                    client_order_id=in_flight_order.client_order_id,
                    exchange_order_id=in_flight_order.exchange_order_id,
                    misc_updates={
                        "creation_transaction_hash": in_flight_order.creation_transaction_hash,
                        "cancelation_transaction_hash": in_flight_order.cancel_tx_hash,
                    },
                )
                self._publisher.trigger_event(event_tag=MarketEvent.OrderUpdate, message=open_update)

        return default

    async def get_all_order_fills(self, in_flight_order: GatewayInFlightOrder) -> List[TradeUpdate]:
        response = await self._gateway.kujira_get_order({
            "chain": self._chain,
            "network": self._network,
            "connector": self._connector,
            "id": in_flight_order.exchange_order_id,
            "marketId": self._market.id,
            "ownerAddress": self._owner_address,
            "status": KujiraOrderStatus.FILLED.value[0]
        })

        filled_order = DotMap(response, _dynamic=False)

        if filled_order:
            timestamp = time()
            trade_id = str(timestamp)

            # Simplified approach
            # is_taker = in_flight_order.order_type == OrderType.LIMIT

            # order_book_message = OrderBookMessage(
            #     message_type=OrderBookMessageType.TRADE,
            #     timestamp=timestamp,
            #     content={
            #         "trade_id": trade_id,
            #         "trading_pair": in_flight_order.trading_pair,
            #         "trade_type": in_flight_order.trade_type,
            #         "amount": in_flight_order.amount,
            #         "price": in_flight_order.price,
            #         "is_taker": is_taker,
            #     },
            # )

            trade_update = TradeUpdate(
                trade_id=trade_id,
                client_order_id=in_flight_order.client_order_id,
                exchange_order_id=in_flight_order.exchange_order_id,
                trading_pair=in_flight_order.trading_pair,
                fill_timestamp=timestamp,
                fill_price=in_flight_order.price,
                fill_base_amount=in_flight_order.amount,
                fill_quote_amount=in_flight_order.price * in_flight_order.amount,
                fee=TradeFeeBase.new_spot_fee(
                    fee_schema=TradeFeeSchema(),
                    trade_type=in_flight_order.trade_type,
                    flat_fees=[TokenAmount(
                        amount=Decimal(self._market.fees.taker),
                        token=self._market.quoteToken.symbol
                    )]
                ),
            )

            return [trade_update]

        return []

    def is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        return str(status_update_exception).startswith("No update found for order")  # TODO is this correct?!!!

    def is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        return False

    async def check_network_status(self) -> NetworkStatus:
        try:
            await self._gateway.ping_gateway()

            return NetworkStatus.CONNECTED
        except asyncio.CancelledError:
            raise
        except Exception as exception:
            self.logger().error(exception)

            return NetworkStatus.NOT_CONNECTED

    @property
    def is_cancel_request_in_exchange_synchronous(self) -> bool:
        return True

    def _check_markets_initialized(self) -> bool:
        return self._markets is not None and bool(self._markets)

    async def _update_markets(self):
        request = {
            "chain": self._chain,
            "network": self._network,
            "connector": self._connector,
        }

        if self._markets_names:
            request["names"] = self._markets_names
            response = await self._gateway.kujira_get_markets(request)
        else:
            response = await self._gateway.kujira_get_markets_all(request)

        self._markets = DotMap(response, _dynamic=False)
        self._markets_name_id_map = {market.name: market.id for market in self._markets.values()}

        if self._market_name:
            self._market = self._markets[self._markets_name_id_map[self._market_name]]

        return self._markets

    def _parse_trading_rule(self, trading_pair: str, market_info: Any) -> TradingRule:
        trading_rule = TradingRule(
            trading_pair=trading_pair,
            min_order_size=Decimal(market_info.minimumOrderSize),
            min_price_increment=Decimal(market_info.minimumPriceIncrement),
            min_base_amount_increment=Decimal(market_info.minimumBaseAmountIncrement),
            min_quote_amount_increment=Decimal(market_info.minimumQuoteAmountIncrement),
        )

        return trading_rule

    def _get_exchange_trading_pair_from_market_info(self, market_info: Any) -> str:
        return market_info.id

    def _get_maker_taker_exchange_fee_rates_from_market_info(self, market_info: Any) -> MakerTakerExchangeFeeRates:
        fee_scaler = Decimal("1") - Decimal(market_info.fees.serviceProvider)
        maker_fee = Decimal(market_info.fees.maker) * fee_scaler
        taker_fee = Decimal(market_info.fees.taker) * fee_scaler

        return MakerTakerExchangeFeeRates(
            maker=maker_fee,
            taker=taker_fee,
            maker_flat_fees=[],
            taker_flat_fees=[]
        )

    async def _update_markets_loop(self):
        while True:
            await self._update_markets()
            await asyncio.sleep(MARKETS_UPDATE_INTERVAL)

    # async def _check_if_order_failed_based_on_transaction(
    #     self,
    #     transaction: Any,
    #     order: GatewayInFlightOrder
    # ) -> bool:
    #     order_id = await order.get_exchange_order_id()
    #
    #     return order_id.lower() not in transaction.data.lower()  # TODO fix, bring data to the transaction object!!!
