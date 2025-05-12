#!/usr/bin/env python
"""
Unified Name Evaluation System for CF Terminology Management.

This module serves as the central integration point for the entire name evaluation system,
combining both Korean-to-English and English-to-Korean evaluation capabilities with
automatic language detection. It provides a comprehensive solution for evaluating proper
names according to the CF Terminology Management Manual.

Key features:
- Automatic language detection to determine appropriate evaluation direction
- Unified interface for both KO-EN and EN-KO evaluations
- Optional LangSmith tracing for evaluation monitoring and debugging
- Flexible Teamwork integration with configurable verification and posting options
- Comprehensive report generation in multiple formats
- Command-line interface with extensive configuration options

This system simplifies the complex process of name verification by providing
a single entry point that handles all aspects of the evaluation workflow,
from language detection to report generation, while adhering to the detailed
guidelines specified in the CF Terminology Management Manual.
"""

import argparse
import json
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from korean_name_evaluator import batch_evaluate_names as evaluate_ko_names
from korean_name_evaluator import generate_html_report
from english_to_korean_evaluator import evaluate_english_names
from english_to_korean_evaluator import generate_termbase_entries as generate_en_ko_termbase_entries
from korean_to_english_evaluator import evaluate_korean_names
from korean_to_english_evaluator import generate_termbase_entries as generate_ko_en_termbase_entries

# Make LangSmith integration optional
LANGSMITH_AVAILABLE = False
try:
    from langsmith_integration import (
        setup_langsmith,
        trace_name_evaluation,
        setup_name_evaluation_monitoring
    )
    LANGSMITH_AVAILABLE = True
except ImportError:
    # Create stub functions for when LangSmith is not available
    def setup_langsmith(*args, **kwargs):
        return None
        
    def trace_name_evaluation(*args, **kwargs):
        pass
        
    def setup_name_evaluation_monitoring(*args, **kwargs):
        pass

from teamwork_integration import verify_name_in_teamwork, post_evaluation_to_teamwork
from terminologists_manual_links import (
    get_resources_for_direction,
    get_verification_process_text,
    load_manual_content,
    DATA_DIR
)

# Load environment variables
load_dotenv()

# Data directory for reference files
DATA_DIRECTORY = DATA_DIR

# Initialize LangSmith if available
if LANGSMITH_AVAILABLE and os.environ.get("LANGCHAIN_API_KEY"):
    console_handler = setup_langsmith(
        project_name=os.environ.get("LANGCHAIN_PROJECT", "cf_name_evaluation"),
        trace_to_console=False
    )
    print("LangSmith tracing enabled for name evaluation")

def detect_language(name: str) -> str:
    """
    Detect whether a name is primarily Korean or English.
    
    Args:
        name: The name to analyze
        
    Returns:
        "ko" for Korean, "en" for English
    """
    # Check for Korean characters (Hangul Unicode range)
    korean_chars = sum(1 for char in name if '\uAC00' <= char <= '\uD7A3')
    # Simple heuristic: if more than 20% Korean characters, treat as Korean
    if korean_chars / len(name) > 0.2:
        return "ko"
    return "en"

def auto_detect_names(names: List[str]) -> Dict[str, List[str]]:
    """
    Automatically categorize names by detected language.
    
    Args:
        names: List of names to categorize
        
    Returns:
        Dictionary with "ko" and "en" keys containing respective name lists
    """
    categorized = {"ko": [], "en": []}
    
    for name in names:
        lang = detect_language(name)
        categorized[lang].append(name)
    
    return categorized

