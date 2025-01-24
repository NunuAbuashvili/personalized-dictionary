from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class CustomLoginRequiredMixin(LoginRequiredMixin):
    """
    A custom mixin that ensures a user is authenticated before accessing a view.

    If the user is not authenticated, they are redirected to the login page
    with a `next` parameter set to the requested path, so they can be redirected
    back to their original destination after logging in.
    """
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatches the request and checks if the user is authenticated.
        """
        if not request.user.is_authenticated:
            return redirect(f"{self.get_login_url()}?next={request.path}")
        return super().dispatch(request, *args, **kwargs)
