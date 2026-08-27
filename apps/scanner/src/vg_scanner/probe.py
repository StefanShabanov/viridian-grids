"""The only place that touches the network.

Rule zero: every request here is one an ordinary visitor could make. No fuzzing,
no brute forcing, no crawling. A whole scan costs the target under ten requests.
"""

from __future__ import annotations

import contextlib
import re
import socket
import ssl
import time
import warnings
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes

from . import __version__
from .errors import describe

USER_AGENT = (
    f"ViridianGrids-HealthCheck/{__version__} "
    "(+https://viridiangrids.example/scanner; non-intrusive website health check)"
)

MAX_BODY_BYTES = 2_000_000
REPLACEMENT_CHAR = chr(0xFFFD)
NUL = chr(0)
DEFAULT_TIMEOUT = 15.0
POLITE_DELAY_S = 0.4


@dataclass
class Fetch:
    """One HTTP response, plus the timing and redirect trail we care about."""

    url: str
    ok: bool = False
    status: int | None = None
    headers: httpx.Headers = field(default_factory=httpx.Headers)
    body: str = ""
    body_bytes: int = 0
    ttfb_ms: float | None = None
    total_ms: float | None = None
    redirects: list[tuple[int, str]] = field(default_factory=list)
    final_url: str | None = None
    scheme: str | None = None
    set_cookie: list[str] = field(default_factory=list)
    body_decoded: bool = True
    error: str | None = None

    def header(self, name: str) -> str | None:
        return self.headers.get(name) if self.headers else None


@dataclass
class TlsInfo:
    """What a TLS handshake plus certificate parse tells us."""

    available: bool = False
    trusted: bool = False
    trust_error: str | None = None
    hostname_ok: bool = True
    negotiated_version: str | None = None
    cipher: str | None = None
    subject: str | None = None
    issuer: str | None = None
    not_before: datetime | None = None
    not_after: datetime | None = None
    days_remaining: int | None = None
    san: list[str] = field(default_factory=list)
    key_type: str | None = None
    key_bits: int | None = None
    signature_algorithm: str | None = None
    legacy_versions: list[str] = field(default_factory=list)
    legacy_tested: bool = False
    error: str | None = None


def normalize_domain(raw: str) -> str:
    """Accept anything a salesperson might paste and return a bare hostname."""
    value = raw.strip().lower()
    value = re.sub(r"^[a-z][a-z0-9+.-]*://", "", value)
    value = value.split("/")[0].split("?")[0].split("#")[0]
    value = value.rstrip(".")
    if "@" in value:
        value = value.split("@", 1)[1]
    if value.count(":") == 1 and not value.startswith("["):
        host, _, port = value.partition(":")
        if port.isdigit():
            value = host
    with contextlib.suppress(UnicodeError):
        value = value.encode("idna").decode("ascii")
    if not value or "." not in value:
        raise ValueError(f"{raw} does not look like a domain")
    return value


def sibling_host(host: str) -> str:
    """www.example.bg <-> example.bg, so we can check canonical-host behaviour."""
    return host[4:] if host.startswith("www.") else f"www.{host}"


def make_client(timeout: float = DEFAULT_TIMEOUT, verify: bool = False) -> httpx.Client:
    """Client for content checks.

    verify=False is deliberate: a broken certificate is a finding, not a reason to
    abandon the scan. Trust is judged separately by inspect_tls, which does verify.
    """
    return httpx.Client(
        timeout=timeout,
        verify=verify,
        follow_redirects=False,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "bg,en;q=0.8",
            # Deliberately no Accept-Encoding: httpx advertises exactly the codings
            # it can decode. Hard-coding "br" once left every check parsing raw
            # Brotli bytes, which silently broke all content detection.
        },
    )


def fetch(
    client: httpx.Client,
    url: str,
    *,
    follow_redirects: bool = True,
    max_redirects: int = 10,
    read_body: bool = True,
) -> Fetch:
    """GET a URL, recording TTFB, the redirect trail and (optionally) the body."""
    result = Fetch(url=url)
    seen: list[str] = []
    current = url
    started = time.perf_counter()

    try:
        for hop in range(max_redirects + 1):
            hop_start = time.perf_counter()
            with client.stream("GET", current) as response:
                ttfb = (time.perf_counter() - hop_start) * 1000
                if hop == 0:
                    result.ttfb_ms = round(ttfb, 1)

                if response.is_redirect and follow_redirects:
                    location = response.headers.get("location", "")
                    target = str(response.url.join(location)) if location else ""
                    result.redirects.append((response.status_code, target))
                    result.set_cookie.extend(response.headers.get_list("set-cookie"))
                    if not target:
                        break
                    if target in seen or target == current:
                        result.redirects.append((0, target))  # loop marker
                        result.error = "redirect loop"
                        break
                    seen.append(current)
                    current = target
                    response.close()
                    time.sleep(POLITE_DELAY_S)
                    continue

                result.status = response.status_code
                result.headers = response.headers
                result.final_url = str(response.url)
                result.scheme = response.url.scheme
                result.set_cookie.extend(response.headers.get_list("set-cookie"))
                if read_body:
                    chunks: list[bytes] = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size <= MAX_BODY_BYTES:
                            chunks.append(chunk)
                        else:
                            break
                    raw = b"".join(chunks)
                    result.body_bytes = size
                    result.body = raw.decode(response.encoding or "utf-8", errors="replace")
                    result.body_decoded = _is_readable_text(result.body)
                else:
                    response.close()
                result.ok = True
                break
        else:
            result.error = "too many redirects"
    except Exception as exc:  # noqa: BLE001 - a failed probe is data, not a crash
        result.error = describe(exc)

    result.total_ms = round((time.perf_counter() - started) * 1000, 1)
    return result


