from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()

router.register("api", views.SearchesViewSet, basename="api")

urlpatterns = []

urlpatterns += router.urls
