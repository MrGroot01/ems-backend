from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    assigned_to_id   = serializers.IntegerField(source='assigned_to.id', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.full_name', read_only=True)

    class Meta:
        model  = Task
        fields = '__all__'
        read_only_fields = ['assigned_by', 'completed_at', 'created_at', 'updated_at']
