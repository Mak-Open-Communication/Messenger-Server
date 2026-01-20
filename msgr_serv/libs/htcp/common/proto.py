"""
HTCP Protocol Module
Defines the binary protocol format for client-server communication.
"""

import struct

from enum import IntEnum
from typing import Any, Dict
from .serialization import serialize, deserialize


class PacketType(IntEnum):
    """Types of packets in HTCP protocol."""
    # Client -> Server
    HANDSHAKE_REQUEST = 0x01
    TRANSACTION_CALL = 0x02
    DISCONNECT = 0x03

    # Server -> Client
    HANDSHAKE_RESPONSE = 0x11
    TRANSACTION_RESULT = 0x12
    ERROR = 0x13


class ErrorCode(IntEnum):
    """Error codes for protocol errors."""
    SUCCESS = 0
    UNKNOWN_TRANSACTION = 1
    INVALID_ARGUMENTS = 2
    EXECUTION_ERROR = 3
    PROTOCOL_ERROR = 4
    INTERNAL_ERROR = 5


# Protocol constants
MAGIC_BYTES = b'HTCP'
PROTOCOL_VERSION = 1
HEADER_SIZE = 12  # MAGIC(4) + VERSION(1) + TYPE(1) + LENGTH(4) + RESERVED(2)


class Packet:
    """
    HTCP Protocol Packet.

    Binary format:
    +--------+--------+------+--------+----------+---------+
    | MAGIC  | VERSION| TYPE | LENGTH | RESERVED | PAYLOAD |
    | 4 bytes| 1 byte |1 byte| 4 bytes| 2 bytes  | N bytes |
    +--------+--------+------+--------+----------+---------+
    """

    def __init__(self, packet_type: PacketType, payload: bytes = b''):
        self.packet_type = packet_type
        self.payload = payload

    def to_bytes(self) -> bytes:
        """Serialize packet to bytes."""
        header = (
            MAGIC_BYTES +
            struct.pack('>B', PROTOCOL_VERSION) +
            struct.pack('>B', self.packet_type) +
            struct.pack('>I', len(self.payload)) +
            b'\x00\x00'  # Reserved bytes
        )
        return header + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Packet':
        """Deserialize packet from bytes."""
        if len(data) < HEADER_SIZE:
            raise ValueError(f"Data too short for packet header: {len(data)} < {HEADER_SIZE}")

        magic = data[:4]
        if magic != MAGIC_BYTES:
            raise ValueError(f"Invalid magic bytes: {magic}")

        version = data[4]
        if version != PROTOCOL_VERSION:
            raise ValueError(f"Unsupported protocol version: {version}")

        packet_type = PacketType(data[5])
        payload_length = struct.unpack('>I', data[6:10])[0]

        if len(data) < HEADER_SIZE + payload_length:
            raise ValueError(f"Incomplete packet: expected {HEADER_SIZE + payload_length}, got {len(data)}")

        payload = data[HEADER_SIZE:HEADER_SIZE + payload_length]
        return cls(packet_type, payload)

    @classmethod
    def read_from_socket(cls, sock) -> 'Packet':
        """Read a complete packet from socket."""
        header = _recv_exact(sock, HEADER_SIZE)
        if not header:
            raise ConnectionError("Connection closed")

        magic = header[:4]
        if magic != MAGIC_BYTES:
            raise ValueError(f"Invalid magic bytes: {magic}")

        version = header[4]
        if version != PROTOCOL_VERSION:
            raise ValueError(f"Unsupported protocol version: {version}")

        packet_type = PacketType(header[5])
        payload_length = struct.unpack('>I', header[6:10])[0]

        payload = b''
        if payload_length > 0:
            payload = _recv_exact(sock, payload_length)
            if len(payload) != payload_length:
                raise ConnectionError("Connection closed while reading payload")

        return cls(packet_type, payload)


def _recv_exact(sock, size: int) -> bytes:
    """Receive exact number of bytes from socket."""
    data = b''
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return data
        data += chunk
    return data


class HandshakeRequest:
    """Handshake request from client to server."""

    def to_packet(self) -> Packet:
        return Packet(PacketType.HANDSHAKE_REQUEST, b'')

    @classmethod
    def from_packet(cls, packet: Packet) -> 'HandshakeRequest':
        return cls()


class HandshakeResponse:
    """Handshake response from server to client."""

    def __init__(self, server_name: str, transactions: list[str]):
        self.server_name = server_name
        self.transactions = transactions

    def to_packet(self) -> Packet:
        payload = serialize({
            "server_name": self.server_name,
            "transactions": self.transactions
        })
        return Packet(PacketType.HANDSHAKE_RESPONSE, payload)

    @classmethod
    def from_packet(cls, packet: Packet) -> 'HandshakeResponse':
        data, _ = deserialize(packet.payload)
        return cls(
            server_name=data.get("server_name", "unknown"),
            transactions=data.get("transactions", [])
        )


class TransactionCall:
    """Transaction call from client to server."""

    def __init__(self, transaction_code: str, arguments: Dict[str, Any]):
        self.transaction_code = transaction_code
        self.arguments = arguments

    def to_packet(self) -> Packet:
        payload = serialize({
            "transaction": self.transaction_code,
            "arguments": self.arguments
        })
        return Packet(PacketType.TRANSACTION_CALL, payload)

    @classmethod
    def from_packet(cls, packet: Packet) -> 'TransactionCall':
        data, _ = deserialize(packet.payload)
        return cls(
            transaction_code=data.get("transaction", ""),
            arguments=data.get("arguments", {})
        )


class TransactionResult:
    """Transaction result from server to client."""

    def __init__(self, success: bool, result: Any = None, error_code: ErrorCode = ErrorCode.SUCCESS, error_message: str = ""):
        self.success = success
        self.result = result
        self.error_code = error_code
        self.error_message = error_message

    def to_packet(self) -> Packet:
        payload = serialize({
            "success": self.success,
            "result": self.result,
            "error_code": int(self.error_code),
            "error_message": self.error_message
        })
        return Packet(PacketType.TRANSACTION_RESULT, payload)

    @classmethod
    def from_packet(cls, packet: Packet, result_type=None) -> 'TransactionResult':
        data, _ = deserialize(packet.payload)

        result = data.get("result")

        # If we have an expected result type and result is dict-like from dataclass
        if result_type is not None and result is not None:
            from .serialization import deserialize as deser
            import dataclasses
            if dataclasses.is_dataclass(result_type) and isinstance(result, dict):
                # Result was serialized as dataclass but came back as dict
                # This happens when the result was serialized without type info
                pass

        return cls(
            success=data.get("success", False),
            result=result,
            error_code=ErrorCode(data.get("error_code", 0)),
            error_message=data.get("error_message", "")
        )


class ErrorPacket:
    """Error packet from server to client."""

    def __init__(self, error_code: ErrorCode, message: str):
        self.error_code = error_code
        self.message = message

    def to_packet(self) -> Packet:
        payload = serialize({
            "error_code": int(self.error_code),
            "message": self.message
        })
        return Packet(PacketType.ERROR, payload)

    @classmethod
    def from_packet(cls, packet: Packet) -> 'ErrorPacket':
        data, _ = deserialize(packet.payload)
        return cls(
            error_code=ErrorCode(data.get("error_code", 0)),
            message=data.get("message", "")
        )
