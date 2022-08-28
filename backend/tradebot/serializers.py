from rest_framework import serializers
from .models import ExampleModel, Volume

class ExampleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleModel
        fields = ('firstname', 'lastname')

class VolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Volume
        fields = ('id', 'date', 'pair', 'marketCoin', 'mainVolume', 'altCoin', 'altVolume')
