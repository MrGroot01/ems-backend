"""
ai_assistant/views.py
Gemini-powered EMS AI Assistant
"""

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
    context_parts = []

    # ── CURRENT USER INFO ──────────────────────────────────────
    context_parts.append(
        f"LOGGED IN USER: {user.full_name}, "
        f"Role={user.role}, "
        f"Department={user.department or 'N/A'}, "
        f"Email={user.email}, "
        f"Employee ID={user.employee_id}."
    )

    # ── EMPLOYEES ──────────────────────────────────────────────
    try:
        if is_admin:
            all_users = User.objects.filter(is_active=True)
            total     = all_users.count()
            emp_users = User.objects.filter(role='employee', is_active=True)
            emp_list  = ", ".join([
                f"{u.full_name} (Dept: {u.department or 'N/A'}, ID: {u.employee_id})"
                for u in emp_users[:20]
            ])
            context_parts.append(
                f"EMPLOYEES: Total Active Users={total}, "
                f"Total Employees={emp_users.count()}. "
                f"List: {emp_list}."
            )
        else:
            context_parts.append(
                f"MY PROFILE: {user.full_name}, "
                f"Department={user.department or 'N/A'}, "
                f"Phone={user.phone or 'N/A'}, "
                f"Employee ID={user.employee_id}."
            )
    except Exception:
        context_parts.append("EMPLOYEES: Data unavailable.")

    # ── ATTENDANCE ─────────────────────────────────────────────
    try:
        if is_admin:
            present = Attendance.objects.filter(date=today, status="present").count()
            absent  = Attendance.objects.filter(date=today, status="absent").count()
            absent_names = list(
                Attendance.objects.filter(date=today, status="absent")
                .select_related("employee")
                .values_list("employee__full_name", flat=True)[:10]
            )
            context_parts.append(
                f"ATTENDANCE ({today}): Present={present}, Absent={absent}. "
                f"Absent: {', '.join(absent_names) if absent_names else 'None'}."
            )
        else:
            try:
                emp = Employee.objects.get(user=user)
                att = Attendance.objects.filter(employee=emp, date=today).first()
            except Exception:
                att = None
            context_parts.append(
                f"MY ATTENDANCE TODAY ({today}): "
                f"{att.status if att else 'No record found'}."
            )
    except Exception:
        context_parts.append("ATTENDANCE: Data unavailable.")

    # ── PAYROLL ────────────────────────────────────────────────
    try:
        if is_admin:
            structures = SalaryStructure.objects.select_related("user").all()[:10]
            pay_info   = ", ".join([
                f"{s.user.full_name} (Basic=\u20b9{s.basic}, "
                f"Gross=\u20b9{s.gross}, Net=\u20b9{s.net})"
                for s in structures
            ])
            context_parts.append(
                f"SALARY STRUCTURES: {pay_info if pay_info else 'No data'}."
            )
            payslips  = Payslip.objects.select_related("user").order_by("-year", "-month")[:10]
            slip_info = ", ".join([
                f"{p.user.full_name} ({p.month}/{p.year}): "
                f"Net=\u20b9{p.net}, Paid={'Yes' if p.paid else 'No'}"
                for p in payslips
            ])
            context_parts.append(
                f"RECENT PAYSLIPS: {slip_info if slip_info else 'No data'}."
            )
        else:
            try:
                salary = SalaryStructure.objects.get(user=user)
                context_parts.append(
                    f"MY SALARY: Basic=\u20b9{salary.basic}, "
                    f"HRA=\u20b9{salary.hra}, "
                    f"Transport=\u20b9{salary.transport}, "
                    f"Medical=\u20b9{salary.medical}, "
                    f"Gross=\u20b9{salary.gross}, "
                    f"PF Deduction=\u20b9{salary.pf_deduction}, "
                    f"Tax=\u20b9{salary.tax_deduction}, "
                    f"Net=\u20b9{salary.net}."
                )
            except SalaryStructure.DoesNotExist:
                context_parts.append("MY SALARY: No salary structure assigned yet.")

            slip = Payslip.objects.filter(user=user).order_by("-year", "-month").first()
            if slip:
                context_parts.append(
                    f"LAST PAYSLIP: {slip.month}/{slip.year}, "
                    f"Basic=\u20b9{slip.basic}, "
                    f"Gross=\u20b9{slip.gross}, "
                    f"Deductions=\u20b9{slip.deductions}, "
                    f"Net=\u20b9{slip.net}, "
                    f"Days Worked={slip.days_worked}, "
                    f"Paid={'Yes' if slip.paid else 'No'}."
                )
            else:
                context_parts.append("LAST PAYSLIP: No payslip generated yet.")
    except Exception:
        context_parts.append("PAYROLL: Data unavailable.")

    # ── LEAVES ─────────────────────────────────────────────────
    try:
        if is_admin:
            pending       = Leave.objects.filter(status="pending").select_related("employee")
            pending_count = pending.count()
            pending_names = ", ".join([
                f"{l.employee.full_name if hasattr(l.employee, 'full_name') else str(l.employee)}"
                for l in pending[:10]
            ])
            context_parts.append(
                f"LEAVES: Pending={pending_count}. "
                f"Employees waiting: {pending_names if pending_names else 'None'}."
            )
        else:
            try:
                emp       = Employee.objects.get(user=user)
                my_leaves = Leave.objects.filter(employee=emp).order_by("-id")[:3]
                leave_info = ", ".join([
                    f"{l.leave_type} ({l.status}) {l.start_date} to {l.end_date}"
                    for l in my_leaves
                ])
                context_parts.append(
                    f"MY LEAVES: {leave_info if leave_info else 'No leave records'}."
                )
            except Exception:
                context_parts.append("MY LEAVES: No leave records found.")
    except Exception:
        context_parts.append("LEAVES: Data unavailable.")

    # ── TASKS ──────────────────────────────────────────────────
    try:
        if is_admin:
            total_t   = Task.objects.count()
            pending_t = Task.objects.filter(status__in=["pending", "todo"]).count()
            inprog_t  = Task.objects.filter(status="in_progress").count()
            overdue_t = Task.objects.filter(
                due_date__lt=timezone.now(),
                status__in=["pending", "in_progress", "todo"],
            ).count()
            context_parts.append(
                f"TASKS: Total={total_t}, "
                f"Pending={pending_t}, "
                f"In Progress={inprog_t}, "
                f"Overdue={overdue_t}."
            )
        else:
            my_tasks  = Task.objects.filter(assigned_to=user).order_by("-id")[:5]
            task_info = ", ".join([
                f"'{t.title}' [{t.status}] "
                f"due {t.due_date.strftime('%b %d, %Y') if t.due_date else 'N/A'}"
                for t in my_tasks
            ])
            context_parts.append(
                f"MY TASKS: {task_info if task_info else 'No tasks assigned'}."
            )
    except Exception:
        context_parts.append("TASKS: Data unavailable.")

    return "\n".join(context_parts)