def process_names(
    names: List[str], 
    direction: Optional[str] = None,
    output_dir: str = "reports",
    auto_detect: bool = False,
    trace_to_langsmith: bool = True,
    verify_in_teamwork: bool = False,
    post_to_teamwork: bool = False,
    teamwork_project_id: Optional[str] = None,
    use_local_only: bool = False
) -> Dict[str, Any]:
    """
    Process names through the appropriate evaluator based on direction or auto-detection.
    
    Args:
        names: List of names to evaluate
        direction: Explicit direction ("KO-EN" or "EN-KO"), or None for auto-detect
        output_dir: Directory to save reports
        auto_detect: Whether to automatically detect language and process accordingly
        trace_to_langsmith: Whether to trace evaluations to LangSmith
        verify_in_teamwork: Whether to verify names in Teamwork
        post_to_teamwork: Whether to post evaluation results to Teamwork
        teamwork_project_id: Optional Teamwork project ID for creating tasks
        use_local_only: Whether to use only local resources available in the data directory
        
    Returns:
        Dictionary with evaluation results
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        "ko_en_results": [],
        "en_ko_results": [],
        "teamwork_verification": []
    }
    
    # Log message about local resources mode
    if use_local_only:
        print("Using local resources mode: Only resources from the data directory will be used.")
        # Set environment variable to indicate local-only mode
        os.environ["USE_LOCAL_RESOURCES_ONLY"] = "true"
    else:
        # Clear the environment variable if not in local-only mode
        if "USE_LOCAL_RESOURCES_ONLY" in os.environ:
            del os.environ["USE_LOCAL_RESOURCES_ONLY"]
    
    # Configure LangSmith monitoring if API key is available
    if LANGSMITH_AVAILABLE and os.environ.get("LANGCHAIN_API_KEY") and trace_to_langsmith:
        setup_name_evaluation_monitoring(
            os.environ.get("LANGCHAIN_PROJECT", "cf_name_evaluation")
        )
    
    # First verify names in Teamwork if enabled
    if verify_in_teamwork and os.environ.get("TEAMWORK_API_KEY"):
        print("Verifying names in Teamwork...")
        teamwork_results = []
        for name in names:
            verification = verify_name_in_teamwork(name)
            teamwork_results.append(verification)
            if verification["found_in_teamwork"]:
                print(f"✓ Found previous entries for '{name}' in Teamwork")
            else:
                print(f"✗ No previous entries for '{name}' in Teamwork")
        
        results["teamwork_verification"] = teamwork_results
    
    if auto_detect:
        print("Auto-detecting name languages...")
        categorized = auto_detect_names(names)
        
        # Process Korean names (KO-EN direction)
        if categorized["ko"]:
            print(f"Processing {len(categorized['ko'])} Korean names (KO-EN)...")
            # Use the specialized Korean to English evaluator
            ko_results = evaluate_korean_names(categorized["ko"], check_teamwork=verify_in_teamwork)
            results["ko_en_results"] = ko_results
            
            # Trace evaluations to LangSmith if enabled
            if LANGSMITH_AVAILABLE and os.environ.get("LANGCHAIN_API_KEY") and trace_to_langsmith:
                for result in ko_results:
                    trace_name_evaluation(
                        name=result.get("name", ""),
                        evaluation_result=result,
                        evaluator_name="korean_to_english_evaluator",
                        direction="KO-EN"
                    )
            
            # Generate report for Korean names
            ko_report_path = os.path.join(output_dir, "ko_en_evaluation_report.html")
            generate_html_report(ko_results, ko_report_path)
            print(f"Korean name evaluation report saved to: {ko_report_path}")
            
            # Generate termbase entries
            ko_termbase_path = os.path.join(output_dir, "ko_en_termbase_entries.txt")
            generate_ko_en_termbase_entries(ko_results, ko_termbase_path)
            print(f"Korean to English termbase entries saved to: {ko_termbase_path}")
            
            # Post to Teamwork if enabled
            if post_to_teamwork and os.environ.get("TEAMWORK_API_KEY") and teamwork_project_id:
                print("Posting Korean name evaluations to Teamwork...")
                for result in ko_results:
                    name = result.get("name", "")
                    success, message = post_evaluation_to_teamwork(
                        name=name,
                        evaluation_results=result,
                        project_id=teamwork_project_id
                    )
                    if success:
                        print(f"✓ Posted evaluation for '{name}' to Teamwork: {message}")
                    else:
                        print(f"✗ Failed to post evaluation for '{name}' to Teamwork: {message}")
        
        # Process English names (EN-KO direction)
        if categorized["en"]:
            print(f"Processing {len(categorized['en'])} English names (EN-KO)...")
            en_results = evaluate_english_names(categorized["en"], check_teamwork=verify_in_teamwork)
            results["en_ko_results"] = en_results
            
            # Trace evaluations to LangSmith if enabled
            if LANGSMITH_AVAILABLE and os.environ.get("LANGCHAIN_API_KEY") and trace_to_langsmith:
                for result in en_results:
                    trace_name_evaluation(
                        name=result.get("name", ""),
                        evaluation_result=result,
                        evaluator_name="english_to_korean_evaluator",
                        direction="EN-KO"
                    )
            
            # Generate termbase entries
            en_termbase_path = os.path.join(output_dir, "en_ko_termbase_entries.txt")
            generate_en_ko_termbase_entries(en_results, en_termbase_path)
            print(f"English to Korean termbase entries saved to: {en_termbase_path}")
            
            # Post to Teamwork if enabled
            if post_to_teamwork and os.environ.get("TEAMWORK_API_KEY") and teamwork_project_id:
                print("Posting English name evaluations to Teamwork...")
                for result in en_results:
                    name = result.get("name", "")
                    success, message = post_evaluation_to_teamwork(
                        name=name,
                        evaluation_results=result,
                        project_id=teamwork_project_id
                    )
                    if success:
                        print(f"✓ Posted evaluation for '{name}' to Teamwork: {message}")
                    else:
                        print(f"✗ Failed to post evaluation for '{name}' to Teamwork: {message}")
    elif direction:
        # Process with specific direction
        if direction == "KO-EN":
            print(f"Processing {len(names)} Korean names for English notation...")
            # Use the specialized Korean to English evaluator
            ko_results = evaluate_korean_names(names, check_teamwork=verify_in_teamwork)
            results["ko_en_results"] = ko_results
            
            # Trace evaluations to LangSmith if enabled
            if LANGSMITH_AVAILABLE and os.environ.get("LANGCHAIN_API_KEY") and trace_to_langsmith:
                for result in ko_results:
                    trace_name_evaluation(
                        name=result.get("name", ""),
                        evaluation_result=result,
                        evaluator_name="korean_to_english_evaluator",
                        direction="KO-EN"
                    )
            
            # Generate report
            ko_report_path = os.path.join(output_dir, "ko_en_evaluation_report.html")
            generate_html_report(ko_results, ko_report_path)
            print(f"Korean name evaluation report saved to: {ko_report_path}")
            
            # Generate termbase entries
            ko_termbase_path = os.path.join(output_dir, "ko_en_termbase_entries.txt")
            generate_ko_en_termbase_entries(ko_results, ko_termbase_path)
            print(f"Korean to English termbase entries saved to: {ko_termbase_path}")
            
            # Post to Teamwork if enabled
            if post_to_teamwork and os.environ.get("TEAMWORK_API_KEY") and teamwork_project_id:
                print("Posting Korean name evaluations to Teamwork...")
                for result in ko_results:
                    name = result.get("name", "")
                    success, message = post_evaluation_to_teamwork(
                        name=name,
                        evaluation_results=result,
                        project_id=teamwork_project_id
                    )
                    if success:
                        print(f"✓ Posted evaluation for '{name}' to Teamwork: {message}")
                    else:
                        print(f"✗ Failed to post evaluation for '{name}' to Teamwork: {message}")
        
        elif direction == "EN-KO":
            print(f"Processing {len(names)} English names for Korean notation...")
            en_results = evaluate_english_names(names, check_teamwork=verify_in_teamwork)
            results["en_ko_results"] = en_results
            
            # Trace evaluations to LangSmith if enabled
            if LANGSMITH_AVAILABLE and os.environ.get("LANGCHAIN_API_KEY") and trace_to_langsmith:
                for result in en_results:
                    trace_name_evaluation(
                        name=result.get("name", ""),
                        evaluation_result=result,
                        evaluator_name="english_to_korean_evaluator",
                        direction="EN-KO"
                    )
            
            # Generate termbase entries
            en_termbase_path = os.path.join(output_dir, "en_ko_termbase_entries.txt")
            generate_en_ko_termbase_entries(en_results, en_termbase_path)
            print(f"English to Korean termbase entries saved to: {en_termbase_path}")
            
            # Post to Teamwork if enabled
            if post_to_teamwork and os.environ.get("TEAMWORK_API_KEY") and teamwork_project_id:
                print("Posting English name evaluations to Teamwork...")
                for result in en_results:
                    name = result.get("name", "")
                    success, message = post_evaluation_to_teamwork(
                        name=name,
                        evaluation_results=result,
                        project_id=teamwork_project_id
                    )
                    if success:
                        print(f"✓ Posted evaluation for '{name}' to Teamwork: {message}")
                    else:
                        print(f"✗ Failed to post evaluation for '{name}' to Teamwork: {message}")
        else:
            print(f"Unknown direction: {direction}. Please use 'KO-EN' or 'EN-KO'.")
    else:
        print("Please specify a direction ('KO-EN' or 'EN-KO') or enable auto-detection.")
    
    # Save all results to JSON file
    results_file = os.path.join(output_dir, "name_evaluation_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate names according to CF Terminology Management Manual guidelines"
    )
    
    # Name input options
    name_group = parser.add_mutually_exclusive_group(required=True)
    name_group.add_argument(
        "--names", 
        type=str, 
        nargs="+", 
        help="Names to evaluate"
    )
    name_group.add_argument(
        "--file", 
        type=str, 
        help="Path to a file containing names to evaluate (one per line)"
    )
    name_group.add_argument(
        "--show-resources",
        action="store_true",
        help="Display verification resources from the Terminologists' Manual"
    )
    name_group.add_argument(
        "--show-local-resources",
        action="store_true",
        help="Display available local resources in the data directory"
    )
    
    # Direction options
    direction_group = parser.add_mutually_exclusive_group()
    direction_group.add_argument(
        "--direction", 
        type=str, 
        choices=["KO-EN", "EN-KO"],
        help="Translation direction (KO-EN: Korean to English, EN-KO: English to Korean)"
    )
    direction_group.add_argument(
        "--auto-detect",
        action="store_true",
        help="Automatically detect language and use appropriate evaluator"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="reports",
        help="Directory to store evaluation reports and results"
    )
    
    # Resource options
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Use only local resources available in the data directory"
    )
    
    # LangSmith options
    parser.add_argument(
        "--disable-tracing",
        action="store_true",
        help="Disable LangSmith tracing even if available"
    )
    
    # Teamwork options
    teamwork_group = parser.add_argument_group("Teamwork Integration")
    teamwork_group.add_argument(
        "--verify-in-teamwork",
        action="store_true",
        help="Verify names against previous translations in Teamwork"
    )
    teamwork_group.add_argument(
        "--post-to-teamwork",
        action="store_true",
        help="Post evaluation results to Teamwork"
    )
    teamwork_group.add_argument(
        "--teamwork-project-id",
        type=str,
        help="Teamwork project ID to create tasks in"
    )
    teamwork_group.add_argument(
        "--no-teamwork",
        action="store_true",
        help="Disable all Teamwork integration (overrides --verify-in-teamwork)"
    )
    
    return parser.parse_args()

def load_names_from_file(file_path: str) -> List[str]:
    """Load names from a file, one per line."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading names from file {file_path}: {e}")
        sys.exit(1)

