#!/usr/bin/env python3
"""
Script to resend the AI Intel report from 2025-07-24
This script loads the existing report and sends it via email using the corrected configuration
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from email_utils import EmailSender
from dotenv import load_dotenv

def resend_report():
    """Resend the AI Intel report from 2025-07-24"""
    
    # Load environment variables
    load_dotenv()
    
    # Define the report date
    report_date = "2025-07-24"
    
    # Define paths to report files
    base_path = Path("ai-intel")
    html_path = base_path / f"{report_date}.html"
    md_path = base_path / f"{report_date}.md"
    
    # Check if files exist
    if not html_path.exists():
        print(f"Error: HTML report not found at {html_path}")
        return False
    
    if not md_path.exists():
        print(f"Error: Markdown report not found at {md_path}")
        return False
    
    # Read the HTML content
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        print(f"✓ Loaded HTML report from {html_path}")
    except Exception as e:
        print(f"Error reading HTML report: {e}")
        return False
    
    # Read the Markdown content for plain text version
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        print(f"✓ Loaded Markdown report from {md_path}")
    except Exception as e:
        print(f"Error reading Markdown report: {e}")
        return False
    
    # Get email recipients from environment
    recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')
    recipients = [r.strip() for r in recipients if r.strip()]
    
    if not recipients:
        print("Error: No email recipients configured in EMAIL_RECIPIENTS")
        return False
    
    print(f"\nPreparing to send report to: {', '.join(recipients)}")
    
    # Initialize email sender
    try:
        email_sender = EmailSender()
        
        # Send the email
        subject = f"AI Intel Report - {report_date} (Resent)"
        
        print(f"\nSending email with subject: {subject}")
        success = email_sender.send_html_report(
            html_content=html_content,
            recipients=recipients,
            subject=subject
        )
        
        if success:
            print(f"\n✅ Successfully resent the AI Intel report from {report_date}")
            print(f"   Recipients: {', '.join(recipients)}")
            return True
        else:
            print(f"\n❌ Failed to resend the report")
            return False
            
    except Exception as e:
        print(f"\nError during email sending: {e}")
        return False

if __name__ == "__main__":
    print("AI Intel Report Resender")
    print("=" * 50)
    print(f"Current directory: {os.getcwd()}")
    print(f"Environment file exists: {os.path.exists('.env')}")
    
    # Verify environment variables are loaded
    load_dotenv()
    
    # Check critical environment variables
    mailgun_api = os.getenv('MAILGUN_API')
    email_from = os.getenv('EMAIL_FROM')
    email_recipients = os.getenv('EMAIL_RECIPIENTS')
    
    print(f"\nEnvironment Check:")
    print(f"- MAILGUN_API: {'✓ Set' if mailgun_api else '✗ Missing'}")
    print(f"- EMAIL_FROM: {email_from if email_from else '✗ Missing'}")
    print(f"- EMAIL_RECIPIENTS: {email_recipients if email_recipients else '✗ Missing'}")
    
    if not all([mailgun_api, email_from, email_recipients]):
        print("\n❌ Missing required environment variables. Please check your .env file.")
        sys.exit(1)
    
    print("\nStarting email resend process...")
    success = resend_report()
    
    sys.exit(0 if success else 1)