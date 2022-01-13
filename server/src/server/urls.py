# -*- coding: utf-8 -*-
"""
Url patterns for UDS project (Django)
"""
from django.urls import include, path


# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()


urlpatterns = [
    path('', include('uds.urls')),
]
