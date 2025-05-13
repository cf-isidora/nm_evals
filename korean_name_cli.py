#!/usr/bin/env python
"""
Command-Line Interface for the CF Name Evaluation System.

This module provides a user-friendly command-line interface for the Korean name
evaluation system, allowing users to easily evaluate names through simple commands.
It serves as the main entry point for users to interact with the system through
the terminal.

The CLI supports:
- Evaluating single or multiple names in either direction (KO-EN or EN-KO)
- Automatically detecting name languages and applying appropriate evaluations
- Reading names from input files for batch processing
- Generating reports in multiple formats (JSON, HTML, text)
- Controlling Teamwork integration with simple flags
- Showing available verification resources
- Configuring evaluation parameters via command-line arguments

This tool makes the name evaluation system accessible to terminologists and
translators who can use it directly from their terminal without needing to
write code or understand the underlying implementation details.
"""

import argparse
import sys
import json
import os
from typing import List
from korean_name_evaluator import batch_evaluate_names, generate_html_report
from terminologists_manual_links import get_verification_process_text


def parse_arguments():
    """Parse command line arguments for the Korean name evaluator."""
    parser = argparse.ArgumentParser(
        description="Evaluate names according to CF Terminology Management Manual guidelines"
    )

    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument("--names", type=str, nargs="+", help="Names to evaluate")

    input_group.add_argument(
        "--file",
        type=str,
        help="Path to a file containing names to evaluate (one per line)",
    )

    input_group.add_argument(
        "--show-resources",
        action="store_true",
        help="Display verification resources from the Terminologists' Manual",
    )

    parser.add_argument(
        "--direction",
        type=str,
        choices=["KO-EN", "EN-KO"],
        default="KO-EN",
        help="Translation direction (KO-EN: Korean to English, EN-KO: English to Korean)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="reports/name_evaluation_report.html",
        help="Output HTML report file path",
    )

    parser.add_argument(
        "--json-output",
        type=str,
        default="reports/name_evaluation_results.json",
        help="Output JSON file path for raw results",
    )

    return parser.parse_args()


def load_names_from_file(file_path: str) -> List[str]:
    """Load names from a file, one per line."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading names from file {file_path}: {e}")
        sys.exit(1)


def display_verification_resources(direction: str):
    """
    Display the verification resources for the specified direction.

    Args:
        direction: Translation direction (KO-EN or EN-KO)
    """
    print(get_verification_process_text(direction))


def main():
    """Main entry point for the name evaluator CLI."""
    args = parse_arguments()

    # Show resources if requested
    if args.show_resources:
        display_verification_resources(args.direction)
        return

    # Load names from args or file
    if args.names:
        names = args.names
    elif args.file:
        names = load_names_from_file(args.file)
    else:
        print("Error: You must provide names to evaluate either with --names or --file")
        sys.exit(1)

    print(f"Starting evaluation of {len(names)} names (direction: {args.direction})...")

    # Run the evaluation
    results = batch_evaluate_names(names, args.direction)

    # Ensure reports directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Generate the HTML report
    generate_html_report(results, args.output)

    # Save raw results to JSON (already done in batch_evaluate_names)
    if args.json_output != "reports/name_evaluation_results.json":
        # If user specified a different JSON output path, save the results there too
        os.makedirs(os.path.dirname(args.json_output), exist_ok=True)
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    compliant_count = sum(1 for r in results if r.get("compliant", False))
    avg_score = (
        int(sum(r.get("overall_score", 0) for r in results) / len(results))
        if results
        else 0
    )

    print("\nEvaluation complete!")
    print(f"Evaluated {len(names)} names")
    print(
        f"Compliant: {compliant_count}, Non-compliant: {len(names) - compliant_count}"
    )
    print(f"Average compliance score: {avg_score}%")
    print(f"HTML report generated: {args.output}")
    print(f"JSON results saved: {args.json_output}")

    # Exit with status code 0 (success) if all names are compliant, otherwise 1
    sys.exit(0 if compliant_count == len(names) else 1)


if __name__ == "__main__":
    main()
