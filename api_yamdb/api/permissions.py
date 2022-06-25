from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class AdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (
                request.user.is_authenticated
                and request.user.is_admin)
        )


user_role = ['moderator', 'admin']


class OnlyReadOrСhangeAuthorAdminModerator(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.role in user_role
            or obj.author == request.user
            or request.user.is_staff == True)
