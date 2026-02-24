# ESEPCS — New Project Setup (Isolated Copy)

Steps to **invoke or copy** the **Earned Schedule Excellence Project Controls System (ESEPCS)** on a **new project** and keep it **isolated** from other projects.

**Canonical source:** The master copy of ESEPCS lives in the **ECEPCS MASTER** folder (same parent as this project, or wherever you keep it). Always copy **from ECEPCS MASTER** into a new project so each project gets a clean, isolated copy.

---

## Option A: New project = new folder (recommended for full isolation)

Each project is a **separate folder** that you open in Cursor. That folder has its own `.cursor` (agents + rules) and its own project data. No shared state with other projects.

### Step 1: Create the new project folder

- Create a new folder for the new project (e.g. `Project_Controls_ClientX`, `Datacenter_Phase2`, or `NewProject_Name`).
- Do **not** put it inside an existing project folder that already has its own `.cursor` if you want strict isolation.

### Step 2: Copy the ESEPCS system from ECEPCS MASTER into the new folder

Copy the **entire `.cursor` folder** from **ECEPCS MASTER** (not from an existing project) into the **root** of the new project folder.

**What to copy:**

| Source (canonical) | Destination (new project folder) |
|--------------------|-----------------------------------|
| `ECEPCS MASTER\.cursor\` (entire folder) | `YourNewProject\.cursor\` |

**Contents of `.cursor` to copy:**

- `.cursor\rules\project-controls-orchestrator.mdc`
- `.cursor\skills\scheduling-agent\SKILL.md`
- `.cursor\skills\cost-agent\SKILL.md`
- `.cursor\skills\risk-agent\SKILL.md`
- `.cursor\skills\volt-agent\SKILL.md`
- `.cursor\skills\project-controls-agent\` (SKILL.md, reference.md, scripts\ if you use PDF extraction)

**Optional (docs only):**

- `.cursor\DEPLOYMENT_READINESS.md`
- `.cursor\HOW_TO_DEPLOY_IN_CURSOR.md`
- `.cursor\ESEPCS_NEW_PROJECT_SETUP.md` (this file)

**Lessons_Learned template:**

- Copy `ECEPCS MASTER\Lessons_Learned.md` into the new project root as `Lessons_Learned.md`, then clear or replace the example entries with project-specific lessons. Do **not** copy another project’s filled-in Lessons_Learned—each project gets its own.

**Do not copy** (project-specific; create fresh per project):

- Filled-in `Lessons_Learned.md` from another project—use the template from ECEPCS MASTER only.
- `Activities.csv`, `Relationships.csv`, `Risk_Register.md`, etc.—these belong to the **current** project; the new project gets its own.

### Step 3: Add project-specific files in the new folder

In the **new project folder**, create or add the data files that the agents will use. Naming can match your convention (e.g. prefix with project code).

**Minimum suggested (create empty or from template):**

| File | Purpose |
|------|---------|
| `Lessons_Learned.md` | Copy the template from **ECEPCS MASTER\Lessons_Learned.md** and clear the example entries (or start empty with the same header/format). |
| `CPM_Development_Guide.md` (or `*_CPM_Development_Guide.md`) | WBS, logic rules, block definitions (A–E), P6 import notes for this project. |
| `Activities.csv` (or `*_Activities.csv`) | Activity list for this project. |
| `Relationships.csv` (or `*_Relationships.csv`) | Predecessor/successor logic for this project. |

**As needed:**

- `Risk_Register.md` — risks for this project.
- `Resources_Cost_Loading.md` — labor rates, CBS, cost loading for this project.
- `Three_Point_Estimates_QSRA_QCRA.md` — 3-point estimates for this project.
- BIM–P6 mapping, RFI log, etc., when you have them.

### Step 4: Set project-specific configuration (optional but recommended)

In the new project folder, define things the agents reference:

- **Blocks (A–E)**: In the CPM Development Guide (or a short `Project_Config.md`), define what “Block A,” “Block B,” etc. mean for **this** project (e.g. East Wing, West Wing, Civil, MEP, Commissioning).
- **LOTO / Hot Work**: If you have a list of activities or zones that are LOTO or Hot Work, add it (e.g. in the CPM guide or an activity code list) so the agents respect Rule #1.
- **Utility gate**: If this project uses a different utility-backfeed milestone than UTIL-2010, document it (e.g. “Utility backfeed = activity XYZ” or “milestone UTIL-2010”) in the CPM guide.
- **Trust Score**: If you will persist Trust Score (Approvals, Total_Proposals, AI_Agency_Score), add a store in the **new** project folder only (e.g. `project_controls_trust_score.json`). Do **not** copy the Trust Score file from another project—each project starts with Advisory Mode and its own score.

### Step 5: Open the new project in Cursor

1. In Cursor: **File → Open Folder**.
2. Select the **new project folder** (the one that now contains `.cursor` and the new project’s files).
3. Use **Chat** or **Composer** in that workspace.

The agents and orchestrator rule apply **only** to this folder. All references to “workspace” (Activities, Risk_Register, Lessons_Learned, etc.) point to **this project’s** files. **Isolation:** no shared schedule, cost, risk, or lessons with other projects.

### Step 6: Start in Advisory Mode

For the new project, treat the first 3 months as **Advisory Mode** (100% Level 2/3) unless you explicitly unlock Level 1. Do not copy “unlocked” or Trust Score from another project—start fresh for the new project.

---

## Option B: One repo, multiple project subfolders (shared ESEPCS, isolated data)

If you prefer **one** Cursor workspace that holds **multiple** projects, use one `.cursor` at the repo root (copied from **ECEPCS MASTER**) and **one subfolder per project** with its own data. Agents then must read/write only the **active** project’s folder.

### Step 1: Folder structure

Example:

```
MyProjectControlsRepo/
├── .cursor/                    # One copy of ESEPCS from ECEPCS MASTER (rules + skills)
│   ├── rules/
│   └── skills/
├── Project_A/                  # Project A data (isolated)
│   ├── Lessons_Learned.md
│   ├── Activities.csv
│   ├── Relationships.csv
│   ├── Risk_Register.md
│   └── ...
├── Project_B/                  # Project B data (isolated)
│   ├── Lessons_Learned.md
│   ├── Activities.csv
│   └── ...
└── active_project.txt          # Optional: contains "Project_B" so agents know which folder to use
```

### Step 2: Keep data isolated

- **Do not** mix files: each project’s Activities, Relationships, Risk_Register, Lessons_Learned, Trust Score, etc. live **only** in that project’s subfolder.
- When you ask the agents to do something, **specify the project** (e.g. “Using Project_B, run the scheduling agent on this delay” or “Update Risk_Register in Project_B”) or **@-mention** the project folder (e.g. `@Project_B/Activities.csv`).
- **Lessons_Learned**: Keep one **Lessons_Learned.md per project** (e.g. `Project_A/Lessons_Learned.md`, `Project_B/Lessons_Learned.md`). Use the template from ECEPCS MASTER when creating a new project folder. Tell the agent which project’s lessons to read (e.g. “Use lessons from Project_B”).
- **Trust Score**: If you persist it, keep one Trust Score file **per project** (e.g. `Project_A/project_controls_trust_score.json`) and tell the agent which project’s score to use.

### Step 3: Switching projects

- **Open the repo** in Cursor (so `.cursor` is loaded).
- When working on Project B, **always specify “Project B”** (or the path `Project_B/`) in your request or in @-mentions so the agent does not use Project A’s data.
- Optionally maintain an **active_project.txt** (or similar) that names the current project; the agents would need to read it when determining where to read/write. The current agent skills say “use whatever files exist in the workspace”—so for Option B, **you** must direct them to the correct subfolder (e.g. by @-mentioning files under `Project_B/`).

**Isolation:** Data is isolated by subfolder; behavioral isolation depends on you (and optionally active_project) pointing the agents at the right project’s files.

---

## Checklist — New project (Option A)

- [ ] New project folder created.
- [ ] Entire `.cursor` folder copied from **ECEPCS MASTER** into the new project folder root.
- [ ] `Lessons_Learned.md` created in new project (from **ECEPCS MASTER\Lessons_Learned.md** template; no copy of another project’s entries).
- [ ] New project has its own schedule/cost/risk files (CPM_Development_Guide, Activities, Relationships, Risk_Register, etc.) or placeholders.
- [ ] Block definitions (A–E) and any LOTO/utility milestone documented for the new project.
- [ ] Trust Score store (if used) is new and empty for the new project; start in Advisory Mode.
- [ ] Opened the **new project folder** in Cursor (File → Open Folder).
- [ ] Confirmed in Chat that the agent sees only the new project’s files (e.g. ask “What schedule files do you see?” and ensure it lists only the new project’s files).

---

## Summary

| Goal | Action |
|------|--------|
| **Where is the canonical ESEPCS?** | **ECEPCS MASTER** folder holds the master copy (`.cursor` + `Lessons_Learned.md` template). |
| **Invoke ESEPCS on a new project** | Copy the `.cursor` folder from **ECEPCS MASTER** into the new project folder. Copy `Lessons_Learned.md` from ECEPCS MASTER as the template. |
| **Keep the new project isolated** | Use a **dedicated folder** for the new project and open **that folder** in Cursor (Option A). All data (schedule, cost, risk, lessons, trust score) stays inside that folder. |
| **Avoid mixing projects** | Do **not** copy Lessons_Learned entries or Trust Score from another project into the new one. Each project gets its own data and its own Trust Score / Advisory Mode start. |

**Recommended:** Use **Option A** (one folder per project, copy `.cursor` from **ECEPCS MASTER** into each). That gives you a clear, isolated copy of ESEPCS per project with no shared state.
