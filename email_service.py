"""
Lavu Email Service — SendGrid Integration
Handles all outbound emails for orders, payments, and notifications
"""

import os
from typing import List, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime


class EmailService:
    """SendGrid-based email service for Lavu"""

    def __init__(self):
        self.sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.from_email = os.getenv(
            'SENDGRID_FROM_EMAIL', 'noreply@lavulaundry.com')
        self.support_email = os.getenv(
            'SUPPORT_EMAIL', 'support@lavulaundry.com')

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None
    ) -> bool:
        """
        Send an email via SendGrid

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_text: Plain text fallback

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=plain_text or self._strip_html(
                    html_content),
                html_content=html_content
            )

            response = self.sg.send(message)
            print(
                f"✓ Email sent to {to_email} - Status: {response.status_code}")
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"✗ Failed to send email to {to_email}: {str(e)}")
            return False

    def send_order_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        order_id: int,
        pickup_address: str,
        pickup_date: str,
        order_notes: str = None
    ) -> bool:
        """Send order confirmation email"""
        subject = f"Order Confirmation #{order_id} - Lavu Laundry"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h1 style="margin: 0;">🧺 Lavu Laundry</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">Order Confirmed</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #eee;">
                        <p>Hi <strong>{customer_name}</strong>,</p>
                        <p>Thank you for placing your order with Lavu! We've received your laundry request and will pick it up as scheduled.</p>
                        
                        <!-- Order Details -->
                        <div style="background: white; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #667eea;">
                            <h2 style="margin-top: 0; color: #667eea; font-size: 18px;">Order Details</h2>
                            <p><strong>Order ID:</strong> #{order_id}</p>
                            <p><strong>Pickup Address:</strong> {pickup_address}</p>
                            <p><strong>Scheduled Pickup:</strong> {pickup_date}</p>
                            {f'<p><strong>Special Instructions:</strong> {order_notes}</p>' if order_notes else ''}
                        </div>
                        
                        <!-- What Happens Next -->
                        <div style="background: #f0f7ff; padding: 20px; border-radius: 6px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #004085;">What Happens Next?</h3>
                            <ul style="margin: 10px 0;">
                                <li>Our team will pick up your laundry on the scheduled date</li>
                                <li>You'll receive a confirmation SMS when we pick up</li>
                                <li>Your clothes will be processed with care</li>
                                <li>We'll deliver it back within 24-48 hours</li>
                            </ul>
                        </div>
                        
                        <!-- Contact Info -->
                        <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin: 20px 0; font-size: 14px;">
                            <p style="margin: 0;"><strong>Need Help?</strong></p>
                            <p style="margin: 5px 0 0 0;">📞 Call: +254 7XX XXX XXXX</p>
                            <p style="margin: 5px 0 0 0;">📧 Email: {self.support_email}</p>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            Thank you for choosing Lavu Laundry!<br>
                            <strong>The Lavu Team</strong>
                        </p>
                    </div>
                    
                    <!-- Footer -->
                    <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
                        <p>© {datetime.now().year} Lavu Laundry Services. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """

        return self.send_email(customer_email, subject, html_content)

    def send_pickup_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        order_id: int,
        weight: float
    ) -> bool:
        """Send confirmation when order is picked up"""
        subject = f"Pickup Confirmed - Order #{order_id}"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h1 style="margin: 0;">✓ Pickup Confirmed</h1>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #eee;">
                        <p>Hi <strong>{customer_name}</strong>,</p>
                        <p>Great news! We've successfully picked up your laundry.</p>
                        
                        <div style="background: #d4edda; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #28a745;">
                            <p style="margin: 0;"><strong>Order #</strong> {order_id}</p>
                            <p style="margin: 10px 0 0 0;"><strong>Weight:</strong> {weight} kg</p>
                            <p style="margin: 10px 0 0 0;"><strong>Status:</strong> 🚚 In Transit</p>
                        </div>
                        
                        <p>Your clothes are now being processed with our premium care treatment. You'll receive a delivery confirmation email once your order is ready!</p>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            Questions? Contact us at {self.support_email}
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

        return self.send_email(customer_email, subject, html_content)

    def send_delivery_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        order_id: int,
        delivery_address: str
    ) -> bool:
        """Send confirmation when order is delivered"""
        subject = f"Order Delivered - Order #{order_id}"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h1 style="margin: 0;">🎉 Order Delivered!</h1>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #eee;">
                        <p>Hi <strong>{customer_name}</strong>,</p>
                        <p>Your laundry has been successfully delivered!</p>
                        
                        <div style="background: #d4edda; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #28a745;">
                            <p style="margin: 0;"><strong>Order #</strong> {order_id}</p>
                            <p style="margin: 10px 0 0 0;"><strong>Delivered to:</strong> {delivery_address}</p>
                            <p style="margin: 10px 0 0 0;"><strong>Delivery Time:</strong> {datetime.now().strftime('%I:%M %p')}</p>
                        </div>
                        
                        <p>Thank you for choosing Lavu! We hope your clothes look great. Your feedback helps us improve our service.</p>
                        
                        <!-- Call to Action -->
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://lavulaundry.com/feedback" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">Share Your Feedback</a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            Ready for another order? Login to schedule your next pickup!
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

        return self.send_email(customer_email, subject, html_content)

    def send_payment_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        amount: float,
        receipt_number: str,
        plan_tier: str
    ) -> bool:
        """Send payment confirmation email"""
        subject = f"Payment Confirmed - KES {amount:,.0f} Receipt"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h1 style="margin: 0;">💳 Payment Successful</h1>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #eee;">
                        <p>Hi <strong>{customer_name}</strong>,</p>
                        <p>Your payment has been processed successfully. Thank you!</p>
                        
                        <!-- Payment Details -->
                        <div style="background: white; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #667eea;">
                            <h2 style="margin-top: 0; color: #667eea; font-size: 18px;">Receipt Details</h2>
                            <p style="margin: 10px 0;"><strong>Amount:</strong> KES {amount:,.2f}</p>
                            <p style="margin: 10px 0;"><strong>Receipt Number:</strong> {receipt_number}</p>
                            <p style="margin: 10px 0;"><strong>Plan Tier:</strong> {plan_tier}</p>
                            <p style="margin: 10px 0;"><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                        </div>
                        
                        <!-- Subscription Info -->
                        <div style="background: #f0f7ff; padding: 20px; border-radius: 6px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #004085;">Your Subscription is Active</h3>
                            <p>You're all set to schedule pickups! Your subscription covers unlimited laundry for the billing period.</p>
                            <ul style="margin: 10px 0;">
                                <li>Unlimited pickups per week</li>
                                <li>Premium care treatment</li>
                                <li>Fast turnaround time</li>
                                <li>Free delivery</li>
                            </ul>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            Keep this receipt for your records.<br>
                            Questions? Contact {self.support_email}
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

        return self.send_email(customer_email, subject, html_content)

    def send_subscription_renewal_reminder(
        self,
        customer_email: str,
        customer_name: str,
        plan_tier: str,
        renewal_date: str,
        amount: float
    ) -> bool:
        """Send subscription renewal reminder"""
        subject = f"Subscription Renewal Reminder - {plan_tier} Plan"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h1 style="margin: 0;">⏰ Subscription Renewal</h1>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #eee;">
                        <p>Hi <strong>{customer_name}</strong>,</p>
                        <p>Your {plan_tier} subscription will renew soon!</p>
                        
                        <div style="background: #fff3cd; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #ffc107;">
                            <p style="margin: 0;"><strong>Renewal Date:</strong> {renewal_date}</p>
                            <p style="margin: 10px 0 0 0;"><strong>Amount Due:</strong> KES {amount:,.2f}</p>
                            <p style="margin: 10px 0 0 0;"><strong>Plan:</strong> {plan_tier}</p>
                        </div>
                        
                        <p>Your subscription will automatically renew on the date above. If you'd like to change your plan or have any questions, login to your account.</p>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            Thank you for being a valued Lavu customer!
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

        return self.send_email(customer_email, subject, html_content)

    def send_usage_alert(
        self,
        customer_email: str,
        customer_name: str,
        plan_tier: str,
        kg_used: float,
        kg_limit: float,
        usage_percent: float
    ) -> bool:
        """Send alert when usage exceeds threshold"""
        subject = f"⚠️ Usage Alert - {usage_percent:.0f}% of Plan Used"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h1 style="margin: 0;">⚠️ Usage Alert</h1>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #eee;">
                        <p>Hi <strong>{customer_name}</strong>,</p>
                        <p>You're approaching your laundry limit for this billing period.</p>
                        
                        <div style="background: #fee; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #ff6b6b;">
                            <h3 style="margin-top: 0; color: #c33;">Usage Summary</h3>
                            <p style="margin: 10px 0;"><strong>Plan:</strong> {plan_tier}</p>
                            <p style="margin: 10px 0;"><strong>Used:</strong> {kg_used} kg of {kg_limit} kg</p>
                            <p style="margin: 10px 0;"><strong>Usage:</strong> {usage_percent:.1f}%</p>
                        </div>
                        
                        <p>Once you reach your limit, you can upgrade to a higher plan or contact support for flexible options.</p>
                        
                        <!-- Call to Action -->
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://lavulaundry.com/upgrade" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">Upgrade Plan</a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            Questions? Reach out to {self.support_email}
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

        return self.send_email(customer_email, subject, html_content)

    def send_admin_alert(
        self,
        admin_email: str,
        subject: str,
        alert_type: str,
        details: dict
    ) -> bool:
        """Send alert to admin"""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: #333; color: white; padding: 15px; border-radius: 6px 6px 0 0; text-align: center;">
                        <h2 style="margin: 0;">🔔 Admin Alert</h2>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 20px; border-radius: 0 0 6px 6px; border: 1px solid #ddd;">
                        <h3>{alert_type}</h3>
                        <pre style="background: white; padding: 15px; border-radius: 4px; overflow-x: auto;">{str(details)}</pre>
                        <p style="color: #666; font-size: 12px;">Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </body>
        </html>
        """

        return self.send_email(admin_email, subject, html_content)

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags for plain text version"""
        import re
        text = re.sub('<[^<]+?>', '', html)
        return text.replace('&nbsp;', ' ').strip()


# Initialize service
email_service = EmailService()
