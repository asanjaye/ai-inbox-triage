# Demo Recording Script

> **Duration**: 2-3 minutes  
> **Purpose**: Walk through the AI Inbox Triage system for a public demo / GitHub README video

---

## Pre-Recording Setup

1. Start with a clean database:
   ```bash
   rm -f data/inbox_triage.db
   ```

2. Start the backend server:
   ```bash
   python main.py --host 127.0.0.1 --port 8731
   ```

3. Start the frontend (in another terminal):
   ```bash
   cd frontend && npm run dev -- --host 127.0.0.1 --port 4177
   ```

4. Open browser to `http://127.0.0.1:4177`

---

## Recording Script

### Scene 1: Introduction (20 seconds)

**[Show: Empty dashboard]**

> "This is the AI Inbox Triage Agent — an intelligent email classification system I built to demonstrate automated email processing with human approval workflows."

**[Point to key UI elements]**

> "The system has three main areas: the Review Queue for prioritized emails, Draft Management for responses, and a complete Audit Log for compliance."

---

### Scene 2: Running Triage (30 seconds)

**[Type your name in the approver field]**

> "First, I'll enter my name as the approver — this is required for the approval workflow."

**[Click "Run Triage" button]**

> "Now I'll run the triage process. This imports 40 synthetic emails, classifies each one using AI, and generates draft replies for emails that need responses."

**[Show the summary that appears]**

> "The summary shows we processed 40 emails across different categories — sales leads, support requests, urgent escalations, and more. The system identified which ones need replies and created drafts automatically."

---

### Scene 3: Review Queue (40 seconds)

**[Click on a Critical priority item]**

> "The queue organizes emails by priority. Let me click on this critical escalation."

**[Show the email details panel]**

> "On the right, we see the original email — a customer reporting a system outage. The AI classified it correctly as an urgent escalation with critical priority."

**[Scroll to show the draft]**

> "Below is the auto-generated draft reply. Notice it acknowledges the urgency and promises immediate action — the tone matches the category guidelines."

**[Click on a Sales Lead]**

> "Here's a sales inquiry. The draft uses a professional, enthusiastic tone appropriate for sales conversations."

---

### Scene 4: Approval Workflow (30 seconds)

**[Select a pending draft]**

> "Now, the critical feature — the approval gate. This draft is pending. Watch what happens if I try to send without approval."

**[Click the draft details, note the pending status]**

> "The system enforces that NOTHING can be sent without explicit human approval. This is hard-coded — there's no way to bypass it."

**[Click Approve button]**

> "I'll approve this draft..."

**[Show status change to 'approved']**

> "Now it shows as approved with my name and timestamp."

**[Click Send button]**

> "And now I can send it. The send goes to a mock outbox — in production this would connect to your actual email service."

---

### Scene 5: Audit Log (20 seconds)

**[Click on Audit Log tab]**

> "Every action is logged in the audit trail — email received, classified, draft created, edited, approved, sent. For compliance, there's also a 'send_blocked' event whenever someone tries to send without approval."

**[Scroll through some entries]**

> "This gives you full accountability and traceability for every email interaction."

---

### Scene 6: Technical Overview (20 seconds)

**[Can show terminal or code briefly]**

> "Under the hood, this uses FastAPI, SQLite, and supports both OpenAI and Anthropic models. It runs in mock mode for testing without API keys, and includes a full evaluation suite measuring classification accuracy."

---

### Scene 7: Closing (10 seconds)

**[Return to dashboard]**

> "This demonstrates production-ready AI automation with safety guardrails — exactly what enterprises need. The system is extensible to Gmail, Outlook, or any email source, and can integrate with CRMs like HubSpot or Salesforce."

> "Thanks for watching!"

---

## Key Points to Emphasize

1. **Human approval is REQUIRED** — nothing sends automatically
2. **Priority-based organization** — critical items surface first
3. **Category-specific responses** — appropriate tone for each type
4. **Full audit trail** — compliance-ready logging
5. **Offline testing** — works without API keys in mock mode
6. **Extensible architecture** — ready for real email integrations

---

## Alternative Shorter Demo (1 minute)

If time-constrained:

1. **0:00-0:10**: Show empty dashboard, explain purpose
2. **0:10-0:25**: Click Run Triage, show summary
3. **0:25-0:40**: Click one email, show classification and draft
4. **0:40-0:55**: Approve and send, emphasize approval requirement
5. **0:55-1:00**: Flash audit log, close

---

## Screen Recording Tips

- Use a clean browser profile (no extensions, bookmarks)
- Set browser zoom to 100%
- Use 1920x1080 resolution
- Record audio separately for cleaner narration
- Keep mouse movements slow and deliberate
- Pause briefly on important UI elements
