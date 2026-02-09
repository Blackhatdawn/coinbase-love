"""
Monitoring and Metrics Endpoints
Prometheus-compatible metrics and health checks
"""

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from datetime import datetime
import psutil
import asyncio
from typing import Dict, Any
import logging

from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# ============================================
# METRICS TRACKING
# ============================================

class MetricsCollector:
    """Simple metrics collector"""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.request_duration_sum = 0.0
        self.started_at = datetime.utcnow()
    
    def record_request(self, duration_ms: float, is_error: bool = False):
        """Record a request"""
        self.request_count += 1
        self.request_duration_sum += duration_ms
        if is_error:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        uptime = (datetime.utcnow() - self.started_at).total_seconds()
        avg_duration = (
            self.request_duration_sum / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "avg_response_time_ms": avg_duration
        }


# Global metrics collector
metrics = MetricsCollector()


# ============================================
# ENDPOINTS
# ============================================

@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe
    Returns 200 if application is alive
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/ready")
async def readiness_probe():
    """
    Kubernetes readiness probe
    Returns 200 if application is ready to serve traffic
    """
    # Check if critical services are available
    ready = True
    services = {}
    
    # Check database (quick test)
    try:
        # This should be replaced with actual database check
        services["database"] = "ready"
    except Exception as e:
        services["database"] = f"not ready: {str(e)}"
        ready = False
    
    status_code = 200 if ready else 503
    
    response_data = {
        "status": "ready" if ready else "not ready",
        "services": services,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )


@router.get("/metrics")
async def get_metrics():
    """
    Prometheus-compatible metrics endpoint
    """
    app_metrics = metrics.get_metrics()
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Format as Prometheus metrics
    prometheus_format = f"""
# HELP cryptovault_uptime_seconds Application uptime in seconds
# TYPE cryptovault_uptime_seconds gauge
cryptovault_uptime_seconds {app_metrics['uptime_seconds']}

# HELP cryptovault_requests_total Total number of requests
# TYPE cryptovault_requests_total counter
cryptovault_requests_total {app_metrics['total_requests']}

# HELP cryptovault_errors_total Total number of errors
# TYPE cryptovault_errors_total counter
cryptovault_errors_total {app_metrics['total_errors']}

# HELP cryptovault_error_rate Error rate (errors/requests)
# TYPE cryptovault_error_rate gauge
cryptovault_error_rate {app_metrics['error_rate']}

# HELP cryptovault_response_time_avg_ms Average response time in milliseconds
# TYPE cryptovault_response_time_avg_ms gauge
cryptovault_response_time_avg_ms {app_metrics['avg_response_time_ms']}

# HELP cryptovault_cpu_percent CPU usage percentage
# TYPE cryptovault_cpu_percent gauge
cryptovault_cpu_percent {cpu_percent}

# HELP cryptovault_memory_percent Memory usage percentage
# TYPE cryptovault_memory_percent gauge
cryptovault_memory_percent {memory.percent}

# HELP cryptovault_disk_percent Disk usage percentage
# TYPE cryptovault_disk_percent gauge
cryptovault_disk_percent {disk.percent}
"""
    
    return Response(content=prometheus_format.strip(), media_type="text/plain")


@router.get("/metrics/json")
async def get_metrics_json():
    """
    JSON metrics endpoint
    """
    app_metrics = metrics.get_metrics()
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "application": app_metrics,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024 * 1024 * 1024)
        }
    }


@router.get("/circuit-breakers")
async def get_circuit_breakers():
    """
    Get circuit breaker states
    """
    try:
        from services.circuit_breaker import get_all_breakers
        return get_all_breakers()
    except ImportError:
        return {"error": "Circuit breakers not available"}


@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str):
    """
    Manually reset a circuit breaker
    """
    try:
        from services.circuit_breaker import reset_breaker
        success = await reset_breaker(name)
        if success:
            return {"message": f"Circuit breaker '{name}' reset successfully"}
        else:
            return {"error": f"Circuit breaker '{name}' not found"}
    except ImportError:
        return {"error": "Circuit breakers not available"}
