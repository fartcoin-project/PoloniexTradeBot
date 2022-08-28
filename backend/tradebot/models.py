from django.db import models

# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField("date created", auto_now_add=True)


class ExampleModel(models.Model):
    firstname    = models.CharField(max_length=200)
    lastname     = models.CharField(max_length=200)

class Volume(models.Model):
    date         = models.CharField(max_length=200)
    pair         = models.CharField(max_length=200)
    marketCoin   = models.CharField(max_length=200)
    mainVolume   = models.CharField(max_length=200)
    altCoin      = models.CharField(max_length=200)
    altVolume    = models.CharField(max_length=200)