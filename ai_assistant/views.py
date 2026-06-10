import traceback
from google import genai
from google.genai import types
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from employees.models import Employee
from attendance.models import Attendance
from payroll.models import SalaryStructure, Payslip
from leaves.models import Leave
from tasks.models import Task
from users.models import User


def build_context(user):
    today    = timezone.now().date()
    is_admin = user.role == 'admin' or user.is_staff or user.is_superuser
    parts    = []

    parts.append(
        f"LOGGED IN USER: {user.full_name}, "
        f"Role={user.role}, "
        f"Department={user.department or 'N/A'}, "
        f"Email={user.email}, "
        f"Employee ID={user.employee_id}."
    )

    # Employees
    try:
        if is_admin:
            emp_users = User.objects.filter(role='employee', is_active=True)
            emp_list  = ", ".join([
                f"{u.full_name} (Dept:{u.department or 'N/A'}, ID:{u.employee_id})"
                for u in emp_users[:20]
            ])
            parts.append(
                f"EMPLOYEES: Total={emp_users.count()}. List: {emp_list}."
            )
        else:
            parts.append(
                f"MY PROFILE: {user.full_name}, "
                f"Dept={user.department or 'N/A'}, "
                f"ID={user.employee_id}."
            )
    except Exception:
        parts.append("EMPLOYEES: Data unavailable.")

    # Attendance
    try:
        if is_admin:
            present = Attendance.objects.filter(date=today, status='present').count()
            total   = Attendance.objects.filter(date=today).count()
            parts.append(
                f"ATTENDANCE TODAY ({today}): Present={present}, Total Records={total}."
            )
        else:
            att = Attendance.objects.filter(user=user, date=today).first()
            parts.append(
                f"MY ATTENDANCE TODAY: "
                f"{'Check-in: '+str(att.check_in)+', Status: '+att.status if att else 'Not checked in yet'}."
            )
    except Exception:
        parts.append("ATTENDANCE: Data unavailable.")

    # Payroll
    try:
        if is_admin:
            structures = SalaryStructure.objects.select_related('user').all()[:10]
            pay_info   = ", ".join([
                f"{s.user.full_name}(Net=₹{s.net})"
                for s in structures
            ])
            parts.append(f"SALARY STRUCTURES: {pay_info or 'No data'}.")
        else:
            try:
                salary = SalaryStructure.objects.get(user=user)
                parts.append(
                    f"MY SALARY: Basic=₹{salary.basic}, "
                    f"HRA=₹{salary.hra}, "
                    f"Gross=₹{salary.gross}, "
                    f"Net=₹{salary.net}."
                )
            except SalaryStructure.DoesNotExist:
                parts.append("MY SALARY: No salary structure assigned yet.")
            slip = Payslip.objects.filter(user=user).order_by('-year', '-month').first()
            if slip:
                parts.append(
                    f"LAST PAYSLIP: {slip.month}/{slip.year}, "
                    f"Net=₹{slip.net}, "
                    f"Paid={'Yes' if slip.paid else 'No'}."
                )
    except Exception:
        parts.append("PAYROLL: Data unavailable.")

    # Leaves
    try:
        if is_admin:
            pending = Leave.objects.filter(status='pending').count()
            parts.append(f"PENDING LEAVES: {pending} requests.")
        else:
            my_leaves = Leave.objects.filter(user=user).order_by('-id')[:5]
            leave_info = ", ".join([
                f"{l.leave_type}({l.status}) {l.start_date} to {l.end_date}"
                for l in my_leaves
            ])
            parts.append(
                f"MY LEAVES: {leave_info or 'No leave records'}."
            )
    except Exception:
        parts.append("LEAVES: Data unavailable.")

    # Tasks
    try:
        if is_admin:
            total_t   = Task.objects.count()
            pending_t = Task.objects.filter(status__in=['pending','todo']).count()
            inprog_t  = Task.objects.filter(status='in_progress').count()
            parts.append(
                f"TASKS: Total={total_t}, "
                f"Pending={pending_t}, "
                f"In Progress={inprog_t}."
            )
        else:
            my_tasks  = Task.objects.filter(assigned_to=user).order_by('-id')[:5]
            task_info = ", ".join([
                f"'{t.title}'[{t.status}] due {t.due_date}"
                for t in my_tasks
            ])
            parts.append(
                f"MY TASKS: {task_info or 'No tasks assigned'}."
            )
    except Exception:
        parts.append("TASKS: Data unavailable.")

    return "\n".join(parts)


