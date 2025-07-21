from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib import messages
from core.models import Profile

class RoleRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Ensure profile exists
            if not hasattr(request.user, 'profile'):
                Profile.objects.create(user=request.user, role='user')

            role = request.user.profile.role

            try:
                current_url_name = resolve(request.path_info).url_name
            except:
                current_url_name = None

            # Restrict admin-only views
            admin_only_urls = ['admin:index', 'analytics_dashboard', 'user_management', 'site_settings', 'admin_dashboard']

            if role != 'admin' and current_url_name in admin_only_urls:
                messages.error(request, "Access denied: Admins only.")
                return redirect(reverse('core:dashboard'))

        return self.get_response(request)