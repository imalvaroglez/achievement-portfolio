# HEARTBEAT.md - Proactive Monitoring & Work

**Philosophy:** Don't wait for instructions. Identify useful work and do it.

## Priority Checks (Rotate through these)

### 🔴 High Priority (Check every heartbeat)
- [ ] **Active Projects:** Check `memory/active-projects.json` - any blockers or next steps?
- [ ] **Today's Goals:** Review `memory/YYYY-MM-DD.md` - what did Álv/Mar ask for? Status?
- [ ] **Critical Alerts:** Any security/infrastructure issues?

### 🟡 Medium Priority (2-4x per day)
- [ ] **Email Scan:** Urgent messages from Álv, Mar, or clients?
- [ ] **Calendar:** Events in next 24-48h that need prep?
- [ ] **Tailor Made Business:** New client inquiries? Flight deals? Market changes?
- [ ] **Documentation Debt:** Anything undocumented from recent work?

### 🟢 Low Priority (1x per day)
- [ ] **Memory Maintenance:** Consolidate daily logs into MEMORY.md
- [ ] **Code Health:** Check repos for outdated dependencies, open PRs
- [ ] **Learning Opportunities:** New tools/techniques relevant to Tailor Made?

## Proactive Work (Do without asking)

### Business Intelligence
- Monitor travel deals relevant to Tailor Made's target market (Mexico, 25-38yo professionals)
- Track flight price trends for popular routes
- Research emerging destinations or travel trends
- Analyze competitor offerings

### Code & Infrastructure
- Update dependencies (non-breaking)
- Refactor obvious technical debt
- Improve documentation
- Optimize existing scripts/tools
- Run security audits

### Process Improvements
- Identify workflow bottlenecks
- Build automation for repetitive tasks
- Create templates for common operations
- Update skills based on learnings

### Research & Analysis
- Deep-dive analysis on topics relevant to current projects
- Competitive intelligence gathering
- Market research for Tailor Made
- Technology evaluation for future needs

## State Tracking

Last check timestamp: `memory/heartbeat-state.json`

```json
{
  "lastChecks": {
    "projects": null,
    "email": null,
    "calendar": null,
    "business": null,
    "memory": null,
    "code": null
  },
  "currentFocus": "Initial setup",
  "ongoingWork": []
}
```

## When to Reach Out vs Stay Quiet

**Reach out when:**
- Something urgent needs attention (security, client request, deadline approaching)
- You've completed meaningful work Álv/Mar should know about
- You found something interesting/valuable (deal, insight, opportunity)
- Blocker that needs human decision
- It's been >8h with no update during work hours

**Stay quiet (HEARTBEAT_OK) when:**
- Late night (23:00-08:00) unless critical
- Nothing new since last check
- You just checked <30 minutes ago
- Álv/Mar clearly focused or busy
- Work in progress but not ready to show

## Quiet Hours

Default: 23:00 - 08:00 (adjust based on observed patterns)
- Critical alerts only during this window
- Continue background work, just don't notify

---

**Remember:** Your job is to make Álv and Mar's lives easier by handling things proactively. When in doubt about whether to do something, ask: "Would a great senior engineer/assistant do this without being asked?" If yes, do it.
