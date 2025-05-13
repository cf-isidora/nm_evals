#!/usr/bin/env python
"""
Specialized Real Person Name Verification for CF Terminology Management.

This module implements the specialized "Verification of Proper Names - EN Target for Real persons' Names"
process from the CF Terminology Management Manual, integrating both Korean-to-English and
English-to-Korean verification flows. It provides comprehensive analysis of real person names
with stricter verification requirements than fictional characters, places, or organizations.

Key features:
- Bidirectional verification (KO-EN and EN-KO) with automatic language detection
- Specialized rules for real people's names in both directions
- Comprehensive verification against multiple official sources
- Detailed compliance reporting focused on real person name requirements
- Integration with Teamwork for previous translation verification

This specialized module enforces the specific requirements for real person names,
including hyphenation rules, capitalization standards, and NIKL romanization compliance
for Korean-to-English, as well as proper transliteration rules for English-to-Korean.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from english_to_korean_evaluator import evaluate_english_name
from korean_name_evaluator import generate_html_report

# Import core functionality from existing modules
from korean_to_english_evaluator import evaluate_korean_name

# Teamwork integration
try:
    from teamwork_integration import verify_name_in_teamwork

    TEAMWORK_AVAILABLE = True
except ImportError:
    TEAMWORK_AVAILABLE = False

# Load environment variables
load_dotenv()


def detect_language(name: str) -> str:
    """
    Detect whether a name is primarily Korean or English.

    Args:
        name: The name to analyze

    Returns:
        "ko" for Korean, "en" for English
    """
    # Check for Korean characters (Hangul Unicode range)
    korean_chars = sum(1 for char in name if "\uac00" <= char <= "\ud7a3")
    # Simple heuristic: if more than 20% Korean characters, treat as Korean
    if korean_chars / len(name) > 0.2:
        return "ko"
    return "en"


def verify_real_person_name(
    name: str, direction: Optional[str] = None, check_teamwork: bool = True
) -> Dict[str, Any]:
    """
    Verify a real person's name according to CF Terminology Management guidelines.
    This function applies specialized verification for real person names.

    Args:
        name: The name to verify
        direction: Translation direction (KO-EN, EN-KO, or None for auto-detection)
        check_teamwork: Whether to check previous translations in Teamwork

    Returns:
        Dictionary with verification results
    """
    # Auto-detect language if direction not provided
    if direction is None:
        lang = detect_language(name)
        direction = "KO-EN" if lang == "ko" else "EN-KO"

    # Check Teamwork for previous translations if enabled
    teamwork_verification = None
    if check_teamwork and TEAMWORK_AVAILABLE and os.environ.get("TEAMWORK_API_KEY"):
        try:
            teamwork_verification = verify_name_in_teamwork(name)
            if teamwork_verification["found_in_teamwork"]:
                print(f"✓ Found previous entries for '{name}' in Teamwork")
            else:
                print(f"✗ No previous entries for '{name}' in Teamwork")
        except Exception as e:
            print(f"Error verifying name in Teamwork: {e}")

    # Process based on direction
    result = None
    if direction == "KO-EN":
        # Apply specialized real person verification for Korean to English
        result = evaluate_korean_name(name, check_teamwork)

        # Add additional real-person specific validation
        result["is_real_person"] = True
        result["real_person_rules"] = {
            "hyphenation_required": True,
            "capitalization_standard": "First letter capitalized, rest lowercase",
            "nikl_compliance_required": True,
            "requires_expert_validation": result.get("overall_score", 0) < 95,
        }

        # Add stricter recommendations for real person names
        recommendations = result.get("recommendations", [])
        recommendations.append(
            "For real person names, hyphenation is mandatory between syllables"
        )
        recommendations.append(
            "Verify with multiple official sources including NIKL standards"
        )
        if "teamwork_verification" in result and result["teamwork_verification"]:
            recommendations.append(
                "Follow existing verified translations in Teamwork for consistency"
            )
        result["recommendations"] = recommendations

    elif direction == "EN-KO":
        # Apply specialized real person verification for English to Korean
        result = evaluate_english_name(name, check_teamwork)

        # Add additional real-person specific validation
        result["is_real_person"] = True
        result["real_person_rules"] = {
            "requires_phonetician_review": True,
            "requires_kyonshik_confirmation": "netflix"
            in result.get("context", "").lower(),
            "record_hz_notation": True,
            "apply_strict_transliteration": True,
        }

        # Add stricter recommendations for real person names
        recommendations = result.get("recommendations", [])
        recommendations.append(
            "For real person names created after 08/11/2020, confirm notation through Kyonshik for NF tasks"
        )
        recommendations.append(
            "For non-NF projects, confirm through Hazel (phonetician)"
        )
        recommendations.append(
            "Record 'HZ Original Notation' in the Korean target of the Termbase"
        )
        result["recommendations"] = recommendations

    # Add Teamwork verification data if available
    if teamwork_verification:
        result["teamwork_verification"] = teamwork_verification

    return result


def batch_verify_real_person_names(
    names: List[str],
    auto_detect: bool = True,
    direction: Optional[str] = None,
    check_teamwork: bool = True,
    output_dir: str = "reports",
) -> Dict[str, Any]:
    """
    Verify multiple real person names and generate comprehensive reports.

    Args:
        names: List of names to verify
        auto_detect: Whether to automatically detect name languages
        direction: Translation direction (if not auto-detecting)
        check_teamwork: Whether to check Teamwork for previous translations
        output_dir: Directory to save verification reports and results

    Returns:
        Dictionary with verification results for all names
    """
    results = {"ko_en_results": [], "en_ko_results": [], "verification_summary": {}}

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Process each name
    for name in names:
        print(f"Verifying real person name: {name}")

        # Determine language and direction
        if auto_detect:
            lang = detect_language(name)
            name_direction = "KO-EN" if lang == "ko" else "EN-KO"
        else:
            name_direction = direction or "KO-EN"

        # Perform verification
        result = verify_real_person_name(name, name_direction, check_teamwork)

        # Add to appropriate results list
        if name_direction == "KO-EN":
            results["ko_en_results"].append(result)
        else:
            results["en_ko_results"].append(result)

    # Generate reports
    if results["ko_en_results"]:
        ko_report_path = os.path.join(output_dir, "real_person_ko_en_report.html")
        generate_html_report(results["ko_en_results"], ko_report_path)
        print(
            f"Korean to English real person verification report saved to: {ko_report_path}"
        )

        # Save raw JSON results
        ko_json_path = os.path.join(output_dir, "real_person_ko_en_results.json")
        with open(ko_json_path, "w", encoding="utf-8") as f:
            json.dump(results["ko_en_results"], f, ensure_ascii=False, indent=2)

    if results["en_ko_results"]:
        # Save raw JSON results for EN-KO
        en_json_path = os.path.join(output_dir, "real_person_en_ko_results.json")
        with open(en_json_path, "w", encoding="utf-8") as f:
            json.dump(results["en_ko_results"], f, ensure_ascii=False, indent=2)

    # Create summary
    results["verification_summary"] = {
        "total_names": len(names),
        "ko_en_count": len(results["ko_en_results"]),
        "en_ko_count": len(results["en_ko_results"]),
        "ko_en_compliant": sum(
            1 for r in results["ko_en_results"] if r.get("compliant", False)
        ),
        "en_ko_compliant": sum(
            1 for r in results["en_ko_results"] if r.get("compliant", False)
        ),
        "timestamp": datetime.now().isoformat(),
    }

    # Save summary report
    summary_path = os.path.join(output_dir, "real_person_verification_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results["verification_summary"], f, ensure_ascii=False, indent=2)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify real person names according to CF Terminology Management Manual"
    )

    # Name input options
    name_group = parser.add_mutually_exclusive_group(required=True)
    name_group.add_argument("--names", type=str, nargs="+", help="Names to verify")
    name_group.add_argument(
        "--file",
        type=str,
        help="Path to a file containing names to verify (one per line)",
    )

    # Direction options
    direction_group = parser.add_mutually_exclusive_group()
    direction_group.add_argument(
        "--direction",
        type=str,
        choices=["KO-EN", "EN-KO"],
        help="Translation direction (KO-EN: Korean to English, EN-KO: English to Korean)",
    )
    direction_group.add_argument(
        "--auto-detect",
        action="store_true",
        help="Automatically detect language and use appropriate evaluator",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Directory to store verification reports and results",
    )

    # Teamwork options
    parser.add_argument(
        "--no-teamwork", action="store_true", help="Disable Teamwork verification"
    )

    args = parser.parse_args()

    # Load names from args or file
    names = []
    if args.names:
        # Process comma-separated names
        for name_arg in args.names:
            # Split by comma and strip whitespace
            split_names = [n.strip() for n in name_arg.split(",")]
            names.extend([n for n in split_names if n])  # Add non-empty names
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip()]

    # Process names
    results = batch_verify_real_person_names(
        names=names,
        auto_detect=args.auto_detect or not args.direction,
        direction=args.direction,
        check_teamwork=not args.no_teamwork,
        output_dir=args.output_dir,
    )

    # Print summary
    summary = results["verification_summary"]
    print("\nVerification complete!")
    print(f"Total names verified: {summary['total_names']}")

    if summary["ko_en_count"] > 0:
        print(
            f"Korean names (KO-EN): {summary['ko_en_count']} verified, {summary['ko_en_compliant']} compliant"
        )

    if summary["en_ko_count"] > 0:
        print(
            f"English names (EN-KO): {summary['en_ko_count']} verified, {summary['en_ko_compliant']} compliant"
        )

    print(f"\nAll reports saved to: {args.output_dir}/")
