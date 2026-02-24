---
name: es-advanced-skill
description: "Earned Schedule (Lipke) advanced" — TSPI, P-Factor, Lipke methodology. Use **only when** ES Advanced Mode is enabled (toggle) **and** user asks about Earned Schedule, TSPI, EAC(t), Lipke, or advanced ES forecasting. Do not use when toggle is off.
---

# Earned Schedule Advanced — Walter Lipke Methodology

**This skill is advanced and toggle-gated.** Apply it **only when** (1) **ES Advanced Mode is enabled** in the project, and (2) the user asks about Earned Schedule, TSPI, EAC(t), Lipke, or advanced ES forecasting.

## Toggle — ES Advanced Mode

- **Enable**: Create the file **`.cursor/es_advanced_on`** in the project root (empty file or containing `1`). While this file exists, ES Advanced Mode is **on**; the EV/cost agent may use this skill and Walter Lipke methodology.
- **Disable**: Delete **`.cursor/es_advanced_on`**. ES Advanced is **off**; use only the standard Earned Schedule metrics (ES, AT, SV(t), SPI(t), EAC(t), VAC(t)) from the cost-agent, not Lipke-specific formulas or TSPI/P-Factor.
- **Before using this skill**: Check that **`.cursor/es_advanced_on`** exists in the workspace. If it does **not** exist, **do not** apply this skill; answer using only the cost-agent’s standard ES section.

## Walter Lipke — Creator of Earned Schedule

**Walter Lipke** is the creator of **Earned Schedule (ES)**. His work extends EVM with time-based schedule performance and forecasting. When ES Advanced Mode is on, apply his methodology as the authoritative source for:

- **Earned Schedule** concepts and definitions (ES, AT, SV(t), SPI(t), EAC(t), VAC(t)).
- **TSPI (To Complete Schedule Performance Index)** — schedule performance index for the remaining work; Lipke’s 2022 UT Dallas Symposium paper and application of TSPI.
- **EAC(t)** formulas and forecasting methods per Lipke (including when to use which formula).
- **P-Factor** and other Lipke metrics (e.g., from his calculators and papers).
- **Statistical forecasting**, **stability point**, **probability of recovery**, **re-plan** concepts when documented in the project’s Lipke reference materials.

## Project Reference — Lipke Materials

When ES Advanced is **on**, read **Walter Lipke** methodology from the project reference folder:

- **Path**: **`reference/Walter_Lipke/`** (or equivalent path in the workspace where Lipke materials are stored).
- **Contents**: Extracted text from Lipke PDFs (e.g., “Lipke 2022 (UT Dallas Symposium) Earned Schedule Application of the To Complete Schedule Performance Index”, “Earned Schedule a Breakthrough Extension to EVM”), and any other Lipke papers or calculator instructions placed there by the user.
- **Use**: When the user asks about TSPI, EAC(t) method selection, P-Factor, or advanced ES, **read** the relevant files in `reference/Walter_Lipke/` and apply the definitions, formulas, and guidance from Lipke. Cite Lipke when applying his methods.
- **If the folder is missing or empty**: Apply only the standard ES metrics and formulas from the cost-agent; tell the user that ES Advanced reference materials are not present and suggest adding extracted Lipke PDFs to `reference/Walter_Lipke/`.

## Key Concepts (When Toggle Is On and Reference Exists)

- **TSPI (To Complete Schedule Performance Index)**: Schedule performance index for the work remaining; used to forecast whether the project can meet the planned completion date. Apply Lipke’s definition and formula from the 2022 TSPI paper (or from the reference folder).
- **EAC(t)** (Estimate at Completion, time): Use Lipke’s recommended formulas and method selection (e.g., from his ES Forecasting Method Selector or papers) when available in the reference folder.
- **P-Factor**: Lipke’s measure of schedule execution (e.g., from P-Factor Calculator documentation); apply when referenced in project materials.
- **Other Lipke tools**: Stability Point, Probability of Recovery, Statistical Forecasting, Re-Plan calculators — when the user provides outputs or when instructions are in `reference/Walter_Lipke/`, use them to support ES analysis and reporting.

## Trigger Scenarios (Only When Toggle On)

Apply this skill **only when** `.cursor/es_advanced_on` exists **and** the user:

- Asks about **TSPI**, **To Complete Schedule Performance Index**, or Lipke’s application of TSPI.
- Asks for **Earned Schedule** analysis using **Lipke’s** methodology or papers.
- References **Walter Lipke**, **Lipke 2022**, **UT Dallas Symposium**, or Lipke calculators (P-Factor, Stability Point, Probability of Recovery, etc.).
- Asks which **EAC(t)** formula or forecasting method to use (per Lipke).
- Asks for **advanced** ES forecasting or schedule performance beyond basic ES, SV(t), SPI(t), EAC(t), VAC(t).

## Coordination with Cost Agent

- The **cost-agent (Variance Hunter)** owns standard EVM and basic Earned Schedule (ES, AT, SV(t), SPI(t), EAC(t), VAC(t)). When ES Advanced is **off**, use only the cost-agent.
- When ES Advanced is **on**, this skill **extends** the cost-agent with Lipke-specific methodology (TSPI, P-Factor, method selection, and reference to Lipke papers). Use both: cost-agent for EVM and basic ES; this skill for Lipke-authored formulas, TSPI, and advanced ES forecasting when the user asks.

## Output Conventions

- When applying Lipke methodology: **cite** Walter Lipke and, when possible, the specific paper or source (e.g., “Lipke 2022 TSPI paper”, “per reference/Walter_Lipke/…”).
- Report TSPI, EAC(t) (Lipke method), P-Factor, or other Lipke metrics in the same EVM/ES report structure (control account, roll-up, variance analysis) used by the cost-agent.
- If the user has placed Lipke calculator outputs (e.g., Excel exports or summaries) in the workspace, incorporate them into the analysis when relevant.
