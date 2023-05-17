from enum import Enum

from pyinjective.async_client import AsyncClient
from pyinjective.composer import Composer as ProtoMsgComposer
from pyinjective.constant import Denom, Network
from pyinjective.orderhash import OrderHashResponse, build_eip712_msg, hash_order
from pyinjective.proto.exchange.injective_accounts_rpc_pb2 import StreamSubaccountBalanceResponse, SubaccountBalance
from pyinjective.proto.exchange.injective_explorer_rpc_pb2 import GetTxByTxHashResponse, StreamTxsResponse
from pyinjective.proto.exchange.injective_portfolio_rpc_pb2 import (
    AccountPortfolioResponse,
    Coin,
    Portfolio,
    StreamAccountPortfolioResponse,
    SubaccountBalanceV2,
)
from pyinjective.proto.exchange.injective_spot_exchange_rpc_pb2 import (
    MarketsResponse,
    SpotMarketInfo,
    SpotOrderHistory,
    SpotTrade,
    StreamOrderbookResponse,
    StreamOrdersResponse,
    StreamTradesResponse,
    TokenMeta,
)
from pyinjective.proto.injective.exchange.v1beta1 import exchange_pb2
from pyinjective.proto.injective.exchange.v1beta1.exchange_pb2 import DerivativeOrder, SpotOrder
from pyinjective.utils import derivative_price_to_backend, derivative_quantity_to_backend
from pyinjective.wallet import Address

from hummingbot.core.data_type.common import OrderType as HummingBotOrderType, TradeType as HummingBotOrderSide
from hummingbot.core.data_type.in_flight_order import OrderState as HummingBotOrderStatus


class OrderStatus(Enum):
    OPEN = "OPEN",
    CANCELLED = "CANCELLED",
    PARTIALLY_FILLED = "PARTIALLY_FILLED",
    FILLED = "FILLED",
    CREATION_PENDING = "CREATION_PENDING",
    CANCELLATION_PENDING = "CANCELLATION_PENDING",
    UNKNOWN = "UNKNOWN"

    @staticmethod
    def from_name(name: str):
        if name == "OPEN":
            return OrderStatus.OPEN
        elif name == "CANCELLED":
            return OrderStatus.CANCELLED
        elif name == "PARTIALLY_FILLED":
            return OrderStatus.PARTIALLY_FILLED
        elif name == "FILLED":
            return OrderStatus.FILLED
        elif name == "CREATION_PENDING":
            return OrderStatus.CREATION_PENDING
        elif name == "CANCELLATION_PENDING":
            return OrderStatus.CANCELLATION_PENDING
        else:
            raise ValueError(f"Unknown order status: {name}")

    @staticmethod
    def from_hummingbot(target: HummingBotOrderStatus):
        if target == HummingBotOrderStatus.PENDING_CREATE:
            return OrderStatus.CREATION_PENDING
        elif target == HummingBotOrderStatus.OPEN:
            return OrderStatus.OPEN
        elif target == HummingBotOrderStatus.PENDING_CANCEL:
            return OrderStatus.CANCELLATION_PENDING
        elif target == HummingBotOrderStatus.CANCELED:
            return OrderStatus.CANCELLED
        elif target == HummingBotOrderStatus.PARTIALLY_FILLED:
            return OrderStatus.PARTIALLY_FILLED
        elif target == HummingBotOrderStatus.FILLED:
            return OrderStatus.FILLED
        # elif target == HummingBotOrderStatus.FAILED:
        #     return OrderStatus.FAILED
        # elif target == HummingBotOrderStatus.PENDING_APPROVAL:
        #     return OrderStatus.APPROVAL_PENDING
        # elif target == HummingBotOrderStatus.APPROVED:
        #     return OrderStatus.APPROVED
        # elif target == HummingBotOrderStatus.CREATED:
        #     return OrderStatus.CREATED
        # elif target == HummingBotOrderStatus.COMPLETED:
        #     return OrderStatus.COMPLETED
        else:
            raise ValueError(f"Unknown order status: {target}")

    @staticmethod
    def to_hummingbot(self):
        if self == OrderStatus.OPEN:
            return HummingBotOrderStatus.OPEN
        elif self == OrderStatus.CANCELLED:
            return HummingBotOrderStatus.CANCELED
        elif self == OrderStatus.PARTIALLY_FILLED:
            return HummingBotOrderStatus.PARTIALLY_FILLED
        elif self == OrderStatus.FILLED:
            return HummingBotOrderStatus.FILLED
        elif self == OrderStatus.CREATION_PENDING:
            return HummingBotOrderStatus.PENDING_CREATE
        elif self == OrderStatus.CANCELLATION_PENDING:
            return HummingBotOrderStatus.PENDING_CANCEL
        # elif self == OrderStatus.UNKNOWN:
        #     return HummingBotOrderStatus.UNKNOWN
        else:
            raise ValueError(f"Unknown order status: {self}")


