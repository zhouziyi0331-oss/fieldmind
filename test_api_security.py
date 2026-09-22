"""
Comprehensive test suite for API Security & Rate Limiting
Phase 5.3: API Security
"""

import pytest
import time
import secrets
from datetime import datetime, timedelta

# Rate Limiting Tests
from app.core.security.rate_limiting import (
    RateLimitAlgorithm,
    RateLimitScope,
    RateLimitConfig,
    RateLimiter,
    MultiScopeRateLimiter,
    create_rate_limit_key,
    initialize_rate_limiting,
)

# Request Signing Tests
from app.core.security.request_signing import (
    SignatureAlgorithm,
    SignatureConfig,
    SignatureComponents,
    RequestSigner,
    MultiKeyRequestSigner,
    initialize_request_signing,
)

# CORS Tests
from app.core.security.cors import (
    CORSPreset,
    CORSConfig,
    CORSValidator,
    get_preset_config,
    create_origin_validator,
)

# CSRF Tests
from app.core.security.csrf import (
    CSRFProtectionMethod,
    SameSitePolicy,
    CSRFConfig,
    CSRFProtection,
)

# Security Headers Tests
from app.core.security.headers import (
    ContentSecurityPolicy,
    HSTSConfig,
    PermissionsPolicy,
    SecurityHeadersConfig,
    SecurityHeaders,
    XFrameOptions,
    ReferrerPolicy,
    get_strict_config,
    get_balanced_config,
)


# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestTokenBucketRateLimiter:
    """Test token bucket algorithm."""

    def test_basic_rate_limiting(self):
        """Test basic token bucket rate limiting."""
        config = RateLimitConfig(
            max_requests=10,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        limiter = RateLimiter(config)

        # Should allow first 10 requests
        for i in range(10):
            result = limiter.check_rate_limit("user:123")
            assert result.allowed
            # Remaining decreases with each request
            assert result.remaining >= 0

        # Should deny 11th request
        result = limiter.check_rate_limit("user:123")
        assert not result.allowed
        assert result.retry_after is not None

    def test_token_refill(self):
        """Test token refill over time."""
        config = RateLimitConfig(
            max_requests=5,
            window_seconds=1,  # 5 tokens per second
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        limiter = RateLimiter(config)

        # Use all tokens
        for _ in range(5):
            result = limiter.check_rate_limit("user:123")
            assert result.allowed

        # Should be denied
        result = limiter.check_rate_limit("user:123")
        assert not result.allowed

        # Wait for refill
        time.sleep(0.5)

        # Should have ~2-3 tokens refilled
        result = limiter.check_rate_limit("user:123")
        assert result.allowed

    def test_burst_tolerance(self):
        """Test burst tolerance with custom burst size."""
        config = RateLimitConfig(
            max_requests=10,
            window_seconds=60,
            burst_size=20,  # Allow bursts up to 20
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        limiter = RateLimiter(config)

        # Should allow burst of 20 requests
        for i in range(20):
            result = limiter.check_rate_limit("user:123")
            assert result.allowed

        # 21st should be denied
        result = limiter.check_rate_limit("user:123")
        assert not result.allowed

    def test_different_keys(self):
        """Test rate limiting with different keys."""
        config = RateLimitConfig(
            max_requests=5,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        limiter = RateLimiter(config)

        # User 1 uses all tokens
        for _ in range(5):
            result = limiter.check_rate_limit("user:1")
            assert result.allowed

        # User 1 denied
        result = limiter.check_rate_limit("user:1")
        assert not result.allowed

        # User 2 still has tokens
        result = limiter.check_rate_limit("user:2")
        assert result.allowed


class TestSlidingWindowRateLimiter:
    """Test sliding window algorithm."""

    def test_basic_sliding_window(self):
        """Test basic sliding window rate limiting."""
        config = RateLimitConfig(
            max_requests=10,
            window_seconds=2,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )
        limiter = RateLimiter(config)

        # Should allow 10 requests
        for i in range(10):
            result = limiter.check_rate_limit("user:123")
            assert result.allowed
            assert result.remaining == 9 - i

        # Should deny 11th
        result = limiter.check_rate_limit("user:123")
        assert not result.allowed

    def test_window_sliding(self):
        """Test that old requests slide out of window."""
        config = RateLimitConfig(
            max_requests=5,
            window_seconds=1,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )
        limiter = RateLimiter(config)

        # Use all requests
        for _ in range(5):
            result = limiter.check_rate_limit("user:123")
            assert result.allowed

        # Should be denied
        result = limiter.check_rate_limit("user:123")
        assert not result.allowed

        # Wait for window to slide
        time.sleep(1.1)

        # Old requests should have slid out
        result = limiter.check_rate_limit("user:123")
        assert result.allowed


class TestFixedWindowRateLimiter:
    """Test fixed window algorithm."""

    def test_basic_fixed_window(self):
        """Test basic fixed window rate limiting."""
        config = RateLimitConfig(
            max_requests=10,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.FIXED_WINDOW
        )
        limiter = RateLimiter(config)

        # Should allow 10 requests
        for i in range(10):
            result = limiter.check_rate_limit("user:123")
            assert result.allowed

        # Should deny 11th
        result = limiter.check_rate_limit("user:123")
        assert not result.allowed

    def test_window_reset(self):
        """Test that counter resets after window expires."""
        config = RateLimitConfig(
            max_requests=5,
            window_seconds=1,
            algorithm=RateLimitAlgorithm.FIXED_WINDOW
        )
        limiter = RateLimiter(config)

        # Use all requests
        for _ in range(5):
            result = limiter.check_rate_limit("user:123")
            assert result.allowed

        # Should be denied
        result = limiter.check_rate_limit("user:123")
        assert not result.allowed

        # Wait for window reset
        time.sleep(1.1)

        # Should be allowed again
        result = limiter.check_rate_limit("user:123")
        assert result.allowed


class TestMultiScopeRateLimiter:
    """Test multi-scope rate limiter."""

    def test_multiple_scopes(self):
        """Test rate limiting across multiple scopes."""
        limiter = MultiScopeRateLimiter({
            RateLimitScope.USER: RateLimitConfig(100, 60),
            RateLimitScope.IP: RateLimitConfig(1000, 60),
            RateLimitScope.ENDPOINT: RateLimitConfig(10, 1)
        })

        identifiers = {
            RateLimitScope.USER: "user:123",
            RateLimitScope.IP: "192.168.1.1",
            RateLimitScope.ENDPOINT: "/api/users"
        }

        # Should check all scopes
        result = limiter.check_all(identifiers)
        assert result.allowed

    def test_most_restrictive_scope(self):
        """Test that most restrictive scope is applied."""
        limiter = MultiScopeRateLimiter({
            RateLimitScope.USER: RateLimitConfig(100, 60),
            RateLimitScope.ENDPOINT: RateLimitConfig(5, 60)  # More restrictive
        })

        identifiers = {
            RateLimitScope.USER: "user:123",
            RateLimitScope.ENDPOINT: "/api/heavy"
        }

        # Exhaust endpoint limit
        for _ in range(5):
            result = limiter.check_all(identifiers)
            assert result.allowed

        # Should be denied by endpoint limit
        result = limiter.check_all(identifiers)
        assert not result.allowed


class TestRateLimitUtilities:
    """Test rate limiting utility functions."""

    def test_create_rate_limit_key(self):
        """Test rate limit key creation."""
        key = create_rate_limit_key(
            RateLimitScope.USER,
            "user123",
            "/api/users"
        )
        assert key.startswith("ratelimit:user:")
        assert len(key) > 20

    def test_global_rate_limiter_initialization(self):
        """Test global rate limiter initialization."""
        limiter = initialize_rate_limiting()
        assert limiter is not None

        # Check default scopes
        result = limiter.check(RateLimitScope.USER, "test_user")
        assert result.allowed


# ============================================================================
# Request Signing Tests
# ============================================================================

class TestRequestSigner:
    """Test HMAC request signature generation and verification."""

    def test_sign_and_verify(self):
        """Test basic sign and verify."""
        signer = RequestSigner("secret-key-123")

        timestamp = str(int(time.time()))
        nonce = "abc123"

        signature = signer.sign_request(
            method="POST",
            path="/api/users",
            body=b'{"name":"Alice"}',
            timestamp=timestamp,
            nonce=nonce
        )

        result = signer.verify_request(
            method="POST",
            path="/api/users",
            signature=signature,
            body=b'{"name":"Alice"}',
            timestamp=timestamp,
            nonce=nonce
        )

        assert result.valid

    def test_tampered_body_fails(self):
        """Test that tampered body fails verification."""
        signer = RequestSigner("secret-key-123")

        timestamp = str(int(time.time()))
        nonce = "abc123-unique"

        signature = signer.sign_request(
            method="POST",
            path="/api/users",
            body=b'{"name":"Alice"}',
            timestamp=timestamp,
            nonce=nonce
        )

        # Verify with different body
        result = signer.verify_request(
            method="POST",
            path="/api/users",
            signature=signature,
            body=b'{"name":"Bob"}',  # Changed!
            timestamp=timestamp,
            nonce=nonce
        )

        assert not result.valid
        assert result.reason  # Should have a reason

    def test_timestamp_validation(self):
        """Test timestamp validation prevents replay attacks."""
        signer = RequestSigner(
            "secret-key-123",
            SignatureConfig(timestamp_tolerance=60)
        )

        # Old timestamp (more than 60 seconds ago)
        old_timestamp = str(int(time.time()) - 120)

        signature = signer.sign_request(
            method="GET",
            path="/api/data",
            timestamp=old_timestamp,
            nonce="abc123"
        )

        result = signer.verify_request(
            method="GET",
            path="/api/data",
            signature=signature,
            timestamp=old_timestamp,
            nonce="abc123"
        )

        assert not result.valid
        assert "timestamp" in result.reason.lower()

    def test_nonce_replay_prevention(self):
        """Test nonce prevents replay attacks."""
        signer = RequestSigner("secret-key-123")

        timestamp = str(int(time.time()))
        nonce = "unique-nonce-123"

        signature = signer.sign_request(
            method="GET",
            path="/api/data",
            timestamp=timestamp,
            nonce=nonce
        )

        # First verification should succeed
        result1 = signer.verify_request(
            method="GET",
            path="/api/data",
            signature=signature,
            timestamp=timestamp,
            nonce=nonce
        )
        assert result1.valid

        # Second verification with same nonce should fail
        result2 = signer.verify_request(
            method="GET",
            path="/api/data",
            signature=signature,
            timestamp=timestamp,
            nonce=nonce
        )
        assert not result2.valid
        assert "nonce" in result2.reason.lower()

    def test_different_algorithms(self):
        """Test different HMAC algorithms."""
        for algo in [SignatureAlgorithm.HMAC_SHA256,
                     SignatureAlgorithm.HMAC_SHA384,
                     SignatureAlgorithm.HMAC_SHA512]:
            config = SignatureConfig(algorithm=algo)
            signer = RequestSigner("secret-key", config)

            timestamp = str(int(time.time()))
            nonce = secrets.token_urlsafe(16)

            signature = signer.sign_request(
                method="POST",
                path="/api/test",
                body=b"test",
                timestamp=timestamp,
                nonce=nonce
            )

            result = signer.verify_request(
                method="POST",
                path="/api/test",
                signature=signature,
                body=b"test",
                timestamp=timestamp,
                nonce=nonce
            )

            assert result.valid
            assert result.algorithm == algo


class TestMultiKeyRequestSigner:
    """Test multi-key request signer."""

    def test_multiple_api_keys(self):
        """Test signing and verifying with multiple API keys."""
        signer = MultiKeyRequestSigner({
            "key1": "secret1",
            "key2": "secret2"
        })

        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)

        # Sign with key1
        signature = signer.sign_request(
            api_key="key1",
            method="GET",
            path="/api/data",
            timestamp=timestamp,
            nonce=nonce
        )

        # Verify with key1
        result = signer.verify_request(
            api_key="key1",
            method="GET",
            path="/api/data",
            signature=signature,
            timestamp=timestamp,
            nonce=nonce
        )

        assert result.valid

    def test_wrong_api_key_fails(self):
        """Test that wrong API key fails verification."""
        signer = MultiKeyRequestSigner({
            "key1": "secret1",
            "key2": "secret2"
        })

        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)

        # Sign with key1
        signature = signer.sign_request(
            api_key="key1",
            method="GET",
            path="/api/data",
            timestamp=timestamp,
            nonce=nonce
        )

        # Try to verify with key2
        result = signer.verify_request(
            api_key="key2",
            method="GET",
            path="/api/data",
            signature=signature,
            timestamp=timestamp,
            nonce=nonce
        )

        assert not result.valid

    def test_key_rotation(self):
        """Test API key rotation."""
        signer = MultiKeyRequestSigner({
            "key1": "old-secret"
        })

        # Rotate key
        signer.rotate_key("key1", "new-secret")

        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)

        # Sign with new secret
        signature = signer.sign_request(
            api_key="key1",
            method="GET",
            path="/api/data",
            timestamp=timestamp,
            nonce=nonce
        )

        # Should verify with new secret
        result = signer.verify_request(
            api_key="key1",
            method="GET",
            path="/api/data",
            signature=signature,
            timestamp=timestamp,
            nonce=nonce
        )

        assert result.valid


# ============================================================================
# CORS Tests
# ============================================================================

class TestCORSValidator:
    """Test CORS validation."""

    def test_allowed_origin(self):
        """Test allowed origin validation."""
        config = CORSConfig(
            allow_origins=["https://app.example.com"]
        )
        validator = CORSValidator(config)

        assert validator.is_origin_allowed("https://app.example.com")
        assert not validator.is_origin_allowed("https://evil.com")

    def test_wildcard_origin(self):
        """Test wildcard origin (allow all)."""
        config = CORSConfig(allow_all_origins=True)
        validator = CORSValidator(config)

        assert validator.is_origin_allowed("https://any-site.com")
        assert validator.is_origin_allowed("http://localhost:3000")

    def test_regex_origin_matching(self):
        """Test regex-based origin matching."""
        config = CORSConfig(
            allow_origins=[],
            allow_origin_regex=r"^https://.*\.example\.com$"
        )
        validator = CORSValidator(config)

        assert validator.is_origin_allowed("https://app.example.com")
        assert validator.is_origin_allowed("https://api.example.com")
        assert not validator.is_origin_allowed("https://example.com")
        assert not validator.is_origin_allowed("https://evil.com")

    def test_cors_headers_generation(self):
        """Test CORS headers generation."""
        config = CORSConfig(
            allow_origins=["https://app.example.com"],
            allow_credentials=True,
            expose_headers=["X-Request-ID"]
        )
        validator = CORSValidator(config)

        headers = validator.get_cors_headers(
            origin="https://app.example.com"
        )

        assert headers["Access-Control-Allow-Origin"] == "https://app.example.com"
        assert headers["Access-Control-Allow-Credentials"] == "true"
        assert "X-Request-ID" in headers["Access-Control-Expose-Headers"]

    def test_preflight_validation(self):
        """Test preflight request validation."""
        config = CORSConfig(
            allow_origins=["https://app.example.com"],
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Authorization"]
        )
        validator = CORSValidator(config)

        is_valid, headers = validator.validate_preflight(
            origin="https://app.example.com",
            method="POST",
            headers=["Content-Type", "Authorization"]
        )

        assert is_valid
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers

    def test_preflight_denied(self):
        """Test preflight denial for disallowed method."""
        config = CORSConfig(
            allow_origins=["https://app.example.com"],
            allow_methods=["GET"]  # Only GET allowed
        )
        validator = CORSValidator(config)

        is_valid, headers = validator.validate_preflight(
            origin="https://app.example.com",
            method="POST",  # Not allowed
            headers=[]
        )

        assert not is_valid

    def test_preset_configs(self):
        """Test preset configurations."""
        for preset in [CORSPreset.STRICT, CORSPreset.DEVELOPMENT,
                       CORSPreset.PRODUCTION, CORSPreset.PUBLIC_API]:
            config = get_preset_config(preset)
            assert isinstance(config, CORSConfig)

    def test_custom_origin_validator(self):
        """Test custom origin validator function."""
        validator_func = create_origin_validator(
            allowed_domains=["example.com"],
            require_https=True
        )

        assert validator_func("https://example.com")
        assert validator_func("https://app.example.com")
        assert not validator_func("http://example.com")  # Not HTTPS
        assert not validator_func("https://evil.com")


# ============================================================================
# CSRF Tests
# ============================================================================

class TestCSRFProtection:
    """Test CSRF protection."""

    def test_double_submit_cookie(self):
        """Test double-submit cookie pattern."""
        csrf = CSRFProtection(CSRFConfig(
            method=CSRFProtectionMethod.DOUBLE_SUBMIT_COOKIE
        ))

        # Generate token
        token = csrf.generate_token()
        assert token.token
        assert "." in token.token  # Should have signature

        # Validate with matching cookie and header
        result = csrf.validate_token(
            cookie_token=token.token,
            header_token=token.token
        )
        assert result.valid

    def test_double_submit_mismatch(self):
        """Test double-submit fails with mismatched tokens."""
        csrf = CSRFProtection(CSRFConfig(
            method=CSRFProtectionMethod.DOUBLE_SUBMIT_COOKIE
        ))

        token1 = csrf.generate_token()
        token2 = csrf.generate_token()

        # Different tokens should fail
        result = csrf.validate_token(
            cookie_token=token1.token,
            header_token=token2.token
        )
        assert not result.valid

    def test_synchronizer_token(self):
        """Test synchronizer token pattern."""
        csrf = CSRFProtection(CSRFConfig(
            method=CSRFProtectionMethod.SYNCHRONIZER_TOKEN
        ))

        # Generate token with session binding
        token = csrf.generate_token(session_id="sess123")

        # Validate with matching session
        result = csrf.validate_token(
            form_token=token.token,
            session_id="sess123"
        )
        assert result.valid

    def test_synchronizer_session_mismatch(self):
        """Test synchronizer fails with wrong session."""
        csrf = CSRFProtection(CSRFConfig(
            method=CSRFProtectionMethod.SYNCHRONIZER_TOKEN
        ))

        token = csrf.generate_token(session_id="sess123")

        # Wrong session should fail
        result = csrf.validate_token(
            form_token=token.token,
            session_id="sess456"
        )
        assert not result.valid

    def test_token_expiration(self):
        """Test token expiration."""
        csrf = CSRFProtection(CSRFConfig(
            method=CSRFProtectionMethod.SYNCHRONIZER_TOKEN,
            token_ttl=1  # 1 second
        ))

        token = csrf.generate_token()

        # Should work immediately
        result = csrf.validate_token(form_token=token.token)
        assert result.valid

        # Wait for expiration
        time.sleep(1.5)

        # Should fail after expiration
        result = csrf.validate_token(form_token=token.token)
        assert not result.valid

    def test_token_rotation(self):
        """Test token rotation on auth events."""
        csrf = CSRFProtection(CSRFConfig(
            method=CSRFProtectionMethod.SYNCHRONIZER_TOKEN
        ))

        old_token = csrf.generate_token(session_id="sess123")

        # Rotate token
        new_token = csrf.rotate_token(
            old_token.token,
            session_id="sess123"
        )

        # Old token should be invalidated
        result_old = csrf.validate_token(
            form_token=old_token.token,
            session_id="sess123"
        )
        assert not result_old.valid

        # New token should work
        result_new = csrf.validate_token(
            form_token=new_token.token,
            session_id="sess123"
        )
        assert result_new.valid

    def test_samesite_cookie_params(self):
        """Test SameSite cookie parameters."""
        for policy in [SameSitePolicy.STRICT, SameSitePolicy.LAX, SameSitePolicy.NONE]:
            csrf = CSRFProtection(CSRFConfig(
                cookie_samesite=policy
            ))

            params = csrf.get_cookie_params()
            assert params["samesite"] == policy.value

    def test_safe_methods_skip(self):
        """Test that safe methods skip CSRF check."""
        csrf = CSRFProtection()

        assert not csrf.should_check("GET")
        assert not csrf.should_check("HEAD")
        assert not csrf.should_check("OPTIONS")
        assert csrf.should_check("POST")
        assert csrf.should_check("PUT")
        assert csrf.should_check("DELETE")


# ============================================================================
# Security Headers Tests
# ============================================================================

class TestSecurityHeaders:
    """Test security headers generation."""

    def test_csp_header_generation(self):
        """Test CSP header generation."""
        csp = ContentSecurityPolicy(
            default_src=["'self'"],
            script_src=["'self'", "https://cdn.example.com"],
            style_src=["'self'", "'unsafe-inline'"]
        )

        header_value = csp.to_header_value()

        assert "default-src 'self'" in header_value
        assert "script-src 'self' https://cdn.example.com" in header_value
        assert "style-src 'self' 'unsafe-inline'" in header_value

    def test_csp_report_only(self):
        """Test CSP report-only mode."""
        csp = ContentSecurityPolicy(
            default_src=["'self'"],
            report_only=True
        )

        assert csp.get_header_name() == "Content-Security-Policy-Report-Only"

    def test_hsts_header_generation(self):
        """Test HSTS header generation."""
        hsts = HSTSConfig(
            max_age=31536000,
            include_subdomains=True,
            preload=True
        )

        header_value = hsts.to_header_value()

        assert "max-age=31536000" in header_value
        assert "includeSubDomains" in header_value
        assert "preload" in header_value

    def test_permissions_policy(self):
        """Test Permissions-Policy header generation."""
        policy = PermissionsPolicy(
            camera=["'none'"],
            microphone=["'none'"],
            geolocation=["'self'"]
        )

        header_value = policy.to_header_value()

        assert "camera=('none')" in header_value
        assert "microphone=('none')" in header_value
        assert "geolocation=('self')" in header_value

    def test_complete_security_headers(self):
        """Test complete security headers generation."""
        config = SecurityHeadersConfig(
            csp=ContentSecurityPolicy(default_src=["'self'"]),
            hsts=HSTSConfig(max_age=31536000),
            x_frame_options=XFrameOptions.DENY,
            x_content_type_options=True,
            x_xss_protection=True,
            referrer_policy=ReferrerPolicy.NO_REFERRER
        )

        headers_manager = SecurityHeaders(config)
        headers = headers_manager.get_headers()

        assert "Content-Security-Policy" in headers
        assert "Strict-Transport-Security" in headers
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-XSS-Protection"] == "1; mode=block"
        assert headers["Referrer-Policy"] == "no-referrer"

    def test_preset_configs(self):
        """Test preset security header configurations."""
        strict = get_strict_config()
        assert strict.x_frame_options == XFrameOptions.DENY
        assert strict.hsts.preload

        balanced = get_balanced_config()
        assert balanced.x_frame_options == XFrameOptions.SAMEORIGIN

    def test_custom_headers(self):
        """Test custom security headers."""
        config = SecurityHeadersConfig()
        headers_manager = SecurityHeaders(config)

        headers_manager.add_custom_header("X-Custom-Security", "value")

        headers = headers_manager.get_headers()
        assert headers["X-Custom-Security"] == "value"


# ============================================================================
# Integration Tests
# ============================================================================

class TestAPISecurityIntegration:
    """Test integration of all API security components."""

    def test_complete_api_security_flow(self):
        """Test complete API security flow."""
        # Initialize all components
        rate_limiter = initialize_rate_limiting()
        signer = MultiKeyRequestSigner({"app1": "secret1"})
        cors = CORSValidator(CORSConfig(
            allow_origins=["https://app.example.com"]
        ))
        csrf = CSRFProtection()
        headers_mgr = SecurityHeaders(get_balanced_config())

        # 1. Check rate limit
        rate_result = rate_limiter.check(
            RateLimitScope.USER,
            "user:123"
        )
        assert rate_result.allowed

        # 2. Verify request signature
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)

        signature = signer.sign_request(
            api_key="app1",
            method="POST",
            path="/api/users",
            body=b'{"name":"Alice"}',
            timestamp=timestamp,
            nonce=nonce
        )

        sig_result = signer.verify_request(
            api_key="app1",
            method="POST",
            path="/api/users",
            signature=signature,
            body=b'{"name":"Alice"}',
            timestamp=timestamp,
            nonce=nonce
        )
        assert sig_result.valid

        # 3. Validate CORS
        assert cors.is_origin_allowed("https://app.example.com")
        cors_headers = cors.get_cors_headers("https://app.example.com")
        assert cors_headers

        # 4. Check CSRF
        csrf_token = csrf.generate_token()
        csrf_result = csrf.validate_token(
            cookie_token=csrf_token.token,
            header_token=csrf_token.token
        )
        assert csrf_result.valid

        # 5. Get security headers
        sec_headers = headers_mgr.get_headers()
        assert "Content-Security-Policy" in sec_headers


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
