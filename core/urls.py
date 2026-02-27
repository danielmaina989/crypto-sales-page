"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users import views as users_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Top-level logout endpoint: use LogoutView which will redirect to LOGOUT_REDIRECT_URL
    path('logout/', LogoutView.as_view(), name='logout'),

    # include frontend URLs with a namespace so that reverse('frontend:...') works
    path('', include(('frontend.urls', 'frontend'), namespace='frontend')),
    path('payments/', include('payments.urls')),
    path('api/', include('trades.urls')),

    # Replace default login with IntelligentLoginView at /accounts/login/
    path('accounts/login/', users_views.IntelligentLoginView.as_view(), name='login'),

    # Built-in auth views (password reset, logout already handled) under /accounts/
    path('accounts/', include('django.contrib.auth.urls')),
    # Custom registration & profile endpoints
    path('accounts/register/', users_views.register, name='register'),
    path('accounts/profile/', users_views.profile, name='profile'),
    path('users/', include('users.urls')),
]
