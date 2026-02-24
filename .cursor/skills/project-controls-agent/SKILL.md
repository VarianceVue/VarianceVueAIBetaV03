---
name: project-controls-agent
description: Reads scheduling specifications from PDF files and reports how to develop a Primavera P6 CPM schedule. Use when the user provides a PDF spec path, asks about P6 schedule development from specs, or mentions scheduling specifications, CPM, WBS, or Primavera P6.
---

# Project Controls Agent

Process PDF scheduling specifications and produce actionable guidance for developing a Primavera P6 CPM schedule.

## Trigger Scenarios

Apply this skill when:
- User provides a PDF file path and asks how to build a P6 schedule
- User asks about developing a CPM schedule from specifications
- User mentions scheduling specs, WBS, Primavera P6, or CPM schedule development

## Workflow

### Step 1: Extract PDF Content

Cursor cannot read PDFs natively. Run the extraction script to get text and tables:

```bash
python .cursor/skills/project-controls-agent/scripts/extract_pdf.py "<path_to_spec.pdf>"
```

Capture the output. If the script fails (missing pypdf), instruct the user to run `pip install pypdf`.

### Step 2: Analyze Extracted Text

Using the extracted content and P6/CPM knowledge from [reference.md](reference.md), analyze the specification and identify:

- Scope and deliverables mentioned
- Required WBS structure (phases, disciplines, areas)
- Activities, milestones, or sequencing described
- Constraints, dates, or reporting requirements
- Standards referenced (NYSDOT, AACE, agency-specific, etc.)
- Calendars, work hours, or resource assumptions

### Step 3: Produce P6 Development Report

Generate a structured report covering:

1. **WBS Recommendations** – Suggested hierarchy, levels, and naming
2. **Activity Identification** – Activities and milestones to create, naming conventions
3. **Relationships and Logic** – Predecessor/successor logic, dependency types
4. **Calendars** – Work days, holidays, shift assumptions
5. **Constraints** – Mandatory dates, milestones, or agency requirements
6. **Compliance Notes** – Any spec-driven rules (float limits, baseline rules, etc.)

## Report Template

```markdown
# P6 CPM Schedule Development Guide

## Executive Summary
[One-paragraph overview of the spec and recommended approach]

## 1. WBS Structure
[Recommended hierarchy and levels]

## 2. Activities and Milestones
[Activity list or categories, naming guidance]

## 3. Logic and Relationships
[Sequencing, dependency types, critical path considerations]

## 4. Calendars and Constraints
[Work calendars, holidays, mandatory dates]

## 5. Compliance and Spec Requirements
[Any agency-specific or standard-driven requirements]
```

## LLM Options

**Default**: Use Cursor's built-in model to analyze the extracted text and produce the report. No API keys required.

**Optional external LLM**: If the user has `OPENAI_API_KEY`, `AZURE_OPENAI_*`, or `OLLAMA_BASE_URL` set and prefers external analysis, you may invoke a helper that calls the configured API. Otherwise, proceed with Cursor's model.

## Additional Resources

- For P6 CPM best practices and spec interpretation, see [reference.md](reference.md)
