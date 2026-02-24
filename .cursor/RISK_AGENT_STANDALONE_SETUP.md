# Risk Agent — Standalone Setup on a New Project

Use the **Risk Sentinel** (Risk agent) **only** on a new project, without the full ESEPCS system (no Scheduling, Cost, or Volt agents, no full orchestrator rule).

---

## What You Get

- **Risk register** — add/update risks, probability/impact, correlation, mitigation.
- **3-point estimates** — optimistic / most likely / pessimistic for schedule (QSRA) and cost (QCRA).
- **QSRA / QCRA** — schedule and cost risk analysis (Monte Carlo or analytical), P50/P80, criticality.
- **Supply chain** — scan for raw material shortages; map to project WBS/procurement.
- **Weather–schedule** — correlate weather (heat, freeze, wind) with concrete pours, crane lifts; **72-hour predictive alerts** to shift crews or reschedule.
- **Lessons Learned** — read project lessons when proposing mitigations; suggest new lessons after RCA.

When used standalone, the agent does **not** hand off to Scheduling or Cost agents; you handle schedule/cost updates yourself or add those agents later.

---

## Steps to Use Risk Agent Standalone on a New Project

### Step 1: Create the new project folder

- Create a new folder for the project (e.g. `Project_X_Risk`, `ClientY_Risk_Only`).
- Do **not** put it inside a folder that already has a full `.cursor` with other agents if you want a risk-only workspace.

### Step 2: Add only the Risk agent from ECEPCS MASTER

Copy **only** the **risk-agent** skill into the new project:

| Copy this | To here (new project) |
|-----------|------------------------|
| **ECEPCS MASTER\.cursor\skills\risk-agent\** (entire folder) | **YourNewProject\.cursor\skills\risk-agent\** |

**How to do it:**

1. In the new project folder, create: `.cursor\skills\`
2. Copy the folder **risk-agent** (containing `SKILL.md`) from **ECEPCS MASTER\.cursor\skills\risk-agent** into **YourNewProject\.cursor\skills\**

You should end up with:

```
YourNewProject/
└── .cursor/
    └── skills/
        └── risk-agent/
            └── SKILL.md
```

**Do not copy** (for standalone Risk agent):

- `rules\project-controls-orchestrator.mdc` — optional; see Step 4.
- `skills\scheduling-agent\`, `skills\cost-agent\`, `skills\volt-agent\`, `skills\project-controls-agent\` — not needed for risk-only.

### Step 3: Add project risk files in the new folder

Put the files the Risk agent uses in the **new project folder** (root or a subfolder you’ll reference):

| File | Purpose |
|------|---------|
| **Risk_Register.md** (or **\*_Risk_Register.md**) | Risks by WBS, probability/impact, schedule/cost impact, risk level, correlation, mitigation. Create empty or from template. |
| **Three_Point_Estimates_QSRA_QCRA.md** (optional) | 3-point durations by WBS (QSRA); 3-point cost by CBS (QCRA). |
| **CPM_Development_Guide.md** or **WBS** (optional) | WBS/CBS for mapping risks and 3-point data. |
| **Activities.csv**, **Relationships.csv** (optional) | For QSRA model input if you run schedule risk. |
| **Lessons_Learned.md** (optional) | So the agent can use past lessons when proposing mitigations. |

**Minimum to start:** Create **Risk_Register.md** with headers (e.g. ID, WBS, Description, Probability, Schedule Impact, Cost Impact, Risk Level, Correlation, Mitigation). The agent can populate it.

### Step 4: Orchestrator rule (optional)

- **No rule:** Cursor still loads the Risk agent from `.cursor/skills/risk-agent/`. You can use Chat or Composer and ask for “risk register,” “QSRA,” “supply chain,” “weather vs schedule,” “72-hour alerts,” etc. The skill’s description tells Cursor when to use it.
- **Minimal rule (optional):** If you want a short note in the workspace that this project uses only the Risk Sentinel, create `.cursor/rules/` and add a small rule file (e.g. “This project uses the Risk Sentinel (risk-agent) for risk register, QSRA, QCRA, supply chain, and weather–schedule alerts only.”). This is optional.

### Step 5: Open the new project in Cursor

1. In Cursor: **File → Open Folder**.
2. Select the **new project folder** (the one that contains `.cursor/skills/risk-agent/` and your risk files).
3. Use **Chat** or **Composer** and ask risk-related questions.

**Example prompts:**

- “Update the risk register with a new risk: [description], WBS X, probability Y, impact Z.”
- “Run a QSRA using the 3-point durations in the workspace.”
- “Scan for supply chain risks that could affect our electrical scope and add them to the risk register.”
- “Correlate the next 7 days’ weather with our concrete and crane activities and give me 72-hour alerts.”
- “Propose mitigation options for risk ID R-003 and cite any relevant lessons from Lessons_Learned.”

### Step 6: HITL / Thresholds (when used standalone)

The Risk agent skill describes **Risk Threshold Matrix** and **HITL** (Level 1/2/3). When used **standalone**:

- There is **no** shared orchestrator, so treat all material changes as **Advisory**: propose options (e.g. Decision Matrix / Change Impact Memo); **you** approve before the agent “executes” (e.g. before you accept edits to Risk_Register or QSRA/QCRA outputs).
- You can still use the same thresholds (e.g. &lt; 2 days and &lt; $5k = log only; 2–7 days or $5k–$50k = propose; &gt; 7 days or &gt; $50k = flag and RCA) as guidance when you ask the agent to “propose” or “flag” based on impact.

---

## Checklist — Standalone Risk Agent

- [ ] New project folder created.
- [ ] **ECEPCS MASTER\.cursor\skills\risk-agent\** copied to **YourNewProject\.cursor\skills\risk-agent\** (only this skill).
- [ ] **Risk_Register.md** (or equivalent) created in the new project.
- [ ] Optional: 3-point table, CPM guide/WBS, Activities/Relationships, Lessons_Learned.
- [ ] New project folder opened in Cursor (**File → Open Folder**).
- [ ] Tested in Chat (e.g. “What risk files do you see?” or “Add a draft risk to the register”).

---

## Summary

| Goal | Action |
|------|--------|
| **Use only the Risk agent** | Copy **only** `ECEPCS MASTER\.cursor\skills\risk-agent\` to `YourNewProject\.cursor\skills\risk-agent\`. |
| **Isolate from other projects** | Use a **dedicated folder** for the new project and open that folder in Cursor. |
| **No full ESEPCS** | Do **not** copy the full `.cursor` (no other agents, no full orchestrator unless you want a minimal rule). |

For the **full ESEPCS** (all agents + orchestrator) on a new project, use **ESEPCS_NEW_PROJECT_SETUP.md** instead.
