# observability-blueprint: Daily Standup Template

Copy this template daily to track progress and maintain momentum.

---

## Week 1, Day 1: Monday

```
# Daily Standup: observability-blueprint
Date: 2024-01-15
Week: 1 / 12
Day: 1 / 5

## Planning
Target Hours: 7
Planned Tasks:
- [ ] Architecture design (Prometheus + Grafana + Loki + Tempo stack)
- [ ] Repo structure setup
- [ ] Define 3 personas (trading ops, finance controller, compliance officer)
- [ ] Create SLI/SLO templates

## In Progress
(none yet - starting day)

## Completed Today
(none yet)

## Blockers
- None yet

## Tomorrow's Focus
- Continue architecture design
- Start metrics definition (20+ core metrics)

## Code Metrics
Lines added: 0
Tests written: 0
Docs updated: Yes (architecture sketch)
Security scan: Pending

## Notes
- Starting fresh, energy high
- Reviewed fintech requirements (FCA, SOX, GDPR)
- Sketched system design: App → Prometheus (150k metrics/sec) → Grafana + Loki + Tempo

## Productivity Score
7/10 (planning day, lower output expected)
```

---

## Template for Daily Use

```markdown
# Daily Standup: observability-blueprint
Date: YYYY-MM-DD
Week: X / 12
Day: Y / 5
Start Time: HH:MM | Target Hours: 7

## Planning
Target Hours: 7
Planned Tasks:
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3
- [ ] Task 4
- [ ] Task 5

Estimated hours: 1 + 1.5 + 2 + 1.5 + 1 = 7

## In Progress
- [ ] Task: [description]
  - Status: [%] (e.g., 50%)
  - Time spent: 2 hours
  - Next: [what's next]

## Completed Today
- [x] Task: [description] ✅
  - Time spent: 1 hour
  - Output: [link to commit/PR]
  - Quality: [assessment]

- [x] Task: [description] ✅
  - Time spent: 1.5 hours
  - Output: [file created, PR merged, etc.]
  - Quality: [assessment]

## Blockers
- Blocker 1: [Description]
  - Mitigation: [What you'll do]
  - Impact: [Low/Medium/High]

- No blockers | [Describe any issue]

## Tomorrow's Focus (Top 3)
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

## Code Metrics (Self-Check)
Lines added: X
Tests written: X
Tests passing: X/Y
Code coverage: Z%
Docs updated: Yes/No
Security scan: Pass/Fail
Terraform validate: Pass/Fail
K8s manifest validation: Pass/Fail

## Actual Hours Spent
Start: HH:MM
End: HH:MM
Total: X hours
Variance: Planned 7 hrs, Actual X hrs (delta: ±Y hrs)

## Productivity Score
[8/10] - [Assessment. Be honest.]
- What went well: [1-2 things]
- What slowed you down: [blockers, distractions, unclear requirements]
- Tomorrow's pace adjustment: [speed up/maintain/slow down]

## Notes & Learnings
- Quick insight 1
- Quick insight 2
- Something to remember for next time

## PR/Commit Links
- [PR#123: Add Prometheus Terraform](https://github.com/...)
- [Commit: Initial repo structure](https://github.com/...)

## Energy Level
Mood: 😊 | Energy: 8/10 | Focus: 7/10
Burnout Risk: Low | Need break: No

---
```

---

## Weekly Summary Template

```markdown
# Weekly Summary: Week X
Dates: [Start] - [End]
Target Hours: 40-50
Actual Hours: X
On Track: Yes/No

## Completed Deliverables
- [x] Deliverable 1: [Description] (PR/commit link)
- [x] Deliverable 2: [Description] (PR/commit link)
- [ ] Deliverable 3: [Description] (Pushed to Week X+1)

## Code Statistics
Total Lines Added: X
Tests Written: X
Code Coverage: X%
Security Vulnerabilities: X
Documentation Pages: X

## Productivity Analysis
- Days on track: 4/5
- Days slipped: 1/5 (reason: [blocker])
- Average daily output: X hours
- Most productive time: [e.g., 9-11am, late evening]

## Blockers & Resolutions
| Blocker | Impact | Resolution | Status |
|---------|--------|-----------|--------|
| Unclear metrics definition | High | Clarified with team | ✅ Resolved |
| Terraform learning curve | Medium | Reviewed HashiCorp docs | ✅ Resolved |
| No actual metrics data | Medium | Created synthetic fintech data | ✅ Resolved |

## Weekly Productivity Score
8/10 - [Why this score]

## Next Week's Priorities
1. Priority 1
2. Priority 2
3. Priority 3

## Health Check
- Burnout risk: Low/Medium/High
- Motivation: [Assessment]
- Personal circumstances affecting progress: [if any]
```

