"""pandora URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include # url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import include

from .views import (
    manage,
)

from .views import about_page
urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    re_path(r'^about/$', about_page, name='about'),
    path('admin/', admin.site.urls),
    path('', include('contest.urls')),
	re_path(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
	re_path(r'^oauth/', include('social_django.urls', namespace='social')),
	#path(
    #'logout/',
    #LogoutView.as_view(template_name=settings.LOGOUT_REDIRECT_URL),
    #name='logout'
    #),
	#path('manage/', manage, name='manage'),
] + staticfiles_urlpatterns()



if settings.DEBUG:
    # test mode
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


