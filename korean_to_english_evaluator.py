#!/usr/bin/env python
"""
Korean to English Name Evaluator for CF Terminology Management.

This module implements the "Verification of Proper Names - EN Target for Real persons' Names"
process from the CF Terminology Management Manual. It evaluates Korean names and provides
detailed analysis of their English notation, ensuring compliance with romanization,
capitalization, and hyphenation rules.

The module includes:
- LangChain integration for intelligent name analysis
- Comprehensive rule checking for each name component
- Verification against reference sources and previous translations
- Teamwork API integration for checking existing terminology
- Report generation in multiple formats (JSON, HTML, text)

This specialized evaluator goes beyond basic transliteration by implementing
the complete verification workflow defined in the CF manual, including checking
official sources, determining name formats, applying specific rules, and
providing detailed compliance scores and recommendations.

This module can also check Teamwork for previous translations of the same name to ensure consistency.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains.openai_functions import create_structured_output_chain
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Use relative imports for our modules
from terminologists_manual_links import (
    get_verification_process_text,
    get_resources_for_direction,
)

# Import functions from the Teamwork integration if available
TEAMWORK_AVAILABLE = False
try:
    from teamwork_integration import verify_name_in_teamwork

    TEAMWORK_AVAILABLE = True
except ImportError:
    # Teamwork integration not available
    pass

# Load environment variables
load_dotenv()


class KoToEnNameEvaluation(BaseModel):
    """Schema for Korean to English name evaluation results."""

    name: str = Field(description="The Korean name being evaluated")
    english_notation: str = Field(description="The recommended English notation")
    romanization_compliant: bool = Field(
        description="Whether the romanization follows NIKL rules"
    )
    hyphenation_compliant: bool = Field(
        description="Whether the hyphenation follows CF guidelines"
    )
    capitalization_compliant: bool = Field(
        description="Whether the capitalization follows CF guidelines"
    )
    verification_process: Dict[str, int] = Field(
        default_factory=dict,
        description="Scores for each verification process step (0-100)",
    )
    verification_sources: List[str] = Field(
        default_factory=list, description="Sources used for verification"
    )
    reference_links: Optional[List[str]] = Field(
        default=None, description="Links to reference materials"
    )
    termbase_entry: Optional[Dict[str, str]] = Field(
        default=None, description="Recommended Termbase entry details"
    )
    compliant: bool = Field(
        description="Whether the English notation is compliant with guidelines"
    )
    overall_score: int = Field(description="Overall verification quality score (0-100)")
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for improvement"
    )
    # Simplify this field to avoid anyOf validation issues with gpt-4o-mini
    teamwork_verification: Optional[Dict[str, Any]] = None


def create_ko_to_en_evaluator():
    """
    Creates an evaluator for Korean to English name verification.

    Returns:
        A callable function for name evaluation
    """
    # Initialize the chat model
    model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")
    temperature = float(os.environ.get("OPENAI_TEMPERATURE", "0"))
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)

    # Get the process text and verification resources
    process_text = get_verification_process_text(direction="KO-EN")
    resources = get_resources_for_direction(direction="KO-EN")
    resources_text = format_resources_text(resources)

    # Initialize the prompt
    evaluation_prompt = ChatPromptTemplate.from_template(
        """You are a Korean language name verification expert that helps evaluate proper names in Korean-English translation contexts.
        
        You should strictly follow these rules for Korean to English name verification:
        
        {process_text}
        
        You can reference the following verification sources:
        {resources_text}
        
        Examine the Korean name "{name}" and determine the proper English notation following the guidelines.
        
        {teamwork_context}
        
        Return your evaluation as a single JSON object with the following fields:
        - name: The Korean name being evaluated
        - english_notation: The recommended English notation
        - romanization_compliant: Whether the romanization follows NIKL rules (true/false)
        - hyphenation_compliant: Whether the hyphenation follows CF guidelines (true/false)
        - capitalization_compliant: Whether the capitalization follows CF guidelines (true/false)
        - verification_process: Object with scores for each verification step (0-100)
        - verification_sources: Array of sources used for verification
        - reference_links: Array of links to reference materials (if any)
        - termbase_entry: Object with recommended Termbase entry details
        - compliant: Whether the English notation is compliant with guidelines (true/false)
        - overall_score: Overall verification quality score (0-100)
        - recommendations: Array of recommendations for improvement
        
        Format your entire response as a valid JSON object. Do not include any text outside the JSON object.
        """
    )

    # Use function calling instead of structured output
    def name_evaluator(name, teamwork_results=None):
        # Format teamwork context
        teamwork_context = ""
        if isinstance(teamwork_results, dict) and teamwork_results.get("matches"):
            matches = teamwork_results.get("matches", [])
            teamwork_context = "Previous translations found in Teamwork:\n"
            for match in matches:
                teamwork_context += f"- Task: {match.get('task_name')}\n"
                teamwork_context += (
                    f"  Translation: {match.get('translation', 'Not specified')}\n"
                )
        else:
            teamwork_context = "No previous translations found in Teamwork."

        # Get the evaluation from LLM
        chain = evaluation_prompt | llm
        result = chain.invoke(
            {
                "name": name,
                "process_text": process_text,
                "resources_text": resources_text,
                "teamwork_context": teamwork_context,
            }
        )

        # Extract the evaluation from the response
        response_text = result.content if hasattr(result, "content") else str(result)

        # Create default evaluation structure
        evaluation = {
            "name": name,
            "english_notation": "",
            "verification_process": {},
            "verification_sources": [],
            "compliant": False,
            "overall_score": 0,
            "notes": f"Raw evaluation:\n{response_text}",
            "teamwork_verification": teamwork_results,
        }

        # Try to parse JSON response
        try:
            # Extract JSON content if wrapped in backticks
            json_text = response_text
            json_match = re.search(r"```(?:json)?(.*?)```", response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1).strip()

            # Parse the JSON
            data = json.loads(json_text)

            # Update evaluation with parsed data
            evaluation.update(
                {
                    "english_notation": data.get("english_notation", ""),
                    "romanization_compliant": data.get("romanization_compliant", False),
                    "hyphenation_compliant": data.get("hyphenation_compliant", False),
                    "capitalization_compliant": data.get(
                        "capitalization_compliant", False
                    ),
                    "verification_process": data.get("verification_process", {}),
                    "verification_sources": data.get("verification_sources", []),
                    "reference_links": data.get("reference_links", []),
                    "termbase_entry": data.get("termbase_entry", {}),
                    "compliant": data.get("compliant", False),
                    "overall_score": data.get("overall_score", 0),
                    "recommendations": data.get("recommendations", []),
                }
            )
        except Exception as e:
            evaluation["notes"] += f"\nJSON parsing error: {str(e)}"

            # Fallback to regex parsing for critical fields
            try:
                # Extract English notation
                english_match = re.search(
                    r'"english_notation":\s*"([^"]+)"', response_text
                )
                if english_match:
                    evaluation["english_notation"] = english_match.group(1).strip()

                # Extract compliance and score
                compliant_match = re.search(
                    r'"compliant":\s*(true|false)', response_text, re.IGNORECASE
                )
                if compliant_match:
                    evaluation["compliant"] = compliant_match.group(1).lower() == "true"

                score_match = re.search(r'"overall_score":\s*(\d+)', response_text)
                if score_match:
                    evaluation["overall_score"] = int(score_match.group(1))
            except Exception as e2:
                evaluation["notes"] += f"\nRegex fallback error: {str(e2)}"

        return evaluation

    return name_evaluator


def evaluate_korean_name(name: str, check_teamwork: bool = True) -> Dict[str, Any]:
    """
    Evaluate a Korean name and provide English notation recommendations.

    Args:
        name: Korean name to evaluate
        check_teamwork: Whether to check Teamwork for previous translations

    Returns:
        Dictionary with evaluation results
    """
    # Get the evaluation function
    evaluator = create_ko_to_en_evaluator()

    # Check Teamwork if enabled
    teamwork_results = None
    if check_teamwork and TEAMWORK_AVAILABLE and os.environ.get("TEAMWORK_API_KEY"):
        try:
            teamwork_results = verify_name_in_teamwork(name)
        except Exception as e:
            print(f"Teamwork verification error: {e}")
            teamwork_results = None

    # Run the evaluation
    return evaluator(name, teamwork_results)


def evaluate_korean_names(names: List[str], check_teamwork: bool = True) -> List[Dict]:
    """
    Evaluates multiple Korean names for English notation.

    Args:
        names: List of Korean names to evaluate
        check_teamwork: Whether to check Teamwork for previous translations

    Returns:
        List of dictionaries with evaluation results
    """
    results = []

    # Create the evaluator function
    evaluator = create_ko_to_en_evaluator()

    # Process each name
    for name in names:
        print(f"Evaluating '{name}'...")
        result = evaluator(name, check_teamwork)
        # Convert Pydantic model to dict if necessary
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        results.append(result)

    # Save results to file
    os.makedirs("reports", exist_ok=True)
    with open("reports/korean_to_english_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results


def generate_termbase_entries(
    results: List[Dict],
    output_file: str = "reports/korean_to_english_termbase_entries.txt",
):
    """
    Generates properly formatted termbase entries from evaluation results.

    Args:
        results: List of evaluation results
        output_file: Path to save the termbase entries
    """
    entries = []

    for result in results:
        # Convert Pydantic model to dict if necessary
        if hasattr(result, "model_dump"):
            result = result.model_dump()

        name = result.get("name", "")
        english_notation = result.get("english_notation", "")

        if not english_notation:
            continue

        # Build termbase entry
        entry = f"## {name} → {english_notation}\n\n"

        # Add verification sources
        sources = result.get("verification_sources", [])
        if sources:
            entry += "### Verification Sources\n"
            for source in sources:
                entry += f"- {source}\n"
            entry += "\n"

        # Add termbase entry details
        termbase_entry = result.get("termbase_entry", {})
        if termbase_entry:
            entry += "### Termbase Entry\n"
            for key, value in termbase_entry.items():
                entry += f"- **{key}**: {value}\n"
            entry += "\n"

        # Add compliance score
        score = result.get("overall_score", 0)
        entry += f"### Compliance Score: {score}/100\n\n"

        # Add recommendations
        recommendations = result.get("recommendations", [])
        if recommendations:
            entry += "### Recommendations\n"
            for rec in recommendations:
                entry += f"- {rec}\n"
            entry += "\n"

        entry += "---\n\n"
        entries.append(entry)

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Korean to English Termbase Entries\n\n")
        f.write("".join(entries))

    print(f"Termbase entries saved to {output_file}")


def format_resources_text(resources: List[Dict[str, Any]]) -> str:
    """
    Format resources for display in the prompt.

    Args:
        resources: List of resource dictionaries

    Returns:
        Formatted resources text
    """
    if not resources:
        return "No resources available."

    formatted = ""
    for resource in resources:
        name = resource.get("name", "Unnamed resource")
        url = resource.get("url", "")
        description = resource.get("description", "")

        formatted += f"- {name}"
        if url:
            formatted += f" ({url})"
        if description:
            formatted += f": {description}"
        formatted += "\n"

    return formatted


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Korean to English Name Evaluator")
    parser.add_argument("--names", nargs="+", help="Korean names to evaluate")
    parser.add_argument("--file", help="File containing Korean names (one per line)")
    parser.add_argument(
        "--output",
        default="reports/korean_to_english_termbase_entries.txt",
        help="Output file path for termbase entries",
    )
    parser.add_argument(
        "--no-teamwork", action="store_true", help="Disable Teamwork verification"
    )

    args = parser.parse_args()

    # Get names from arguments or file
    names = []
    if args.names:
        names = args.names
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip()]
    else:
        print("Please provide names to evaluate using --names or --file")
        sys.exit(1)

    # Run evaluation
    results = evaluate_korean_names(names, check_teamwork=not args.no_teamwork)

    # Generate termbase entries
    generate_termbase_entries(results, args.output)
