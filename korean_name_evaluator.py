#!/usr/bin/env python
"""
Core Korean Name Evaluation System for CF Terminology Management.

This module serves as the foundation of the name evaluation system, providing
the core logic for analyzing names against the CF Terminology Management Manual
requirements. It works as a flexible evaluation engine that can be used for
both Korean to English and English to Korean name verification.

The module includes:
- Generic name evaluation chains using LangChain and LLM models
- Customizable verification processes for different name types
- Comprehensive rule application and compliance checking
- Support for both directions (KO-EN and EN-KO)
- Detailed reporting with scores, recommendations, and compliance status
- Optional LangSmith integration for tracing evaluations
- Batch processing capabilities for multiple names

This central component acts as the underlying framework that other more
specialized evaluators build upon, implementing the shared logic and
verification workflow while allowing for direction-specific customization.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.chains.openai_functions import create_structured_output_chain
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import Teamwork integration if available
try:
    from teamwork_integration import verify_name_in_teamwork
    TEAMWORK_AVAILABLE = True
except ImportError:
    TEAMWORK_AVAILABLE = False

# Load environment variables
load_dotenv()

class NameEvaluationResult(BaseModel):
    """Schema for name evaluation results."""
    name: str = Field(description="The name being evaluated")
    language_direction: str = Field(description="EN-KO or KO-EN direction")
    compliant: bool = Field(description="Whether the name complies with guidelines")
    rule_scores: Dict[str, int] = Field(description="Scores for each rule category (0-100)")
    overall_score: int = Field(description="Overall compliance score (0-100)")
    recommendations: List[str] = Field(description="Recommendations for improvement")
    verification_sources: List[str] = Field(description="Sources used for verification")
    notes: Optional[str] = Field(description="Additional notes about evaluation")
    teamwork_verification: Optional[Dict[str, Any]] = Field(description="Teamwork verification results if available")

def create_ko_name_evaluator_chain():
    """
    Creates a chain for evaluating Korean name translations.
    
    Returns:
        A function that evaluates names
    """
    # Initialize the OpenAI model
    model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4")
    temperature = float(os.environ.get("OPENAI_TEMPERATURE", "0"))
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)
    
    # Create a prompt template based on the CF Terminology Management Manual
    prompt = ChatPromptTemplate.from_template(
        """You are a terminology expert following the CF Terminology Management Manual.
        
        Evaluate the following name according to the CF terminology guidelines for {direction} name verification:
        
        Name: {name}
        
        {teamwork_info}
        
        GUIDELINES FOR KOREAN NAME VERIFICATION:
        
        1. Internal Data Verification:
           - CF's own Termbase Search: Use 'TMD Clean 20200923' as default search pool in SmartCAT Glossary
           - Check existing submissions in CF Teamwork (do not trust records before 2019): https://cultureflipper.teamwork.com
           - NFLX Lucid TM Check for notation history: https://localization-lucid.netflix.com/translation/search/?targetLocales=ko
           - Follow Kyonshik's confirmed notation
           - Check email verification in CF or Lead PM account inboxes
           - TM Depository: https://docs.google.com/spreadsheets/d/1A8QpynPg5rNJR2MPkPeyw7WDf5x-NiZauU5b2mN6NE0/edit#gid=0
           - CF Terminology Depository: https://docs.google.com/spreadsheets/d/1bktPGup6cixITi35RBtgZY41pGqguu93m8noGXQ5ffk/edit#gid=670266495&range=AA38
           - For inconsistencies, confirm with phonetic experts (Hans and Hazel) or Kyonshik
        
        2. Netflix-Specific Resources:
           - NF Original Credits (NOC): https://docs.google.com/spreadsheets/d/1AxXZfMZGmGMryaH4waVMvKoYps59owtyuBuTI2T_8pQ/edit#gid=554552356
           - NF Master Marketing Translations (MMT): https://docs.google.com/spreadsheets/d/1oNJQBbfTCGBeziKjYftn-J5JU2KHFU7_CThZryQ_llg/edit?ts=5c1a9b19#gid=0
           - NF Korean Ratings Trackers: https://docs.google.com/spreadsheets/d/1i7RFBjbHaqsLC4LZz50kdvp1bcWbO4eOILc1kml6Gcc/edit#gid=1190947542
           - NF LRT: https://lrt.netflix.net/
           - LEGO subtitle search page: https://lego.netflix.com/#
        
        3. External Data Verification:
           - For author names of domestically published books, follow notation in translated book
           - Verify with National Institute of Korean Language (NIKL): https://kornorms.korean.go.kr//regltn/regltnView.do?regltn_code=0004#a
           - NIKL "Example Search" on Korean Language Standards page: https://kornorms.korean.go.kr//example/exampleList.do?regltn_code=0003
           - KOFIC KoBiz (Korean Film Council): http://www.koreanfilm.or.kr/eng/main/main.jsp
           - KMDb (Korean Movie Database): https://www.kmdb.or.kr/main
           - KMRB (Korea Media Rating Board): https://www.kmrb.or.kr/kor/Main.do
           - Romanization Converter: http://roman.cs.pusan.ac.kr/
           - YouTube (for pronunciation verification): https://www.youtube.com/
           - Ensure language/country information matches name context
           - Search surnames and given names separately, but don't split single names into phoneme units
           - If name spelling matches place name, follow place name notation for consistency
           - IMDb (for international verification): https://www.imdb.com/
        
        4. Special Rules for English Target:
           - All real names should use hyphenation by default
           - For North Korean names with spaces between syllables, replace spaces with hyphens and lowercase first letter of second syllable
           - For idol group/stage names in uppercase, capitalize first letter of each word, rest lowercase
           - Animal names should be written without hyphens
           - For organization names with Korean names, follow official English notation style
        
        5. Recording in Termbase:
           - Include task number where proper noun is mentioned
           - Include nationality, original name, verification reference
           - Include pronunciation video link if available
           - Include NTV Verification Status and Naver Notation
        
        Evaluate the name's compliance with these guidelines and provide:
        1. Specific scores (0-100) for each verification category
        2. Overall compliance score
        3. Recommendations for improvement
        4. Sources that should be checked
        """
    )
    
    # Create the extraction chain for structured output - updated approach
    extraction_chain = create_structured_output_chain(NameEvaluationResult, llm, prompt)
    
    # Build the complete evaluation function
    def evaluate_name(name: str, direction: str = "KO-EN", check_teamwork: bool = True):
        # Check Teamwork for previous translations if enabled and available
        teamwork_info = ""
        teamwork_verification = None
        
        if check_teamwork and TEAMWORK_AVAILABLE and os.environ.get("TEAMWORK_API_KEY"):
            try:
                teamwork_verification = verify_name_in_teamwork(name)
                if teamwork_verification["found_in_teamwork"]:
                    teamwork_info = "TEAMWORK VERIFICATION RESULTS:\n"
                    
                    # Add previous evaluations if found
                    if teamwork_verification["previous_evaluations"]:
                        teamwork_info += f"- Found {len(teamwork_verification['previous_evaluations'])} previous evaluations in Teamwork\n"
                        for eval in teamwork_verification["previous_evaluations"][:3]:  # Limit to first 3
                            teamwork_info += f"  * {eval['title']} ({eval['created_at']})\n"
                    
                    # Add previous translations if found
                    if teamwork_verification["previous_translations"]:
                        teamwork_info += f"- Found {len(teamwork_verification['previous_translations'])} previous translations in Teamwork\n"
                        for trans in teamwork_verification["previous_translations"][:3]:  # Limit to first 3
                            teamwork_info += f"  * {trans['title']} ({trans['created_at']})\n"
                    
                    teamwork_info += f"- Verification status: {teamwork_verification['verification_status']}\n"
                else:
                    teamwork_info = "TEAMWORK VERIFICATION RESULTS:\n- No previous records found in Teamwork\n"
            except Exception as e:
                teamwork_info = f"TEAMWORK VERIFICATION ERROR: {str(e)}\n"
        
        # Use the structured output chain directly with the input
        input_data = {
            "name": name,
            "direction": direction,
            "teamwork_info": teamwork_info
        }
        
        try:
            # Get structured result directly from the extraction chain
            result = extraction_chain.invoke(input_data)
            
            # Add Teamwork verification data to the result
            if teamwork_verification:
                result.teamwork_verification = teamwork_verification
            
            return result
        except Exception as e:
            print(f"Error extracting structured data: {e}")
            # Fallback to text output if structured extraction fails
            evaluation_text = (prompt | llm | StrOutputParser()).invoke(input_data)
            
            # Create a minimal result with the text
            return {
                "name": name,
                "language_direction": direction,
                "compliant": "compliant" in evaluation_text.lower(),
                "overall_score": 0,
                "rule_scores": {
                    "Internal Verification": 0,
                    "External Verification": 0,
                    "Rule Compliance": 0
                },
                "recommendations": ["Review the manual verification process"],
                "verification_sources": ["CF Terminology Management Manual"],
                "notes": f"Error in structured extraction. Raw evaluation:\n{evaluation_text}",
                "teamwork_verification": teamwork_verification
            }
    
    return evaluate_name

def batch_evaluate_names(names: List[str], direction: str = "KO-EN", check_teamwork: bool = True) -> List[Dict]:
    """
    Evaluates multiple names against Korean terminology guidelines.
    
    Args:
        names: List of names to evaluate
        direction: Translation direction (KO-EN or EN-KO)
        check_teamwork: Whether to check Teamwork for previous translations
        
    Returns:
        List of evaluation results for each name
    """
    # Create the evaluator function
    evaluate_name = create_ko_name_evaluator_chain()
    
    # Process all names
    results = []
    for name in names:
        print(f"Evaluating name: {name}")
        try:
            result = evaluate_name(name, direction, check_teamwork)
            if isinstance(result, BaseModel):
                results.append(result.dict())
            else:
                results.append(result)
        except Exception as e:
            print(f"Error evaluating {name}: {e}")
            results.append({
                "name": name,
                "error": str(e),
                "compliant": False,
                "overall_score": 0
            })
    
    # Save results to file
    os.makedirs("reports", exist_ok=True)
    with open("reports/name_evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

def generate_html_report(results: List[Dict], output_file: str):
    """
    Generate an HTML report for Korean name evaluations.
    
    Args:
        results: List of evaluation result dictionaries
        output_file: Output file path for HTML report
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Korean Name Evaluation Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }
            .name-card {
                background-color: #f9f9f9;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .name-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            .name-title {
                font-size: 24px;
                font-weight: bold;
                color: #2980b9;
            }
            .score {
                font-size: 18px;
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 4px;
                color: white;
            }
            .score-high {
                background-color: #27ae60;
            }
            .score-medium {
                background-color: #f39c12;
            }
            .score-low {
                background-color: #e74c3c;
            }
            .details {
                margin-top: 15px;
            }
            .detail-row {
                display: flex;
                margin-bottom: 8px;
            }
            .detail-label {
                flex: 0 0 200px;
                font-weight: bold;
            }
            .detail-value {
                flex: 1;
            }
            .tag {
                display: inline-block;
                background-color: #eee;
                padding: 3px 8px;
                border-radius: 3px;
                margin-right: 5px;
                font-size: 14px;
            }
            .compliance {
                margin-top: 15px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
            .check {
                color: #27ae60;
            }
            .cross {
                color: #e74c3c;
            }
            .recommendations {
                margin-top: 15px;
                padding: 10px;
                background-color: #f0f7fb;
                border-radius: 4px;
                border-left: 5px solid #3498db;
            }
            .teamwork {
                margin-top: 15px;
                padding: 10px;
                background-color: #fff8e1;
                border-radius: 4px;
                border-left: 5px solid #ffc107;
            }
        </style>
    </head>
    <body>
        <h1>Korean Name Evaluation Report</h1>
    """
    
    # Add results to the HTML
    for result in results:
        name = result.get("name", "")
        english_notation = result.get("english_notation", "")
        overall_score = result.get("overall_score", 0)
        
        # Determine score class
        score_class = "score-low"
        if overall_score >= 80:
            score_class = "score-high"
        elif overall_score >= 50:
            score_class = "score-medium"
        
        html += f"""
        <div class="name-card">
            <div class="name-header">
                <div class="name-title">{name} → {english_notation}</div>
                <div class="score {score_class}">{overall_score}/100</div>
            </div>
            
            <div class="details">
                <div class="detail-row">
                    <div class="detail-label">Name Type:</div>
                    <div class="detail-value">{result.get("name_type", "Person")}</div>
                </div>
        """
        
        # Add detailed scores
        if result.get("detailed_scores"):
            html += f"""
                <div class="detail-row">
                    <div class="detail-label">Detailed Scores:</div>
                    <div class="detail-value">
            """
            
            for criterion, score in result.get("detailed_scores", {}).items():
                html += f"<div>{criterion}: {score}/100</div>"
                
            html += """
                    </div>
                </div>
            """
            
        # Add verification sources
        if result.get("verification_sources"):
            html += f"""
                <div class="detail-row">
                    <div class="detail-label">Verification Sources:</div>
                    <div class="detail-value">
            """
            
            for source in result.get("verification_sources", []):
                html += f"<div class='tag'>{source}</div>"
                
            html += """
                    </div>
                </div>
            """
            
        # Add compliance checks
        html += f"""
            <div class="compliance">
                <h3>Compliance Checks</h3>
                <div>Romanization: {"<span class='check'>✓</span>" if result.get("romanization_compliant", False) else "<span class='cross'>✗</span>"}</div>
                <div>Hyphenation: {"<span class='check'>✓</span>" if result.get("hyphenation_compliant", False) else "<span class='cross'>✗</span>"}</div>
                <div>Capitalization: {"<span class='check'>✓</span>" if result.get("capitalization_compliant", False) else "<span class='cross'>✗</span>"}</div>
                <div>Overall: {"<span class='check'>✓ Compliant</span>" if result.get("compliant", False) else "<span class='cross'>✗ Non-compliant</span>"}</div>
            </div>
        """
        
        # Add recommendations
        if result.get("recommendations"):
            html += f"""
            <div class="recommendations">
                <h3>Recommendations</h3>
                <ul>
            """
            
            for rec in result.get("recommendations", []):
                html += f"<li>{rec}</li>"
                
            html += """
                </ul>
            </div>
            """
            
        # Add Teamwork verification if available
        teamwork_verification = result.get("teamwork_verification")
        if isinstance(teamwork_verification, dict) and teamwork_verification.get("found_in_teamwork", False):
            html += f"""
            <div class="teamwork">
                <h3>Teamwork Verification</h3>
                <p>Found {len(teamwork_verification.get("matches", []))} previous translations in Teamwork:</p>
                <ul>
            """
            
            for match in teamwork_verification.get("matches", []):
                task_name = match.get("task_name", "Unknown task")
                translation = match.get("translation", "Not specified")
                html += f"<li>{task_name}: {translation}</li>"
                
            html += """
                </ul>
            </div>
            """
            
        html += """
            </div>
        </div>
        """
    
    # Close the HTML
    html += """
    </body>
    </html>
    """
    
    # Write to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"HTML report saved to {output_file}")

if __name__ == "__main__":
    # Sample names for testing
    test_names = [
        "김지원 (Kim Ji-won)",
        "박서준 (Park Seo-joon)",
        "이종석 (Lee Jong-suk)",
        "전지현 (Jun Ji-hyun)",
        "BTS (방탄소년단)"
    ]
    
    print("Starting Korean name evaluation...")
    # Evaluate from Korean to English
    ko_en_results = batch_evaluate_names(test_names, "KO-EN")
    
    # Generate HTML report
    generate_html_report(ko_en_results)
    
    print("\nEvaluation complete! View detailed results in the HTML report.")
    print("Report: name_evaluation_report.html") 