SYSTEM_PROMPT = """You are a helpful AI assistant for EMS Pro (Employee Management System).

RULES:
1. Answer based ONLY on the context data provided.
2. Be concise, clear and professional.
3. Use ₹ for salary amounts.
4. If data not available, say "No data found".
5. Admin can see all company data. Employee sees only their own data.
6. Be friendly and helpful like an HR assistant.

USER ROLE: {role}

REAL-TIME DATABASE CONTEXT:
{context}"""


# ── Available models to try in order ──────────────────────
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-pro",
]


def call_gemini(api_key, prompt):
    """Try multiple Gemini models until one works"""
    client = genai.Client(api_key=api_key)
    last_error = None

    for model_name in GEMINI_MODELS:
        try:
            print(f"[GEMINI] Trying model: {model_name}", flush=True)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1024,
                    temperature=0.3,
                ),
            )
            print(f"[GEMINI] Success with model: {model_name}", flush=True)
            return response.text.strip(), model_name
        except Exception as e:
            error_str = str(e)
            print(f"[GEMINI] Model {model_name} failed: {error_str}", flush=True)
            last_error = e
            # Stop trying if quota exceeded — no point trying other models
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                raise e
            continue

    raise last_error


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_assistant_chat(request):
    """
    POST /api/ai-assistant/chat/
    Body: { "message": "...", "history": [] }
    """
    user_message = request.data.get('message', '').strip()
    history      = request.data.get('history', [])

    if not user_message:
        return Response(
            {'error': 'Message is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        return Response({
            'reply': '⚠️ GEMINI_API_KEY not set. Please add it to your environment variables.',
            'role':  'unknown',
        })

    context  = build_context(request.user)
    role_str = 'Admin' if (
        request.user.role == 'admin' or
        request.user.is_staff or
        request.user.is_superuser
    ) else 'Employee'

    system_prompt = SYSTEM_PROMPT.format(role=role_str, context=context)

    # Build history text
    history_text = ''
    for turn in history[-8:]:
        if turn.get('role') == 'user':
            history_text += f"User: {turn['content']}\n"
        elif turn.get('role') == 'assistant':
            history_text += f"Assistant: {turn['content']}\n"

    full_prompt = (
        f"{system_prompt}\n\n"
        f"CONVERSATION HISTORY:\n{history_text}\n"
        f"User: {user_message}\n"
        f"Assistant:"
    )

    try:
        reply, used_model = call_gemini(api_key, full_prompt)
        print(f"[AI] Response generated using {used_model}", flush=True)

    except Exception as e:
        traceback.print_exc()
        error_msg = str(e)
        print(f"[AI ERROR] {error_msg}", flush=True)

        if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
            reply = (
                "⚠️ API quota exceeded. Please wait a few minutes and try again.\n\n"
                "To get a new free API key: https://aistudio.google.com/app/apikey"
            )
        elif '401' in error_msg or 'API_KEY_INVALID' in error_msg:
            reply = (
                "⚠️ Invalid API key. Please update GEMINI_API_KEY in your "
                "Render environment variables.\n\n"
                "Get a new key: https://aistudio.google.com/app/apikey"
            )
        elif '403' in error_msg or 'PERMISSION_DENIED' in error_msg:
            reply = (
                "⚠️ API key doesn't have permission. "
                "Make sure Gemini API is enabled for your key."
            )
        else:
            reply = f"⚠️ AI Error: {error_msg[:200]}"

    return Response({
        'reply': reply,
        'role':  role_str,
    })