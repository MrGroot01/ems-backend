from rest_framework import serializers
from .models import Leave


class LeaveSerializer(serializers.ModelSerializer):
    user_name       = serializers.CharField(source='user.full_name', read_only=True)
    user_email      = serializers.CharField(source='user.email', read_only=True)
    user_id         = serializers.IntegerField(source='user.id', read_only=True)
    approved_by_name= serializers.CharField(source='approved_by.full_name', read_only=True)

    class Meta:
        model  = Leave
        fields = '__all__'
        read_only_fields = ['user','status','approved_by','days','applied_on','updated_at']
