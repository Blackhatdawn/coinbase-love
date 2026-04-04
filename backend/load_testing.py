"""
Load Testing Suite
Comprehensive load testing for API resilience and performance validation
Phase 4: Advanced Request Management
"""

import asyncio
import time
import logging
import statistics
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class LoadTestScenario(Enum):
    """Load testing scenarios"""
    RAMP_UP = "ramp_up"  # Gradually increase load
    SPIKE = "spike"  # Sudden traffic spike
    SUSTAINED = "sustained"  # Constant load
    OSCILLATING = "oscillating"  # Varies up and down


@dataclass
class RequestResult:
    """Result of a single request"""
    request_id: int
    scenario: str
    endpoint: str
    start_time: float
    end_time: float
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None
    response_time_ms: float = field(init=False)
    
    def __post_init__(self):
        self.response_time_ms = (self.end_time - self.start_time) * 1000


@dataclass
class LoadTestReport:
    """Results from load test execution"""
    scenario: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_seconds: float
    requests_per_second: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    avg_response_time_ms: float = 0.0
    error_rate_percentage: float = 0.0
    circuit_breaker_openings: int = 0
    timeout_errors: int = 0
    
    def success_rate_percentage(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


class LoadTestSuite:
    """
    Comprehensive load testing for API resilience validation.
    
    Scenarios:
    - RAMP_UP: Gradually increase concurrent users (10->100->1000)
    - SPIKE: Sudden traffic spike (normal -> 5x -> normal)
    - SUSTAINED: Constant high load for extended period
    - OSCILLATING: Load varies up and down periodically
    """
    
    def __init__(self):
        self.results: List[RequestResult] = []
        self.reports: List[LoadTestReport] = []
        self.start_time: float = 0
        self.end_time: float = 0
    
    async def run_ramp_up_test(
        self,
        endpoint: str,
        request_func: Callable,
        stages: List[int] = None,
        duration_per_stage_seconds: int = 30
    ) -> LoadTestReport:
        """
        Gradually increase load (ramp up test).
        
        Args:
            endpoint: API endpoint to test
            request_func: Async function that makes a request
            stages: List of concurrent users per stage [10, 100, 1000]
            duration_per_stage_seconds: How long each stage lasts
        """
        if stages is None:
            stages = [10, 50, 100, 500, 1000]
        
        logger.info(f"🚀 Starting ramp-up load test: {endpoint}")
        logger.info(f"   Stages: {stages}, Duration per stage: {duration_per_stage_seconds}s")
        
        self.start_time = time.time()
        request_id = 0
        
        for stage_num, concurrent_users in enumerate(stages):
            logger.info(f"📊 Stage {stage_num + 1}: {concurrent_users} concurrent users")
            
            stage_start = time.time()
            while time.time() - stage_start < duration_per_stage_seconds:
                # Launch concurrent requests
                tasks = [
                    self._execute_request(
                        request_id + i,
                        "ramp_up",
                        endpoint,
                        request_func
                    )
                    for i in range(concurrent_users)
                ]
                
                await asyncio.gather(*tasks, return_exceptions=True)
                request_id += concurrent_users
                
                # Brief pause between batches
                await asyncio.sleep(0.1)
        
        self.end_time = time.time()
        report = self._generate_report("ramp_up")
        self.reports.append(report)
        return report
    
    async def run_spike_test(
        self,
        endpoint: str,
        request_func: Callable,
        normal_load: int = 50,
        spike_load: int = 500,
        duration_seconds: int = 60
    ) -> LoadTestReport:
        """
        Sudden traffic spike test.
        
        Args:
            endpoint: API endpoint to test
            request_func: Async function that makes a request
            normal_load: Normal concurrent users
            spike_load: Spike concurrent users
            duration_seconds: Total test duration
        """
        logger.info(f"⚡ Starting spike load test: {endpoint}")
        logger.info(f"   Normal: {normal_load} users, Spike: {spike_load} users")
        
        self.start_time = time.time()
        request_id = 0
        spike_phase = 0  # 0=normal, 1=spike, 2=recovering, 3=normal
        
        while time.time() - self.start_time < duration_seconds:
            elapsed = time.time() - self.start_time
            
            # Determine phase
            if elapsed < 15:
                spike_phase = 0
                concurrent = normal_load
            elif elapsed < 25:
                spike_phase = 1
                concurrent = spike_load
                logger.warning("⚡ SPIKE!")
            elif elapsed < 40:
                spike_phase = 2
                concurrent = int(normal_load + (spike_load - normal_load) * (40 - elapsed) / 15)
            else:
                spike_phase = 3
                concurrent = normal_load
            
            # Launch batch
            tasks = [
                self._execute_request(
                    request_id + i,
                    "spike",
                    endpoint,
                    request_func
                )
                for i in range(concurrent)
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            request_id += concurrent
            await asyncio.sleep(0.5)
        
        self.end_time = time.time()
        report = self._generate_report("spike")
        self.reports.append(report)
        return report
    
    async def run_sustained_load_test(
        self,
        endpoint: str,
        request_func: Callable,
        concurrent_users: int = 100,
        duration_minutes: int = 5
    ) -> LoadTestReport:
        """
        Sustained high load test.
        
        Args:
            endpoint: API endpoint to test
            request_func: Async function that makes a request
            concurrent_users: Number of concurrent users
            duration_minutes: How long to run test
        """
        logger.info(f"📈 Starting sustained load test: {endpoint}")
        logger.info(f"   Load: {concurrent_users} concurrent users for {duration_minutes} minutes")
        
        self.start_time = time.time()
        duration_seconds = duration_minutes * 60
        request_id = 0
        
        while time.time() - self.start_time < duration_seconds:
            # Launch concurrent batch
            tasks = [
                self._execute_request(
                    request_id + i,
                    "sustained",
                    endpoint,
                    request_func
                )
                for i in range(concurrent_users)
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            request_id += concurrent_users
            
            elapsed = time.time() - self.start_time
            rate = request_id / elapsed
            logger.info(f"   {elapsed:.0f}s: {request_id} requests, {rate:.1f} req/s")
            
            await asyncio.sleep(0.5)
        
        self.end_time = time.time()
        report = self._generate_report("sustained")
        self.reports.append(report)
        return report
    
    async def _execute_request(
        self,
        request_id: int,
        scenario: str,
        endpoint: str,
        request_func: Callable
    ):
        """Execute a single request and record result"""
        start = time.time()
        success = False
        status_code = None
        error = None
        
        try:
            result = await asyncio.wait_for(request_func(), timeout=30)
            success = True
            status_code = 200
        except asyncio.TimeoutError:
            error = "timeout"
        except Exception as e:
            error = str(e)
        
        end = time.time()
        
        result_obj = RequestResult(
            request_id=request_id,
            scenario=scenario,
            endpoint=endpoint,
            start_time=start,
            end_time=end,
            success=success,
            status_code=status_code,
            error=error
        )
        
        self.results.append(result_obj)
    
    def _generate_report(self, scenario: str) -> LoadTestReport:
        """Generate report from results"""
        scenario_results = [r for r in self.results if r.scenario == scenario]
        
        if not scenario_results:
            return LoadTestReport(
                scenario=scenario,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                total_duration_seconds=0
            )
        
        successful = [r for r in scenario_results if r.success]
        failed = [r for r in scenario_results if not r.success]
        
        response_times = [r.response_time_ms for r in successful]
        response_times.sort()
        
        total_duration = self.end_time - self.start_time
        rps = len(scenario_results) / total_duration if total_duration > 0 else 0
        
        report = LoadTestReport(
            scenario=scenario,
            total_requests=len(scenario_results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            total_duration_seconds=total_duration,
            requests_per_second=rps,
            p50_response_time_ms=response_times[int(len(response_times) * 0.50)] if response_times else 0,
            p95_response_time_ms=response_times[int(len(response_times) * 0.95)] if response_times else 0,
            p99_response_time_ms=response_times[int(len(response_times) * 0.99)] if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            error_rate_percentage=(len(failed) / len(scenario_results) * 100) if scenario_results else 0,
        )
        
        return report
    
    def print_report(self, report: LoadTestReport):
        """Pretty print test report"""
        logger.info("=" * 80)
        logger.info(f"LOAD TEST REPORT: {report.scenario.upper()}")
        logger.info("=" * 80)
        logger.info(f"Total Requests:     {report.total_requests:,}")
        logger.info(f"Successful:         {report.successful_requests:,} ({report.success_rate_percentage():.1f}%)")
        logger.info(f"Failed:             {report.failed_requests:,}")
        logger.info(f"Duration:           {report.total_duration_seconds:.1f} seconds")
        logger.info(f"Throughput:         {report.requests_per_second:.1f} req/s")
        logger.info("")
        logger.info("Response Times:")
        logger.info(f"  Min:              {report.min_response_time_ms:.1f} ms")
        logger.info(f"  P50 (Median):     {report.p50_response_time_ms:.1f} ms")
        logger.info(f"  P95:              {report.p95_response_time_ms:.1f} ms")
        logger.info(f"  P99:              {report.p99_response_time_ms:.1f} ms")
        logger.info(f"  Max:              {report.max_response_time_ms:.1f} ms")
        logger.info(f"  Avg:              {report.avg_response_time_ms:.1f} ms")
        logger.info("=" * 80)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current test status"""
        return {
            "total_requests": len(self.results),
            "completed_reports": len(self.reports),
            "latest_report": self.reports[-1].__dict__ if self.reports else None
        }
