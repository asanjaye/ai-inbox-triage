# AI Inbox Triage — Web UI

React + TypeScript + Vite + Tailwind frontend for reviewing the triage queue, editing drafts, approving/rejecting replies, and viewing the audit log.

## Development

Requires the API server running (default proxy target: `http://127.0.0.1:8731`).

```bash
npm install
npm run dev -- --host 127.0.0.1 --port 4177
```

Override the API proxy with `VITE_API_PROXY` if needed.
