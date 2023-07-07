from enum import Enum

from hummingbot.core.data_type.common import OrderType as HummingBotOrderType, TradeType as HummingBotOrderSide
from hummingbot.core.data_type.in_flight_order import OrderState as HummingBotOrderStatus


class HTTPMethod(Enum):
    GET = 'get',
    POST = 'post',
    PATCH = 'patch',
    UPDATE = 'update',
    DELETE = 'delete'


class Route(Enum):
    GET_STATUS = (HTTPMethod.GET.value[0], 'status'),
    GET_TOKEN = (HTTPMethod.GET.value[0], 'token'),
    GET_TOKENS = (HTTPMethod.GET.value[0], 'tokens'),
    GET_TOKENS_ALL = (HTTPMethod.GET.value[0], 'tokens/all'),
    GET_MARKET = (HTTPMethod.GET.value[0], 'market'),
    GET_MARKETS = (HTTPMethod.GET.value[0], 'markets'),
    GET_MARKETS_ALL = (HTTPMethod.GET.value[0], 'markets/all'),
    GET_ORDER_BOOK = (HTTPMethod.GET.value[0], 'orderBook'),
    GET_ORDER_BOOKS = (HTTPMethod.GET.value[0], 'orderBooks'),
    GET_ORDER_BOOKS_ALL = (HTTPMethod.GET.value[0], 'orderBooks/all'),
    GET_TICKER = (HTTPMethod.GET.value[0], 'ticker'),
    GET_TICKERS = (HTTPMethod.GET.value[0], 'tickers'),
    GET_TICKERS_ALL = (HTTPMethod.GET.value[0], 'tickers/all'),
    GET_BALANCE = (HTTPMethod.GET.value[0], 'balance'),
    GET_BALANCES = (HTTPMethod.GET.value[0], 'balances'),
    GET_BALANCES_ALL = (HTTPMethod.GET.value[0], 'balances/all'),
    GET_ORDER = (HTTPMethod.GET.value[0], 'order'),
    GET_ORDERS = (HTTPMethod.GET.value[0], 'orders'),
    POST_ORDER = (HTTPMethod.POST.value[0], 'order'),
    POST_ORDERS = (HTTPMethod.POST.value[0], 'orders'),
    DELETE_ORDER = ('delete', 'order'),
    DELETE_ORDERS = ('delete', 'orders'),
    DELETE_ORDERS_ALL = ('delete', 'orders/all'),
    POST_MARKET_WITHDRAW = (HTTPMethod.POST.value[0], 'market/withdraw'),
    POST_MARKET_WITHDRAWS = (HTTPMethod.POST.value[0], 'market/withdraws'),
    POST_MARKET_WITHDRAWS_ALL = (HTTPMethod.POST.value[0], 'market/withdraws/all'),
    GET_TRANSACTION = (HTTPMethod.GET.value[0], 'transaction'),
    GET_TRANSACTIONS = (HTTPMethod.GET.value[0], 'transactions'),
    GET_WALLET_PUBLIC_KEY = (HTTPMethod.GET.value[0], 'wallet/publicKey'),
    GET_WALLET_PUBLIC_KEYS = (HTTPMethod.GET.value[0], 'wallet/publicKeys'),
    GET_BLOCK_CURRENT = (HTTPMethod.GET.value[0], 'block/current'),
    GET_FEES_ESTIMATED = (HTTPMethod.GET.value[0], 'fees/estimated'),


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
