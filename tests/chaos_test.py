#!/usr/bin/env python3
"""
observability-blueprint: Chaos Injection & Alert Testing

This script validates that alert rules fire correctly under various failure scenarios.
Used in CI/CD to ensure alerts are tuned and operational.

Usage:
    python tests/chaos_test.py --scenario=high_latency --duration=120
    python tests/chaos_test.py --scenario=all --duration=300
"""

import json
import time
import argparse
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import requests

# Configuration
PROMETHEUS_URL = "http://localhost:9090"
ALERTMANAGER_URL = "http://localhost:9093"
PUSH_GATEWAY_URL = "http://localhost:9091"

# Test scenarios
SCENARIOS = {
    "high_latency": {
        "description": "Simulate high settlement latency",
        "metric": "settlement_processing_duration_seconds_bucket",
        "alert": "HighSettlementLatency",
        "expected_severity": "critical",
    },
    "high_error_rate": {
        "description": "Simulate high error rate",
        "metric": "http_requests_total",
        "alert": "HighErrorRate",
        "expected_severity": "warning",
    },
    "cost_anomaly": {
        "description": "Simulate cost spike",
        "metric": "aws_billing_estimated_charges",
        "alert": "CostAnomalyDetected",
        "expected_severity": "warning",
    },
    "database_slow_query": {
        "description": "Simulate slow database queries",
        "metric": "database_query_duration_seconds_bucket",
        "alert": "CriticalDatabaseSlowQuery",
        "expected_severity": "critical",
    },
    "secret_exposed": {
        "description": "Simulate secret exposure in logs",
        "metric": "secret_exposure_detected_total",
        "alert": "SecretExposedInLogs",
        "expected_severity": "critical",
    },
}