SYSTEM_PROMPT_TEMPLATE = """You are an intelligent AI assistant for an Employee Management System (EMS).
Answer questions based ONLY on the context data provided below.

RULES:
1. Give clear, short, and accurate answers.
2. Use ONLY the context data — never guess or make up data.
3. If data is not available, say: "No data found".
4. Be professional like an HR assistant.
5. Use the Rupee symbol for all salary amounts.
6. If the question is unclear, ask a follow-up question.
7. For Admin: you can see all company data.
8. For Employee: you can only see your own personal data.

USER ROLE: {role}

CONTEXT DATA (REAL-TIME FROM DATABASE):
{context}

TONE: Professional, helpful, friendly but concise."""


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ai_assistant_chat(request):
    """
    POST /api/ai-assistant/chat/
    Body: { "message": "How many employees?", "history": [] }
    """
    user_message = request.data.get("message", "").strip()
    history      = request.data.get("history", [])

    if not user_message:
        return Response(
            {"error": "Message is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    context  = build_context(request.user)
    role_str = "Admin" if (
        request.user.role == 'admin' or
        request.user.is_staff or
        request.user.is_superuser
    ) else "Employee"

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        role=role_str,
        context=context,
    )

    history_text = ""
    for turn in history[-10:]:
        if turn.get("role") == "user":
            history_text += f"User: {turn['content']}\n"
        elif turn.get("role") == "assistant":
            history_text += f"Assistant: {turn['content']}\n"

    full_prompt = (
        f"{system_prompt}\n\n"
        f"{history_text}"
        f"User: {user_message}\n"
        f"Assistant:"
    )

    # ── Call Gemini API ────────────────────────────────────────
    try:
        api_key = getattr(settings, 'GEMINI_API_KEY', None)

        # Check key exists
        if not api_key or api_key == 'your-gemini-key-here':
            return Response({
                "reply": "⚠️ GEMINI_API_KEY is not set in settings.py. Please add your API key.",
                "role": role_str,
            })

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0.3,
            ),
        )
        reply = response.text.strip()

    except Exception as e:
        # Print full traceback to Django terminal for debugging
        traceback.print_exc()
        error_msg = str(e)
        print(f"\n[AI ASSISTANT ERROR]: {error_msg}\n")

        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            reply = (
                "⚠️ Free quota limit reached. "
                "Please wait 1-2 minutes and try again, "
                "or create a new API key at https://aistudio.google.com/app/apikey"
            )
        elif "401" in error_msg or "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            reply = (
                "⚠️ Invalid Gemini API key. "
                "Please check your GEMINI_API_KEY in settings.py. "
                "Get a free key at https://aistudio.google.com/app/apikey"
            )
        elif "403" in error_msg or "PERMISSION_DENIED" in error_msg:
            reply = (
                "⚠️ API key doesn't have permission. "
                "Make sure your key has Gemini API access enabled."
            )
        elif "404" in error_msg or "not found" in error_msg.lower():
            reply = (
                "⚠️ Model not found. "
                "The gemini-1.5-flash model may not be available in your region."
            )
        else:
            # Show actual error in development so we can debug
            reply = f"⚠️ AI Error: {error_msg[:200]}"

    return Response({
        "reply": reply,
        "role":  role_str,
    })