"""
URL configuration for zameen project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path,include
from zameen import views
from django.views.generic import RedirectView
from django.conf.urls.static import static
from django.conf import settings
from login import urls
from partner import urls
from .views import SupportLoginView, support_logout, support_dashboard, toggle_resolved
from django.contrib.auth import views as auth_views
from .views import onesignal_worker
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap
from .views import submit_support_query
from zameen.views import user_list
from django.contrib.sitemaps.views import sitemap
from .sitemaps import ListingSitemap, StaticViewSitemap
from .views import AboutFounderView

sitemaps = {
    'listings': ListingSitemap,
    'static': StaticViewSitemap,
}
urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('login/', views.login ,name="login"),
    
    path('room/<int:id>/', views.room, name= "room"),
    path('', views.base, name="base"),
    path('2bhk/', views.bhk2, name="bhk2"),
    path('About-Us/', views.AboutUs,name="aboutus"),
    path('Terms-condition/', views.terms_conditions,name="Terms-condition"),
    path('Privacy-policy/', views.privacy_policy,name="privacy-policy"),
    path('3bhk/', views.bhk3, name="bhk3"),
    path('pg/', views.pg, name="pg"),
    path('bookingconfirm/<int:id>', views.bookingcon, name="bookingconfirm"),
    path('mybooking/', views.mybooking, name="mybooking"),
    path('more', views.more, name="more"),
    path('bookingform/<int:id>', views.bookingform, name="bookingform"),
    path('pauth/', include('login.urls')),
    path('partner/', include('partner.urls')),
    path('invoice/<int:booking_id>/', views.invoice_view, name='invoice'),
    path('invoice/<int:booking_id>/download/', views.download_invoice, name='download_invoice'),
    path('', include('listings.urls')),
    path('chatbot/', include('chatbot.urls')),
    path("OneSignalSDKWorker.js", onesignal_worker),
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'
    ),
    path('help-support/', views.help_support, name='help_support'),
    path('how-to-book/', views.how_to_book, name='how_to_book'),
    path('support/submit/', submit_support_query, name='submit_support_query'),
    path('support/login/', SupportLoginView.as_view(), name='support_login'),
    path('support/logout/', support_logout, name='support_logout'),
    path('support/dashboard/', support_dashboard, name='support_dashboard'),
    path('support/query/<int:query_id>/toggle/', toggle_resolved, name='toggle_resolved'),
    path(
        'review/<int:room_id>/',
        views.submit_review,
        name='submit_review'
    ),
    path('accounts/', include('allauth.urls')),
    
    path('accounts/', include('allauth.urls')),  # yeh last mein
    path('admin-dashboard/users/', views.user_list, name='user_list'),
    path("about/founder/", AboutFounderView.as_view(), name="about_founder"),
    path('reviews/submit/', views.create_review, name='create_review'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)