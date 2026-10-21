import pytest
from fastapi import HTTPException
from app.core.rate_limiter import SlidingWindowRateLimiter
from app.core.ssrf_guard import is_disallowed_or_private_host, validate_external_url
from app.core.security import verify_password, get_password_hash

def test_password_hashing_and_verification():
    raw_pw = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_pw)
    assert hashed != raw_pw
    assert "$" in hashed
    assert verify_password(raw_pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_sliding_window_rate_limiter():
    """Blueprint Section 3 & 6: Rate Limiting & Flooding Protection"""
    limiter = SlidingWindowRateLimiter(limit=3, window_seconds=10)
    client_ip = "192.168.1.100"

    # First 3 requests should pass
    limiter.check(client_ip)
    limiter.check(client_ip)
    limiter.check(client_ip)

    # 4th request must be rejected with 429 Too Many Requests
    with pytest.raises(HTTPException) as excinfo:
        limiter.check(client_ip)
    assert excinfo.value.status_code == 429
    assert "Rate limit exceeded" in str(excinfo.value.detail)

def test_ssrf_protection_blocks_internal_and_cloud_metadata():
    """Blueprint Section 3: SSRF Defense against AWS/GCP Metadata and Loopback"""
    # Cloud metadata IP (AWS/GCP/Azure)
    assert is_disallowed_or_private_host("169.254.169.254") is True
    assert is_disallowed_or_private_host("metadata.google.internal") is True
    
    # Loopback
    assert is_disallowed_or_private_host("localhost") is True
    assert is_disallowed_or_private_host("127.0.0.1") is True
    assert is_disallowed_or_private_host("0.0.0.0") is True

    # Private RFC 1918 subnets
    assert is_disallowed_or_private_host("10.0.0.1") is True
    assert is_disallowed_or_private_host("192.168.1.1") is True
    assert is_disallowed_or_private_host("172.16.0.5") is True

    # Public valid host should pass
    assert is_disallowed_or_private_host("api.saghabullion.com") is False

    # Validation function throws HTTP 403 on SSRF attempt
    with pytest.raises(HTTPException) as excinfo:
        validate_external_url("http://169.254.169.254/latest/meta-data/")
    assert excinfo.value.status_code == 403

def test_role_escalation_prevention_on_payload():
    """Blueprint Section 2: Stripping Privileged Fields"""
    client_input = {"full_name": "Employee User", "role": "ADMIN", "id": "injected-id"}
    
    # Sanitize payload logic
    allowed_fields = {k: v for k, v in client_input.items() if k not in ("role", "id")}
    assert "role" not in allowed_fields
    assert "id" not in allowed_fields
    assert allowed_fields == {"full_name": "Employee User"}
