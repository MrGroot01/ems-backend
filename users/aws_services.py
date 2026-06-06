import os
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_brevo_headers():
    return {
        'accept':       'application/json',
        'api-key':      os.environ.get('BREVO_API_KEY', ''),
        'content-type': 'application/json',
    }


def send_otp_email(email, otp, user_name=''):
    """Send OTP via Brevo HTTP API"""
    try:
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers=get_brevo_headers(),
            json={
                'sender': {'name': 'EMS Pro', 'email': 'kirand09876@gmail.com'},
                'to': [{'email': email, 'name': user_name}],
                'subject': '🔐 EMS Pro — Your Password Reset OTP',
                'textContent': f'Your EMS Pro OTP is: {otp}. Valid for 5 minutes.',
                'htmlContent': f'''
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:30px 0;">
<table width="500" cellpadding="0" cellspacing="0"
       style="background:#ffffff;border-radius:12px;overflow:hidden;
              box-shadow:0 4px 20px rgba(0,0,0,0.1);">

    <!-- Header -->
    <tr>
        <td style="background:linear-gradient(135deg,#2563eb,#7c3aed);
                   padding:40px;text-align:center;">
            <div style="font-size:48px;">🏢</div>
            <h1 style="color:#ffffff;margin:10px 0 5px;
                       font-size:28px;letter-spacing:2px;">EMS Pro</h1>
            <p style="color:rgba(255,255,255,0.8);margin:0;font-size:14px;">
                Employee Management System
            </p>
        </td>
    </tr>

    <!-- Title -->
    <tr>
        <td style="padding:35px 40px 20px;text-align:center;">
            <h2 style="color:#1e293b;margin:0 0 8px;font-size:22px;">
                🔐 OTP Verification
            </h2>
            <p style="color:#64748b;margin:0;font-size:14px;">
                Password Reset Request
            </p>
        </td>
    </tr>

    <!-- Greeting -->
    <tr>
        <td style="padding:0 40px 20px;">
            <p style="color:#334155;font-size:15px;margin:0;">
                Hello <strong>{user_name}</strong>,
            </p>
            <p style="color:#64748b;font-size:14px;margin:8px 0 0;">
                Please use the following One-Time Password to reset your password.
            </p>
        </td>
    </tr>

    <!-- OTP Box -->
    <tr>
        <td style="padding:0 40px 25px;">
            <div style="background:linear-gradient(135deg,#eff6ff,#f5f3ff);
                        border:2px dashed #2563eb;border-radius:12px;
                        padding:25px;text-align:center;">
                <p style="color:#64748b;font-size:12px;text-transform:uppercase;
                          letter-spacing:2px;margin:0 0 10px;">
                    Your OTP Code
                </p>
                <h1 style="color:#2563eb;font-size:48px;letter-spacing:12px;
                           margin:0;font-weight:900;">{otp}</h1>
            </div>
        </td>
    </tr>

    <!-- Warning -->
    <tr>
        <td style="padding:0 40px 20px;">
            <div style="background:#fef9c3;border-left:4px solid #eab308;
                        border-radius:8px;padding:15px;">
                <p style="color:#854d0e;font-size:13px;margin:0;">
                    ⏰ This OTP is valid for <strong>5 minutes</strong> only.
                    Do not share this code with anyone.
                </p>
            </div>
        </td>
    </tr>

    <!-- Security Tips -->
    <tr>
        <td style="padding:0 40px 25px;">
            <div style="background:#f8fafc;border-radius:8px;padding:20px;">
                <p style="color:#475569;font-size:13px;font-weight:bold;margin:0 0 10px;">
                    🛡️ Security Tips
                </p>
                <ul style="color:#64748b;font-size:13px;margin:0;padding-left:20px;">
                    <li style="margin-bottom:6px;">Never share your OTP with anyone</li>
                    <li style="margin-bottom:6px;">
                        EMS Pro will never ask for your OTP via phone or chat
                    </li>
                    <li>If you didn't request this, ignore this email immediately</li>
                </ul>
            </div>
        </td>
    </tr>

    <!-- Footer -->
    <tr>
        <td style="background:#f8fafc;padding:20px 40px;text-align:center;
                   border-top:1px solid #e2e8f0;">
            <p style="color:#94a3b8;font-size:12px;margin:0;">
                © 2026 EMS Pro. All rights reserved.
            </p>
            <p style="color:#cbd5e1;font-size:11px;margin:5px 0 0;">
                You received this email because a password reset
                was requested for your account.
            </p>
        </td>
    </tr>

</table>
</td></tr>
</table>
</body>
</html>
                ''',
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
    """Send payslip notification via Brevo API"""
    try:
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers=get_brevo_headers(),
            json={
                'sender': {'name': 'EMS Pro', 'email': 'kirand09876@gmail.com'},
                'to': [{'email': email, 'name': user_name}],
                'subject': f'💰 Payslip for {month}/{year} — EMS Pro',
                'htmlContent': f'''
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:30px 0;">
<table width="500" cellpadding="0" cellspacing="0"
       style="background:#ffffff;border-radius:12px;overflow:hidden;
              box-shadow:0 4px 20px rgba(0,0,0,0.1);">
    <tr>
        <td style="background:linear-gradient(135deg,#16a34a,#15803d);
                   padding:40px;text-align:center;">
            <div style="font-size:48px;">💰</div>
            <h1 style="color:#ffffff;margin:10px 0 5px;font-size:28px;">EMS Pro</h1>
            <p style="color:rgba(255,255,255,0.8);margin:0;font-size:14px;">
                Payroll Department
            </p>
        </td>
    </tr>
    <tr>
        <td style="padding:35px 40px 20px;text-align:center;">
            <h2 style="color:#1e293b;margin:0;">💼 Payslip Generated</h2>
            <p style="color:#64748b;font-size:14px;">
                {month} {year}
            </p>
        </td>
    </tr>
    <tr>
        <td style="padding:0 40px 25px;">
            <p style="color:#334155;font-size:15px;">
                Hello <strong>{user_name}</strong>,
            </p>
            <p style="color:#64748b;font-size:14px;">
                Your payslip for <strong>{month}/{year}</strong> has been generated.
            </p>
            <div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);
                        border:2px solid #16a34a;border-radius:12px;
                        padding:25px;text-align:center;margin:20px 0;">
                <p style="color:#15803d;font-size:13px;margin:0 0 8px;
                          text-transform:uppercase;letter-spacing:1px;">
                    Net Salary
                </p>
                <h1 style="color:#16a34a;font-size:40px;margin:0;">
                    ₹{net_salary}
                </h1>
            </div>
            <p style="color:#64748b;font-size:14px;text-align:center;">
                Login to EMS Pro to view your complete payslip.
            </p>
        </td>
    </tr>
    <tr>
        <td style="background:#f8fafc;padding:20px 40px;text-align:center;
                   border-top:1px solid #e2e8f0;">
            <p style="color:#94a3b8;font-size:12px;margin:0;">
                © 2026 EMS Pro. All rights reserved.
            </p>
        </td>
    </tr>
</table>
</td></tr>
</table>
</body>
</html>
                ''',
            },
            timeout=15
        )
        return response.status_code == 201
    except Exception as e:
        logger.error(f'Payslip email error: {str(e)}')
        return False


