"""
Email service for sending notifications
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.office365.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "systembugs@jgfgroup.co.uk")
        self.support_email = os.getenv("SUPPORT_EMAIL", "systembugs@jgfgroup.co.uk")
        
        # Check if email is configured
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        
        if not self.is_configured:
            logger.warning("Email service not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")

    def send_contact_form_email(self, user_info: dict, form_data: dict) -> bool:
        """Send contact form submission email to support team"""
        if not self.is_configured:
            logger.warning("Email not configured, skipping email send")
            return False
            
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.from_email
            message["To"] = self.support_email
            message["Subject"] = f"ClockIt Contact Form: {form_data.get('subject', 'No Subject')}"
            
            # Create email body
            body = self._create_contact_email_body(user_info, form_data)
            message.attach(MIMEText(body, "html"))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, self.support_email, message.as_string())
                
            logger.info(f"Contact form email sent successfully to {self.support_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send contact form email: {e}")
            return False
    
    def _create_contact_email_body(self, user_info: dict, form_data: dict) -> str:
        """Create HTML email body for contact form"""
        contact_type = form_data.get('type', 'general')
        is_bug_report = contact_type == 'bug_report'
        
        # Map contact types to emojis and labels
        type_mapping = {
            'bug_report': '🐛 Bug Report',
            'feature_request': '💡 Feature Request',
            'general': '💬 General Inquiry',
            'support': '🛠️ Technical Support',
            'feedback': '📝 Feedback'
        }
        
        priority_colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        
        priority = form_data.get('priority', 'medium')
        priority_color = priority_colors.get(priority, '#6c757d')
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #4CAF50, #2E7D32); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
                .footer {{ background: #e9ecef; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; }}
                .field {{ margin-bottom: 15px; }}
                .label {{ font-weight: bold; color: #495057; }}
                .value {{ margin-top: 5px; padding: 10px; background: white; border-left: 4px solid #4CAF50; border-radius: 4px; }}
                .priority {{ display: inline-block; padding: 4px 12px; color: white; border-radius: 20px; font-size: 0.9em; font-weight: bold; }}
                .bug-section {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 15px 0; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🕐 ClockIt Contact Form Submission</h2>
                <p><strong>Type:</strong> {type_mapping.get(contact_type, contact_type.title())}</p>
                <p><strong>Priority:</strong> <span class="priority" style="background-color: {priority_color};">{priority.upper()}</span></p>
            </div>
            
            <div class="content">
                <div class="field">
                    <div class="label">👤 User Information:</div>
                    <div class="value">
                        <strong>Name:</strong> {form_data.get('name', 'Not provided')}<br>
                        <strong>Email:</strong> {form_data.get('email', 'Not provided')}<br>
                        <strong>Username:</strong> {user_info.get('username', 'Not provided')}<br>
                        <strong>User ID:</strong> {user_info.get('user_id', 'Not provided')}
                    </div>
                </div>
                
                <div class="field">
                    <div class="label">📝 Subject:</div>
                    <div class="value">{form_data.get('subject', 'No subject provided')}</div>
                </div>
                
                <div class="field">
                    <div class="label">💬 Description:</div>
                    <div class="value">{form_data.get('description', 'No description provided').replace(chr(10), '<br>')}</div>
                </div>
        """
        
        # Add bug report specific fields
        if is_bug_report:
            html_body += """
                <div class="bug-section">
                    <h3>🐛 Bug Report Details</h3>
            """
            
            if form_data.get('steps_to_reproduce'):
                html_body += f"""
                    <div class="field">
                        <div class="label">🔄 Steps to Reproduce:</div>
                        <div class="value">{form_data.get('steps_to_reproduce', '').replace(chr(10), '<br>')}</div>
                    </div>
                """
            
            if form_data.get('expected_behavior'):
                html_body += f"""
                    <div class="field">
                        <div class="label">✅ Expected Behavior:</div>
                        <div class="value">{form_data.get('expected_behavior', '').replace(chr(10), '<br>')}</div>
                    </div>
                """
            
            if form_data.get('actual_behavior'):
                html_body += f"""
                    <div class="field">
                        <div class="label">❌ Actual Behavior:</div>
                        <div class="value">{form_data.get('actual_behavior', '').replace(chr(10), '<br>')}</div>
                    </div>
                """
            
            html_body += "</div>"
        
        # Add technical information
        html_body += f"""
                <div class="field">
                    <div class="label">🔧 Technical Information:</div>
                    <div class="value">
                        <strong>Browser:</strong> {form_data.get('browser_info', 'Not provided')}<br>
                        <strong>Timestamp:</strong> {user_info.get('timestamp', 'Not provided')}
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>This email was automatically generated by ClockIt contact form.</p>
                <p><strong>Reply to this email to respond to the user directly.</strong></p>
            </div>
        </body>
        </html>
        """
        
        return html_body


# Global email service instance
email_service = EmailService()