def _is_readable_text(body: str) -> bool:
    """Did we actually get text, or bytes we could not decode?

    Content checks fed undecoded bytes do not fail loudly - they quietly report
    that nothing was found, which is far worse. This catches that.
    """
    if not body:
        return True
    sample = body[:4000]
    unreadable = sample.count(REPLACEMENT_CHAR) + sample.count(NUL)
    return unreadable / len(sample) < 0.05


def _parse_certificate(der: bytes, host: str, info: TlsInfo) -> None:
    cert = x509.load_der_x509_certificate(der)
    info.subject = cert.subject.rfc4514_string()
    info.issuer = _issuer_name(cert)
    info.not_before = cert.not_valid_before_utc
    info.not_after = cert.not_valid_after_utc
    info.days_remaining = (cert.not_valid_after_utc - datetime.now(UTC)).days
    info.signature_algorithm = _signature_algorithm(cert)

    key = cert.public_key()
    info.key_type = type(key).__name__.strip("_").removesuffix("PublicKey")
    curve = getattr(key, "curve", None)
    info.key_bits = getattr(key, "key_size", None) or getattr(curve, "key_size", None)

    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        info.san = san.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        info.san = []
    info.hostname_ok = _hostname_matches(host, info.san, cert)


def _issuer_name(cert: x509.Certificate) -> str:
    for attr in (x509.NameOID.ORGANIZATION_NAME, x509.NameOID.COMMON_NAME):
        values = cert.issuer.get_attributes_for_oid(attr)
        if values:
            return str(values[0].value)
    return cert.issuer.rfc4514_string()


def _signature_algorithm(cert: x509.Certificate) -> str | None:
    try:
        algorithm = cert.signature_hash_algorithm
    except Exception:  # noqa: BLE001 - exotic algorithms raise here
        return None
    return algorithm.name if isinstance(algorithm, hashes.HashAlgorithm) else None


def _hostname_matches(host: str, san: list[str], cert: x509.Certificate) -> bool:
    names = list(san)
    if not names:
        common = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        names = [str(v.value) for v in common]
    for raw in names:
        name = raw.lower()
        if name == host:
            return True
        if name.startswith("*.") and host.split(".", 1)[-1] == name[2:]:
            return True
    return False


def _handshake(host: str, port: int, context: ssl.SSLContext, timeout: float) -> ssl.SSLSocket:
    sock = socket.create_connection((host, port), timeout)
    return context.wrap_socket(sock, server_hostname=host)


def inspect_tls(
    host: str,
    port: int = 443,
    timeout: float = 10.0,
    *,
    test_legacy: bool = True,
) -> TlsInfo:
    """Handshake once to read the certificate, once to judge trust, and optionally
    once more to see whether TLS 1.0/1.1 are still accepted. All passive."""
    info = TlsInfo()

    permissive = ssl.create_default_context()
    permissive.check_hostname = False
    permissive.verify_mode = ssl.CERT_NONE
    try:
        with _handshake(host, port, permissive, timeout) as tls:
            info.available = True
            info.negotiated_version = tls.version()
            cipher = tls.cipher()
            info.cipher = cipher[0] if cipher else None
            der = tls.getpeercert(binary_form=True)
        if der:
            _parse_certificate(der, host, info)
    except Exception as exc:  # noqa: BLE001
        info.error = describe(exc)
        return info

    strict = ssl.create_default_context()
    try:
        with _handshake(host, port, strict, timeout):
            info.trusted = True
    except ssl.SSLCertVerificationError as exc:
        info.trust_error = getattr(exc, "verify_message", None) or str(exc)
    except Exception as exc:  # noqa: BLE001
        info.trust_error = describe(exc)

    if test_legacy:
        info.legacy_versions, info.legacy_tested = _probe_legacy(host, port, timeout)

    return info


def _probe_legacy(host: str, port: int, timeout: float) -> tuple[list[str], bool]:
    """Ask whether TLS 1.0/1.1 still work. One handshake each, no data sent.

    Naming the deprecated versions is the entire point of the check, so Python's
    DeprecationWarning about them is noise here rather than a signal.
    """
    found: list[str] = []
    tested = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        legacy_versions = (ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1_1)

    for version in legacy_versions:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                context.set_ciphers("DEFAULT@SECLEVEL=0")
                context.minimum_version = version
                context.maximum_version = version
        except (ssl.SSLError, ValueError):
            # The local OpenSSL policy refuses to speak it, so this says nothing
            # about the server. Distros differ here - Ubuntu can ship a MinProtocol
            # that silently turns this check into a false all-clear.
            continue
        tested += 1
        try:
            with _handshake(host, port, context, timeout) as tls:
                negotiated = tls.version()
                if negotiated:
                    found.append(negotiated)
        except Exception:  # noqa: BLE001 - refusing legacy TLS is the good outcome
            pass

    # Nothing testable means we learned nothing. Reporting "switched off" here would
    # put a reassurance in a customer report that we never actually established.
    return found, tested > 0
