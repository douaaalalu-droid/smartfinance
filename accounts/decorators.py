from django.core.exceptions import PermissionDenied
from functools import wraps


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                raise PermissionDenied

            if hasattr(user, 'role') and user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            raise PermissionDenied

        return _wrapped_view
    return decorator
