"""Prompts for email classification."""

CLASSIFICATION_SYSTEM_PROMPT = """You are an expert email triage assistant. Your job is to classify incoming emails and determine the appropriate response.

For each email, you must determine:
1. CATEGORY - One of:
   - sales_lead: Potential business opportunity, inquiry about services
   - support_request: Customer needing help, bug reports, complaints
   - invoice: Bills, payment requests, financial documents
   - scheduling: Meeting requests, calendar invites, availability inquiries
   - newsletter: Marketing emails, subscriptions, promotional content
   - spam: Unsolicited, scam attempts, phishing
   - urgent_escalation: Critical issues requiring immediate attention
   - personal: Personal correspondence not business-related
   - other: Doesn't fit other categories

2. PRIORITY - One of:
   - critical: Requires immediate action (security issues, critical outages, angry VIP)
   - high: Should be addressed within hours (time-sensitive requests, important clients)
   - medium: Normal business priority (standard requests, follow-ups)
   - low: Can wait (newsletters, FYI messages, non-urgent notifications)

3. NEEDS_REPLY - Boolean indicating if the email requires a response

4. SUMMARY - A brief 1-2 sentence summary of the email's purpose

Consider these factors:
- Sender reputation and relationship
- Time-sensitivity keywords ("urgent", "ASAP", "deadline")
- Financial implications
- Customer sentiment
- Security concerns"""

CLASSIFICATION_USER_PROMPT = """Classify this email:

From: {from_name} <{from_address}>
To: {to_address}
Subject: {subject}
Date: {received_at}

Body:
{body}

Respond with a JSON object containing:
{{
  "category": "<category>",
  "priority": "<priority>",
  "needs_reply": true/false,
  "summary": "<brief summary>",
  "reasoning": "<explanation of your classification>"
}}"""


REPLY_GUIDELINES = {
    "sales_lead": {
        "tone": "professional and enthusiastic",
        "template": """Thank you for reaching out about {topic}!

I'd be happy to discuss how we can help. {custom_response}

Would you be available for a brief call this week to explore this further?

Best regards""",
    },
    "support_request": {
        "tone": "empathetic and solution-focused",
        "template": """Thank you for bringing this to our attention.

I understand {issue_acknowledgment}. {solution_or_next_steps}

Please let me know if you need any additional assistance.

Best regards""",
    },
    "invoice": {
        "tone": "professional and precise",
        "template": """Thank you for sending this invoice.

{acknowledgment_or_question}

Best regards""",
    },
    "scheduling": {
        "tone": "friendly and accommodating",
        "template": """Thank you for reaching out about scheduling.

{availability_response}

Looking forward to connecting!

Best regards""",
    },
    "urgent_escalation": {
        "tone": "urgent and reassuring",
        "template": """I'm treating this as a priority matter.

{immediate_action}

I'll keep you updated on progress.

Best regards""",
    },
}

DRAFT_GENERATION_PROMPT = """Generate a reply to this email following these guidelines:

Original Email:
From: {from_name} <{from_address}>
Subject: {subject}
Body:
{body}

Classification:
- Category: {category}
- Priority: {priority}
- Summary: {summary}

Guidelines for {category} emails:
- Tone: {tone}
- Template structure: {template}

Write a professional, helpful reply. Be concise but thorough.
Address the sender's needs directly.
If you need more information from them, ask specific questions.

Respond with just the reply body text, no JSON formatting."""
