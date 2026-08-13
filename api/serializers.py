from rest_framework import serializers
from .models import Employee, LocationLog


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationLog
        fields = "__all__"