def send_leave_status_email(email, user_name, status, leave_type, dates):
    """Send leave approval/rejection via Brevo API"""
    try:
        color      = '#16a34a' if status == 'approved' else '#dc2626'
        bg_color   = '#f0fdf4' if status == 'approved' else '#fef2f2'
        emoji      = '✅' if status == 'approved' else '❌'
        hdr_color  = '#16a34a' if status == 'approved' else '#dc2626'
        hdr_color2 = '#15803d' if status == 'approved' else '#b91c1c'

        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers=get_brevo_headers(),
            json={
                'sender': {'name': 'EMS Pro', 'email': 'kirand09876@gmail.com'},
                'to': [{'email': email, 'name': user_name}],
                'subject': f'{emoji} Leave {status.title()} — EMS Pro',
                'htmlContent': f'''
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:30px 0;">
<table width="500" cellpadding="0" cellspacing="0"
       style="background:#ffffff;border-radius:12px;overflow:hidden;
              box-shadow:0 4px 20px rgba(0,0,0,0.1);">
    <tr>
        <td style="background:linear-gradient(135deg,{hdr_color},{hdr_color2});
                   padding:40px;text-align:center;">
            <div style="font-size:48px;">{emoji}</div>
            <h1 style="color:#ffffff;margin:10px 0 5px;font-size:28px;">EMS Pro</h1>
            <p style="color:rgba(255,255,255,0.8);margin:0;font-size:14px;">
                Leave Management
            </p>
        </td>
    </tr>
    <tr>
        <td style="padding:35px 40px;">
            <p style="color:#334155;font-size:15px;">
                Hello <strong>{user_name}</strong>,
            </p>
            <div style="background:{bg_color};border-left:4px solid {color};
                        border-radius:8px;padding:20px;margin:20px 0;">
                <p style="color:{color};font-size:16px;font-weight:bold;margin:0 0 8px;">
                    Leave {status.title()}
                </p>
                <p style="color:#475569;font-size:14px;margin:0;">
                    Your <strong>{leave_type}</strong> leave request has been
                    <strong style="color:{color};">{status}</strong>.
                </p>
                <p style="color:#64748b;font-size:13px;margin:8px 0 0;">
                    📅 Dates: {dates}
                </p>
            </div>
            <p style="color:#64748b;font-size:14px;">
                Login to EMS Pro for more details.
            </p>
        </td>
    </tr>
    <tr>
        <td style="background:#f8fafc;padding:20px 40px;text-align:center;
                   border-top:1px solid #e2e8f0;">
            <p style="color:#94a3b8;font-size:12px;margin:0;">
                © 2026 EMS Pro. All rights reserved.
            </p>
        </td>
    </tr>
</table>
</td></tr>
</table>
</body>
</html>
                ''',
            },
            timeout=15
        )
        return response.status_code == 201
    except Exception as e:
        logger.error(f'Leave email error: {str(e)}')
        return False


