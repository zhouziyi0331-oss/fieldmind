"""
Test Suite for External API Integration (Phase 6.1)
Tests HTTP client, API adapters, and error handling.
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integration import (
    # HTTP Client
    HTTPMethod,
    RetryStrategy,
    CacheStrategy,
    TimeoutConfig,
    RetryConfig,
    CacheConfig,
    HTTPClientConfig,
    HTTPRequest,
    HTTPResponse,
    HTTPClient,
    MemoryCache,
    # API Adapters
    AdapterStatus,
    FallbackStrategy,
    AdapterConfig,
    AdapterMetrics,
    BaseAPIAdapter,
    RESTAPIAdapter,
    GraphQLAPIAdapter,
    SOAPAPIAdapter,
    # Error Handling
    ErrorType,
    DegradationLevel,
    ErrorContext,
    ErrorClassifier,
    GracefulDegradation,
    ErrorRecovery,
)


# ============================================================================
# HTTP Client Tests
# ============================================================================

class TestHTTPClient:
    """Test HTTP client functionality"""

    @pytest.mark.asyncio
    async def test_basic_request(self):
        """Test basic HTTP request"""
        config = HTTPClientConfig(base_url="https://api.example.com")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.content = b'{"status": "ok"}'
            mock_response.text = '{"status": "ok"}'
            mock_response.json.return_value = {"status": "ok"}

            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            client = HTTPClient(config)

            request = HTTPRequest(
                method=HTTPMethod.GET,
                url="/test",
            )

            response = await client.request(request)

            assert response.status_code == 200
            assert response.is_success()
            assert response.json_data == {"status": "ok"}

            await client.close()

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry logic on failure"""
        config = HTTPClientConfig(
            base_url="https://api.example.com",
            retry=RetryConfig(
                max_attempts=3,
                strategy=RetryStrategy.EXPONENTIAL,
                base_delay=0.01,  # Fast for testing
                jitter=False,
            ),
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # First two attempts fail, third succeeds
            call_count = 0

            async def mock_request(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count < 3:
                    mock_response = MagicMock()
                    mock_response.status_code = 503
                    mock_response.headers = {}
                    mock_response.content = b'Service Unavailable'
                    mock_response.text = 'Service Unavailable'
                    mock_response.json.side_effect = Exception("Not JSON")
                    return mock_response
                else:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.headers = {"content-type": "application/json"}
                    mock_response.content = b'{"status": "ok"}'
                    mock_response.text = '{"status": "ok"}'
                    mock_response.json.return_value = {"status": "ok"}
                    return mock_response

            mock_client.request = mock_request
            mock_client_class.return_value = mock_client

            client = HTTPClient(config)

            request = HTTPRequest(
                method=HTTPMethod.GET,
                url="/test",
            )

            response = await client.request(request)

            assert response.status_code == 200
            assert response.attempt_count == 3
            assert call_count == 3

            await client.close()

    @pytest.mark.asyncio
    async def test_response_caching(self):
        """Test response caching"""
        config = HTTPClientConfig(
            base_url="https://api.example.com",
            cache=CacheConfig(
                strategy=CacheStrategy.MEMORY,
                ttl=300,
            ),
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.content = b'{"data": "test"}'
            mock_response.text = '{"data": "test"}'
            mock_response.json.return_value = {"data": "test"}

            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            client = HTTPClient(config)

            request = HTTPRequest(
                method=HTTPMethod.GET,
                url="/test",
            )

            # First request
            response1 = await client.request(request)
            assert not response1.from_cache

            # Second request should be cached
            response2 = await client.request(request)
            assert response2.from_cache
            assert response2.json_data == {"data": "test"}

            # Should only call HTTP client once
            assert mock_client.request.call_count == 1

            await client.close()


class TestMemoryCache:
    """Test memory cache functionality"""

    def test_cache_set_and_get(self):
        """Test setting and getting cache entries"""
        cache = MemoryCache(max_size=10)

        response = HTTPResponse(
            status_code=200,
            headers={},
            body=b"test",
            text="test",
        )

        cache.set("key1", response, ttl=60)

        cached = cache.get("key1")
        assert cached is not None
        assert cached.status_code == 200
        assert cached.text == "test"

    def test_cache_expiration(self):
        """Test cache entry expiration"""
        cache = MemoryCache(max_size=10)

        response = HTTPResponse(
            status_code=200,
            headers={},
            body=b"test",
            text="test",
        )

        # Set with 0 second TTL (immediate expiration)
        cache.set("key1", response, ttl=0)

        # Should be expired
        cached = cache.get("key1")
        assert cached is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = MemoryCache(max_size=3)

        response = HTTPResponse(
            status_code=200,
            headers={},
            body=b"test",
            text="test",
        )

        # Fill cache
        cache.set("key1", response, ttl=60)
        cache.set("key2", response, ttl=60)
        cache.set("key3", response, ttl=60)

        assert cache.size() == 3

        # Add one more - should evict key1 (oldest)
        cache.set("key4", response, ttl=60)

        assert cache.size() == 3
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None


class TestRetryConfig:
    """Test retry configuration"""

    def test_exponential_backoff(self):
        """Test exponential backoff calculation"""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=60.0,
            jitter=False,
        )

        delay1 = config.calculate_delay(0)
        delay2 = config.calculate_delay(1)
        delay3 = config.calculate_delay(2)

        assert delay1 == 1.0  # 1 * 2^0
        assert delay2 == 2.0  # 1 * 2^1
        assert delay3 == 4.0  # 1 * 2^2

    def test_linear_backoff(self):
        """Test linear backoff calculation"""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR,
            base_delay=2.0,
            max_delay=60.0,
            jitter=False,
        )

        delay1 = config.calculate_delay(0)
        delay2 = config.calculate_delay(1)
        delay3 = config.calculate_delay(2)

        assert delay1 == 0.0  # 2 * 0
        assert delay2 == 2.0  # 2 * 1
        assert delay3 == 4.0  # 2 * 2

    def test_fibonacci_backoff(self):
        """Test fibonacci backoff calculation"""
        config = RetryConfig(
            strategy=RetryStrategy.FIBONACCI,
            base_delay=1.0,
            max_delay=60.0,
            jitter=False,
        )

        delay1 = config.calculate_delay(0)
        delay2 = config.calculate_delay(1)
        delay3 = config.calculate_delay(2)
        delay4 = config.calculate_delay(3)

        assert delay1 == 1.0  # fib(1) = 1
        assert delay2 == 1.0  # fib(2) = 1
        assert delay3 == 2.0  # fib(3) = 2
        assert delay4 == 3.0  # fib(4) = 3


# ============================================================================
# API Adapter Tests
# ============================================================================

class TestRESTAPIAdapter:
    """Test REST API adapter"""

    @pytest.mark.asyncio
    async def test_get_request(self):
        """Test GET request through adapter"""
        config = AdapterConfig(
            service_name="test_service",
            base_url="https://api.example.com",
        )

        mock_client = AsyncMock()
        mock_response = HTTPResponse(
            status_code=200,
            headers={},
            body=b'{"id": 1, "name": "test"}',
            text='{"id": 1, "name": "test"}',
            json_data={"id": 1, "name": "test"},
        )
        mock_client.request = AsyncMock(return_value=mock_response)

        adapter = RESTAPIAdapter(config, mock_client)

        result = await adapter.get("/users/1")

        assert result == {"id": 1, "name": "test"}
        assert adapter.metrics.total_requests == 1
        assert adapter.metrics.successful_requests == 1

    @pytest.mark.asyncio
    async def test_post_request(self):
        """Test POST request through adapter"""
        config = AdapterConfig(
            service_name="test_service",
            base_url="https://api.example.com",
        )

        mock_client = AsyncMock()
        mock_response = HTTPResponse(
            status_code=201,
            headers={},
            body=b'{"id": 2, "name": "created"}',
            text='{"id": 2, "name": "created"}',
            json_data={"id": 2, "name": "created"},
        )
        mock_client.request = AsyncMock(return_value=mock_response)

        adapter = RESTAPIAdapter(config, mock_client)

        result = await adapter.post("/users", data={"name": "created"})

        assert result == {"id": 2, "name": "created"}
        assert adapter.metrics.successful_requests == 1


class TestAdapterMetrics:
    """Test adapter metrics"""

    def test_record_success(self):
        """Test recording successful request"""
        metrics = AdapterMetrics()

        metrics.record_request(success=True, latency=0.5)

        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.average_latency() == 0.5
        assert metrics.success_rate() == 1.0

    def test_record_failure(self):
        """Test recording failed request"""
        metrics = AdapterMetrics()

        metrics.record_request(success=False, latency=1.0)

        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.consecutive_failures == 1
        assert metrics.success_rate() == 0.0

    def test_cache_hit_rate(self):
        """Test cache hit rate calculation"""
        metrics = AdapterMetrics()

        metrics.record_request(success=True, latency=0.5, from_cache=True)
        metrics.record_request(success=True, latency=0.3, from_cache=False)
        metrics.record_request(success=True, latency=0.1, from_cache=True)

        assert metrics.total_requests == 3
        assert metrics.cached_responses == 2
        assert metrics.cache_hit_rate() == 2.0 / 3.0


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorClassifier:
    """Test error classifier"""

    def test_classify_http_errors(self):
        """Test HTTP error classification"""
        assert ErrorClassifier.classify_http_error(401) == ErrorType.AUTHENTICATION
        assert ErrorClassifier.classify_http_error(403) == ErrorType.AUTHORIZATION
        assert ErrorClassifier.classify_http_error(404) == ErrorType.NOT_FOUND
        assert ErrorClassifier.classify_http_error(429) == ErrorType.RATE_LIMIT
        assert ErrorClassifier.classify_http_error(400) == ErrorType.VALIDATION
        assert ErrorClassifier.classify_http_error(500) == ErrorType.SERVER_ERROR
        assert ErrorClassifier.classify_http_error(503) == ErrorType.SERVICE_UNAVAILABLE

    def test_classify_exceptions(self):
        """Test exception classification"""
        import asyncio

        timeout_error = asyncio.TimeoutError("Timeout")
        assert ErrorClassifier.classify_exception(timeout_error) == ErrorType.TIMEOUT

        connection_error = Exception("Connection refused")
        assert ErrorClassifier.classify_exception(connection_error) == ErrorType.CONNECTION


class TestGracefulDegradation:
    """Test graceful degradation"""

    def test_normal_state(self):
        """Test service in normal state"""
        degradation = GracefulDegradation()

        level = degradation.get_degradation_level("test_service")
        assert level == DegradationLevel.NORMAL

    def test_degradation_on_errors(self):
        """Test degradation level changes on errors"""
        degradation = GracefulDegradation()

        error_context = ErrorContext(
            error_type=ErrorType.TIMEOUT,
            original_error=Exception("Timeout"),
            service_name="test_service",
            endpoint="/test",
            method="GET",
        )

        # Record multiple errors
        for _ in range(3):
            degradation.record_error("test_service", error_context)

        level = degradation.get_degradation_level("test_service")
        assert level == DegradationLevel.PARTIAL

        # More errors -> higher degradation
        for _ in range(3):
            degradation.record_error("test_service", error_context)

        level = degradation.get_degradation_level("test_service")
        assert level in [DegradationLevel.LIMITED, DegradationLevel.UNAVAILABLE]

    def test_recovery_on_success(self):
        """Test recovery on successful requests"""
        degradation = GracefulDegradation()

        error_context = ErrorContext(
            error_type=ErrorType.TIMEOUT,
            original_error=Exception("Timeout"),
            service_name="test_service",
            endpoint="/test",
            method="GET",
        )

        # Record errors
        for _ in range(3):
            degradation.record_error("test_service", error_context)

        assert degradation.get_degradation_level("test_service") == DegradationLevel.PARTIAL

        # Record successes
        for _ in range(5):
            degradation.record_success("test_service")

        # Should improve
        level = degradation.get_degradation_level("test_service")
        assert level in [DegradationLevel.NORMAL, DegradationLevel.PARTIAL]


class TestErrorRecovery:
    """Test error recovery strategies"""

    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        """Test fallback execution on error"""

        async def primary_func():
            raise Exception("Primary failed")

        async def fallback_func():
            return "fallback_result"

        result = await ErrorRecovery.with_fallback(
            primary_func=primary_func,
            fallback_func=fallback_func,
        )

        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_fallback_value(self):
        """Test static fallback value"""

        async def primary_func():
            raise Exception("Primary failed")

        result = await ErrorRecovery.with_fallback(
            primary_func=primary_func,
            fallback_value="default_value",
        )

        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_timeout_escalation(self):
        """Test timeout escalation"""

        call_count = 0

        async def func_with_delay():
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                await asyncio.sleep(0.1)  # Timeout on first attempt
                return "should_not_reach"
            else:
                return "success"

        result = await ErrorRecovery.with_timeout_escalation(
            func=func_with_delay,
            base_timeout=0.05,
            max_attempts=2,
            timeout_multiplier=3.0,
        )

        assert result == "success"
        assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
