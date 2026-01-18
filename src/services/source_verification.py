"""Source Verification System for ISR Platform.

Verifies the authenticity and legitimacy of information sources through
multiple verification methods including domain validation, identity checks,
and cross-referencing with trusted registries.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
import re


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class VerificationStatus(str, Enum):
    """Verification status levels."""
    VERIFIED = "VERIFIED"  # Fully verified
    PENDING = "PENDING"  # Verification in progress
    PARTIAL = "PARTIAL"  # Some checks passed
    FAILED = "FAILED"  # Verification failed
    REVOKED = "REVOKED"  # Previously verified, now revoked
    UNKNOWN = "UNKNOWN"  # Not yet verified


class VerificationMethod(str, Enum):
    """Methods used for verification."""
    DOMAIN_VALIDATION = "DOMAIN_VALIDATION"
    IDENTITY_DOCUMENT = "IDENTITY_DOCUMENT"
    PHONE_VERIFICATION = "PHONE_VERIFICATION"
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    GOVERNMENT_REGISTRY = "GOVERNMENT_REGISTRY"
    ORGANIZATIONAL_BADGE = "ORGANIZATIONAL_BADGE"
    THIRD_PARTY_VERIFICATION = "THIRD_PARTY_VERIFICATION"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    CROSS_REFERENCE = "CROSS_REFERENCE"


class SourceCategory(str, Enum):
    """Categories of sources."""
    GOVERNMENT_OFFICIAL = "GOVERNMENT_OFFICIAL"
    NEWS_MEDIA = "NEWS_MEDIA"
    INTERNATIONAL_ORG = "INTERNATIONAL_ORG"
    NGO_HUMANITARIAN = "NGO_HUMANITARIAN"
    ACADEMIC_RESEARCH = "ACADEMIC_RESEARCH"
    JOURNALIST = "JOURNALIST"
    ACTIVIST = "ACTIVIST"
    CITIZEN = "CITIZEN"
    BUSINESS = "BUSINESS"
    UNKNOWN = "UNKNOWN"


@dataclass
class VerificationCheck:
    """Individual verification check result."""
    check_id: UUID
    check_type: VerificationMethod
    status: str  # PASSED, FAILED, PENDING
    performed_at: datetime
    performed_by: str
    confidence: float  # 0-1
    details: str
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceIdentity:
    """Verified identity information for a source."""
    source_id: str
    display_name: str
    legal_name: str | None = None
    category: SourceCategory = SourceCategory.UNKNOWN
    
    # Contact information
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    
    # Location
    country: str | None = None
    city: str | None = None
    address: str | None = None
    
    # Organization details
    organization: str | None = None
    position: str | None = None
    department: str | None = None
    
    # Registration/licensing
    registration_number: str | None = None
    license_number: str | None = None
    tax_id: str | None = None
    
    # Social media
    twitter_handle: str | None = None
    telegram_username: str | None = None
    facebook_page: str | None = None
    
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationRecord:
    """Complete verification record for a source."""
    record_id: UUID
    source_id: str
    identity: SourceIdentity
    status: VerificationStatus
    verification_level: int  # 1-5, higher is more verified
    created_at: datetime
    verified_at: datetime | None = None
    expires_at: datetime | None = None
    verified_by: str | None = None
    
    # Verification checks performed
    checks: list[VerificationCheck] = field(default_factory=list)
    
    # Verification scores
    identity_confidence: float = 0.0  # 0-1
    legitimacy_score: float = 0.0  # 0-1
    authenticity_score: float = 0.0  # 0-1
    
    # Badges and certifications
    badges: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    
    # Notes and warnings
    notes: str = ""
    warnings: list[str] = field(default_factory=list)
    
    # Audit trail
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class VerificationRequest:
    """Request for source verification."""
    request_id: UUID
    source_id: str
    requested_by: str
    requested_at: datetime
    priority: str  # HIGH, MEDIUM, LOW
    reason: str
    methods_requested: list[VerificationMethod]
    status: str  # PENDING, IN_PROGRESS, COMPLETED, REJECTED
    assigned_to: str | None = None
    notes: str = ""


class SourceVerificationService:
    """Service for verifying source authenticity and legitimacy."""

    def __init__(self):
        """Initialize source verification service."""
        self.verification_records: dict[str, VerificationRecord] = {}
        self.verification_requests: dict[UUID, VerificationRequest] = {}
        
        # Trusted registries (would be loaded from database/external APIs)
        self.government_domains = {
            "gov.af", "gov.pk", "gov.ir", "un.org", "nato.int",
        }
        
        self.verified_news_orgs = {
            "reuters.com", "apnews.com", "bbc.com", "cnn.com",
            "aljazeera.com", "nytimes.com", "theguardian.com",
        }
        
        self.verified_ngos = {
            "unhcr.org", "wfp.org", "icrc.org", "msf.org",
            "redcross.org", "savethechildren.org", "unicef.org",
        }
        
        # Verification thresholds
        self.min_checks_for_verification = 3
        self.min_confidence_threshold = 0.7
        self.verification_validity_days = 365  # 1 year
    
    def verify_source(
        self,
        source_id: str,
        identity: SourceIdentity,
        methods: list[VerificationMethod],
        verified_by: str,
    ) -> VerificationRecord:
        """Perform comprehensive source verification."""
        # Create or get existing record
        if source_id in self.verification_records:
            record = self.verification_records[source_id]
            record.history.append({
                "action": "reverification",
                "timestamp": utcnow().isoformat(),
                "by": verified_by,
            })
        else:
            record = VerificationRecord(
                record_id=uuid4(),
                source_id=source_id,
                identity=identity,
                status=VerificationStatus.PENDING,
                verification_level=0,
                created_at=utcnow(),
            )
        
        # Perform verification checks
        checks = []
        for method in methods:
            check = self._perform_verification_check(source_id, identity, method, verified_by)
            checks.append(check)
        
        record.checks.extend(checks)
        
        # Calculate verification scores
        record.identity_confidence = self._calculate_identity_confidence(checks)
        record.legitimacy_score = self._calculate_legitimacy_score(identity, checks)
        record.authenticity_score = self._calculate_authenticity_score(checks)
        
        # Determine verification status
        passed_checks = sum(1 for c in checks if c.status == "PASSED")
        failed_checks = sum(1 for c in checks if c.status == "FAILED")
        
        if passed_checks >= self.min_checks_for_verification and record.identity_confidence >= self.min_confidence_threshold:
            record.status = VerificationStatus.VERIFIED
            record.verified_at = utcnow()
            record.verified_by = verified_by
            record.expires_at = utcnow() + timedelta(days=self.verification_validity_days)
            record.verification_level = min(5, passed_checks)
        elif failed_checks > 0:
            record.status = VerificationStatus.FAILED
        elif passed_checks > 0:
            record.status = VerificationStatus.PARTIAL
        else:
            record.status = VerificationStatus.PENDING
        
        # Assign badges
        record.badges = self._assign_badges(identity, record.status, record.verification_level)
        
        # Generate warnings
        record.warnings = self._generate_warnings(identity, checks)
        
        self.verification_records[source_id] = record
        return record
    
    def _perform_verification_check(
        self,
        source_id: str,
        identity: SourceIdentity,
        method: VerificationMethod,
        performed_by: str,
    ) -> VerificationCheck:
        """Perform a specific verification check."""
        check = VerificationCheck(
            check_id=uuid4(),
            check_type=method,
            status="PENDING",
            performed_at=utcnow(),
            performed_by=performed_by,
            confidence=0.0,
            details="",
        )
        
        if method == VerificationMethod.DOMAIN_VALIDATION:
            result = self._check_domain_validation(identity)
            check.status = result["status"]
            check.confidence = result["confidence"]
            check.details = result["details"]
            check.evidence = result["evidence"]
        
        elif method == VerificationMethod.EMAIL_VERIFICATION:
            result = self._check_email_verification(identity)
            check.status = result["status"]
            check.confidence = result["confidence"]
            check.details = result["details"]
        
        elif method == VerificationMethod.GOVERNMENT_REGISTRY:
            result = self._check_government_registry(identity)
            check.status = result["status"]
            check.confidence = result["confidence"]
            check.details = result["details"]
        
        elif method == VerificationMethod.ORGANIZATIONAL_BADGE:
            result = self._check_organizational_badge(identity)
            check.status = result["status"]
            check.confidence = result["confidence"]
            check.details = result["details"]
        
        elif method == VerificationMethod.CROSS_REFERENCE:
            result = self._check_cross_reference(source_id, identity)
            check.status = result["status"]
            check.confidence = result["confidence"]
            check.details = result["details"]
        
        else:
            # Default for manual methods
            check.status = "PENDING"
            check.confidence = 0.5
            check.details = f"Manual verification required for {method.value}"
        
        return check
    
    def _check_domain_validation(self, identity: SourceIdentity) -> dict[str, Any]:
        """Validate source domain."""
        if not identity.website:
            return {
                "status": "FAILED",
                "confidence": 0.0,
                "details": "No website provided",
                "evidence": [],
            }
        
        # Extract domain
        domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', identity.website)
        if not domain_match:
            return {
                "status": "FAILED",
                "confidence": 0.0,
                "details": "Invalid website format",
                "evidence": [],
            }
        
        domain = domain_match.group(1).lower()
        
        # Check against trusted registries
        if domain in self.government_domains:
            return {
                "status": "PASSED",
                "confidence": 0.95,
                "details": f"Domain {domain} is a verified government domain",
                "evidence": ["Government registry match"],
            }
        
        if domain in self.verified_news_orgs:
            return {
                "status": "PASSED",
                "confidence": 0.9,
                "details": f"Domain {domain} is a verified news organization",
                "evidence": ["News organization registry match"],
            }
        
        if domain in self.verified_ngos:
            return {
                "status": "PASSED",
                "confidence": 0.9,
                "details": f"Domain {domain} is a verified NGO/humanitarian organization",
                "evidence": ["NGO registry match"],
            }
        
        # Domain exists but not in trusted registries
        return {
            "status": "PARTIAL",
            "confidence": 0.5,
            "details": f"Domain {domain} not in trusted registries",
            "evidence": [],
        }
    
    def _check_email_verification(self, identity: SourceIdentity) -> dict[str, Any]:
        """Verify email address."""
        if not identity.email:
            return {
                "status": "FAILED",
                "confidence": 0.0,
                "details": "No email provided",
            }
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, identity.email):
            return {
                "status": "FAILED",
                "confidence": 0.0,
                "details": "Invalid email format",
            }
        
        # Check domain
        domain = identity.email.split('@')[1].lower()
        
        if domain in self.government_domains or domain in self.verified_news_orgs or domain in self.verified_ngos:
            return {
                "status": "PASSED",
                "confidence": 0.85,
                "details": f"Email from verified domain: {domain}",
            }
        
        return {
            "status": "PARTIAL",
            "confidence": 0.6,
            "details": "Email format valid but domain not verified",
        }
    
    def _check_government_registry(self, identity: SourceIdentity) -> dict[str, Any]:
        """Check against government registries."""
        # In production, would query actual government APIs/databases
        
        if identity.category == SourceCategory.GOVERNMENT_OFFICIAL:
            if identity.registration_number or identity.department:
                return {
                    "status": "PASSED",
                    "confidence": 0.8,
                    "details": "Government official credentials provided",
                }
        
        return {
            "status": "PENDING",
            "confidence": 0.5,
            "details": "Manual verification required for government registry",
        }
    
    def _check_organizational_badge(self, identity: SourceIdentity) -> dict[str, Any]:
        """Check for organizational badges and credentials."""
        badges_found = []
        
        # Check for journalist credentials
        if identity.category == SourceCategory.JOURNALIST:
            if identity.license_number or identity.organization:
                badges_found.append("Press credentials")
        
        # Check for academic credentials
        if identity.category == SourceCategory.ACADEMIC_RESEARCH:
            if identity.organization:
                badges_found.append("Academic affiliation")
        
        # Check for NGO credentials
        if identity.category == SourceCategory.NGO_HUMANITARIAN:
            if identity.registration_number:
                badges_found.append("NGO registration")
        
        if badges_found:
            return {
                "status": "PASSED",
                "confidence": 0.75,
                "details": f"Organizational badges verified: {', '.join(badges_found)}",
            }
        
        return {
            "status": "PARTIAL",
            "confidence": 0.5,
            "details": "No organizational badges found",
        }
    
    def _check_cross_reference(self, source_id: str, identity: SourceIdentity) -> dict[str, Any]:
        """Cross-reference with other verified sources."""
        # In production, would check if source is mentioned/cited by verified sources
        
        # Simplified check
        if identity.category in [SourceCategory.GOVERNMENT_OFFICIAL, SourceCategory.INTERNATIONAL_ORG]:
            return {
                "status": "PASSED",
                "confidence": 0.7,
                "details": "Source category typically cross-referenced",
            }
        
        return {
            "status": "PARTIAL",
            "confidence": 0.5,
            "details": "Limited cross-reference data available",
        }
    
    def _calculate_identity_confidence(self, checks: list[VerificationCheck]) -> float:
        """Calculate overall identity confidence."""
        if not checks:
            return 0.0
        
        passed_checks = [c for c in checks if c.status == "PASSED"]
        if not passed_checks:
            return 0.3  # Low confidence
        
        avg_confidence = sum(c.confidence for c in passed_checks) / len(passed_checks)
        return avg_confidence
    
    def _calculate_legitimacy_score(
        self,
        identity: SourceIdentity,
        checks: list[VerificationCheck],
    ) -> float:
        """Calculate source legitimacy score."""
        score = 0.5  # Baseline
        
        # Category-based adjustment
        high_trust_categories = [
            SourceCategory.GOVERNMENT_OFFICIAL,
            SourceCategory.INTERNATIONAL_ORG,
            SourceCategory.NEWS_MEDIA,
            SourceCategory.ACADEMIC_RESEARCH,
        ]
        
        if identity.category in high_trust_categories:
            score += 0.2
        
        # Passed checks boost score
        passed_checks = sum(1 for c in checks if c.status == "PASSED")
        score += passed_checks * 0.1
        
        # Contact information completeness
        contact_fields = [identity.email, identity.phone, identity.website]
        completeness = sum(1 for f in contact_fields if f) / len(contact_fields)
        score += completeness * 0.1
        
        return min(1.0, score)
    
    def _calculate_authenticity_score(self, checks: list[VerificationCheck]) -> float:
        """Calculate authenticity score."""
        if not checks:
            return 0.0
        
        passed = sum(1 for c in checks if c.status == "PASSED")
        failed = sum(1 for c in checks if c.status == "FAILED")
        
        if failed > passed:
            return 0.2
        
        return min(1.0, passed / len(checks))
    
    def _assign_badges(
        self,
        identity: SourceIdentity,
        status: VerificationStatus,
        level: int,
    ) -> list[str]:
        """Assign verification badges."""
        badges = []
        
        if status == VerificationStatus.VERIFIED:
            badges.append("Verified")
            
            if level >= 4:
                badges.append("Highly Verified")
            
            # Category-specific badges
            if identity.category == SourceCategory.GOVERNMENT_OFFICIAL:
                badges.append("Government Official")
            elif identity.category == SourceCategory.NEWS_MEDIA:
                badges.append("Verified Media")
            elif identity.category == SourceCategory.INTERNATIONAL_ORG:
                badges.append("International Organization")
            elif identity.category == SourceCategory.NGO_HUMANITARIAN:
                badges.append("Verified NGO")
            elif identity.category == SourceCategory.ACADEMIC_RESEARCH:
                badges.append("Academic")
        
        return badges
    
    def _generate_warnings(
        self,
        identity: SourceIdentity,
        checks: list[VerificationCheck],
    ) -> list[str]:
        """Generate verification warnings."""
        warnings = []
        
        failed_checks = [c for c in checks if c.status == "FAILED"]
        if failed_checks:
            warnings.append(f"{len(failed_checks)} verification check(s) failed")
        
        if not identity.email and not identity.phone:
            warnings.append("No contact information provided")
        
        if not identity.website:
            warnings.append("No website provided")
        
        return warnings
    
    def request_verification(
        self,
        source_id: str,
        requested_by: str,
        priority: str,
        reason: str,
        methods: list[VerificationMethod],
    ) -> VerificationRequest:
        """Submit a verification request."""
        request = VerificationRequest(
            request_id=uuid4(),
            source_id=source_id,
            requested_by=requested_by,
            requested_at=utcnow(),
            priority=priority,
            reason=reason,
            methods_requested=methods,
            status="PENDING",
        )
        
        self.verification_requests[request.request_id] = request
        return request
    
    def revoke_verification(
        self,
        source_id: str,
        reason: str,
        revoked_by: str,
    ) -> bool:
        """Revoke source verification."""
        if source_id not in self.verification_records:
            return False
        
        record = self.verification_records[source_id]
        record.status = VerificationStatus.REVOKED
        record.history.append({
            "action": "revoked",
            "timestamp": utcnow().isoformat(),
            "by": revoked_by,
            "reason": reason,
        })
        
        return True
    
    def get_verification_record(self, source_id: str) -> VerificationRecord | None:
        """Get verification record for a source."""
        return self.verification_records.get(source_id)
    
    def is_verified(self, source_id: str) -> bool:
        """Check if source is verified."""
        record = self.verification_records.get(source_id)
        if not record:
            return False
        
        # Check if verified and not expired
        if record.status != VerificationStatus.VERIFIED:
            return False
        
        if record.expires_at and record.expires_at < utcnow():
            return False
        
        return True
    
    def get_verification_level(self, source_id: str) -> int:
        """Get verification level (1-5)."""
        record = self.verification_records.get(source_id)
        return record.verification_level if record else 0
    
    def list_verification_requests(
        self,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[VerificationRequest]:
        """List verification requests with filters."""
        requests = list(self.verification_requests.values())
        
        if status:
            requests = [r for r in requests if r.status == status]
        
        if priority:
            requests = [r for r in requests if r.priority == priority]
        
        # Sort by priority and date
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        requests.sort(key=lambda r: (priority_order.get(r.priority, 3), r.requested_at))
        
        return requests
    
    def get_stats(self) -> dict[str, Any]:
        """Get verification statistics."""
        return {
            "total_records": len(self.verification_records),
            "verified_sources": sum(
                1 for r in self.verification_records.values()
                if r.status == VerificationStatus.VERIFIED
            ),
            "pending_requests": sum(
                1 for r in self.verification_requests.values()
                if r.status == "PENDING"
            ),
            "verification_distribution": {
                status.value: sum(
                    1 for r in self.verification_records.values()
                    if r.status == status
                )
                for status in VerificationStatus
            },
            "verification_levels": {
                f"level_{i}": sum(
                    1 for r in self.verification_records.values()
                    if r.verification_level == i
                )
                for i in range(6)
            },
        }


# Global instance
_verification_service: SourceVerificationService | None = None


def get_verification_service() -> SourceVerificationService:
    """Get the source verification service instance."""
    global _verification_service
    if _verification_service is None:
        _verification_service = SourceVerificationService()
    return _verification_service