def send_task_reminder_email(email, user_name, task_title, due_date):
    """Send task deadline reminder via Brevo API"""
    try:
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers=get_brevo_headers(),
            json={
                'sender': {'name': 'EMS Pro', 'email': 'kirand09876@gmail.com'},
                'to': [{'email': email, 'name': user_name}],
                'subject': f'⚠️ Task Deadline Reminder: {task_title}',
                'htmlContent': f'''
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:30px 0;">
<table width="500" cellpadding="0" cellspacing="0"
       style="background:#ffffff;border-radius:12px;overflow:hidden;
              box-shadow:0 4px 20px rgba(0,0,0,0.1);">
    <tr>
        <td style="background:linear-gradient(135deg,#f59e0b,#d97706);
                   padding:40px;text-align:center;">
            <div style="font-size:48px;">⚠️</div>
            <h1 style="color:#ffffff;margin:10px 0 5px;font-size:28px;">EMS Pro</h1>
            <p style="color:rgba(255,255,255,0.8);margin:0;font-size:14px;">
                Task Management
            </p>
        </td>
    </tr>
    <tr>
        <td style="padding:35px 40px;">
            <p style="color:#334155;font-size:15px;">
                Hello <strong>{user_name}</strong>,
            </p>
            <div style="background:#fffbeb;border-left:4px solid #f59e0b;
                        border-radius:8px;padding:20px;margin:20px 0;">
                <p style="color:#92400e;font-size:16px;font-weight:bold;margin:0 0 8px;">
                    Task Deadline Reminder
                </p>
                <p style="color:#475569;font-size:14px;margin:0;">
                    Task: <strong>{task_title}</strong>
                </p>
                <p style="color:#dc2626;font-size:14px;margin:8px 0 0;">
                    📅 Due: <strong>{due_date}</strong>
                </p>
            </div>
            <p style="color:#64748b;font-size:14px;">
                Please login to EMS Pro to update your task progress.
            </p>
        </td>
    </tr>
    <tr>
        <td style="background:#f8fafc;padding:20px 40px;text-align:center;
                   border-top:1px solid #e2e8f0;">
            <p style="color:#94a3b8;font-size:12px;margin:0;">
                © 2026 EMS Pro. All rights reserved.
            </p>
        </td>
    </tr>
</table>
</td></tr>
</table>
</body>
</html>
                ''',
            },
            timeout=15
        )
        return response.status_code == 201
    except Exception as e:
        logger.error(f'Task reminder error: {str(e)}')
        return False