---

## Milestone Checklist (Bi-Weekly)

```markdown
# Milestone: Week 1-2 Complete
Target: Architecture + Terraform + Basic Stack

## Deliverables
- [x] Architecture diagram (Prometheus + Grafana + Loki + Tempo)
- [x] Terraform IaC (VPC, EKS, RDS, S3)
- [x] Kubernetes manifests (deployments, services)
- [x] README.md (executive summary + quick start)
- [x] GitHub Actions CI/CD pipeline (basic)

## Code Quality Metrics
- Test coverage: 85%+ → ✅ Achieved 94%
- Security scan: 0 critical → ✅ Pass
- Documentation: Complete → ✅ 30+ pages

## Productivity
- Planned 80 hours: Actual 78 hours → 2.5% ahead
- Output quality: High (no rework needed)
- Team feedback: "Exceeds expectations"

## On Schedule?
✅ **YES** - Week 1-2 complete, on track for Week 3 start

## Decision Points for Week 3
- Continue with Dashboards (planned) or
- Add advanced features (optional)?
→ Decision: Stick to plan, dashboards in Week 3
```

---

## Red Flags & Course Correction

**If you see ANY of these, pause and adjust:**

| Red Flag | Response |
|----------|----------|
| Days 1-2: Spending >2 hours on single task (perfectionism) | Move on, iterate later. Aim for 50/50 rule: 50% done better than 100% late. |
| Day 3: No working code, only planning | Cut scope. MVP first, polish later. |
| Day 4-5: Already 3 hours behind daily target | Reduce next week's scope. 45 hrs real output > 50 hrs planned fantasy. |
| All week: Tests not written | Stop. Write tests before more features. Debt compounds. |
| Mid-week: Skipped security scan | Go back, run it. Non-negotiable. |
| Friday: Haven't shipped anything | Merge WIP anyway. "Done" > "perfect but hidden". |

**Course Correction Formula:**
```
If (actual_time - planned_time) > 2 hours:
  scope_cut = 20%
  re_plan week N+1
Else:
  maintain pace
```

---

## Weekly Metrics You Care About

Track these numbers obsessively:

```
Week 1: 30 hours actual → avg 6 hrs/day → ✅ On track
Week 2: 35 hours actual → avg 7 hrs/day → ✅ Accelerating
Week 3: 40 hours actual → avg 8 hrs/day → ✅ Sustainable pace
Week 4: 45 hours actual → avg 9 hrs/day → ⚠️ At capacity (max is 50)
Week 5: 50 hours actual → avg 10 hrs/day → 🔴 Unsustainable (reduce scope)
```

**Your Target Velocity:**
- Steady: 40-45 hours/week (sustainable for 12 weeks)
- Sprints: 50 hours/week (max, only for 2-3 weeks)
- Recovery: 30 hours/week (after intensive sprint)

---

## Real Example: Week 1, Day 3 (Wednesday)

