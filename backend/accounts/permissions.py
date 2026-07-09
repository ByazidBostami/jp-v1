from rest_framework.permissions import BasePermission
from .models import Role


class IsCandidate(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.has_role(Role.CANDIDATE))


class IsEmployer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.has_role(Role.EMPLOYER))


class IsApprovedEmployer(BasePermission):
    message = "Your employer account is awaiting admin approval."

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated and u.has_role(Role.EMPLOYER)):
            return False
        profile = getattr(u, "employer_profile", None)
        return bool(profile and profile.approval_status == "approved")


class IsAdminStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.is_admin_staff)


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.has_role(Role.SUPER_ADMIN))
