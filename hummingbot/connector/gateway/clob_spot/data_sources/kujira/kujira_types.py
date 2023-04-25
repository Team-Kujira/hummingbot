from enum import Enum

from pyinjective.async_client import AsyncClient
from pyinjective.composer import Composer as ProtoMsgComposer
from pyinjective.constant import Denom, Network
from pyinjective.orderhash import OrderHashResponse, build_eip712_msg, hash_order
from pyinjective.proto.exchange.injective_accounts_rpc_pb2 import StreamSubaccountBalanceResponse, SubaccountBalance
from pyinjective.proto.exchange.injective_explorer_rpc_pb2 import GetTxByTxHashResponse, StreamTxsResponse
from pyinjective.proto.exchange.injective_portfolio_rpc_pb2 import StreamAccountPortfolioResponse
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


class OrderStatus(Enum):
    OPEN = "OPEN",
    CANCELLED = "CANCELLED",
    PARTIALLY_FILLED = "PARTIALLY_FILLED",
    FILLED = "FILLED",
    CREATION_PENDING = "CREATION_PENDING",
    CANCELLATION_PENDING = "CANCELLATION_PENDING",
    UNKNOWN = "UNKNOWN"


class OrderType(Enum):
    MARKET = "MARKET",
    LIMIT = "LIMIT"


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
StreamAccountPortfolioResponse = StreamAccountPortfolioResponse
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
    "StreamAccountPortfolioResponse",
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
