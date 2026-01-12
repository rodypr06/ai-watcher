#!/usr/bin/env python3.11

import os
import re
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    """Utility class for sending emails via Mailgun API"""

    api_key: str
    domain: str
    base_url: str
    from_email: str

    def __init__(self) -> None:
        api_key: str | None = os.getenv('MAILGUN_API')
        domain: str | None = os.getenv('MAILGUN_DOMAIN')

        if not api_key:
            raise ValueError("MAILGUN_API environment variable is not set")
        if not domain:
            raise ValueError("MAILGUN_DOMAIN environment variable is not set")

        self.api_key = api_key
        self.domain = domain
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
        self.from_email = os.getenv('EMAIL_FROM', f"AI Watcher <postmaster@{self.domain}>")

    def send_report(
        self,
        report_content: str,
        recipients: list[str],
        subject: str | None = None
    ) -> bool:
        """
        Send AI intelligence report via email

        Args:
            report_content: The markdown report content to send
            recipients: List of recipient email addresses
            subject: Email subject (auto-generated if not provided)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not recipients:
            logger.warning("No recipients specified for email")
            return False

        if not subject:
            subject = f"AI Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}"

        # Convert markdown to plain text for better email compatibility
        text_content = self._markdown_to_text(report_content)

        try:
            response = requests.post(
                self.base_url,
                auth=("api", self.api_key),
                data={
                    "from": self.from_email,
                    "to": recipients,
                    "subject": subject,
                    "text": text_content,
                    "html": self._markdown_to_html(report_content)
                }
            )

            if response.status_code == 200:
                logger.info(f"Email sent successfully to {len(recipients)} recipients")
                return True
            elif response.status_code == 403:
                logger.error(f"Mailgun authorization error: {response.json().get('message', 'Access denied')}")
                logger.error(f"Note: Ensure your Mailgun domain ({self.domain}) is properly configured and verified")
                return False
            else:
                logger.error(f"Failed to send email. Status: {response.status_code}, Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.exception(f"Network error sending email: {str(e)}")
            return False
        except ValueError as e:
            logger.exception(f"Value error sending email: {str(e)}")
            return False

    def send_html_report(
        self,
        html_content: str,
        recipients: list[str],
        subject: str | None = None
    ) -> bool:
        """
        Send HTML AI intelligence report via email

        Args:
            html_content: The HTML report content to send
            recipients: List of recipient email addresses
            subject: Email subject (auto-generated if not provided)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not recipients:
            logger.warning("No recipients specified for email")
            return False

        if not subject:
            subject = f"AI Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}"

        # Extract text content from HTML for plain text version
        text_content: str = re.sub('<[^<]+?>', '', html_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()

        try:
            response = requests.post(
                self.base_url,
                auth=("api", self.api_key),
                data={
                    "from": self.from_email,
                    "to": recipients,
                    "subject": subject,
                    "text": text_content,
                    "html": html_content
                }
            )

            if response.status_code == 200:
                logger.info(f"HTML email sent successfully to {len(recipients)} recipients")
                return True
            elif response.status_code == 403:
                logger.error(f"Mailgun authorization error: {response.json().get('message', 'Access denied')}")
                logger.error(f"Note: Ensure your Mailgun domain ({self.domain}) is properly configured and verified")
                return False
            else:
                logger.error(f"Failed to send HTML email. Status: {response.status_code}, Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.exception(f"Network error sending HTML email: {str(e)}")
            return False
        except ValueError as e:
            logger.exception(f"Value error sending HTML email: {str(e)}")
            return False

    def send_alert(self, title: str, message: str, recipients: list[str]) -> bool:
        """
        Send a quick alert email

        Args:
            title: Alert title
            message: Alert message
            recipients: List of recipient email addresses

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = f"AI Watcher Alert: {title}"

        try:
            response = requests.post(
                self.base_url,
                auth=("api", self.api_key),
                data={
                    "from": self.from_email,
                    "to": recipients,
                    "subject": subject,
                    "text": message
                }
            )

            if response.status_code == 200:
                logger.info(f"Alert email sent successfully: {title}")
                return True
            elif response.status_code == 403:
                logger.error(f"Mailgun authorization error: {response.json().get('message', 'Access denied')}")
                logger.error(f"Note: Ensure your Mailgun domain ({self.domain}) is properly configured and verified")
                return False
            else:
                logger.error(f"Failed to send alert email. Status: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.exception(f"Network error sending alert email: {str(e)}")
            return False
        except ValueError as e:
            logger.exception(f"Value error sending alert email: {str(e)}")
            return False

    def _markdown_to_text(self, markdown_content: str) -> str:
        """Convert markdown to plain text for email"""
        # Remove markdown formatting
        text = re.sub(r'#+ ', '', markdown_content)  # Headers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)  # Inline code
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links

        return text

    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown to beautifully formatted HTML for glass-style email"""
        html: str = markdown_content

        # Headers with glass-style theming
        html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Horizontal rules
        html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)

        # Lists (let CSS handle the styling)
        html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^(\d+)\. (.*?)$', r'<li>\2</li>', html, flags=re.MULTILINE)

        # Wrap consecutive list items in ul tags
        html = re.sub(r'(<li[^>]*>.*?</li>(?:\s*<li[^>]*>.*?</li>)*)', r'<ul>\1</ul>', html, flags=re.DOTALL)

        # Bold and italic (let CSS handle colors)
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)

        # Code blocks and inline code
        html = re.sub(r'```(\w+)?\n(.*?)\n```', self._format_glass_code_block, html, flags=re.DOTALL)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)

        # Links (let CSS handle styling)
        html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)

        # Images with better handling
        html = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', lambda m: self._format_glass_image_simple(m.group(1), m.group(2)), html)

        # Tables
        html = self._format_glass_tables(html)

        # Emojis with glass-style coloring
        html = re.sub(r'⭐', r'<span style="color: #00BCD4;">⭐</span>', html)
        html = re.sub(r'🔥', r'<span style="color: #00BCD4;">🔥</span>', html)
        html = re.sub(r'📦', r'<span style="color: #00BCD4;">📦</span>', html)
        html = re.sub(r'📊', r'<span style="color: #00BCD4;">📊</span>', html)
        html = re.sub(r'🔍', r'<span style="color: #00BCD4;">🔍</span>', html)
        html = re.sub(r'📈', r'<span style="color: #00BCD4;">📈</span>', html)
        html = re.sub(r'🎯', r'<span style="color: #00BCD4;">🎯</span>', html)
        html = re.sub(r'📚', r'<span style="color: #00BCD4;">📚</span>', html)

        # Handle line breaks more intelligently
        # Split into paragraphs on double newlines first
        paragraphs = html.split('\n\n')
        formatted_paragraphs = []

        for paragraph in paragraphs:
            if paragraph.strip():
                # For content inside HTML tags, don't add extra breaks
                if '<h' in paragraph or '<li>' in paragraph or '<table>' in paragraph or '<ul>' in paragraph or '<div' in paragraph:
                    formatted_paragraphs.append(paragraph.strip())
                else:
                    # For regular text paragraphs, wrap in <p> tags instead of using <br>
                    paragraph = paragraph.replace('\n', ' ').strip()
                    if paragraph:
                        formatted_paragraphs.append(f'<p>{paragraph}</p>')

        html = '\n\n'.join(formatted_paragraphs)

        # Wrap in styled HTML
        return self._create_html_template(html)

    def _format_glass_code_block(self, match: re.Match[str]) -> str:
        """Format code blocks with glass-style theming"""
        language: str = match.group(1) or 'text'
        code: str = match.group(2)
        return f'''<div class="glass-code-block" style="background: rgba(0, 0, 0, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.75rem; padding: 1.5rem; margin: 1.5rem 0; overflow-x: auto; box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);">
                    <div style="color: #00BCD4; font-size: 0.75rem; margin-bottom: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{language}</div>
                    <pre style="color: #E0E0E0; font-family: 'Courier New', monospace; font-size: 0.875rem; line-height: 1.5; margin: 0; white-space: pre-wrap;">{code}</pre>
                   </div>'''

    def _format_glass_image_simple(self, alt_text: str, image_url: str) -> str:
        """Format images with glass-style theming and fallback"""
        alt_text = alt_text or 'Image'

        if not image_url or 'placeholder' in image_url.lower():
            return '<div class="fallback-image">📷 <div style="margin-left: 0.5rem; font-size: 0.875rem;">Image not available</div></div>'

        caption_html: str = f'<div class="image-caption">{alt_text}</div>' if alt_text else ''
        return f'<div class="image-container"><img src="{image_url}" alt="{alt_text}" loading="lazy">{caption_html}</div>'

    def _format_glass_tables(self, html: str) -> str:
        """Convert markdown tables to glass-styled HTML tables"""

        # Find table patterns
        table_pattern = r'\|([^|\n]+\|[^|\n]*)+\n\|[-\s:|]+\|[-\s:|]*\n(\|[^|\n]+\|[^|\n]*\n?)+'

        for table_match in re.finditer(table_pattern, html):
            table_text = table_match.group(0)
            lines = table_text.strip().split('\n')

            # Parse header
            header_cells = [cell.strip() for cell in lines[0].split('|')[1:-1]]

            # Parse rows (skip separator line)
            rows = []
            for line in lines[2:]:
                if line.strip():
                    row_cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    rows.append(row_cells)

            # Create HTML table with glass styling
            table_html = '''<table>'''

            # Header
            table_html += '<thead>'
            table_html += '<tr>'
            for cell in header_cells:
                table_html += f'<th>{cell}</th>'
            table_html += '</tr>'
            table_html += '</thead>'

            # Body
            table_html += '<tbody>'
            for i, row in enumerate(rows):
                table_html += '<tr>'
                for cell in row:
                    table_html += f'<td>{cell}</td>'
                table_html += '</tr>'
            table_html += '</tbody>'
            table_html += '</table>'

            html = html.replace(table_text, table_html)

        return html

    def _create_html_template(self, content: str) -> str:
        """Create a complete HTML email template with Liquid Glass styling"""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Intelligence Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: #E0E0E0;
            background: #121212;
            padding: 40px 20px;
            min-height: 100vh;
            position: relative;
        }}

        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, #121212 0%, #1a1a1a 50%, #121212 100%);
            background-attachment: fixed;
            z-index: -2;
        }}

        body::after {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 20% 80%, rgba(0, 188, 212, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(0, 188, 212, 0.08) 0%, transparent 50%);
            z-index: -1;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            position: relative;
        }}

        .glass-panel {{
            background: rgba(30, 30, 30, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            overflow: hidden;
            margin-bottom: 2rem;
        }}

        .header {{
            background: rgba(30, 30, 30, 0.8);
            backdrop-filter: blur(16px);
            color: #FFFFFF;
            padding: 3rem 2.5rem;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent 0%, #00BCD4 50%, transparent 100%);
        }}

        .header h1 {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: #FFFFFF;
            text-shadow: 0 2px 8px rgba(0, 188, 212, 0.3);
        }}

        .header p {{
            font-size: 1rem;
            color: #E0E0E0;
            font-weight: 400;
            opacity: 0.9;
            margin-bottom: 1.5rem;
        }}

        .brand-badge {{
            display: inline-block;
            background: #00BCD4;
            color: #000000;
            padding: 0.5rem 1rem;
            border-radius: 0.75rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 16px rgba(0, 188, 212, 0.3);
            transition: all 0.3s ease;
        }}

        .brand-badge:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 188, 212, 0.4);
        }}

        .content {{
            padding: 2.5rem;
            color: #E0E0E0;
        }}

        .content h1 {{
            color: #FFFFFF;
            font-weight: 700;
            font-size: 1.75rem;
            margin: 2rem 0 1.5rem 0;
            text-align: center;
        }}

        .content h2 {{
            color: #FFFFFF;
            font-weight: 700;
            font-size: 1.5rem;
            margin: 2rem 0 1rem 0;
            padding-left: 1rem;
            border-left: 4px solid #00BCD4;
            position: relative;
        }}

        .content h2::before {{
            content: '';
            position: absolute;
            left: -1px;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, #00BCD4 0%, rgba(0, 188, 212, 0.3) 100%);
            border-radius: 2px;
        }}

        .content h3 {{
            color: #E0E0E0;
            font-weight: 600;
            font-size: 1.25rem;
            margin: 1.5rem 0 0.75rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 0.5rem;
        }}

        .content h4 {{
            color: #E0E0E0;
            font-weight: 600;
            font-size: 1.1rem;
            margin: 1.25rem 0 0.5rem 0;
        }}

        .content p {{
            margin: 0.75rem 0;
            line-height: 1.6;
        }}

        .content ul {{
            margin: 1rem 0;
            padding-left: 0;
            list-style: none;
        }}

        .content li {{
            margin: 0.5rem 0;
            padding-left: 1.5rem;
            position: relative;
        }}

        .content li::before {{
            content: '▸';
            position: absolute;
            left: 0;
            color: #00BCD4;
            font-weight: 600;
        }}

        .content strong {{
            color: #FFFFFF;
            font-weight: 600;
        }}

        .content em {{
            color: #00BCD4;
            font-style: italic;
        }}

        .content a {{
            color: #00BCD4;
            text-decoration: none;
            font-weight: 600;
            border-bottom: 1px solid rgba(0, 188, 212, 0.3);
            transition: all 0.3s ease;
        }}

        .content a:hover {{
            border-bottom-color: #00BCD4;
            color: #FFFFFF;
        }}

        .content code {{
            background: rgba(0, 0, 0, 0.4);
            color: #00BCD4;
            padding: 0.25rem 0.5rem;
            border-radius: 0.375rem;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .content pre {{
            background: rgba(0, 0, 0, 0.6);
            color: #E0E0E0;
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin: 1.5rem 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow-x: auto;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
        }}

        .content table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 1.5rem 0;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 0.75rem;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .content th {{
            background: rgba(0, 188, 212, 0.2);
            color: #FFFFFF;
            font-weight: 600;
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .content td {{
            padding: 0.875rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: #E0E0E0;
        }}

        .content tr:nth-child(even) td {{
            background: rgba(255, 255, 255, 0.02);
        }}

        .content tr:hover td {{
            background: rgba(0, 188, 212, 0.05);
        }}

        .highlight-box {{
            background: rgba(0, 188, 212, 0.1);
            border: 1px solid rgba(0, 188, 212, 0.3);
            color: #E0E0E0;
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin: 1.5rem 0;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 16px rgba(0, 188, 212, 0.1);
        }}

        .footer {{
            background: rgba(18, 18, 18, 0.8);
            backdrop-filter: blur(16px);
            padding: 2rem 2.5rem;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #888888;
        }}

        .footer p {{
            margin-bottom: 0.75rem;
            font-size: 0.875rem;
        }}

        .footer strong {{
            color: #E0E0E0;
            font-weight: 600;
        }}

        .footer-accent {{
            color: #00BCD4;
            font-weight: 600;
        }}

        hr {{
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.1) 50%, transparent 100%);
            margin: 2rem 0;
        }}

        @media (max-width: 600px) {{
            body {{
                padding: 20px 10px;
            }}

            .header {{
                padding: 2rem 1.5rem;
            }}

            .content {{
                padding: 1.5rem;
            }}

            .footer {{
                padding: 1.5rem;
            }}

            .header h1 {{
                font-size: 1.5rem;
            }}

            .content h2 {{
                font-size: 1.25rem;
            }}
        }}

        @keyframes glass-glow {{
            0%, 100% {{
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            }}
            50% {{
                box-shadow: 0 8px 32px rgba(0, 188, 212, 0.1);
            }}
        }}

        .glass-panel {{
            animation: glass-glow 6s ease-in-out infinite;
        }}

        .content img {{
            max-width: 100%;
            height: auto;
            border-radius: 0.75rem;
            margin: 1rem 0;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            display: block;
        }}

        .image-container {{
            position: relative;
            margin: 1.5rem 0;
            border-radius: 0.75rem;
            overflow: hidden;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .image-container img {{
            width: 100%;
            height: auto;
            display: block;
            margin: 0;
            border-radius: 0;
        }}

        .image-caption {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
            color: #E0E0E0;
            padding: 1rem;
            font-size: 0.875rem;
        }}

        .fallback-image {{
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, rgba(0, 188, 212, 0.1) 0%, rgba(0, 188, 212, 0.05) 100%);
            border: 2px dashed rgba(0, 188, 212, 0.3);
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #00BCD4;
            font-size: 2rem;
            margin: 1rem 0;
        }}

        .article-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
            transition: all 0.3s ease;
        }}

        .article-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }}

        .trending-badge {{
            background: linear-gradient(135deg, #00BCD4, #0097A7);
            color: #000;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: inline-block;
            margin: 0.25rem 0.5rem 0.25rem 0;
        }}

        .credibility-score {{
            background: rgba(0, 188, 212, 0.2);
            color: #00BCD4;
            padding: 0.25rem 0.5rem;
            border-radius: 0.5rem;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
            margin-left: 0.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="glass-panel">
            <div class="header">
                <h1>AI Intelligence Report</h1>
                <p>Your daily digest of AI developments and trends</p>
                <span class="brand-badge">Generated by AI-Watcher</span>
            </div>

            <div class="content">
                {content}
            </div>

            <div class="footer">
                <p><strong>AI-Watcher Enhanced v2.0</strong></p>
                <p>Powered by <span class="footer-accent">CrewAI</span> • Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                <p style="margin-top: 1.5rem; font-size: 0.75rem; color: #666;">
                    This report was automatically generated and curated by AI agents.<br>
                    For questions or feedback, please reply to this email.
                </p>
            </div>
        </div>
    </div>
</body>
</html>'''

def get_email_recipients() -> list[str]:
    """Get email recipients from environment variable"""
    recipients_str: str = os.getenv('EMAIL_RECIPIENTS', '')
    if recipients_str:
        return [email.strip() for email in recipients_str.split(',')]
    return []