def display_verification_resources(direction: str = None):
    """
    Display the verification resources that should be used for a specific direction.
    
    Args:
        direction: Optional direction to show resources for (KO-EN or EN-KO)
                  If None, shows resources for both directions
    """
    if direction and direction.upper() in ["KO-EN", "EN-KO"]:
        print(get_verification_process_text(direction))
    else:
        print(get_verification_process_text("KO-EN"))
        print("\n" + "="*80 + "\n")
        print(get_verification_process_text("EN-KO"))

def check_available_local_resources():
    """
    Check which resource files are available locally in the data directory.
    
    Returns:
        Dictionary with resource types and their local availability
    """
    local_resources = {
        "manual": os.path.exists(os.path.join(DATA_DIRECTORY, "CF Terminology Management Manual_en excerpts (translated by ChatGPT).txt")),
        "links": os.path.exists(os.path.join(DATA_DIRECTORY, "terminologists_manual_links.txt")),
        "tm_depository": os.path.exists(os.path.join(DATA_DIRECTORY, "TM Training Landscape.xlsx")),
        "terminology_depository": os.path.exists(os.path.join(DATA_DIRECTORY, "Terminologists' Depository.xlsx")),
        "mmt": os.path.exists(os.path.join(DATA_DIRECTORY, "MAIN MARKETING TRANSLATIONS (MMT - Source of Truth).xlsx")),
        "tm_job_organizer": os.path.exists(os.path.join(DATA_DIRECTORY, "TM Job Organizer.xlsx")),
        "task_tracker": os.path.exists(os.path.join(DATA_DIRECTORY, "Task Tracker.xlsx"))
    }
    
    return local_resources

