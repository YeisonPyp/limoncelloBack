from rest_framework import permissions, generics
from .models import UserRoles, RolePermissions

class HasPermission(permissions.BasePermission):
    """
    Sistema de permisos basado en roles para verificar permisos por acción.
    """
    def has_permission(self, request, view):
        # Asegurarse de que el usuario esté autenticado
        if not request.user.is_authenticated:
            return False

        # Obtener el permiso necesario para la vista
        required_permission = self.get_required_permission(request, view)
        if not required_permission:
            return True  # Si no se requiere permiso explícito, permitir el acceso.

        # Verificar si el usuario tiene el permiso
        user_roles = UserRoles.objects.filter(user_id=request.user)
        for user_role in user_roles:
            role_permissions = RolePermissions.objects.filter(
                role_id=user_role.role_id, 
                permission_cod=required_permission
            )
            if role_permissions.exists():
                return True
        return False

    def get_required_permission(self, request, view):
        """
        Define qué permiso se requiere basado en el tipo de vista y el método HTTP.
        """
        # Mapear métodos HTTP a permisos
        method_permission_map = {
            'GET': 'CON',  # Consultar
            'POST': 'CRE', # Crear
            'PUT': 'ACT',  # Actualizar
            'PATCH': 'ACT',  # Actualizar parcial
            'DELETE': 'BOR'  # Borrar
        }

        # Mapear vistas específicas (por ejemplo, ListCreateAPIView) a permisos
        if isinstance(view, generics.ListCreateAPIView):
            return method_permission_map.get(request.method)
        elif isinstance(view, generics.RetrieveUpdateDestroyAPIView):
            return method_permission_map.get(request.method)
        elif isinstance(view, generics.CreateAPIView):
            return method_permission_map.get(request.method)
        elif isinstance(view, generics.UpdateAPIView):
            return method_permission_map.get(request.method)
        elif isinstance(view, generics.DestroyAPIView):
            return method_permission_map.get(request.method)
        elif isinstance(view, generics.RetrieveAPIView):
            return method_permission_map.get(request.method)
        elif isinstance(view, generics.ListAPIView):
            return method_permission_map.get(request.method)
        elif isinstance(view, generics.RetrieveUpdateAPIView):
            return method_permission_map.get(request.method)
        
        
        # Si no se puede determinar el permiso, devolver None
        return None
