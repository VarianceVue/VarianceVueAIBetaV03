# P6 CPM Best Practices and Spec Interpretation

Concise reference for interpreting scheduling specifications and developing Primavera P6 CPM schedules.

---

## Work Breakdown Structure (WBS)

- **Purpose**: Organize project scope hierarchically. WBS is the foundation of CPM scheduling.
- **Levels**: Prefer 3–4 levels. Avoid excessive depth.
- **Root**: Project name at top level.
- **Structure**: Scope-based (what is being produced), not organizational.
- **Common patterns**:
  - Phase-based: Design → Procurement → Construction → Commissioning
  - Discipline-based: Civil, Mechanical, Electrical, I&C
  - Area-based: Zone A, Zone B, Systems
- **Spec interpretation**: Look for deliverables, phases, disciplines, or areas in the spec to infer WBS structure.

---

## Activities

- **Definition**: Lowest-level work elements. Activities sit under WBS elements.
- **Naming**: Use action verbs (e.g., "Pour foundation", "Install HVAC", "Submit submittals").
- **Activity types**:
  - **Task**: Work with duration and resources
  - **Milestone**: Zero-duration marker (completions, approvals, gates)
  - **Summary**: Aggregates child activities; typically WBS-level
- **Activity ID**: Unique code per activity. Often hierarchical (e.g., 1.1.1, 1.1.2).
- **Spec interpretation**: Extract activity-like items, milestones, and deliverables from the spec text and tables.

---

## Relationships and Logic

- **Types**:
  - **FS (Finish-to-Start)**: Most common; successor starts when predecessor finishes
  - **SS (Start-to-Start)**: Both start together or with lag
  - **FF (Finish-to-Finish)**: Both finish together or with lag
  - **SF (Start-to-Finish)**: Less common
- **Lag/Lead**: Negative lag = lead; positive lag = delay.
- **Best practice**: Logic-driven schedule. Minimize date constraints unless the spec requires them.
- **Spec interpretation**: Look for sequencing ("after", "before", "upon completion"), dependencies, and phase gates.

---

## Calendars

- **Global calendar**: Default work week (e.g., 5-day, 8-hour).
- **Resource calendars**: For labor, equipment, or weather-sensitive work.
- **Spec interpretation**: Note work hours, shift assumptions, holidays, and weather windows.

---

## Constraints

- **Mandatory Start/Finish**: Spec may require specific dates.
- **Start No Earlier Than / Finish No Later Than**: Common for milestones.
- **As Late As Possible**: Use sparingly.
- **Spec interpretation**: Flag any mandated dates or milestone requirements.

---

## CPM Concepts

- **Critical path**: Longest path through the network; determines project end date.
- **Float**: Total float = slack; zero float = critical.
- **Baseline**: Snapshot for comparison. Specs may require baseline approval.
- **Progress tracking**: Actual start/finish, percent complete, remaining duration.

---

## Common Spec Standards

| Standard/Agency | Typical Requirements |
|-----------------|----------------------|
| **NYSDOT** | CPM Scheduling Guide; baseline approval; float limits; specific activity types |
| **AACE** | Practice standards; earned value; schedule quality metrics |
| **Owner/agency** | WBS structure, activity codes, report formats, update frequency |

---

## Spec Interpretation Checklist

- [ ] Scope, deliverables, and phases
- [ ] WBS structure or templates mentioned
- [ ] Activities, milestones, or work packages
- [ ] Sequencing, dependencies, or phase gates
- [ ] Calendars, work hours, holidays
- [ ] Constraints, mandatory dates, or milestones
- [ ] Standards (NYSDOT, AACE, owner-specific)
- [ ] Reporting or update requirements
