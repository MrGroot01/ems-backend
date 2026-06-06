import os
import logging
import threading
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_email(email, otp, user_name=''):
    """Send OTP via Gmail SMTP in background thread"""
    def _send():
        try:
            send_mail(
                subject        = 'EMS Pro — Your Password Reset OTP',
                message        = f'Your OTP is: {otp}\nValid for 5 minutes.',
                from_email     = settings.DEFAULT_FROM_EMAIL,
                recipient_list = [email],
                fail_silently  = True,   # ← don't crash if fails
                html_message   = f'''
                <div style="font-family:Arial,sans-serif;max-width:500px;
                            margin:auto;padding:30px;border:1px solid #e2e8f0;
                            border-radius:10px;">
                    <h2 style="color:#2563eb;">🔐 EMS Pro</h2>
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>Your password reset OTP is:</p>
                    <div style="background:#f1f5f9;padding:20px;
                                text-align:center;border-radius:8px;
                                margin:20px 0;">
                        <h1 style="color:#2563eb;letter-spacing:10px;
                                   font-size:36px;">{otp}</h1>
                    </div>
                    <p>⏰ Valid for <strong>5 minutes</strong> only.</p>
                    <p>🔒 Do not share this OTP with anyone.</p>
                    <hr style="margin:20px 0;"/>
                    <small style="color:#94a3b8;">
                        EMS Pro — Employee Management System
                    </small>
                </div>
                '''
            )
            logger.info(f'OTP email sent to {email}')
        except Exception as e:
            logger.error(f'Email error: {str(e)}')

    # ── Send in background — won't block or kill worker ───
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()
    return True


def send_payslip_email(email, user_name, month, year, net_salary):
    """Send payslip notification via Gmail SMTP"""
    def _send():
        try:
            send_mail(
                subject        = f'Payslip for {month}/{year} — EMS Pro',
                message        = f'Net Salary: Rs.{net_salary}',
                from_email     = settings.DEFAULT_FROM_EMAIL,
                recipient_list = [email],
                fail_silently  = True,
                html_message   = f'''
                <div style="font-family:Arial,sans-serif;max-width:500px;
                            margin:auto;padding:30px;">
                    <h2 style="color:#2563eb;">💰 Payslip Generated</h2>
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>Your payslip for <strong>{month}/{year}</strong>
                       has been generated.</p>
                    <div style="background:#f0fdf4;padding:20px;
                                border-radius:8px;margin:20px 0;">
                        <h3 style="color:#16a34a;">
                            Net Salary: ₹{net_salary}
                        </h3>
                    </div>
                    <p>Login to EMS Pro to view your full payslip.</p>
                    <hr/>
                    <small style="color:#94a3b8;">EMS Pro</small>
                </div>
                '''
            )
            logger.info(f'Payslip email sent to {email}')
        except Exception as e:
            logger.error(f'Payslip email error: {str(e)}')

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()
    return True


def send_leave_status_email(email, user_name, status, leave_type, dates):
    """Send leave approval/rejection via Gmail SMTP"""
    def _send():
        try:
            color = '#16a34a' if status == 'approved' else '#dc2626'
            emoji = '✅' if status == 'approved' else '❌'
            send_mail(
                subject        = f'{emoji} Leave {status.title()} — EMS Pro',
                message        = f'Your {leave_type} leave has been {status}.',
                from_email     = settings.DEFAULT_FROM_EMAIL,
                recipient_list = [email],
                fail_silently  = True,
                html_message   = f'''
                <div style="font-family:Arial,sans-serif;max-width:500px;
                            margin:auto;padding:30px;">
                    <h2 style="color:{color};">{emoji} Leave {status.title()}</h2>
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>Your <strong>{leave_type}</strong> leave has been
                       <strong style="color:{color};">{status}</strong>.</p>
                    <p>📅 Dates: {dates}</p>
                    <hr/>
                    <small style="color:#94a3b8;">EMS Pro</small>
                </div>
                '''
            )
        except Exception as e:
            logger.error(f'Leave email error: {str(e)}')

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()
    return True


def send_task_reminder_email(email, user_name, task_title, due_date):
    """Send task deadline reminder via Gmail SMTP"""
    def _send():
        try:
            send_mail(
                subject        = f'⚠️ Task Deadline: {task_title}',
                message        = f'Task {task_title} is due on {due_date}.',
                from_email     = settings.DEFAULT_FROM_EMAIL,
                recipient_list = [email],
                fail_silently  = True,
                html_message   = f'''
                <div style="font-family:Arial,sans-serif;max-width:500px;
                            margin:auto;padding:30px;">
                    <h2 style="color:#f59e0b;">⚠️ Task Deadline Reminder</h2>
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>Task <strong>{task_title}</strong> is due on
                       <strong>{due_date}</strong>.</p>
                    <hr/>
                    <small style="color:#94a3b8;">EMS Pro</small>
                </div>
                '''
            )
        except Exception as e:
            logger.error(f'Task reminder error: {str(e)}')

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()
    return True