"""
Stage 5: Delivery & integration — dashboard, alerts, report drafting, audit trail.
"""
from schedule_agent_web.delivery.audit_trail import append_audit, get_audit_trail
from schedule_agent_web.delivery.alerts import send_alert
from schedule_agent_web.delivery.report_draft import build_report_context, draft_report
from schedule_agent_web.delivery.dashboard import get_dashboard

__all__ = [
    "append_audit",
    "get_audit_trail",
    "send_alert",
    "build_report_context",
    "draft_report",
    "get_dashboard",
]
