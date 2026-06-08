import json
import base64
import numpy as np
from io import BytesIO
from PIL import Image

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.core.files.base import ContentFile

from .models import Attendance
from .serializers import AttendanceSerializer


# ── InsightFace singleton (loaded once at startup) ────────
_face_app = None

def get_face_app():
    global _face_app
    if _face_app is None:
        from insightface.app import FaceAnalysis
        _face_app = FaceAnalysis(
            name='buffalo_sc',                      # small but accurate model
            providers=['CPUExecutionProvider'],     # CPU only on Render
        )
        _face_app.prepare(ctx_id=0, det_size=(320, 320))
    return _face_app


def decode_base64_image(b64_string):
    """
    Convert base64 data-URL to:
      - numpy BGR array  (for insightface / OpenCV)
      - raw bytes        (for saving to disk)
    """
    if ',' in b64_string:
        b64_string = b64_string.split(',')[1]

    img_data  = base64.b64decode(b64_string)
    pil_image = Image.open(BytesIO(img_data)).convert('RGB')

    # insightface expects BGR (same as OpenCV)
    rgb_array = np.array(pil_image)
    bgr_array = rgb_array[:, :, ::-1].copy()

    return bgr_array, img_data


def cosine_similarity(a, b):
    """Return cosine similarity between two 1-D vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class   = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Attendance.objects.select_related('user').all()
        return Attendance.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # ── Manual Check-In ───────────────────────────────────
    @action(detail=False, methods=['post'])
    def check_in(self, request):
        today    = timezone.now().date()
        now_time = timezone.now().time()
        obj, created = Attendance.objects.get_or_create(
            user=request.user, date=today,
            defaults={
                'check_in':        now_time,
                'status':          'present',
                'attendance_type': 'manual',
            }
        )
        if not created:
            return Response({'error': 'Already checked in today'}, status=400)
        return Response(AttendanceSerializer(obj).data, status=201)

    # ── Check-Out ─────────────────────────────────────────
    @action(detail=False, methods=['post'])
    def check_out(self, request):
        today    = timezone.now().date()
        now_time = timezone.now().time()
        try:
            obj = Attendance.objects.get(user=request.user, date=today)
            if obj.check_out:
                return Response({'error': 'Already checked out'}, status=400)
            obj.check_out = now_time
            if obj.check_in:
                from datetime import datetime, date
                ci   = datetime.combine(date.today(), obj.check_in)
                co   = datetime.combine(date.today(), now_time)
                diff = (co - ci).seconds / 3600
                obj.working_hours = round(diff, 2)
            obj.save()
            return Response(AttendanceSerializer(obj).data)
        except Attendance.DoesNotExist:
            return Response({'error': 'No check-in found today'}, status=404)

    # ── Today Summary ─────────────────────────────────────
    @action(detail=False, methods=['get'])
    def today_summary(self, request):
        today   = timezone.now().date()
        total   = Attendance.objects.filter(date=today).count()
        present = Attendance.objects.filter(date=today, status='present').count()
        return Response({
            'total':   total,
            'present': present,
            'absent':  total - present,
            'date':    str(today),
        })

    # ── Register Face ─────────────────────────────────────
    @action(detail=False, methods=['post'], url_path='register-face')
    def register_face(self, request):
        """
        POST /api/attendance/register-face/
        Body: { "image": "data:image/jpeg;base64,..." }
        """
        image_b64 = request.data.get('image')
        if not image_b64:
            return Response({'error': 'No image provided'}, status=400)

        try:
            bgr_array, img_data = decode_base64_image(image_b64)
        except Exception:
            return Response({'error': 'Invalid image data'}, status=400)

        try:
            fa    = get_face_app()
            faces = fa.get(bgr_array)
        except Exception as e:
            return Response({'error': f'Face detection failed: {str(e)}'}, status=500)

        if len(faces) == 0:
            return Response(
                {'error': 'No face detected. Please look at the camera clearly.'},
                status=400
            )
        if len(faces) > 1:
            return Response(
                {'error': 'Multiple faces detected. Please ensure only your face is visible.'},
                status=400
            )

        # Save 512-dim embedding as JSON
        embedding   = faces[0].embedding          # numpy float32 array, shape (512,)
        embed_list  = embedding.tolist()

        user = request.user
        user.face_encoding   = json.dumps(embed_list)
        user.face_registered = True

        # Save face image
        user.face_image.save(
            f'face_{user.employee_id}.jpg',
            ContentFile(img_data),
            save=False
        )
        user.save(update_fields=['face_encoding', 'face_registered', 'face_image'])

        return Response({
            'success':        True,
            'message':        f'Face registered successfully for {user.full_name}!',
            'face_registered': True,
        })

    # ── Face Check-In ─────────────────────────────────────
    @action(detail=False, methods=['post'], url_path='face-checkin')
    def face_checkin(self, request):
        """
        POST /api/attendance/face-checkin/
        Body: { "image": "data:image/jpeg;base64,..." }
        """
        image_b64 = request.data.get('image')
        if not image_b64:
            return Response({'error': 'No image provided'}, status=400)

        user = request.user

        # Check face is registered
        if not user.face_registered or not user.face_encoding:
            return Response(
                {'error': 'Face not registered yet', 'need_registration': True},
                status=400
            )

        try:
            bgr_array, _ = decode_base64_image(image_b64)
        except Exception:
            return Response({'error': 'Invalid image data'}, status=400)

        # Detect face in live image
        try:
            fa         = get_face_app()
            live_faces = fa.get(bgr_array)
        except Exception as e:
            return Response({'error': f'Face detection failed: {str(e)}'}, status=500)

        if len(live_faces) == 0:
            return Response(
                {'error': 'No face detected. Please look at the camera.'},
                status=400
            )

        # Load stored embedding & compare
        stored_embedding = np.array(json.loads(user.face_encoding), dtype=np.float32)
        live_embedding   = live_faces[0].embedding

        similarity = cosine_similarity(stored_embedding, live_embedding)
        # insightface cosine similarity: >0.35 is a solid match (buffalo_sc)
        THRESHOLD  = 0.35

        if similarity < THRESHOLD:
            return Response({
                'error':      'Face not recognized. Please try again.',
                'matched':    False,
                'similarity': round(similarity, 3),
            }, status=400)

        # ── Face matched — create attendance ──────────────
        today    = timezone.now().date()
        now_time = timezone.now().time()

        existing = Attendance.objects.filter(user=user, date=today).first()
        if existing:
            return Response({
                'error':      'Already checked in today',
                'matched':    True,
                'checked_in': True,
                'attendance': AttendanceSerializer(existing).data,
            }, status=400)

        confidence = round(similarity * 100, 1)
        obj = Attendance.objects.create(
            user            = user,
            date            = today,
            check_in        = now_time,
            status          = 'present',
            attendance_type = 'face_scan',
            notes           = f'Face scan check-in (confidence: {confidence}%)',
        )

        return Response({
            'success':    True,
            'matched':    True,
            'message':    f'Welcome {user.full_name}! Attendance marked ✅',
            'confidence': confidence,
            'attendance': AttendanceSerializer(obj).data,
        }, status=201)

    # ── Check Face Status ─────────────────────────────────
    @action(detail=False, methods=['get'], url_path='face-status')
    def face_status(self, request):
        user  = request.user
        today = timezone.now().date()
        today_attendance = Attendance.objects.filter(user=user, date=today).first()

        return Response({
            'face_registered':   user.face_registered,
            'checked_in_today':  bool(today_attendance),
            'checked_out_today': bool(today_attendance and today_attendance.check_out),
            'today_attendance':  AttendanceSerializer(today_attendance).data
                                 if today_attendance else None,
        })