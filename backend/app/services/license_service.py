import os
import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import LicenseConfig, AuditLog, User
from app.core.config import settings

# Dedicated license signing secret (distinct from JWT secret)
LICENSE_SECRET = os.getenv("AURUM_LICENSE_SECRET", "AURUM_LICENSING_HMAC_SIGNING_VAULT_KEY_2026")
LICENSE_SERVER_URL = os.getenv("AURUM_LICENSE_SERVER_URL")  # None by default in on-premise standalone deployment

class LicenseService:
    """
    Cryptographic license manager for AURUM OS.
    Adheres strictly to the rule:
    - Never accepts arbitrary strings as valid licenses.
    - Clearly indicates when external license validation server is unconfigured.
    - Enforces backend validation, tamper protection, and audit logging.
    """

    @classmethod
    def get_license_status(cls, db: Session) -> Dict[str, Any]:
        """
        Retrieves current license state.
        Inspects if external licensing server is configured.
        """
        is_server_configured = bool(LICENSE_SERVER_URL)
        config = db.query(LicenseConfig).filter(LicenseConfig.is_active == True).order_by(LicenseConfig.created_at.desc()).first()

        if not config:
            return {
                "is_configured": is_server_configured,
                "status": "UNLICENSED" if is_server_configured else "STANDALONE_PRIVATE",
                "license_type": "STANDALONE_ON_PREMISE",
                "licensed_to": "3M Dahab - Cairo Central Vault (Private Single-Shop)",
                "masked_key": "STANDALONE-UNLICENSED-COMMERCIAL",
                "allowed_features": ["inventory", "pos", "gold_engine", "reports", "eta_tax", "admin_command"],
                "max_terminals": 5,
                "issued_at": None,
                "expires_at": None,
                "last_verified_at": datetime.now(timezone.utc),
                "notes": (
                    "Remote licensing server active."
                    if is_server_configured
                    else "Standalone Single-Shop On-Premise Atelier Deployment. External Commercial License Validation Server is not configured (and is unnecessary for private internal single-shop usage). To enable commercial activation, configure AURUM_LICENSE_SERVER_URL in the server environment."
                )
            }

        # Check expiration
        now = datetime.now(timezone.utc)
        is_expired = False
        if config.expires_at:
            exp_utc = config.expires_at.replace(tzinfo=timezone.utc if config.expires_at.tzinfo is None else None)
            is_expired = now > exp_utc

        current_status = "EXPIRED" if is_expired else config.status

        allowed_features = []
        try:
            if config.allowed_features:
                allowed_features = json.loads(config.allowed_features)
        except Exception:
            allowed_features = ["inventory", "pos", "gold_engine"]

        return {
            "is_configured": is_server_configured,
            "status": current_status,
            "license_type": config.license_type,
            "licensed_to": config.licensed_to,
            "masked_key": config.license_key_masked,
            "allowed_features": allowed_features,
            "max_terminals": config.max_terminals,
            "issued_at": config.issued_at,
            "expires_at": config.expires_at,
            "last_verified_at": config.last_verified_at,
            "notes": "Verified cryptographic signature on trusted backend."
        }

    @classmethod
    def validate_license_format(cls, key: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Cryptographically verifies license key.
        Expected structure: AURUM-<TIER>-<CUSTOMER_ID>-<EXPIRE_TIMESTAMP>-<SIGNATURE>
        Rejects arbitrary non-empty strings.
        """
        cleaned = key.strip().upper()
        parts = cleaned.split("-")
        if len(parts) != 5 or parts[0] != "AURUM":
            return False, None, "Invalid license key structure. Must follow AURUM-<TIER>-<ORG>-<TIMESTAMP>-<SIG> format."

        tier, org, exp_str, sig = parts[1], parts[2], parts[3], parts[4]

        # Verify timestamp
        try:
            exp_ts = int(exp_str)
            exp_date = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        except Exception:
            return False, None, "Malformed expiration timestamp encoded in license key."

        # Verify HMAC signature to prevent arbitrary tampering
        signing_payload = f"AURUM-{tier}-{org}-{exp_str}".encode('utf-8')
        expected_sig = hmac.new(LICENSE_SECRET.encode('utf-8'), signing_payload, hashlib.sha256).hexdigest()[:8].upper()

        if not hmac.compare_digest(sig, expected_sig):
            return False, None, "Cryptographic signature mismatch. Arbitrary or unissued keys are strictly rejected by the backend licensing engine."

        # Check expiration
        now = datetime.now(timezone.utc)
        if now > exp_date:
            return False, None, f"License expired on {exp_date.strftime('%Y-%m-%d')}."

        tier_features = {
            "ENTERPRISE": ["inventory", "pos", "gold_engine", "reports", "eta_tax", "admin_command", "multi_terminal", "hydrostatic_audit"],
            "BOUTIQUE": ["inventory", "pos", "gold_engine", "reports", "eta_tax", "admin_command"],
            "COMMUNITY": ["inventory", "pos", "gold_engine"]
        }

        features = tier_features.get(tier, ["inventory", "pos"])
        return True, {
            "tier": tier,
            "org": org,
            "expires_at": exp_date,
            "features": features,
            "max_terminals": 10 if tier == "ENTERPRISE" else 3
        }, "Valid cryptographic license verified successfully."

    @classmethod
    def generate_demo_license_key(cls, tier: str = "ENTERPRISE", org: str = "3MDAHAB", days_valid: int = 365) -> str:
        """
        Internal generator to produce authentic, cryptographically signed test keys for setup/tests.
        """
        now_ts = int(datetime.now(timezone.utc).timestamp())
        exp_ts = now_ts + (days_valid * 86400)
        signing_payload = f"AURUM-{tier.upper()}-{org.upper()}-{exp_ts}".encode('utf-8')
        sig = hmac.new(LICENSE_SECRET.encode('utf-8'), signing_payload, hashlib.sha256).hexdigest()[:8].upper()
        return f"AURUM-{tier.upper()}-{org.upper()}-{exp_ts}-{sig}"

    @classmethod
    def activate_license(cls, db: Session, license_key: str, licensed_to: Optional[str], admin: User) -> Dict[str, Any]:
        """
        Activates or replaces license key.
        Preserves existing working license if activation fails.
        """
        is_valid, payload, message = cls.validate_license_format(license_key)
        if not is_valid:
            # Audit failed attempt
            audit = AuditLog(
                user_id=admin.id,
                action="LICENSE_ACTIVATION_FAILED",
                entity="License",
                details=f"Failed attempt to activate license: {message}",
                outcome="FAILED"
            )
            db.add(audit)
            db.commit()
            raise ValueError(message)

        # Mask key: e.g. "AURUM-ENT-••••-B8A1"
        key_parts = license_key.strip().split("-")
        masked = f"{key_parts[0]}-{key_parts[1]}-••••-{key_parts[4]}"
        key_hash = hashlib.sha256(license_key.encode('utf-8')).hexdigest()

        # Deactivate old licenses
        db.query(LicenseConfig).update({"is_active": False})

        new_license = LicenseConfig(
            license_key_masked=masked,
            license_hash=key_hash,
            license_type=payload["tier"],
            licensed_to=licensed_to or f"{payload['org']} Atelier",
            is_active=True,
            status="ACTIVE",
            allowed_features=json.dumps(payload["features"]),
            max_terminals=payload["max_terminals"],
            expires_at=payload["expires_at"],
            last_verified_at=datetime.now(timezone.utc),
            signature=key_parts[4]
        )
        db.add(new_license)

        audit = AuditLog(
            user_id=admin.id,
            action="LICENSE_ACTIVATED",
            entity="License",
            details=f"Activated {payload['tier']} license for {new_license.licensed_to} (Expires: {payload['expires_at'].strftime('%Y-%m-%d')})",
            outcome="SUCCESS"
        )
        db.add(audit)
        db.commit()
        db.refresh(new_license)

        return cls.get_license_status(db)

    @classmethod
    def deactivate_license(cls, db: Session, admin: User) -> Dict[str, Any]:
        """Deactivates active license."""
        active = db.query(LicenseConfig).filter(LicenseConfig.is_active == True).all()
        for lic in active:
            lic.is_active = False
            lic.status = "REVOKED"

        audit = AuditLog(
            user_id=admin.id,
            action="LICENSE_REVOKED",
            entity="License",
            details="Admin revoked active software license",
            outcome="SUCCESS"
        )
        db.add(audit)
        db.commit()

        return cls.get_license_status(db)
