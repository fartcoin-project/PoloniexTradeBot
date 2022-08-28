from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from .models import Greeting, ExampleModel, Volume
from .serializers import ExampleModelSerializer, VolumeSerializer

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework import serializers
from rest_framework import viewsets


def index(request):
    # return HttpResponse('tradebot from Python!')
    return render(request, "index.html")

# @csrf_exempt
def get_data(request):
    data = ExampleModel.objects.all()
    if request.method == 'GET':
        serializer = ExampleModelSerializer(data, many=True)
        return JsonResponse(serializer.data, safe=False)

def get_vol(request):
    data = Volume.objects.all()
    if request.method == 'GET':
        serializer = VolumeSerializer(data, many=True)
        return JsonResponse(serializer.data, safe=False)

def db(request):
    greeting = Greeting()
    greeting.save()
    greetings = Greeting.objects.all()
    return render(request, "dbold.html", {"greetings": greetings})

class HomePageView(TemplateView):
    template_name = "index.html"


class AboutPageView(TemplateView):
    template_name = "about.html"

class LinksPageView(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'links.html', context=None)

class Customers(TemplateView):
    def getCust(request):
        name='liran'
        return HttpResponse('{ "name":"' + name + '", "age":31, "city":"New York" }')

@api_view(["POST"])
def CalcTest(x1):
    try:
        x=json.loads(x1.body)
        y=str(x*100)
        return JsonResponse("Result:"+y,safe=False)
    except ValueError as e:
        return Response(e.args[0],status.HTTP_400_BAD_REQUEST)