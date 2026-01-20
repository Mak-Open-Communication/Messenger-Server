"""
HTCP - Binary TCP Protocol for Python

A library for building encrypted TCP-based client-server applications
with automatic type serialization and RPC support.
"""

from .server import Server
from .client import Client

__version__ = "0.1.0"
__all__ = ['Server', 'Client']
