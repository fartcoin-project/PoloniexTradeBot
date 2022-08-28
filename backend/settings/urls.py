from django.urls import path, include
from django.contrib import admin
from django.views.generic.base import TemplateView
admin.autodiscover()
import tradebot.views
# from rest_framework import routers


# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/
# router = routers.DefaultRouter()
# router.register("customers", tradebot.views.CustViewSet)

urlpatterns = [
    path("", tradebot.views.index, name="home"),
    path("getData/", tradebot.views.get_data),
    path("getVol/", tradebot.views.get_vol),
    path("admin/", admin.site.urls),
    path("getcust/", tradebot.views.Customers.getCust), # simple view
    path("", tradebot.views.HomePageView.as_view(), name="home"),
    path("about/", tradebot.views.AboutPageView.as_view(), name="about"),

]
