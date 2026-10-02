#!/usr/bin/env python3
"""
observability-blueprint: ROI Calculator

Calculate return on investment for observability-blueprint vs commercial solutions.
Useful for pitch decks and financial discussions with CFOs.

Usage:
    python scripts/calculate_roi.py --gmv=2000000000 --team_size=50
    python scripts/calculate_roi.py --gmv=2B --team_size=50 --output=roi_report.pdf
"""

import json
import argparse
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime


@dataclass
class Assumptions:
    """Financial assumptions for ROI calculation"""
    
    # Business metrics
    annual_gmv: float  # Gross Merchandise Value
    team_size: int  # Platform engineering team size
    incident_frequency: float  # Incidents per month
    avg_incident_duration: float  # Hours per incident
    
    # Cost assumptions
    engineer_hourly_rate: float = 150  # Burdened cost
    datadog_monthly_cost: float = 2500
    newrelic_monthly_cost: float = 2000
    cloudwatch_monthly_cost: float = 1200
    
    # Business impact assumptions
    revenue_per_minute: float = 0  # Calculated from GMV
    customer_churn_rate_per_incident: float = 0.001  # 0.1% of users churn
    avg_customer_lifetime_value: float = 1000
    regulatory_fine_per_incident: float = 50000


class ROICalculator:
    """Calculate financial impact of observability-blueprint"""
    
    def __init__(self, assumptions: Assumptions):
        self.assumptions = assumptions
        # Calculate derived metrics
        self.assumptions.revenue_per_minute = assumptions.annual_gmv / (365 * 24 * 60)
    
    def calculate_infrastructure_costs(self) -> Dict[str, Dict[str, float]]:
        """Calculate monthly infrastructure costs for each solution"""
        
        return {
            "datadog": {
                "metrics": 1500,
                "logs": 500,
                "apm": 300,
                "total_monthly": self.assumptions.datadog_monthly_cost,
                "total_annual": self.assumptions.datadog_monthly_cost * 12,
            },
            "newrelic": {
                "total_monthly": self.assumptions.newrelic_monthly_cost,
                "total_annual": self.assumptions.newrelic_monthly_cost * 12,
            },
            "cloudwatch": {
                "total_monthly": self.assumptions.cloudwatch_monthly_cost,
                "total_annual": self.assumptions.cloudwatch_monthly_cost * 12,
            },
            "observability_blueprint": {
                "prometheus": 150,
                "grafana": 300,
                "loki": 200,
                "tempo": 250,
                "infrastructure_overhead": 100,
                "total_monthly": 900,
                "total_annual": 900 * 12,
            },
        }
    
    def calculate_incident_costs(self, detection_time_improvement: float = 0.5) -> Dict[str, float]:
        """
        Calculate cost of incidents (both with and without observability)
        
        Args:
            detection_time_improvement: How much faster detection is (0.5 = 50% faster)
        """
        
        # Baseline: incidents per month
        incidents_per_month = self.assumptions.incident_frequency
        
        # Time to detect (baseline 4 hours, with observability 30 minutes)
        baseline_detection_hours = 4.0
        improved_detection_hours = baseline_detection_hours * (1 - detection_time_improvement)
        
        # Total incident duration (detection + remediation)
        baseline_duration = self.assumptions.avg_incident_duration
        improved_duration = baseline_duration - (baseline_detection_hours - improved_detection_hours)
        
        # Cost per incident
        time_cost_per_incident = baseline_duration * self.assumptions.engineer_hourly_rate * 3  # 3 engineers
        
        # Revenue impact during incident (locked transactions)
        locked_transactions = baseline_detection_hours * self.assumptions.revenue_per_minute * 60
        customer_churn_impact = locked_transactions * self.assumptions.customer_churn_rate_per_incident * self.assumptions.avg_customer_lifetime_value
        
        # Regulatory fines (for settlement delays, compliance issues)
        regulatory_impact = self.assumptions.regulatory_fine_per_incident
        
        # Calculate annual impact
        incidents_per_year = incidents_per_month * 12
        
        baseline_total_cost = incidents_per_year * (time_cost_per_incident + customer_churn_impact + regulatory_impact)
        
        # With observability: reduced detection time
        improved_duration_minutes = improved_duration * 60
        improved_locked_transactions = improved_detection_hours * self.assumptions.revenue_per_minute * 60
        improved_customer_churn = improved_locked_transactions * self.assumptions.customer_churn_rate_per_incident * self.assumptions.avg_customer_lifetime_value
        
        improved_cost_per_incident = (
            improved_duration * self.assumptions.engineer_hourly_rate * 3 +
            improved_customer_churn +
            regulatory_impact  # Even with obs, some regulatory risk remains
        )
        
        improved_total_cost = incidents_per_year * improved_cost_per_incident
        
        return {
            "baseline_incidents_per_year": incidents_per_year,
            "baseline_detection_hours": baseline_detection_hours,
            "baseline_incident_duration": baseline_duration,
            "baseline_cost_per_incident": time_cost_per_incident + customer_churn_impact + regulatory_impact,
            "baseline_annual_cost": baseline_total_cost,
            
            "improved_detection_hours": improved_detection_hours,
            "improved_incident_duration": improved_duration,
            "improved_cost_per_incident": improved_cost_per_incident,
            "improved_annual_cost": improved_total_cost,
            
            "annual_savings": baseline_total_cost - improved_total_cost,
        }
    
    def calculate_team_productivity(self) -> Dict[str, float]:
        """Calculate time savings for platform engineering team"""
        
        # Hours per week on observability management
        hours_managing_datadog_per_week = 8  # Configuration, alerts, dashboards
        hours_with_blueprint_per_week = 3  # Maintenance, tuning, minor changes
        
        hours_saved_per_week = hours_managing_datadog_per_week - hours_with_blueprint_per_week
        hours_saved_per_year = hours_saved_per_week * 52
        
        # Value of freed-up time
        value_of_freed_time = hours_saved_per_year * self.assumptions.engineer_hourly_rate
        
        # What they can do with freed-up time
        # Example: 1 engineer can spend 50% on observability, 50% on other projects
        headcount_equivalent = hours_saved_per_year / (2080 * 0.5)  # 2080 = hours/year, 0.5 = allocation
        
        return {
            "hours_saved_per_week": hours_saved_per_week,
            "hours_saved_per_year": hours_saved_per_year,
            "value_in_engineer_time": value_of_freed_time,
            "headcount_equivalent": headcount_equivalent,
        }
    
    def calculate_5_year_roi(self) -> Dict[str, any]:
        """Calculate 5-year ROI"""
        
        years = 5
        
        # Costs
        infrastructure = self.calculate_infrastructure_costs()
        
        baseline_infra_cost = infrastructure["datadog"]["total_annual"] * years
        blueprint_infra_cost = infrastructure["observability_blueprint"]["total_annual"] * years
        
        # Implementation cost (one-time)
        implementation_cost = 60 * 150 * 2  # 60 hours at $150/hr for 2 engineers
        
        # Incident costs
        incident_costs = self.calculate_incident_costs()
        baseline_incident_cost = incident_costs["baseline_annual_cost"] * years
        improved_incident_cost = incident_costs["improved_annual_cost"] * years
        
        # Productivity gains
        productivity = self.calculate_team_productivity()
        productivity_gain = productivity["value_in_engineer_time"] * years
        
        # Total costs
        baseline_total = baseline_infra_cost + baseline_incident_cost
        blueprint_total = blueprint_infra_cost + improved_incident_cost + implementation_cost
        
        # Net benefit
        net_benefit = baseline_total - blueprint_total
        roi_percent = (net_benefit / implementation_cost * 100) if implementation_cost > 0 else 0
        payback_period_months = (implementation_cost / incident_costs["annual_savings"]) * 12 if incident_costs["annual_savings"] > 0 else float('inf')
        
        return {
            "implementation_cost": implementation_cost,
            "baseline_infrastructure_cost_5yr": baseline_infra_cost,
            "blueprint_infrastructure_cost_5yr": blueprint_infra_cost,
            "infrastructure_savings_5yr": baseline_infra_cost - blueprint_infra_cost,
            
            "baseline_incident_cost_5yr": baseline_incident_cost,
            "blueprint_incident_cost_5yr": improved_incident_cost,
            "incident_savings_5yr": baseline_incident_cost - improved_incident_cost,
            
            "productivity_gain_5yr": productivity_gain,
            
            "total_5yr_benefit": net_benefit,
            "roi_percent": roi_percent,
            "payback_period_months": payback_period_months,
        }
    
    def generate_report(self) -> str:
        """Generate human-readable ROI report"""
        
        infrastructure = self.calculate_infrastructure_costs()
        incident = self.calculate_incident_costs()
        productivity = self.calculate_team_productivity()
        roi = self.calculate_5_year_roi()
        
        report = "\n" + "=" * 80 + "\n"
        report += "💰 observability-blueprint: FINANCIAL IMPACT ANALYSIS\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "=" * 80 + "\n\n"
        
        # Assumptions
        report += "📊 ASSUMPTIONS\n"
        report += "-" * 80 + "\n"
        report += f"Annual GMV: ${self.assumptions.annual_gmv:,.0f}\n"
        report += f"Team Size: {self.assumptions.team_size} engineers\n"
        report += f"Incident Frequency: {self.assumptions.incident_frequency:.1f} incidents/month\n"
        report += f"Avg Incident Duration: {self.assumptions.avg_incident_duration:.1f} hours\n"
        report += f"Engineer Hourly Rate: ${self.assumptions.engineer_hourly_rate:.0f}\n\n"
        
        # Infrastructure Costs
        report += "💻 INFRASTRUCTURE COSTS (Monthly)\n"
        report += "-" * 80 + "\n"
        for solution, costs in infrastructure.items():
            monthly = costs.get("total_monthly", sum([v for k, v in costs.items() if k != "total_monthly" and k != "total_annual"]))
            report += f"{solution.upper():30} ${monthly:>10,.0f}\n"
        report += f"\nAnnual Cost Difference: ${infrastructure['datadog']['total_annual'] - infrastructure['observability_blueprint']['total_annual']:,.0f}\n\n"
        
        # Incident Costs
        report += "🚨 INCIDENT IMPACT (Annual)\n"
        report += "-" * 80 + "\n"
        report += f"Incidents per Year: {incident['baseline_incidents_per_year']:.0f}\n"
        report += f"Detection Time (Before): {incident['baseline_detection_hours']:.1f} hours\n"
        report += f"Detection Time (After): {incident['improved_detection_hours']:.1f} hours\n"
        report += f"Improvement: {((incident['baseline_detection_hours'] - incident['improved_detection_hours']) / incident['baseline_detection_hours'] * 100):.0f}% faster\n\n"
        report += f"Cost per Incident (Before): ${incident['baseline_cost_per_incident']:,.0f}\n"
        report += f"Cost per Incident (After): ${incident['improved_cost_per_incident']:,.0f}\n"
        report += f"Annual Incident Cost Savings: ${incident['annual_savings']:,.0f}\n\n"
        
        # Productivity
        report += "👥 TEAM PRODUCTIVITY GAINS (Annual)\n"
        report += "-" * 80 + "\n"
        report += f"Hours Saved per Week: {productivity['hours_saved_per_week']:.0f}\n"
        report += f"Hours Saved per Year: {productivity['hours_saved_per_year']:.0f}\n"
        report += f"Value of Freed Time: ${productivity['value_in_engineer_time']:,.0f}\n"
        report += f"Headcount Equivalent: {productivity['headcount_equivalent']:.1f} FTE\n\n"
        
        # 5-Year ROI
        report += "📈 5-YEAR ROI ANALYSIS\n"
        report += "=" * 80 + "\n"
        report += f"Implementation Cost: ${roi['implementation_cost']:,.0f}\n"
        report += f"Infrastructure Savings (5yr): ${roi['infrastructure_savings_5yr']:,.0f}\n"
        report += f"Incident Savings (5yr): ${roi['incident_savings_5yr']:,.0f}\n"
        report += f"Total 5-Year Benefit: ${roi['total_5yr_benefit']:,.0f}\n\n"
        report += f"ROI: {roi['roi_percent']:.0f}%\n"
        report += f"Payback Period: {roi['payback_period_months']:.1f} months\n\n"
        
        # Summary
        report += "=" * 80 + "\n"
        if roi['payback_period_months'] < 12:
            report += f"✅ RECOMMENDATION: STRONG POSITIVE\n"
            report += f"   Payback in {roi['payback_period_months']:.1f} months\n"
            report += f"   {roi['total_5yr_benefit']:,.0f} net benefit over 5 years\n"
        else:
            report += f"⚠️  RECOMMENDATION: EVALUATE FURTHER\n"
            report += f"   Payback in {roi['payback_period_months']:.1f} months\n"
        
        report += "=" * 80 + "\n\n"
        
        return report