def show_local_resources():
    """Display available local resources in the data directory."""
    resources = check_available_local_resources()
    
    print("LOCAL RESOURCES AVAILABLE:")
    print("==========================")
    
    for resource, available in resources.items():
        status = "✓ Available" if available else "✗ Not found"
        print(f"{resource.replace('_', ' ').title()}: {status}")
    
    print("\nThese local files can be used for offline verification when online resources are unavailable.")
    print(f"Local files are stored in: {DATA_DIRECTORY}")

def main():
    """Main entry point for the combined name evaluation system."""
    args = parse_arguments()
    
    # Show verification resources if requested
    if args.show_resources:
        display_verification_resources(args.direction)
        print("\n" + "="*80 + "\n")
        show_local_resources()
        return
    
    # Show local resources if requested
    if args.show_local_resources:
        show_local_resources()
        return
    
    # Load names from args or file
    if args.names:
        # Process comma-separated names
        names = []
        for name_arg in args.names:
            # Split by comma and strip whitespace
            split_names = [n.strip() for n in name_arg.split(',')]
            names.extend([n for n in split_names if n])  # Add non-empty names
    elif args.file:
        names = load_names_from_file(args.file)
    else:
        print("Error: You must provide names to evaluate either with --names or --file")
        sys.exit(1)
    
    print(f"Starting evaluation of {len(names)} names...")
    
    # Check if using local-only mode
    if args.local_only:
        local_resources = check_available_local_resources()
        
        # Count available resources
        available_count = sum(1 for v in local_resources.values() if v)
        
        if available_count == 0:
            print("Error: No local resources available in the data directory.")
            print("Run with --show-local-resources to see what's missing.")
            sys.exit(1)
        
        print("Using local resources only for verification.")
        print(f"Found {available_count} local resources in {DATA_DIRECTORY}.")
    
    # Apply no-teamwork override if specified
    verify_in_teamwork = args.verify_in_teamwork and not args.no_teamwork
    post_to_teamwork = args.post_to_teamwork and not args.no_teamwork
    
    # Process names
    results = process_names(
        names=names,
        direction=args.direction,
        output_dir=args.output_dir,
        auto_detect=args.auto_detect,
        trace_to_langsmith=not args.disable_tracing,
        verify_in_teamwork=verify_in_teamwork,
        post_to_teamwork=post_to_teamwork,
        teamwork_project_id=args.teamwork_project_id,
        use_local_only=args.local_only
    )
    
    # Print summary
    ko_en_count = len(results.get("ko_en_results", []))
    en_ko_count = len(results.get("en_ko_results", []))
    
    print("\nEvaluation complete!")
    print(f"Total names evaluated: {ko_en_count + en_ko_count}")
    if ko_en_count > 0:
        ko_compliant = sum(1 for r in results["ko_en_results"] if r.get("compliant", False))
        print(f"Korean names (KO-EN): {ko_en_count} evaluated, {ko_compliant} compliant")
    
    if en_ko_count > 0:
        en_compliant = sum(1 for r in results["en_ko_results"] if r.get("compliant", False))
        print(f"English names (EN-KO): {en_ko_count} evaluated, {en_compliant} compliant")
    
    print(f"\nAll reports saved to: {args.output_dir}/")
    
    # Print LangSmith info if applicable
    if LANGSMITH_AVAILABLE and not args.disable_tracing:
        project_name = os.environ.get("LANGCHAIN_PROJECT", "cf_name_evaluation")
        print(f"\nView detailed evaluation traces in LangSmith:")
        print(f"https://smith.langchain.com/project/{project_name}")
    
    # Print Teamwork info if applicable
    if args.verify_in_teamwork or args.post_to_teamwork:
        teamwork_domain = os.environ.get("TEAMWORK_DOMAIN", "cultureflipper")
        print(f"\nTeamwork Integration:")
        if args.verify_in_teamwork:
            print("- Name verification was performed against Teamwork data")
        if args.post_to_teamwork:
            print("- Evaluation results were posted to Teamwork")
            if args.teamwork_project_id:
                print(f"- View tasks in project: https://{teamwork_domain}.teamwork.com/app/projects/{args.teamwork_project_id}/tasks")

if __name__ == "__main__":
    main() 