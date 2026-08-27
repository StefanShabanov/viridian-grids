"""Human-readable reasons a probe failed, without leaking stack traces into reports."""

from __future__ import annotations

import socket
import ssl

import httpx


def describe(exc: Exception) -> str:
    match exc:
        case httpx.ConnectTimeout() | httpx.ReadTimeout() | socket.timeout():
            return "timed out"
        case ssl.SSLCertVerificationError():
            return f"certificate verification failed: {getattr(exc, 'verify_message', exc)}"
        case ssl.SSLError():
            return f"TLS error: {exc}"
        case socket.gaierror():
            return "DNS lookup failed"
        case httpx.ConnectError():
            return f"connection failed: {exc}"
        case httpx.TooManyRedirects():
            return "too many redirects"
        case httpx.HTTPError():
            return f"HTTP error: {exc}"
        case _:
            return f"{type(exc).__name__}: {exc}"
