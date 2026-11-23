#!/usr/bin/env python3
"""
AI Inbox Triage Agent - Main Entry Point

Usage:
    python main.py                  # Start the web server
    python main.py --triage         # Run full triage on emails
    python main.py --eval           # Run evaluation
    python main.py --eval --mock    # Run evaluation in mock mode
"""
import asyncio
import argparse
import sys
from pathlib import Path

import uvicorn


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server."""
    Path("./data").mkdir(exist_ok=True)
    
    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=True,
    )


async def run_triage(limit: int = None, dry_run: bool = False):
    """Run full triage workflow."""
    from src.database import init_db, get_session
    from src.email_sources import JsonEmailSource
    from src.services import EmailService, ClassificationService, DraftService, AuditService
    from src.llm import get_classifier
    from src.llm.draft_generator import DraftGenerator
    from src.config import get_settings
    
    Path("./data").mkdir(exist_ok=True)
    await init_db()
    
    settings = get_settings()
    
    async for session in get_session():
        audit = AuditService(session)
        email_service = EmailService(session, audit)
        classifier = get_classifier()
        classification_service = ClassificationService(session, classifier, audit)
        draft_generator = DraftGenerator(use_mock=settings.mock_mode)
        draft_service = DraftService(session, audit, draft_generator)
        
        source = JsonEmailSource(settings.email_source_path)
        emails = await email_service.import_from_source(source, limit=limit)
        print(f"Imported {len(emails)} emails")
        
        for email in emails:
            classification = await classification_service.classify_email(email)
            print(f"  {email.id}: {classification.category.value} ({classification.priority.value})")
            
            if classification.needs_reply and not dry_run:
                draft = await draft_service.create_draft(email, classification)
                print(f"    -> Draft created: {draft.id}")
        
        all_emails = await email_service.list_emails(limit=100)
        print(f"\nTotal emails in system: {len(all_emails)}")
        
        pending = await draft_service.get_pending_queue()
        print(f"Drafts pending approval: {len(pending)}")


def run_eval(mock: bool = False):
    """Run evaluation."""
    sys.path.insert(0, str(Path(__file__).parent / "scripts"))
    from scripts.evaluate import evaluate
    asyncio.run(evaluate(force_mock=mock))


def main():
    parser = argparse.ArgumentParser(
        description="AI Inbox Triage Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                   Start web server on port 8000
  python main.py --port 3000       Start web server on port 3000
  python main.py --triage          Process all emails
  python main.py --eval            Run accuracy evaluation
  python main.py --eval --mock     Run evaluation with mock classifier
        """
    )
    
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--triage", action="store_true", help="Run triage workflow")
    parser.add_argument("--eval", action="store_true", help="Run evaluation")
    parser.add_argument("--mock", action="store_true", help="Force mock mode for eval")
    parser.add_argument("--limit", type=int, help="Limit number of emails to process")
    parser.add_argument("--dry-run", action="store_true", help="Don't create drafts")
    
    args = parser.parse_args()
    
    if args.eval:
        run_eval(mock=args.mock)
    elif args.triage:
        asyncio.run(run_triage(limit=args.limit, dry_run=args.dry_run))
    else:
        run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
