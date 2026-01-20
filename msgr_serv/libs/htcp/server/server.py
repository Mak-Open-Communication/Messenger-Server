"""
HTCP Server Module
TCP server with transaction decorator support.
"""

import socket
import threading
import logging

from typing import Callable, Dict, Optional

from ..common.proto import (
    Packet, PacketType, ErrorCode,
    HandshakeRequest, HandshakeResponse,
    TransactionCall, TransactionResult, ErrorPacket
)
from ..common.utils import get_function_signature, get_return_type, prepare_arguments


class Transaction:
    """Registered transaction information."""

    def __init__(self, code: str, func: Callable, param_types: Dict[str, type], return_type: type):
        self.code = code
        self.func = func
        self.param_types = param_types
        self.return_type = return_type


class ClientConnection:
    """Represents a connected client."""

    def __init__(self, sock: socket.socket, address: tuple):
        self.socket = sock
        self.address = address
        self.connected = True


class Server:
    """
    HTCP Server.

    Example usage:
        app = Server(name="my-server", host="0.0.0.0", port=2353)

        @app.transaction(code="greet")
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        app.up()
    """

    def __init__(
        self,
        name: str = "htcp-server",
        host: str = "0.0.0.0",
        port: int = 2353,
        max_connections: int = 100,
        expose_transactions: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        self.name = name
        self.host = host
        self.port = port
        self.max_connections = max_connections  # 0 = unlimited
        self.expose_transactions = expose_transactions
        self.logger = logger or logging.getLogger(__name__)

        self._transactions: Dict[str, Transaction] = {}
        self._socket: Optional[socket.socket] = None
        self._running = False
        self._accept_thread: Optional[threading.Thread] = None
        self._clients: Dict[tuple, ClientConnection] = {}
        self._clients_lock = threading.Lock()

    def transaction(self, code: str) -> Callable:
        """
        Decorator to register a transaction handler.

        Args:
            code: Unique transaction identifier

        Example:
            @app.transaction(code="get_user")
            def get_user(user_id: int) -> User:
                return db.get_user(user_id)
        """
        def decorator(func: Callable) -> Callable:
            param_types = get_function_signature(func)
            return_type = get_return_type(func)

            trans = Transaction(
                code=code,
                func=func,
                param_types=param_types,
                return_type=return_type
            )
            self._transactions[code] = trans

            self.logger.debug(f"Registered transaction '{code}'")
            return func

        return decorator

    def up(self) -> None:
        """Start the server and begin accepting connections."""
        if self._running:
            self.logger.warning("Server is already running")
            return

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.listen(5)

        self._running = True
        if logging.getLevelName(self.logger.level) == "INFO":
            self.logger.info(f"Registered {len(self._transactions)} transactions")
        self.logger.info(f"Server '{self.name}' started on {self.host}:{self.port}")

        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()

        # Block main thread
        try:
            self._accept_thread.join()
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            self.down()

    def down(self) -> None:
        """Stop the server."""
        if not self._running:
            return

        self._running = False

        # Close all client connections
        with self._clients_lock:
            for client in self._clients.values():
                try:
                    client.socket.close()
                except Exception:
                    pass
            self._clients.clear()

        # Close server socket
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        self.logger.info(f"Server '{self.name}' stopped")

    def _accept_loop(self) -> None:
        """Accept incoming connections."""
        while self._running:
            try:
                client_sock, address = self._socket.accept()

                # Check max connections limit
                with self._clients_lock:
                    current_connections = len(self._clients)

                if 0 < self.max_connections <= current_connections:
                    self.logger.warning(f"Connection from {address} rejected: max connections ({self.max_connections}) reached")
                    client_sock.close()
                    continue

                self.logger.info(f"New connection from {address[0]}:{address[1]}")

                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, address),
                    daemon=True
                )
                thread.start()

            except OSError:
                # Socket was closed
                break
            except Exception as e:
                if self._running:
                    self.logger.error(f"Error accepting connection: {e}")

    def _handle_client(self, sock: socket.socket, address: tuple) -> None:
        """Handle a single client connection."""
        client = ClientConnection(sock, address)

        with self._clients_lock:
            self._clients[address] = client

        try:
            while self._running and client.connected:
                try:
                    packet = Packet.read_from_socket(sock)
                    self._process_packet(client, packet)
                except ConnectionError:
                    break
                except Exception as e:
                    self.logger.error(f"Error processing packet from {address}: {e}")
                    self._send_error(client, ErrorCode.PROTOCOL_ERROR, str(e))
                    break

        finally:
            with self._clients_lock:
                self._clients.pop(address, None)
            try:
                sock.close()
            except Exception:
                pass
            self.logger.info(f"Client {address[0]}:{address[1]} disconnected")

    def _process_packet(self, client: ClientConnection, packet: Packet) -> None:
        """Process incoming packet from client."""
        if packet.packet_type == PacketType.HANDSHAKE_REQUEST:
            self._handle_handshake(client, packet)

        elif packet.packet_type == PacketType.TRANSACTION_CALL:
            self._handle_transaction(client, packet)

        elif packet.packet_type == PacketType.DISCONNECT:
            client.connected = False

        else:
            self._send_error(client, ErrorCode.PROTOCOL_ERROR, f"Unknown packet type: {packet.packet_type}")

    def _handle_handshake(self, client: ClientConnection, packet: Packet) -> None:
        """Handle handshake request."""
        try:
            HandshakeRequest.from_packet(packet)

            transactions = list(self._transactions.keys()) if self.expose_transactions else []
            response = HandshakeResponse(
                server_name=self.name,
                transactions=transactions
            )
            self._send_packet(client, response.to_packet())

        except Exception as e:
            self.logger.error(f"Handshake error: {e}")
            self._send_error(client, ErrorCode.PROTOCOL_ERROR, str(e))

    def _handle_transaction(self, client: ClientConnection, packet: Packet) -> None:
        """Handle transaction call."""
        try:
            call = TransactionCall.from_packet(packet)
            transaction_code = call.transaction_code

            self.logger.info(f"Transaction call '{transaction_code}' from {client.address[0]}:{client.address[1]}")

            # Find transaction
            trans = self._transactions.get(transaction_code)
            if not trans:
                self.logger.info(f"Unknown transaction: {transaction_code}")
                self._send_result(client, TransactionResult(
                    success=False,
                    error_code=ErrorCode.UNKNOWN_TRANSACTION,
                    error_message=f"Unknown transaction: {transaction_code}"
                ))
                return

            # Prepare arguments with type conversion
            try:
                prepared_args = prepare_arguments(trans.func, call.arguments)
            except Exception as e:
                self.logger.error(f"Argument preparation error: {e}")
                self._send_result(client, TransactionResult(
                    success=False,
                    error_code=ErrorCode.INVALID_ARGUMENTS,
                    error_message=str(e)
                ))
                return

            # Execute transaction
            try:
                result = trans.func(**prepared_args)

                self.logger.debug(f"Transaction '{transaction_code}' completed successfully")
                self._send_result(client, TransactionResult(
                    success=True,
                    result=result,
                    error_code=ErrorCode.SUCCESS
                ))

            except Exception as e:
                self.logger.error(f"Transaction execution error: {e}")
                self._send_result(client, TransactionResult(
                    success=False,
                    error_code=ErrorCode.EXECUTION_ERROR,
                    error_message=str(e)
                ))

        except Exception as e:
            self.logger.error(f"Transaction handling error: {e}")
            self._send_error(client, ErrorCode.INTERNAL_ERROR, str(e))

    def _send_packet(self, client: ClientConnection, packet: Packet) -> None:
        """Send packet to client."""
        try:
            client.socket.sendall(packet.to_bytes())
        except Exception as e:
            self.logger.error(f"Error sending packet: {e}")
            client.connected = False

    def _send_result(self, client: ClientConnection, result: TransactionResult) -> None:
        """Send transaction result to client."""
        self._send_packet(client, result.to_packet())

    def _send_error(self, client: ClientConnection, error_code: ErrorCode, message: str) -> None:
        """Send error packet to client."""
        error = ErrorPacket(error_code, message)
        self._send_packet(client, error.to_packet())
