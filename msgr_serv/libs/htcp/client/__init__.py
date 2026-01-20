"""
HTCP Client Module
TCP client for connecting to HTCP servers.
"""

import socket
import logging
from typing import Any, Dict, Optional, Type

from ..common.proto import (
    Packet, PacketType, ErrorPacket,
    HandshakeRequest, HandshakeResponse,
    TransactionCall, TransactionResult
)
from ..common.utils import convert_to_type


class Client:
    """
    HTCP Client.

    Example usage:
        client = Client(server_host="127.0.0.1", server_port=2353)
        client.connect()

        result = client.call(transaction="greet", name="World")
        print(result)  # "Hello, World!"

        client.disconnect()
    """

    def __init__(
        self,
        server_host: str = "127.0.0.1",
        server_port: int = 2353,
        logger: Optional[logging.Logger] = None
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.logger = logger or logging.getLogger(__name__)

        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._server_name = "unknown"
        self._available_transactions: list[str] = []

    @property
    def connected(self) -> bool:
        """Check if client is connected to server."""
        return self._connected

    def connect(self) -> None:
        """Connect to the HTCP server."""
        if self._connected:
            self.logger.warning("Already connected")
            return

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.server_host, self.server_port))

            # Perform handshake
            self._handshake()
            self._connected = True

            self.logger.info(f"Connected to {self.server_host}:{self.server_port}")

        except Exception as e:
            self._cleanup()
            raise ConnectionError(f"Failed to connect: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from the server."""
        if not self._connected:
            return

        try:
            # Send disconnect packet
            packet = Packet(PacketType.DISCONNECT)
            self._send_packet(packet)
        except Exception:
            pass

        self._cleanup()
        self.logger.info("Disconnected from server")

    def _cleanup(self) -> None:
        """Clean up connection resources."""
        self._connected = False
        self._server_name = "unknown"
        self._available_transactions = []

        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def _handshake(self) -> None:
        """Perform handshake with server."""
        request = HandshakeRequest()
        self._send_packet(request.to_packet())

        response_packet = Packet.read_from_socket(self._socket)

        if response_packet.packet_type == PacketType.ERROR:
            error = ErrorPacket.from_packet(response_packet)
            raise ConnectionError(f"Handshake error: {error.message}")

        if response_packet.packet_type != PacketType.HANDSHAKE_RESPONSE:
            raise ConnectionError(f"Unexpected response type: {response_packet.packet_type}")

        response = HandshakeResponse.from_packet(response_packet)
        self._server_name = response.server_name
        self._available_transactions = response.transactions

    def server_info(self) -> Dict[str, Any]:
        """
        Get server information.

        Returns:
            Dict with server_name, server_addr (host, port), and connected status
        """
        return {
            "server_name": self._server_name,
            "server_addr": {
                "host": self.server_host if self._connected else "unknown",
                "port": self.server_port if self._connected else 0
            },
            "connected": self._connected,
            "available_transactions": self._available_transactions
        }

    def call(self, transaction: str, result_type: Type = None, **kwargs) -> Any:
        """
        Call a transaction on the server.

        Args:
            transaction: Transaction code to call
            result_type: Optional expected return type for proper deserialization
            **kwargs: Arguments to pass to the transaction

        Returns:
            The result of the transaction

        Example:
            # Simple call
            result = client.call(transaction="greet", name="World")

            # Call with expected type for dataclass
            result = client.call(
                transaction="get_user",
                result_type=User,
                user_id=123
            )
        """
        if not self._connected:
            raise ConnectionError("Not connected to server")

        # Send transaction call
        call = TransactionCall(transaction_code=transaction, arguments=kwargs)
        self._send_packet(call.to_packet())

        if logging.getLevelName(self.logger.level) == "DEBUG":
            self.logger.debug(f"Called transaction '{transaction}' with args: {kwargs}")
        else:
            self.logger.info(f"Called transaction '{transaction}'")

        # Receive response
        response_packet = Packet.read_from_socket(self._socket)

        if response_packet.packet_type == PacketType.ERROR:
            error = ErrorPacket.from_packet(response_packet)
            raise RuntimeError(f"Server error: {error.message}")

        if response_packet.packet_type != PacketType.TRANSACTION_RESULT:
            raise RuntimeError(f"Unexpected response type: {response_packet.packet_type}")

        result = TransactionResult.from_packet(response_packet)

        if not result.success:
            raise RuntimeError(f"Transaction failed: {result.error_message}")

        # Convert result to expected type if specified
        if result_type is not None and result.result is not None:
            return convert_to_type(result.result, result_type)

        return result.result

    def _send_packet(self, packet: Packet) -> None:
        """Send packet to server."""
        if not self._socket:
            raise ConnectionError("Not connected")

        self._socket.sendall(packet.to_bytes())

    def __enter__(self) -> 'Client':
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()
