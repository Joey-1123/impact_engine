# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from django.urls import path
from .views import home

urlpatterns = [
    path("",home)
]