def parse_gmv(gmv_str: str) -> float:
    """Parse GMV string like '2B' or '2000000000' to float"""
    
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000, "t": 1_000_000_000_000}
    
    gmv_str = gmv_str.lower().strip()
    
    for suffix, multiplier in multipliers.items():
        if gmv_str.endswith(suffix):
            try:
                return float(gmv_str[:-1]) * multiplier
            except ValueError:
                pass
    
    try:
        return float(gmv_str)
    except ValueError:
        raise ValueError(f"Invalid GMV format: {gmv_str}")


def main():
    parser = argparse.ArgumentParser(
        description="Calculate ROI for observability-blueprint"
    )
    parser.add_argument(
        "--gmv",
        default="2B",
        help="Annual GMV (e.g., '2B', '2000000000')",
    )
    parser.add_argument(
        "--team_size",
        type=int,
        default=50,
        help="Platform engineering team size",
    )
    parser.add_argument(
        "--incident_frequency",
        type=float,
        default=2,
        help="Incidents per month",
    )
    parser.add_argument(
        "--incident_duration",
        type=float,
        default=4,
        help="Average incident duration (hours)",
    )
    parser.add_argument(
        "--output",
        help="Output file (JSON or text)",
    )
    
    args = parser.parse_args()
    
    # Parse GMV
    annual_gmv = parse_gmv(args.gmv)
    
    # Create assumptions
    assumptions = Assumptions(
        annual_gmv=annual_gmv,
        team_size=args.team_size,
        incident_frequency=args.incident_frequency,
        avg_incident_duration=args.incident_duration,
    )
    
    # Calculate ROI
    calculator = ROICalculator(assumptions)
    report = calculator.generate_report()
    
    # Print report
    print(report)
    
    # Save if requested
    if args.output:
        if args.output.endswith('.json'):
            roi = calculator.calculate_5_year_roi()
            with open(args.output, 'w') as f:
                json.dump(roi, f, indent=2)
        else:
            with open(args.output, 'w') as f:
                f.write(report)
        print(f"📄 Report saved to: {args.output}\n")


if __name__ == "__main__":
    main()
