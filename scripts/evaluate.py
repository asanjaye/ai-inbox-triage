#!/usr/bin/env python3
"""
Evaluation script for the AI inbox triage system.

Measures classification accuracy against labeled synthetic emails.
Supports both real LLM mode and mock/dry-run mode.
"""
import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models import Email, EmailCategory, EmailPriority
from src.llm import get_classifier, MockClassifier
from src.config import get_settings


class EvaluationResults:
    """Stores and computes evaluation metrics."""
    
    def __init__(self):
        self.predictions: list[tuple[str, str]] = []  # (predicted, actual)
        self.priority_predictions: list[tuple[str, str]] = []
        self.needs_reply_predictions: list[tuple[bool, bool]] = []
        self.errors: list[str] = []
    
    def add_result(
        self,
        email_id: str,
        pred_category: EmailCategory,
        actual_category: EmailCategory,
        pred_priority: EmailPriority,
        actual_priority: EmailPriority,
        pred_needs_reply: bool,
        actual_needs_reply: bool,
    ):
        self.predictions.append((pred_category.value, actual_category.value))
        self.priority_predictions.append((pred_priority.value, actual_priority.value))
        self.needs_reply_predictions.append((pred_needs_reply, actual_needs_reply))
    
    def category_accuracy(self) -> float:
        if not self.predictions:
            return 0.0
        correct = sum(1 for pred, actual in self.predictions if pred == actual)
        return correct / len(self.predictions)
    
    def priority_accuracy(self) -> float:
        if not self.priority_predictions:
            return 0.0
        correct = sum(1 for pred, actual in self.priority_predictions if pred == actual)
        return correct / len(self.priority_predictions)
    
    def needs_reply_accuracy(self) -> float:
        if not self.needs_reply_predictions:
            return 0.0
        correct = sum(1 for pred, actual in self.needs_reply_predictions if pred == actual)
        return correct / len(self.needs_reply_predictions)
    
    def category_confusion_matrix(self) -> dict[str, dict[str, int]]:
        """Generate confusion matrix for categories."""
        categories = [c.value for c in EmailCategory]
        matrix = {actual: {pred: 0 for pred in categories} for actual in categories}
        
        for pred, actual in self.predictions:
            matrix[actual][pred] += 1
        
        return matrix
    
    def priority_confusion_matrix(self) -> dict[str, dict[str, int]]:
        """Generate confusion matrix for priorities."""
        priorities = [p.value for p in EmailPriority]
        matrix = {actual: {pred: 0 for pred in priorities} for actual in priorities}
        
        for pred, actual in self.priority_predictions:
            matrix[actual][pred] += 1
        
        return matrix
    
    def print_report(self, is_mock: bool = False):
        """Print formatted evaluation report."""
        mode = "DRY-RUN (Mock Classifier)" if is_mock else "LIVE (Real LLM)"
        
        print("\n" + "=" * 60)
        print(f"EVALUATION REPORT - {mode}")
        print("=" * 60)
        
        print(f"\nTotal Emails Evaluated: {len(self.predictions)}")
        print(f"Errors: {len(self.errors)}")
        
        print("\n--- ACCURACY METRICS ---")
        print(f"Category Accuracy:    {self.category_accuracy():.1%}")
        print(f"Priority Accuracy:    {self.priority_accuracy():.1%}")
        print(f"Needs-Reply Accuracy: {self.needs_reply_accuracy():.1%}")
        
        print("\n--- CATEGORY CONFUSION MATRIX ---")
        self._print_confusion_matrix(
            self.category_confusion_matrix(),
            [c.value for c in EmailCategory]
        )
        
        print("\n--- PRIORITY CONFUSION MATRIX ---")
        self._print_confusion_matrix(
            self.priority_confusion_matrix(),
            [p.value for p in EmailPriority]
        )
        
        if self.errors:
            print("\n--- ERRORS ---")
            for error in self.errors[:10]:
                print(f"  - {error}")
        
        print("\n" + "=" * 60)
        
        if is_mock:
            print("NOTE: Results are from mock classifier (deterministic rules).")
            print("For real accuracy measurement, run with MOCK_MODE=false and API key.")
        
        print("=" * 60 + "\n")
    
    def _print_confusion_matrix(self, matrix: dict, labels: list[str]):
        """Print a formatted confusion matrix."""
        present_labels = []
        for label in labels:
            if any(matrix[label][p] > 0 for p in labels) or \
               any(matrix[a][label] > 0 for a in labels):
                present_labels.append(label)
        
        if not present_labels:
            print("  (no data)")
            return
        
        abbrev = {label: label[:8] for label in present_labels}
        
        header = "Actual \\ Pred".ljust(18) + " ".join(abbrev[l].rjust(8) for l in present_labels)
        print(header)
        print("-" * len(header))
        
        for actual in present_labels:
            row = abbrev[actual].ljust(18)
            for pred in present_labels:
                count = matrix[actual][pred]
                row += str(count).rjust(8) + " "
            print(row)


async def load_emails(path: str) -> list[Email]:
    """Load emails from JSON file."""
    with open(path) as f:
        data = json.load(f)
    
    emails = []
    for email_data in data.get("emails", []):
        email = Email(**email_data)
        if email.label_category and email.label_priority and email.label_needs_reply is not None:
            emails.append(email)
    
    return emails


async def evaluate(
    emails_path: str = "./data/synthetic_emails.json",
    force_mock: bool = False,
) -> EvaluationResults:
    """Run evaluation on labeled emails."""
    settings = get_settings()
    
    is_mock = force_mock or settings.mock_mode
    classifier = get_classifier(force_mock=force_mock)
    
    print(f"\nLoading emails from: {emails_path}")
    emails = await load_emails(emails_path)
    print(f"Found {len(emails)} labeled emails")
    
    print(f"\nClassifier: {classifier.model_name}")
    print(f"Mode: {'Mock (deterministic)' if is_mock else 'Live (API calls)'}")
    print("\nClassifying emails...")
    
    results = EvaluationResults()
    
    for i, email in enumerate(emails, 1):
        try:
            classification = await classifier.classify(email)
            
            results.add_result(
                email_id=email.id,
                pred_category=classification.category,
                actual_category=email.label_category,
                pred_priority=classification.priority,
                actual_priority=email.label_priority,
                pred_needs_reply=classification.needs_reply,
                actual_needs_reply=email.label_needs_reply,
            )
            
            status = "✓" if classification.category == email.label_category else "✗"
            print(f"  [{i}/{len(emails)}] {email.id}: {status} "
                  f"(pred={classification.category.value}, actual={email.label_category.value})")
            
        except Exception as e:
            results.errors.append(f"{email.id}: {str(e)}")
            print(f"  [{i}/{len(emails)}] {email.id}: ERROR - {e}")
    
    results.print_report(is_mock=is_mock)
    
    return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate email classification accuracy")
    parser.add_argument(
        "--emails", "-e",
        default="./data/synthetic_emails.json",
        help="Path to labeled emails JSON file"
    )
    parser.add_argument(
        "--mock", "-m",
        action="store_true",
        help="Force mock mode (ignore MOCK_MODE env var)"
    )
    
    args = parser.parse_args()
    
    results = asyncio.run(evaluate(
        emails_path=args.emails,
        force_mock=args.mock,
    ))
    
    if results.category_accuracy() < 0.5 and not args.mock:
        print("WARNING: Category accuracy below 50%")
        sys.exit(1)


if __name__ == "__main__":
    main()