```
# Daily Standup: observability-blueprint
Date: 2024-01-17
Week: 1 / 12
Day: 3 / 5
Start Time: 08:30 | Target Hours: 7

## Planning
Target Hours: 7
Planned Tasks:
- [ ] Finish metrics definition (20+ metrics)
- [ ] Create SLO templates
- [ ] Start Terraform scaffolding
- [ ] Write first test suite outline

## In Progress
- [ ] Metrics definition (70% complete)
  - Status: Defined 18/20 metrics
  - Time spent: 2.5 hours
  - Next: Add payment gateway latency + cost-per-tx metrics

## Completed Today
- [x] Finalized 3 personas (trading ops, finance, compliance) ✅
  - Time spent: 0.5 hours
  - Output: personas.md (500 words)
  - Quality: Great, very detailed

- [x] Reviewed SLO frameworks (Google SRE, AWS) ✅
  - Time spent: 1.5 hours
  - Output: learning notes, ready to write templates
  - Quality: Good, learned about error budgets

- [x] Created metrics taxonomy (by service, by tier) ✅
  - Time spent: 1 hour
  - Output: metrics_taxonomy.md (GitHub commit xyz123)
  - Quality: Solid foundation, no rework needed

## Blockers
- None so far - smooth sailing

## Tomorrow's Focus (Top 3)
1. Finish metrics definition (2 more metrics)
2. Write SLO templates (error budget, latency SLOs)
3. Create Terraform folder structure + start VPC code

## Code Metrics
Lines added: 240 (mostly docs, some YAML)
Tests written: 0 (not applicable yet, docs phase)
Docs updated: Yes (+3 new markdown files)
Terraform validate: Not started yet

## Actual Hours Spent
Start: 08:30
End: 17:00 (with 1 hour lunch)
Total: 7.5 hours
Variance: Planned 7 hrs, Actual 7.5 hrs (delta: +0.5 hrs, within tolerance)

## Productivity Score
8/10 - Good progress, clear thinking, no wasted time
- What went well: Clear direction, found great SRE docs, metrics feel right
- What slowed me down: Minute perfectionism on metrics naming (stopped myself at 1 hour)
- Tomorrow's pace: Maintain, maybe speed up

## Notes & Learnings
- SLO design is hard; need to balance ambition vs reality
- Google SRE book's "error budget" concept is KEY for fintech (e.g., "0.01% error = $2k/day cost")
- Realized I should add "compliance drift" as a metric (add detection of unencrypted secrets)
- Team working in observability space seems small - that's good for portfolio differentiation

## PR/Commit Links
- [Commit: Personas and use case definition](https://github.com/yourusername/observability-blueprint/commit/abc123)
- [Commit: Metrics taxonomy](https://github.com/yourusername/observability-blueprint/commit/def456)

## Energy Level
Mood: 😊 | Energy: 8/10 | Focus: 8/10
Burnout Risk: None | On track: Yes
```

---

## End-of-Week Ritual (Friday Evening)

**Do this every Friday at 5pm:**

```
1. Run this command:
   git log --oneline --since="7 days ago" | wc -l
   → How many commits this week?

2. Count files created:
   find . -name "*.md" -o -name "*.yaml" -o -name "*.tf" | wc -l
   → How many artifacts?

3. Verify tests passing:
   pytest tests/ -v --tb=short
   → All green?

4. Check security:
   tfsec terraform/ && trivy . && snyk test
   → Any new vulns?

5. Generate metrics:
   echo "Week X: Y hours, Z artifacts, W commits"
   → Track in spreadsheet

6. Write weekly summary (template above)

7. Celebrate! 🎉
   "This week I [shipped X, learned Y, prevented Z]"
```

---

## Burnout Prevention

**If you feel any of these, STOP and adjust:**
- Sunday night dread about Monday
- Skipping breaks/meals to "catch up"
- Thinking about work at 11pm
- Less enthusiasm than Week 1
- Defensive about your pace

**Adjustment formula:**
```
If burnout_risk > "low":
  reduce_weekly_target_by(10_hours)
  take_full_weekend_off()
  schedule_15min_standdown_daily()
```

---

## Success Criteria

**You've succeeded when:**

✅ 12 weeks complete
✅ All 12 week milestones achieved
✅ GitHub repo at 50+ stars (proof of quality)
✅ Case studies downloadable + impressive
✅ Ready for interviews ("Walk me through this")
✅ Burnout: None (sustainable pace)
✅ Portfolio: Strongest piece yet

---

**Print this template, fill it out daily, celebrate progress.** 🚀