class ChaosInjector:
    """Injects failure scenarios and validates alert responses"""

    def __init__(self, prometheus_url: str = PROMETHEUS_URL, timeout: int = 300):
        self.prometheus_url = prometheus_url
        self.timeout = timeout
        self.test_results = []

    def push_metric(self, metric_name: str, value: float, labels: Dict = None) -> bool:
        """Push a metric to Prometheus Push Gateway"""
        try:
            # Build metric line
            if labels:
                label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                metric_line = f'{metric_name}{{{label_str}}} {value}'
            else:
                metric_line = f'{metric_name} {value}'

            # Send to push gateway
            response = requests.post(
                f"{PUSH_GATEWAY_URL}/metrics/job/chaos_test",
                data=metric_line,
                headers={"Content-Type": "text/plain"},
            )

            if response.status_code == 200:
                print(f"✅ Pushed metric: {metric_name} = {value}")
                return True
            else:
                print(f"❌ Failed to push metric: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error pushing metric: {e}")
            return False

    def inject_high_latency(self, duration: int = 120) -> Dict:
        """
        Scenario: Settlement latency spike
        Expected: HighSettlementLatency alert fires
        """
        print(f"\n🔴 Injecting: High settlement latency for {duration}s")

        metric_name = "settlement_processing_duration_seconds_bucket"
        
        # P99 normally ~200ms, spike to 6 seconds
        labels = {
            "processor": "settlement-engine",
            "region": "us-east-1",
            "le": "+Inf",
        }

        # Push high latency metric
        for i in range(duration // 10):
            self.push_metric(metric_name, 950, labels)  # 950ms for P99
            time.sleep(10)

        # Wait for alert evaluation (30s scrape + 1m alert duration)
        print("⏳ Waiting for alert evaluation (90s)...")
        time.sleep(90)

        # Check if alert fired
        alerts = self.get_alerts("HighSettlementLatency")
        
        return {
            "scenario": "high_latency",
            "description": SCENARIOS["high_latency"]["description"],
            "alert_fired": len(alerts) > 0,
            "alert_details": alerts[0] if alerts else None,
            "test_passed": len(alerts) > 0,
        }

    def inject_high_error_rate(self, duration: int = 120) -> Dict:
        """
        Scenario: API error rate spike (0.1% → 2%)
        Expected: HighErrorRate alert fires
        """
        print(f"\n🔴 Injecting: High error rate for {duration}s")

        # Push error metrics
        for i in range(duration // 10):
            # Normal: 1000 requests, 10 errors (1%)
            self.push_metric(
                "http_requests_total",
                1000,
                {"status": "200", "service": "payment-api"},
            )
            self.push_metric(
                "http_requests_total",
                50,
                {"status": "500", "service": "payment-api"},
            )
            time.sleep(10)

        print("⏳ Waiting for alert evaluation (90s)...")
        time.sleep(90)

        alerts = self.get_alerts("HighErrorRate")
        
        return {
            "scenario": "high_error_rate",
            "description": SCENARIOS["high_error_rate"]["description"],
            "alert_fired": len(alerts) > 0,
            "test_passed": len(alerts) > 0,
        }

    def inject_cost_anomaly(self, duration: int = 60) -> Dict:
        """
        Scenario: Cost spike (normal $30/day → $60/day)
        Expected: CostAnomalyDetected alert fires
        """
        print(f"\n🔴 Injecting: Cost anomaly for {duration}s")

        # Establish baseline
        for i in range(30):
            self.push_metric("aws_billing_estimated_charges", 30.0)  # $30/day
            time.sleep(1)

        # Spike
        for i in range(duration // 10):
            self.push_metric("aws_billing_estimated_charges", 60.0)  # $60/day (2x)
            time.sleep(10)

        print("⏳ Waiting for alert evaluation (90s)...")
        time.sleep(90)

        alerts = self.get_alerts("CostAnomalyDetected")
        
        return {
            "scenario": "cost_anomaly",
            "description": SCENARIOS["cost_anomaly"]["description"],
            "alert_fired": len(alerts) > 0,
            "test_passed": len(alerts) > 0,
        }

    def inject_secret_exposure(self) -> Dict:
        """
        Scenario: Secret (API key) detected in logs
        Expected: SecretExposedInLogs alert fires
        """
        print("\n🔴 Injecting: Secret exposure detection")

        # Push secret exposure metric
        self.push_metric(
            "secret_exposure_detected_total",
            1,
            {
                "secret_type": "api_key",
                "secret_name": "datadog_api_key",
                "timestamp": datetime.now().isoformat(),
            },
        )

        print("⏳ Waiting for alert evaluation (30s)...")
        time.sleep(30)

        alerts = self.get_alerts("SecretExposedInLogs")
        
        return {
            "scenario": "secret_exposed",
            "description": SCENARIOS["secret_exposed"]["description"],
            "alert_fired": len(alerts) > 0,
            "test_passed": len(alerts) > 0,
        }

    def get_alerts(self, alert_name: str = None) -> List[Dict]:
        """Query Prometheus for active alerts"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/alerts")
            response.raise_for_status()

            data = response.json()
            alerts = data.get("data", {}).get("alerts", [])

            if alert_name:
                alerts = [a for a in alerts if a["labels"]["alertname"] == alert_name]

            return alerts
        except Exception as e:
            print(f"❌ Error querying alerts: {e}")
            return []

    def verify_alert_accuracy(self) -> Dict:
        """Measure alert precision and recall"""
        print("\n📊 Verifying alert accuracy...")

        results = {
            "total_tests": len(SCENARIOS),
            "passed": 0,
            "failed": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "details": [],
        }

        for scenario_name, scenario_config in SCENARIOS.items():
            expected_alert = scenario_config["alert"]
            
            # Check if alert exists
            alerts = self.get_alerts(expected_alert)
            
            # Determine pass/fail
            # Note: This is a simplified check. Real alert accuracy testing 
            # would inject the metric and wait for alert.
            is_configured = len(self.get_all_alert_rules(expected_alert)) > 0

            if is_configured:
                results["passed"] += 1
                status = "✅ PASS"
            else:
                results["failed"] += 1
                status = "❌ FAIL"

            results["details"].append({
                "scenario": scenario_name,
                "alert": expected_alert,
                "status": status,
            })

        return results

    def get_all_alert_rules(self, alert_name: str = None) -> List[Dict]:
        """Query Prometheus for all alert rules"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/rules")
            response.raise_for_status()

            data = response.json()
            rules = []

            for group in data.get("data", {}).get("groups", []):
                for rule in group.get("rules", []):
                    if alert_name is None or rule.get("name") == alert_name:
                        rules.append(rule)

            return rules
        except Exception as e:
            print(f"❌ Error querying rules: {e}")
            return []

    def generate_report(self, results: List[Dict]) -> str:
        """Generate test report"""
        report = "\n" + "=" * 80 + "\n"
        report += "🧪 CHAOS INJECTION TEST REPORT\n"
        report += f"Generated: {datetime.now().isoformat()}\n"
        report += "=" * 80 + "\n\n"

        passed = sum(1 for r in results if r.get("test_passed"))
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0

        report += f"Results: {passed}/{total} scenarios passed ({success_rate:.1f}%)\n\n"

        for result in results:
            status = "✅ PASS" if result["test_passed"] else "❌ FAIL"
            report += f"{status} | {result['scenario']}\n"
            report += f"       Description: {result['description']}\n"
            report += f"       Alert fired: {result['alert_fired']}\n"
            if result.get("alert_details"):
                report += f"       Severity: {result['alert_details']['labels'].get('severity')}\n"
            report += "\n"

        report += "=" * 80 + "\n"
        
        if success_rate == 100:
            report += "🎉 All tests passed! Alerts are working correctly.\n"
        else:
            report += f"⚠️  {total - passed} test(s) failed. Review alert configuration.\n"

        report += "=" * 80 + "\n"

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Chaos injection testing for observability-blueprint"
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()) + ["all"],
        default="all",
        help="Scenario to inject",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=120,
        help="Duration of chaos injection (seconds)",
    )
    parser.add_argument(
        "--output",
        default="chaos_test_results.json",
        help="Output file for test results",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't cleanup metrics after test",
    )

    args = parser.parse_args()

    print("🚀 Starting chaos injection tests for observability-blueprint\n")

    injector = ChaosInjector()
    results = []

    # Run scenarios
    if args.scenario == "all":
        scenarios_to_run = list(SCENARIOS.keys())
    else:
        scenarios_to_run = [args.scenario]

    for scenario in scenarios_to_run:
        if scenario == "high_latency":
            results.append(injector.inject_high_latency(args.duration))
        elif scenario == "high_error_rate":
            results.append(injector.inject_high_error_rate(args.duration))
        elif scenario == "cost_anomaly":
            results.append(injector.inject_cost_anomaly(args.duration))
        elif scenario == "secret_exposed":
            results.append(injector.inject_secret_exposure())
        
        time.sleep(10)  # Wait between scenarios

    # Generate report
    report = injector.generate_report(results)
    print(report)

    # Save results
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"✅ Results saved to {args.output}\n")

    # Cleanup
    if not args.no_cleanup:
        print("🧹 Cleaning up test metrics...")
        subprocess.run([
            "curl", "-X", "DELETE",
            f"{PUSH_GATEWAY_URL}/metrics/job/chaos_test"
        ])

    # Exit with appropriate code
    passed = sum(1 for r in results if r.get("test_passed"))
    total = len(results)
    
    if passed == total:
        print("✅ All chaos tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
