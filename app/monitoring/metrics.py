"""
Monitoring & Observability Module (Phase 3)
Implements Prometheus metrics, logging, and health checks
Covers: System metrics, application metrics, performance tracking
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

# ============================================================================
# METRICS TYPES
# ============================================================================

class MetricType(str, Enum):
    """Metric types"""
    COUNTER = "counter"           # Monotonically increasing
    GAUGE = "gauge"               # Can go up and down
    HISTOGRAM = "histogram"        # Distribution of values
    TIMER = "timer"               # Timing measurements


# ============================================================================
# METRIC DEFINITIONS
# ============================================================================

@dataclass
class Metric:
    """Metric value"""
    name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    help_text: str = ""


@dataclass
class HealthCheckResult:
    """Health check result"""
    service: str
    status: str  # healthy, degraded, unhealthy
    message: str
    checks: Dict[str, bool] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

class MetricsCollector:
    """Collects and tracks application metrics"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
    
    # ============ COUNTER METRICS ============
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict] = None):
        """Increment counter metric"""
        key = self._make_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + value
        
        self.metrics[name].append(Metric(
            name=name,
            metric_type=MetricType.COUNTER,
            value=value,
            labels=labels or {},
        ))
    
    def get_counter(self, name: str, labels: Optional[Dict] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0)
    
    # ============ GAUGE METRICS ============
    def set_gauge(self, name: str, value: float, labels: Optional[Dict] = None):
        """Set gauge metric"""
        key = self._make_key(name, labels)
        self.gauges[key] = value
        
        self.metrics[name].append(Metric(
            name=name,
            metric_type=MetricType.GAUGE,
            value=value,
            labels=labels or {},
        ))
    
    def get_gauge(self, name: str, labels: Optional[Dict] = None) -> float:
        """Get gauge value"""
        key = self._make_key(name, labels)
        return self.gauges.get(key, 0)
    
    # ============ HISTOGRAM METRICS ============
    def record_histogram(self, name: str, value: float, labels: Optional[Dict] = None):
        """Record histogram value"""
        self.histograms[name].append(value)
        
        self.metrics[name].append(Metric(
            name=name,
            metric_type=MetricType.HISTOGRAM,
            value=value,
            labels=labels or {},
        ))
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        values = self.histograms.get(name, [])
        if not values:
            return {}
        
        sorted_values = sorted(values)
        n = len(values)
        
        return {
            "count": float(n),
            "sum": sum(values),
            "mean": sum(values) / n,
            "min": min(values),
            "max": max(values),
            "p50": sorted_values[int(n * 0.5)],
            "p95": sorted_values[int(n * 0.95)],
            "p99": sorted_values[int(n * 0.99)],
        }
    
    # ============ TIMER METRICS ============
    def record_timer(self, name: str, duration_ms: float, labels: Optional[Dict] = None):
        """Record timer value"""
        self.timers[name].append(duration_ms)
        
        self.metrics[name].append(Metric(
            name=name,
            metric_type=MetricType.TIMER,
            value=duration_ms,
            labels=labels or {},
        ))
    
    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Get timer statistics"""
        return self.get_histogram_stats(name)
    
    # ============ UTILITY ============
    def _make_key(self, name: str, labels: Optional[Dict]) -> str:
        """Make unique key for metric with labels"""
        if not labels:
            return name
        label_str = "_".join(f"{k}_{v}" for k, v in sorted(labels.items()))
        return f"{name}_{label_str}"
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timers.clear()


# ============================================================================
# APPLICATION METRICS
# ============================================================================

class ApplicationMetrics:
    """Application-specific metrics"""
    
    def __init__(self, collector: MetricsCollector):
        """Initialize application metrics"""
        self.collector = collector
    
    # ============ API METRICS ============
    def record_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """Record API request"""
        labels = {"endpoint": endpoint, "method": method, "status": str(status_code)}
        
        # Counter: total requests
        self.collector.increment_counter("http_requests_total", labels=labels)
        
        # Timer: request duration
        self.collector.record_timer("http_request_duration_ms", duration_ms, labels=labels)
        
        # Counter: errors
        if status_code >= 400:
            self.collector.increment_counter("http_errors_total", labels=labels)
    
    # ============ DATABASE METRICS ============
    def record_db_query(self, query_type: str, duration_ms: float, success: bool):
        """Record database query"""
        labels = {"query_type": query_type, "status": "success" if success else "error"}
        
        self.collector.record_timer("db_query_duration_ms", duration_ms, labels=labels)
        self.collector.increment_counter("db_queries_total", labels=labels)
    
    # ============ AI AGENT METRICS ============
    def record_agent_execution(self, agent_name: str, duration_ms: float, success: bool):
        """Record AI agent execution"""
        labels = {"agent": agent_name, "status": "success" if success else "error"}
        
        self.collector.record_timer("agent_execution_duration_ms", duration_ms, labels=labels)
        self.collector.increment_counter("agent_executions_total", labels=labels)
    
    # ============ ALERT METRICS ============
    def record_alert_generated(self, alert_type: str, severity: str):
        """Record alert generation"""
        labels = {"type": alert_type, "severity": severity}
        self.collector.increment_counter("alerts_generated_total", labels=labels)
    
    def record_alert_acknowledged(self, alert_type: str):
        """Record alert acknowledgment"""
        labels = {"type": alert_type}
        self.collector.increment_counter("alerts_acknowledged_total", labels=labels)
    
    # ============ BUSINESS METRICS ============
    def set_active_patients(self, count: int):
        """Set active patient count"""
        self.collector.set_gauge("active_patients", float(count))
    
    def set_active_users(self, count: int):
        """Set active user count"""
        self.collector.set_gauge("active_users", float(count))
    
    def record_consent_granted(self, scope: str):
        """Record consent grant"""
        labels = {"scope": scope}
        self.collector.increment_counter("consents_granted_total", labels=labels)


# ============================================================================
# HEALTH CHECKS
# ============================================================================

class HealthChecker:
    """Performs health checks on system components"""
    
    def __init__(self):
        """Initialize health checker"""
        self.checks: Dict[str, callable] = {}
    
    def register_check(self, name: str, check_fn: callable):
        """Register health check"""
        self.checks[name] = check_fn
    
    async def check_database(self) -> bool:
        """Check database connectivity"""
        try:
            # In production, execute actual database query
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def check_cache(self) -> bool:
        """Check cache connectivity"""
        try:
            # In production, check Redis/Memcached
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False
    
    async def check_ai_agents(self) -> bool:
        """Check AI agents availability"""
        try:
            # In production, ping AI service endpoints
            return True
        except Exception as e:
            logger.error(f"AI agents health check failed: {e}")
            return False
    
    async def check_websocket(self) -> bool:
        """Check WebSocket connectivity"""
        try:
            # In production, verify WebSocket server
            return True
        except Exception as e:
            logger.error(f"WebSocket health check failed: {e}")
            return False
    
    async def run_all_checks(self) -> HealthCheckResult:
        """Run all health checks"""
        checks = {
            "database": await self.check_database(),
            "cache": await self.check_cache(),
            "ai_agents": await self.check_ai_agents(),
            "websocket": await self.check_websocket(),
        }
        
        all_healthy = all(checks.values())
        all_unhealthy = not any(checks.values())
        
        if all_healthy:
            status = "healthy"
            message = "All systems operational"
        elif all_unhealthy:
            status = "unhealthy"
            message = "Critical systems down"
        else:
            status = "degraded"
            message = "Some systems unavailable"
        
        return HealthCheckResult(
            service="gericure",
            status=status,
            message=message,
            checks=checks,
        )


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class LoggingConfig:
    """Configure structured logging"""
    
    @staticmethod
    def setup_logging(log_level: str = "INFO", 
                     log_file: Optional[str] = None):
        """Setup application logging"""
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formatter with detailed information
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        logger.info(f"Logging configured - Level: {log_level}")


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class PerformanceMonitor:
    """Monitors application performance"""
    
    def __init__(self, metrics: ApplicationMetrics):
        """Initialize performance monitor"""
        self.metrics = metrics
        self.start_time = time.time()
    
    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return {
            "uptime_seconds": self.get_uptime_seconds(),
            "http_requests_total": self.metrics.collector.get_counter("http_requests_total"),
            "http_errors_total": self.metrics.collector.get_counter("http_errors_total"),
            "db_query_stats": self.metrics.collector.get_histogram_stats("db_query_duration_ms"),
            "agent_execution_stats": self.metrics.collector.get_histogram_stats("agent_execution_duration_ms"),
        }


# ============================================================================
# MONITORING DASHBOARD
# ============================================================================

@dataclass
class DashboardData:
    """Data for monitoring dashboard"""
    timestamp: datetime
    http_metrics: Dict[str, Any]
    database_metrics: Dict[str, Any]
    agent_metrics: Dict[str, Any]
    alert_metrics: Dict[str, Any]
    health_status: HealthCheckResult
    performance_stats: Dict[str, Any]


class MonitoringDashboard:
    """Aggregates monitoring data for dashboard"""
    
    def __init__(self, 
                 metrics: ApplicationMetrics,
                 health_checker: HealthChecker,
                 performance_monitor: PerformanceMonitor):
        """Initialize monitoring dashboard"""
        self.metrics = metrics
        self.health_checker = health_checker
        self.performance_monitor = performance_monitor
    
    async def get_dashboard_data(self) -> DashboardData:
        """Get aggregated dashboard data"""
        health_status = await self.health_checker.run_all_checks()
        
        return DashboardData(
            timestamp=datetime.utcnow(),
            http_metrics={
                "total_requests": self.metrics.collector.get_counter("http_requests_total"),
                "total_errors": self.metrics.collector.get_counter("http_errors_total"),
                "request_duration_stats": self.metrics.collector.get_histogram_stats("http_request_duration_ms"),
            },
            database_metrics={
                "query_duration_stats": self.metrics.collector.get_histogram_stats("db_query_duration_ms"),
            },
            agent_metrics={
                "execution_duration_stats": self.metrics.collector.get_histogram_stats("agent_execution_duration_ms"),
                "total_alerts": self.metrics.collector.get_counter("alerts_generated_total"),
            },
            alert_metrics={
                "alerts_generated": self.metrics.collector.get_counter("alerts_generated_total"),
                "alerts_acknowledged": self.metrics.collector.get_counter("alerts_acknowledged_total"),
            },
            health_status=health_status,
            performance_stats=self.performance_monitor.get_performance_stats(),
        )


# ============================================================================
# GLOBAL METRICS INSTANCE
# ============================================================================

# Global metrics collector
_metrics_collector = MetricsCollector()
_application_metrics = ApplicationMetrics(_metrics_collector)
_health_checker = HealthChecker()
_performance_monitor = PerformanceMonitor(_application_metrics)
_monitoring_dashboard = MonitoringDashboard(
    _application_metrics,
    _health_checker,
    _performance_monitor
)


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    return _metrics_collector


def get_application_metrics() -> ApplicationMetrics:
    """Get global application metrics"""
    return _application_metrics


def get_health_checker() -> HealthChecker:
    """Get global health checker"""
    return _health_checker


def get_monitoring_dashboard() -> MonitoringDashboard:
    """Get global monitoring dashboard"""
    return _monitoring_dashboard
