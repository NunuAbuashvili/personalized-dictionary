from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that uses email instead of username.
    Extends Django's ModelBackend to support email-based authentication.
    """
    def authenticate(self,
                     request: HttpRequest,
                     username: Optional[str] = None,
                     password: Optional[str] = None,
                     **kwargs: Any) -> Optional['CustomUser']:
        """
        Authenticate a user using their email address and password.

        Args:
            request: The HTTP request object
            username: The email address used for authentication
            password: The user's password
            **kwargs: Additional authentication parameters

        Returns:
            Optional[CustomUser]: The authenticated user or None if authentication fails.
        """
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None
        return None
