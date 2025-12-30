"""Govee ArtNet Console - Interactive CLI for managing Govee ArtNet LAN Bridge.

This package provides a standalone CLI tool for controlling and monitoring
Govee devices via the ArtNet LAN Bridge REST API.
"""

__version__ = "0.1.0"
__author__ = "mccartyp"

from .cli import ClientConfig, main

__all__ = ["ClientConfig", "main", "__version__"]
