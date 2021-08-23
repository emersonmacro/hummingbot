import aiohttp
import asyncio
from typing import AsyncIterable, Dict, Any, Optional, List

import hummingbot.connector.derivative.bybit_perpetual.bybit_perpetual_constants as CONSTANTS


class BybitPerpetualWebSocketAdaptor:

    _operation_field_name = "op"
    _payload_field_name = "args"
    _subscription_operation = "subscribe"

    """
    Auxiliary class that works as a wrapper of a low level web socket. It contains the logic to create messages
    with the format expected by Bybit
    :param websocket: The low level socket to be used to send and receive messages
    """
    MESSAGE_TIMEOUT = 30.0
    PING_TIMEOUT = 5.0

    def __init__(self, websocket: aiohttp.ClientWebSocketResponse):
        self._websocket = websocket

    async def send_request(self, payload: Dict[str, Any]):
        await self._websocket.send_json(payload)

    def _symbols_filter(self, symbols):
        if symbols:
            symbol_filter = "|".join(symbols)
        else:
            symbol_filter = "*"
        return symbol_filter

    async def subscribe_to_order_book(self, symbols: Optional[List[str]] = None):
        symbol_filter = self._symbols_filter(symbols)
        subscription_message = {self._operation_field_name: self._subscription_operation,
                                self._payload_field_name: [f"{CONSTANTS.WS_ORDER_BOOK_EVENTS_TOPIC}.{symbol_filter}"]}
        await self.send_request(subscription_message)

    async def subscribe_to_trades(self, symbols: Optional[List[str]] = None):
        symbol_filter = self._symbols_filter(symbols)
        subscription_message = {self._operation_field_name: self._subscription_operation,
                                self._payload_field_name: [f"{CONSTANTS.WS_TRADES_TOPIC}.{symbol_filter}"]}
        await self.send_request(subscription_message)

    async def subscribe_to_instruments_info(self, symbols: Optional[List[str]] = None):
        symbol_filter = self._symbols_filter(symbols)
        subscription_message = {self._operation_field_name: self._subscription_operation,
                                self._payload_field_name: [f"{CONSTANTS.WS_INSTRUMENTS_INFO_TOPIC}.{symbol_filter}"]}
        await self.send_request(subscription_message)

    async def receive_json(self, *args, **kwars):
        return await self._websocket.receive_json(*args, **kwars)

    async def iter_messages(self) -> AsyncIterable[Dict[str, Any]]:
        try:
            while True:
                try:
                    msg = await self.receive_json(timeout=self.MESSAGE_TIMEOUT)
                    yield msg
                except asyncio.TimeoutError:
                    await asyncio.wait_for(
                        self.send_request(payload={self._operation_field_name: CONSTANTS.WS_PING_REQUEST}),
                        timeout=self.PING_TIMEOUT
                    )
        finally:
            await self.close()

    async def close(self, *args, **kwars):
        return await self._websocket.close(*args, **kwars)