class OrderType(Enum):
    MARKET = 'MARKET',
    LIMIT = 'LIMIT',
    IOC = 'IOC',  # Immediate or Cancel
    POST_ONLY = 'POST_ONLY',

    @staticmethod
    def from_name(name: str):
        if name == "MARKET":
            return OrderType.MARKET
        elif name == "LIMIT":
            return OrderType.LIMIT
        elif name == "IOC":
            return OrderType.IOC
        elif name == "POST_ONLY":
            return OrderType.POST_ONLY
        else:
            raise ValueError(f"Unknown order type: {name}")

    @staticmethod
    def from_hummingbot(target: HummingBotOrderType):
        if target == HummingBotOrderType.LIMIT:
            return OrderType.LIMIT
        else:
            raise ValueError(f'Unrecognized order type "{target}".')

    @staticmethod
    def to_hummingbot(self):
        if self == OrderType.LIMIT:
            return HummingBotOrderType.LIMIT
        else:
            raise ValueError(f'Unrecognized order type "{self}".')


class OrderSide(Enum):
    BUY = 'BUY',
    SELL = 'SELL',

    @staticmethod
    def from_name(name: str):
        if name == "BUY":
            return OrderSide.BUY
        elif name == "SELL":
            return OrderSide.SELL
        else:
            raise ValueError(f"Unknown order side: {name}")

    @staticmethod
    def from_hummingbot(target: HummingBotOrderSide):
        if target == HummingBotOrderSide.BUY:
            return OrderSide.BUY
        elif target == HummingBotOrderSide.SELL:
            return OrderSide.SELL
        else:
            raise ValueError(f'Unrecognized order side "{target}".')

    def to_hummingbot(self):
        if self == OrderSide.BUY:
            return HummingBotOrderSide.BUY
        elif self == OrderSide.SELL:
            return HummingBotOrderSide.SELL
        else:
            raise ValueError(f'Unrecognized order side "{self}".')


class TickerSource(Enum):
    ORDER_BOOK_SAP = "orderBookSimpleAveragePrice",
    ORDER_BOOK_WAP = "orderBookWeightedAveragePrice",
    ORDER_BOOK_VWAP = "orderBookVolumeWeightedAveragePrice",
    LAST_FILLED_ORDER = "lastFilledOrder",
    NOMICS = "nomics",


##########################
# Injective related types:
##########################


AsyncClient = AsyncClient
ProtoMsgComposer = ProtoMsgComposer
Network = Network
OrderHashResponse = OrderHashResponse
build_eip712_msg = build_eip712_msg
hash_order = hash_order
StreamSubaccountBalanceResponse = StreamSubaccountBalanceResponse
SubaccountBalance = SubaccountBalance
GetTxByTxHashResponse = GetTxByTxHashResponse
StreamTxsResponse = StreamTxsResponse
AccountPortfolioResponse = AccountPortfolioResponse
Coin = Coin
Portfolio = Portfolio
StreamAccountPortfolioResponse = StreamAccountPortfolioResponse
SubaccountBalanceV2 = SubaccountBalanceV2
MarketsResponse = MarketsResponse
SpotMarketInfo = SpotMarketInfo
SpotOrderHistory = SpotOrderHistory
SpotTrade = SpotTrade
StreamOrderbookResponse = StreamOrderbookResponse
StreamOrdersResponse = StreamOrdersResponse
StreamTradesResponse = StreamTradesResponse
TokenMeta = TokenMeta
exchange_pb2 = exchange_pb2
DerivativeOrder = DerivativeOrder
SpotOrder = SpotOrder
Address = Address
Denom = Denom
derivative_price_to_backend = derivative_price_to_backend
derivative_quantity_to_backend = derivative_quantity_to_backend


__all__ = [
    "AsyncClient",
    "ProtoMsgComposer",
    "Network",
    "OrderHashResponse",
    "build_eip712_msg",
    "hash_order",
    "StreamSubaccountBalanceResponse",
    "SubaccountBalance",
    "GetTxByTxHashResponse",
    "StreamTxsResponse",
    "AccountPortfolioResponse",
    "Coin",
    "Portfolio",
    "StreamAccountPortfolioResponse",
    "SubaccountBalanceV2",
    "MarketsResponse",
    "SpotMarketInfo",
    "SpotOrderHistory",
    "SpotTrade",
    "StreamOrderbookResponse",
    "StreamOrdersResponse",
    "StreamTradesResponse",
    "TokenMeta",
    "exchange_pb2",
    "DerivativeOrder",
    "SpotOrder",
    "Address",
    "Denom",
    "derivative_price_to_backend",
    "derivative_quantity_to_backend",
]
