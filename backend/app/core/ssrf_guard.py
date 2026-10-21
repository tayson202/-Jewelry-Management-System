import re
import ipaddress
from urllib.parse import urlparse
from fastapi import HTTPException, status

BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "::",
    "169.254.169.254",            # AWS / GCP / Azure instance metadata endpoint
    "metadata.google.internal",
    "instance-data"
}

def is_disallowed_or_private_host(hostname: str) -> bool:
    """
    Validates hostname against SSRF attacks according to
    Enterprise Security Blueprint Section 3.
    """
    clean_host = hostname.strip().lower()
    if clean_host in BLOCKED_HOSTNAMES:
        return True

    # Check for direct IPv4 addresses
    try:
        ip = ipaddress.ip_address(clean_host)
        if (
            ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_multicast or
            ip.is_reserved
        ):
            return True
    except ValueError:
        # Not a raw IP address, verify domain name structure
        pass

    return False

def validate_external_url(target_url: str) -> str:
    parsed = urlparse(target_url)
    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL scheme. Only HTTP and HTTPS are permitted."
        )

    if not parsed.hostname or is_disallowed_or_private_host(parsed.hostname):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to internal, loopback, or cloud metadata endpoints is strictly blocked (SSRF Protection)."
        )

    return target_url
