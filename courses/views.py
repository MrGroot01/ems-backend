import uuid
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Course, CourseEnrollment
from .serializers import CourseSerializer, CourseEnrollmentSerializer
from users.models import User


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class   = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs   = Course.objects.filter(is_active=True)
        if user.role != 'admin':
            dept = user.department.lower() if user.department else ''
            qs   = qs.filter(department=dept)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # ── Get courses for a specific department ──────────────
    @action(detail=False, methods=['get'], url_path='by-department')
    def by_department(self, request):
        dept = request.query_params.get('dept', '').lower()
        courses = Course.objects.filter(
            department=dept, is_active=True
        )
        return Response(CourseSerializer(courses, many=True).data)

    # ── Enroll employee(s) ─────────────────────────────────
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course   = self.get_object()
        user_ids = request.data.get('user_ids', [])
        # If no user_ids, enroll all employees of the course department
        if not user_ids:
            users = User.objects.filter(
                department__iexact=course.department,
                role='employee', is_active=True
            )
        else:
            users = User.objects.filter(id__in=user_ids)

        created = 0
        for u in users:
            _, was_created = CourseEnrollment.objects.get_or_create(
                user=u, course=course
            )
            if was_created:
                created += 1

        return Response({
            'message':  f'Enrolled {created} employees',
            'total':    users.count(),
            'new':      created,
        })


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class   = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return CourseEnrollment.objects.select_related(
                'user', 'course'
            ).all().order_by('-enrolled_at')
        return CourseEnrollment.objects.filter(
            user=user
        ).select_related('course').order_by('-enrolled_at')

    # ── Complete a lesson ──────────────────────────────────
    @action(detail=True, methods=['post'], url_path='complete-lesson')
    def complete_lesson(self, request, pk=None):
        enrollment  = self.get_object()
        lesson_idx  = request.data.get('lesson_index')
        if lesson_idx is None:
            return Response({'error': 'lesson_index required'}, status=400)

        done = enrollment.lessons_done or []
        if lesson_idx not in done:
            done.append(lesson_idx)
            enrollment.lessons_done = done

        total    = len(enrollment.course.lessons)
        progress = int((len(done) / total) * 100) if total > 0 else 0
        enrollment.progress = progress
        enrollment.status   = 'in_progress' if progress > 0 else 'enrolled'
        enrollment.save(update_fields=['lessons_done', 'progress', 'status'])

        return Response(CourseEnrollmentSerializer(enrollment).data)

    # ── Submit quiz ────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='submit-quiz')
    def submit_quiz(self, request, pk=None):
        enrollment = self.get_object()
        answers    = request.data.get('answers', {})  # {question_index: answer}
        quiz       = enrollment.course.quiz

        if not quiz:
            return Response({'error': 'No quiz available'}, status=400)

        # Grade quiz
        correct = 0
        for i, q in enumerate(quiz):
            if str(answers.get(str(i), '')) == str(q.get('answer', '')):
                correct += 1

        score  = int((correct / len(quiz)) * 100)
        passed = score >= enrollment.course.pass_score

        enrollment.quiz_score  = score
        enrollment.quiz_passed = passed

        if passed and enrollment.progress >= 100:
            enrollment.status        = 'completed'
            enrollment.completed_at  = timezone.now()
            enrollment.certificate_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"

        enrollment.save(update_fields=[
            'quiz_score', 'quiz_passed', 'status',
            'completed_at', 'certificate_id'
        ])

        return Response({
            'score':       score,
            'passed':      passed,
            'correct':     correct,
            'total':       len(quiz),
            'pass_score':  enrollment.course.pass_score,
            'certificate_id': enrollment.certificate_id,
            'enrollment':  CourseEnrollmentSerializer(enrollment).data,
        })

    # ── Admin: enrollment stats ────────────────────────────
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin only'}, status=403)

        total      = CourseEnrollment.objects.count()
        completed  = CourseEnrollment.objects.filter(status='completed').count()
        in_progress= CourseEnrollment.objects.filter(status='in_progress').count()
        certified  = CourseEnrollment.objects.exclude(certificate_id='').count()

        return Response({
            'total':       total,
            'completed':   completed,
            'in_progress': in_progress,
            'certified':   certified,
        })