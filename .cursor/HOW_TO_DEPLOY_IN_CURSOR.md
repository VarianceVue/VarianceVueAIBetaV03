# How to Deploy (Use) the Earned Schedule Excellence Project Controls System in Cursor

## You’re already “deployed”

The **Earned Schedule Excellence Project Controls System** agents are **already active** in this workspace. Cursor loads them automatically:

| What | Where | How Cursor uses it |
|------|--------|---------------------|
| **Orchestrator rule** | `.cursor/rules/project-controls-orchestrator.mdc` | Loaded every time (alwaysApply: true). Tells the AI about HITL, Trust Score, thresholds, Action UI, Rules of Engagement, etc. |
| **Sequence Architect** | `.cursor/skills/scheduling-agent/SKILL.md` | Applied when your message matches the skill description (schedule, WBS, P6, delays, re-sequencing, critical path, etc.). |
| **Variance Hunter** | `.cursor/skills/cost-agent/SKILL.md` | Applied when you mention cost, EVM, EAC, RFIs, submittals, change orders, scope creep. |
| **Risk Sentinel** | `.cursor/skills/risk-agent/SKILL.md` | Applied when you mention risks, QSRA, QCRA, supply chain, weather, alerts. |
| **Volt** | `.cursor/skills/volt-agent/SKILL.md` | Applied when you mention commissioning, BIM vs P6, equipment failure re-sequence, PTO, white space. |

No extra “deploy” step is required. **Open this folder in Cursor** and start chatting.

---

## Step 1: Open the project in Cursor

1. In Cursor: **File → Open Folder** (or **Open**).
2. Choose: `Project_Controls` (the folder that contains `.cursor`).
3. Use **Chat** (or Composer) in this workspace.

The orchestrator rule and skills apply only when you’re in **this workspace** (this folder).

---

## Step 2: Invoke the agents with natural language

You don’t install anything else. You **ask in plain language**; Cursor picks the right agent from your words.

**Examples:**

| You want to… | Try saying… |
|---------------|-------------|
| Use the **scheduling** agent | *"Generator #4 is 10 days late. Run the scheduling agent: assess float and propose re-sequencing options."* |
| Use the **cost** agent | *"Scan the RFI log for cost impact and update EAC."* or *"Use the Variance Hunter on these submittals."* |
| Use the **risk** agent | *"Check supply chain risk for copper and weather impact on concrete pours next week."* |
| Use the **commissioning** agent | *"Use Volt: Generator failed L3 test. Re-sequence the remaining units and give me the Decision Matrix."* |
| Get the **Decision Matrix** format | *"Switchgear Group C is 12 days late. Propose mitigations in the Action UI format (Option A, Option B, [Approve A] [Approve B] [Request Alternate])."* |

You can also name the agent:

- *"Use the Sequence Architect to…"*
- *"Run the Variance Hunter on…"*
- *"Risk Sentinel: …"*
- *"Volt: …"*

---

## Step 3: “Approve” in chat (pilot)

Right now there’s no Slack/Teams or P6 sync. **You approve in Cursor chat**:

1. The AI answers with a **Decision Matrix** (Agent Warning → Option A, Option B → [Approve Option A] [Approve Option B] [Request Alternate]).
2. You reply with e.g. **"Approve Option B"** or **"Accept"** (for Level 2).
3. The AI then continues as if you had clicked that option (e.g. applies Option B across schedule/cost/risk in the conversation and any files it updates).

For the **first 3 months** keep **Advisory Mode** on: don’t ask the AI to auto-update without your explicit approval in chat.

---

## Step 4: Give context with @

To tie the agent to your data, **@-mention** files or folders:

- *"Using @Data_Center_300MW_NM_Activities.csv and @Data_Center_300MW_NM_Relationships.csv, run the scheduling agent on a 10-day generator delay."*
- *"Variance Hunter: scan @RFI_Log.csv for cost impact."*
- *"Risk Sentinel: use @Data_Center_300MW_NM_Risk_Register.md and check weather vs the schedule in @Data_Center_300MW_NM_Activities.csv."*

That keeps answers grounded in your project.

---

## Quick checklist

- [ ] Cursor is opened on the **Project_Controls** folder (the one that contains `.cursor`).
- [ ] You’re using **Chat** or **Composer** in this workspace.
- [ ] You phrase requests so they mention **schedule / cost / risk / commissioning** (or agent names) so the right skill is used.
- [ ] For the pilot you **approve in chat** (“Approve Option A/B” or “Accept”) and avoid asking for full auto-updates without approval.

---

## If an agent isn’t used

If the AI doesn’t follow the orchestrator or the right agent:

1. **Name the agent** in your message (e.g. *"Use the Sequence Architect…"*).
2. **Mention the capability** (e.g. *"Give me a Decision Matrix with two options"*, *"Run Monte Carlo re-sequencing"*).
3. **Start a new chat** so the context is focused on this workspace and its rules.

---

## Summary

| Question | Answer |
|----------|--------|
| Do I need to run a deploy command? | **No.** Rules and skills in `.cursor/` are loaded automatically when you open this folder in Cursor. |
| How do I “deploy”? | **Open this project in Cursor** and use Chat/Composer. The agents are already deployed. |
| How do I use an agent? | **Ask in natural language** (or name the agent); include @-mentions to your data when helpful. |
| How do I approve? | **Reply in chat** with “Approve Option A”, “Approve Option B”, or “Accept” (for Level 2). |
