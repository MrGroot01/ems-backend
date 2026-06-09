from rest_framework import serializers
from .models import Course, CourseEnrollment


class CourseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.full_name', read_only=True
    )
    enrolled_count  = serializers.SerializerMethodField()

    class Meta:
        model  = Course
        fields = '__all__'
        read_only_fields = ['created_by']

    def get_enrolled_count(self, obj):
        return obj.enrollments.count()


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course_title      = serializers.CharField(source='course.title',      read_only=True)
    course_dept       = serializers.CharField(source='course.department',  read_only=True)
    course_difficulty = serializers.CharField(source='course.difficulty',  read_only=True)
    course_duration   = serializers.IntegerField(source='course.duration_hrs', read_only=True)
    course_thumbnail  = serializers.CharField(source='course.thumbnail',  read_only=True)
    course_lessons    = serializers.JSONField(source='course.lessons',     read_only=True)
    course_quiz       = serializers.JSONField(source='course.quiz',        read_only=True)
    course_pass_score = serializers.IntegerField(source='course.pass_score', read_only=True)
    course_description= serializers.CharField(source='course.description', read_only=True)
    user_name         = serializers.CharField(source='user.full_name',     read_only=True)
    user_dept         = serializers.CharField(source='user.department',    read_only=True)
    user_email        = serializers.CharField(source='user.email',         read_only=True)

    class Meta:
        model  = CourseEnrollment
        fields = '__all__'
        read_only_fields = ['user', 'certificate_id']