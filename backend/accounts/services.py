"""Cross-cutting helpers: audit logging and notification creation."""
from .middleware import get_current_request
from .models import AuditLog


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(user, action, entity_type="", entity_id="", old=None, new=None):
    request = get_current_request()
    AuditLog.objects.create(
        user=user if (user and getattr(user, "is_authenticated", False)) else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else "",
        old_values_json=old,
        new_values_json=new,
        ip_address=_client_ip(request) if request else None,
        user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else ""),
    )
