from django.urls import path
from .views import home, market, features, whitepapers, about, dashboard

urlpatterns = [
    path('', home, name='home'),

    # Navbar links
    path('market/', market, name='market'),
    path('features/', features, name='features'),
    path('whitepapers/', whitepapers, name='whitepapers'),
    path('about/', about, name='about'),

    # Dashboard (global route)
    path('dashboard/', dashboard, name='dashboard'),
]
