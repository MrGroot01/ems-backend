import os
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_email(email, otp, user_name=''):
    """Send OTP via Brevo HTTP API — works on Render free tier"""
    try:
        api_key = os.environ.get('BREVO_API_KEY', '')

        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'accept':       'application/json',
                'api-key':      api_key,
                'content-type': 'application/json',
            },
            json={
                'sender': {
                    'name':  'EMS Pro',
                    'email': 'kirand09876@gmail.com'
                },
                'to': [{'email': email}],
                'subject': 'EMS Pro — Your Password Reset OTP',
                'htmlContent': f'''
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
                    <small style="color:#94a3b8;">EMS Pro</small>
                </div>
                ''',
                'textContent': f'Your EMS Pro OTP is: {otp}. Valid for 5 minutes.'
            },
            timeout=15
        )

        if response.status_code == 201:
            print(f'[EMAIL SENT] OTP to {email}', flush=True)
            logger.info(f'OTP email sent to {email}')
            return True
        else:
            print(f'[EMAIL FAILED] {response.status_code}: {response.text}', flush=True)
            return False

    except Exception as e:
        print(f'[EMAIL ERROR] {email}: {str(e)}', flush=True)
        logger.error(f'Email error: {str(e)}')
        return False


def send_payslip_email(email, user_name, month, year, net_salary):
    try:
        api_key = os.environ.get('BREVO_API_KEY', '')
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'accept':       'application/json',
                'api-key':      api_key,
                'content-type': 'application/json',
            },
            json={
                'sender': {'name': 'EMS Pro', 'email': 'kirand09876@gmail.com'},
                'to': [{'email': email}],
                'subject': f'Payslip for {month}/{year} — EMS Pro',
                'htmlContent': f'''
                <div style="font-family:Arial,sans-serif;max-width:500px;
                            margin:auto;padding:30px;">
                    <h2 style="color:#2563eb;">💰 Payslip Generated</h2>
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>Your payslip for <strong>{month}/{year}</strong>
                       has been generated.</p>
                    <div style="background:#f0fdf4;padding:20px;
                                border-radius:8px;margin:20px 0;">
                        <h3 style="color:#16a34a;">Net Salary: ₹{net_salary}</h3>
                    </div>
                    <p>Login to EMS Pro to view your full payslip.</p>
                    <hr/><small style="color:#94a3b8;">EMS Pro</small>
                </div>
                ''',
            },
            timeout=15
        )
        return response.status_code == 201
    except Exception as e:
        logger.error(f'Payslip email error: {str(e)}')
        return False


def send_leave_status_email(email, user_name, status, leave_type, dates):
    try:
        api_key = os.environ.get('BREVO_API_KEY', '')
        color   = '#16a34a' if status == 'approved' else '#dc2626'
        emoji   = '✅' if status == 'approved' else '❌'
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'accept':       'application/json',
                'api-key':      api_key,
                'content-type': 'application/json',
            },
            json={
                'sender': {'name': 'EMS Pro', 'email': 'kirand09876@gmail.com'},
                'to': [{'email': email}],
                'subject': f'{emoji} Leave {status.title()} — EMS Pro',
                'htmlContent': f'''
                <div style="font-family:Arial,sans-serif;max-width:500px;
                            margin:auto;padding:30px;">
                    <h2 style="color:{color};">{emoji} Leave {status.title()}</h2>
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>Your <strong>{leave_type}</strong> leave has been
                       <strong style="color:{color};">{status}</strong>.</p>
                    <p>📅 Dates: {dates}</p>
                    <hr/><small style="color:#94a3b8;">EMS Pro</small>
                </div>
                ''',
            },
            timeout=15
        )
        return response.status_code == 201
    except Exception as e:
        logger.error(f'Leave email error: {str(e)}')
        return False


def send_task_reminder_email(email, user_name, task_title, due_date):
    try:
        api_key = os.environ.get('BREVO_API_KEY', '')
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'accept':       'application/json',
                'api-key':      api_key,
                'content-type': 'application/json',
            },
            json={
                'sender': {'name': 'EMS Pro', 'email': 'kirand09876@gmail.com'},
                'to': [{'email': email}],
                'subject': f'⚠️ Task Deadline: {task_title}',
                'htmlContent': f'''
                <div style="font-family:Arial,sans-serif;max-width:500px;
                            margin:auto;padding:30px;">
                    <h2 style="color:#f59e0b;">⚠️ Task Deadline Reminder</h2>
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>Task <strong>{task_title}</strong> is due on
                       <strong>{due_date}</strong>.</p>
                    <hr/><small style="color:#94a3b8;">EMS Pro</small>
                </div>
                ''',
            },
            timeout=15
        )
        return response.status_code == 201
    except Exception as e:
        logger.error(f'Task reminder error: {str(e)}')
        return False