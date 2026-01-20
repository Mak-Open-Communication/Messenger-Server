"""HTCP Common Package - shared utilities and protocol definitions."""

from .serialization import serialize, deserialize, TypeTag
from .proto import Packet, PacketType, ErrorCode
from .utils import get_function_signature, get_return_type, convert_to_type

__all__ = [
    'serialize', 'deserialize', 'TypeTag',
    'Packet', 'PacketType', 'ErrorCode',
    'get_function_signature', 'get_return_type', 'convert_to_type'
]
