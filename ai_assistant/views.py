import time
import traceback
import requests as http_requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

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
                f"{u.full_name}(Dept:{u.department or 'N/A'},ID:{u.employee_id})"
                for u in emp_users[:20]
            ])
            parts.append(f"EMPLOYEES: Total={emp_users.count()}. {emp_list}.")
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
                f"ATTENDANCE TODAY ({today}): Present={present}, Records={total}."
            )
        else:
            att = Attendance.objects.filter(user=user, date=today).first()
            parts.append(
                f"MY ATTENDANCE: "
                f"{'CheckIn:'+str(att.check_in)+',Status:'+att.status if att else 'Not checked in'}."
            )
    except Exception:
        parts.append("ATTENDANCE: Data unavailable.")

    # Payroll
    try:
        if is_admin:
            structures = SalaryStructure.objects.select_related('user').all()[:10]
            pay_info   = ", ".join([
                f"{s.user.full_name}(Net=₹{s.net})" for s in structures
            ])
            parts.append(f"SALARIES: {pay_info or 'No data'}.")
        else:
            try:
                s = SalaryStructure.objects.get(user=user)
                parts.append(
                    f"MY SALARY: Basic=₹{s.basic}, HRA=₹{s.hra}, "
                    f"Gross=₹{s.gross}, Net=₹{s.net}."
                )
            except SalaryStructure.DoesNotExist:
                parts.append("MY SALARY: Not assigned yet.")
            slip = Payslip.objects.filter(user=user).order_by('-year','-month').first()
            if slip:
                parts.append(
                    f"LAST PAYSLIP: {slip.month}/{slip.year}, "
                    f"Net=₹{slip.net}, Paid={'Yes' if slip.paid else 'No'}."
                )
    except Exception:
        parts.append("PAYROLL: Data unavailable.")

    # Leaves
    try:
        if is_admin:
            pending = Leave.objects.filter(status='pending').count()
            parts.append(f"PENDING LEAVES: {pending}.")
        else:
            my_leaves = Leave.objects.filter(user=user).order_by('-id')[:5]
            info = ", ".join([
                f"{l.leave_type}({l.status}){l.start_date}-{l.end_date}"
                for l in my_leaves
            ])
            parts.append(f"MY LEAVES: {info or 'None'}.")
    except Exception:
        parts.append("LEAVES: Data unavailable.")

    # Tasks
    try:
        if is_admin:
            parts.append(
                f"TASKS: Total={Task.objects.count()}, "
                f"Pending={Task.objects.filter(status__in=['pending','todo']).count()}, "
                f"InProgress={Task.objects.filter(status='in_progress').count()}."
            )
        else:
            my_tasks = Task.objects.filter(assigned_to=user).order_by('-id')[:5]
            info = ", ".join([
                f"'{t.title}'[{t.status}]due:{t.due_date}" for t in my_tasks
            ])
            parts.append(f"MY TASKS: {info or 'None'}.")
    except Exception:
        parts.append("TASKS: Data unavailable.")

    return "\n".join(parts)


SYSTEM_PROMPT = """You are EMS Pro AI Assistant — a helpful HR assistant.

RULES:
1. Answer ONLY based on the context data below.
2. Be concise, clear, professional and friendly.
3. Use ₹ for salary amounts.
4. If data not available, say "No data found".
5. Admin sees all company data. Employee sees only their own data.

USER ROLE: {role}
CONTEXT:
{context}
---"""


def call_gemini(api_key, prompt):
    """Try Gemini models"""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise Exception("google-genai not installed")

    client = genai.Client(api_key=api_key)
    models = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ]

    last_err = None
    for model in models:
        try:
            print(f"[GEMINI] Trying {model}...", flush=True)
            res = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=512,
                    temperature=0.3,
                ),
            )
            print(f"[GEMINI] ✅ {model} worked!", flush=True)
            return res.text.strip()
        except Exception as e:
            print(f"[GEMINI] ❌ {model}: {str(e)[:100]}", flush=True)
            last_err = e
            if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
                continue  # try next model
            raise e

    raise last_err or Exception("All Gemini models failed")


def call_anthropic(api_key, prompt):
    """Use Anthropic Claude as fallback"""
    print("[ANTHROPIC] Trying Claude...", flush=True)
    res = http_requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key':         api_key,
            'anthropic-version': '2023-06-01',
            'content-type':      'application/json',
        },
        json={
            'model':      'claude-haiku-4-5-20251001',
            'max_tokens': 512,
            'messages':   [{'role': 'user', 'content': prompt}],
        },
        timeout=30,
    )
    if res.status_code == 200:
        data  = res.json()
        reply = data['content'][0]['text'].strip()
        print("[ANTHROPIC] ✅ Claude responded!", flush=True)
        return reply
    else:
        raise Exception(f"Anthropic error {res.status_code}: {res.text[:200]}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_assistant_chat(request):
    user_message = request.data.get('message', '').strip()
    history      = request.data.get('history', [])

    if not user_message:
        return Response(
            {'error': 'Message is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    context  = build_context(request.user)
    role_str = 'Admin' if (
        request.user.role == 'admin' or
        request.user.is_staff or
        request.user.is_superuser
    ) else 'Employee'

    system_prompt = SYSTEM_PROMPT.format(role=role_str, context=context)

    history_text = ''
    for turn in history[-6:]:
        if turn.get('role') == 'user':
            history_text += f"User: {turn['content']}\n"
        elif turn.get('role') == 'assistant':
            history_text += f"Assistant: {turn['content']}\n"

    full_prompt = (
        f"{system_prompt}\n"
        f"HISTORY:\n{history_text}"
        f"User: {user_message}\n"
        f"Assistant:"
    )

    reply     = None
    used_api  = None

    # ── Try Gemini first ──────────────────────────────────
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    if gemini_key:
        try:
            reply    = call_gemini(gemini_key, full_prompt)
            used_api = 'Gemini'
        except Exception as e:
            err = str(e)
            print(f"[AI] Gemini failed: {err[:100]}", flush=True)
            if '429' in err or 'RESOURCE_EXHAUSTED' in err or 'quota' in err.lower():
                print("[AI] Gemini quota exceeded, trying Anthropic...", flush=True)
            else:
                reply = f"⚠️ Gemini Error: {err[:150]}"

    # ── Fallback to Anthropic Claude ──────────────────────
    if reply is None:
        anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if anthropic_key:
            try:
                reply    = call_anthropic(anthropic_key, full_prompt)
                used_api = 'Claude'
            except Exception as e:
                print(f"[AI] Anthropic failed: {str(e)[:100]}", flush=True)
                reply = None

    # ── Both failed ───────────────────────────────────────
    if reply is None:
        reply = (
            "⚠️ AI service temporarily unavailable.\n\n"
            "Your Gemini API quota is exhausted. "
            "Please get a new API key:\n"
            "👉 https://aistudio.google.com/app/apikey\n\n"
            "Then update GEMINI_API_KEY in Render environment variables."
        )

    if used_api:
        print(f"[AI] ✅ Response via {used_api}", flush=True)

    return Response({'reply': reply, 'role': role_str})