from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Check if the user who made the request is admin.
    Use like that : permission_classes = [IsAdmin]
    """
    def has_permission(self, request, view):
        if not 'Authorization' in request.headers:
            return False
        else:
            return request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) # reuse `has_permission`

class IsFactoryAdmin(permissions.BasePermission):
    """
    Check if the user who made the request is admin.
    Use like that : permission_classes = [IsFactoryAdmin]
    """
    def has_permission(self, request, view):
        if not 'Authorization' in request.headers:
            return False
        else:
            return request.user.user_type == 'FACTORY_ADMIN'
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) # reuse `has_permission`

class IsStaff(permissions.BasePermission):
    """
    Check if the user who made the request is staff.
    Use like that : permission_classes = [IsStaff]
    """
    def has_permission(self, request, view):
        if not 'Authorization' in request.headers:
            return False
        else:
            return request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) # reuse `has_permission`

class IsOwner(permissions.BasePermission):
    """
    Check if the user who made the request is owner.
    Use like that : permission_classes = [IsOwner]
    """
    def has_permission(self, request, view):
        if not 'Authorization' in request.headers:
            return False
        else:
            return request.user.is_customer
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) # reuse `has_permission`
