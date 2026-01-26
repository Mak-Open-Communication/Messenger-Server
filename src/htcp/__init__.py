"""
HTCP - Binary TCP Protocol for Python

A library for building TCP-based client-server applications
with automatic type serialization and RPC support.
"""

from .aio_server import AsyncServer
from .exceptions import (
    HTCPError,
    ConnectionError,
    ProtocolError,
    SerializationError,
    TransactionError,
    TimeoutError,
    MaxPayloadExceededError,
    UnknownPacketTypeError,
    HandshakeError,
)

__version__ = "0.2.0"
__all__ = [
    # Async
    'AsyncServer',
    # Exceptions
    'HTCPError',
    'ConnectionError',
    'ProtocolError',
    'SerializationError',
    'TransactionError',
    'TimeoutError',
    'MaxPayloadExceededError',
    'UnknownPacketTypeError',
    'HandshakeError',
]
