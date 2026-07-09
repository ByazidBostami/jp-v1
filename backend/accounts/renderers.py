"""Standard API response envelope (SRS §11)."""
from rest_framework.renderers import JSONRenderer
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response


class EnvelopeJSONRenderer(JSONRenderer):
    """Wraps every successful response as {success, message, data, meta}."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        status_code = getattr(response, "status_code", 200)

        # Already-enveloped errors pass straight through.
        if isinstance(data, dict) and data.get("success") is False:
            return super().render(data, accepted_media_type, renderer_context)

        # Paginated payloads carry their own meta block.
        if isinstance(data, dict) and "results" in data and "meta" in data:
            payload = {
                "success": True,
                "message": "Request completed successfully.",
                "data": data["results"],
                "meta": data["meta"],
            }
        else:
            payload = {
                "success": status_code < 400,
                "message": "Request completed successfully." if status_code < 400
                else "Request failed.",
                "data": data,
                "meta": {},
            }
        return super().render(payload, accepted_media_type, renderer_context)


def envelope_exception_handler(exc, context):
    """Consistent error envelope (SRS §11 error format)."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data
    errors = {}
    message = "Request failed."
    if isinstance(detail, dict):
        if "detail" in detail and len(detail) == 1:
            message = str(detail["detail"])
        else:
            errors = detail
            message = "Validation failed."
    elif isinstance(detail, list):
        errors = {"non_field_errors": detail}
        message = "Validation failed."

    response.data = {"success": False, "message": message, "errors": errors}
    return response
