from django.urls import path
from . import views

urlpatterns = [
    # capture any url path and pass it to the view
    path("<path:path>", views.generate_seo_tags, name="generate_seo_tags"),
]
