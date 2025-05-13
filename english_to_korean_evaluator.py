#!/usr/bin/env python
"""
English to Korean Name Evaluator for CF Terminology Management.

This module implements the process of evaluating English names for proper Korean notation
according to the CF Terminology Management Manual. It analyzes English names and provides
recommendations for their correct Korean representation based on established rules for
transliteration, Korean orthography, and consistency with previous translations.

The module includes:
- Functions to evaluate single English names or batches of names
- Integration with Teamwork for previous translation verification
- Compliance checking against terminology guidelines
- Report generation in multiple formats (JSON, HTML, text)

When used as a standalone script, it accepts English names as input and produces
comprehensive evaluation reports that can be used by terminologists and translators
to ensure compliance with CF naming standards.
"""

import os
import json
from typing import Dict, List, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
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


class EnToKoNameEvaluation(BaseModel):
    """Schema for English to Korean name evaluation results."""

    name: str = Field(description="The English name being evaluated")
    korean_notation: str = Field(description="The recommended Korean notation")
    verification_process: Dict[str, int] = Field(
        description="Scores for each verification process step (0-100)"
    )
    verification_sources: List[str] = Field(description="Sources used for verification")
    reference_links: Optional[List[str]] = Field(
        description="Links to reference materials"
    )
    pronunciation_guide: Optional[str] = Field(
        description="Guide to pronunciation in Korean"
    )
    termbase_entry: Optional[Dict[str, str]] = Field(
        description="Recommended Termbase entry details"
    )
    compliant: bool = Field(
        description="Whether the Korean notation is compliant with guidelines"
    )
    overall_score: int = Field(description="Overall verification quality score (0-100)")


def create_en_to_ko_evaluator():
    """
    Creates an evaluator for English to Korean name verification.

    Returns:
        A callable function for name evaluation
    """
    # Initialize the chat model
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

    # Create a prompt template focused on English to Korean verification
    prompt = ChatPromptTemplate.from_template(
        """You are a terminology expert following the CF Terminology Management Manual for English to Korean name verification.
        
        Evaluate the following English name and determine the proper Korean notation:
        
        Name: {name}
        
        GUIDELINES FOR ENGLISH TO KOREAN NAME VERIFICATION:
        
        1. Internal Data Verification (Priority Order):
           - CF's own Termbase Search: Use 'TMD Clean 20200923' as default search pool in SmartCAT Glossary
           - Check existing submissions in CF Teamwork (do not trust records before 2019): https://cultureflipper.teamwork.com
           - NFLX Lucid TM Check for notation history: https://localization-lucid.netflix.com/translation/search/?targetLocales=ko
           - TM Depository: https://docs.google.com/spreadsheets/d/1A8QpynPg5rNJR2MPkPeyw7WDf5x-NiZauU5b2mN6NE0/edit#gid=0
           - CF Terminology Depository: https://docs.google.com/spreadsheets/d/1bktPGup6cixITi35RBtgZY41pGqguu93m8noGXQ5ffk/edit#gid=670266495&range=AA38
           - Email verification in CF or Lead PM account inboxes
           - For inconsistencies, confirm with phonetic experts (Hans and Hazel) or Kyonshik
        
        2. Netflix-Specific Resources:
           - NF Tiloc: https://localization-lucid.netflix.com/titles/search?cl=1
           - NF Original Credits (NOC): https://docs.google.com/spreadsheets/d/1AxXZfMZGmGMryaH4waVMvKoYps59owtyuBuTI2T_8pQ/edit#gid=554552356
           - NF Master Marketing Translations (MMT): https://docs.google.com/spreadsheets/d/1oNJQBbfTCGBeziKjYftn-J5JU2KHFU7_CThZryQ_llg/edit?ts=5c1a9b19#gid=0
           - NF Korean Ratings Trackers: https://docs.google.com/spreadsheets/d/1i7RFBjbHaqsLC4LZz50kdvp1bcWbO4eOILc1kml6Gcc/edit#gid=1190947542
           - NF Service Page: https://www.netflix.com/browse
           - NF LRT: https://lrt.netflix.net/
        
        3. External Data Verification:
           - For author names of domestically published books, follow notation in the translated book
           - Verify with the National Institute of Korean Language (NIKL): https://kornorms.korean.go.kr/
           - NIKL "Example Search" feature on Korean Language Standards page: https://kornorms.korean.go.kr//example/exampleList.do?regltn_code=0003
           - KMRB (Korea Media Rating Board): https://www.kmrb.or.kr/kor/Main.do
           - Cambridge Dictionary: https://dictionary.cambridge.org/dictionary/english/
           - YouTube (for pronunciation verification): https://www.youtube.com/
           - IMDb (for celebrity info): https://www.imdb.com/
           - Ensure language/country information matches the context of the name
           - Search for surname and given name separately, but don't split a single name
           - If name spelling matches a place name, follow place name notation for consistency
        
        4. Recording in Termbase:
           - Include task number where the proper noun is mentioned
           - Include nationality, original name, verification reference
           - Include pronunciation video link if available
           - Include NTV Verification Status and Naver Notation
        
        5. Specific Rules for Real Person Names:
           - Do not trust records created before 2019
           - Follow Kyonshik's confirmed notation for any matches
           - For newly confirmed real names (after 08/11/2020), confirm notation through Kyonshik for NF tasks
           - For non-NF projects, confirm through Hazel (phonetician)
           - Record "HZ Original Notation" in the Korean target of the Termbase
        
        Provide:
        1. The recommended Korean notation
        2. Your verification process (which sources should be checked)
        3. Scores for how well each verification step can be completed
        4. Overall compliance score
        5. Recommended Termbase entry details
        """
    )

    # Create the extraction chain
    extraction_chain = create_structured_output_chain(EnToKoNameEvaluation, llm, prompt)

    # Build the complete evaluation function
    def evaluate_en_to_ko(name: str):
        # Get the evaluation directly using the structured output chain
        try:
            result = extraction_chain.invoke({"name": name})
            return result
        except Exception as e:
            print(f"Error extracting structured data: {e}")
            # Fallback to text output if structured extraction fails
            evaluation_text = (prompt | llm | StrOutputParser()).invoke({"name": name})

            # Create a minimal result with the text
            return {
                "name": name,
                "korean_notation": "",
                "verification_process": {},
                "verification_sources": [],
                "compliant": False,
                "overall_score": 0,
                "notes": f"Error in structured extraction. Raw evaluation:\n{evaluation_text}",
            }

    return evaluate_en_to_ko


def evaluate_english_name(name: str, check_teamwork: bool = True) -> Dict[str, Any]:
    """
    Evaluate an English name for Korean notation.

    Args:
        name: The English name to evaluate
        check_teamwork: Whether to check Teamwork for previous translations

    Returns:
        Dictionary with evaluation results
    """
    # Initialize the OpenAI model
    model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")
    temperature = float(os.environ.get("OPENAI_TEMPERATURE", "0"))
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)

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
                    for eval in teamwork_verification["previous_evaluations"][
                        :3
                    ]:  # Limit to first 3
                        teamwork_info += f"  * {eval['title']} ({eval['created_at']})\n"

                # Add previous translations if found
                if teamwork_verification["previous_translations"]:
                    teamwork_info += f"- Found {len(teamwork_verification['previous_translations'])} previous translations in Teamwork\n"
                    for trans in teamwork_verification["previous_translations"][
                        :3
                    ]:  # Limit to first 3
                        teamwork_info += (
                            f"  * {trans['title']} ({trans['created_at']})\n"
                        )

                teamwork_info += f"- Verification status: {teamwork_verification['verification_status']}\n"
            else:
                teamwork_info = "TEAMWORK VERIFICATION RESULTS:\n- No previous records found in Teamwork\n"
        except Exception as e:
            teamwork_info = f"TEAMWORK VERIFICATION ERROR: {str(e)}\n"

    # Create the prompt template based on CF guidelines
    prompt = ChatPromptTemplate.from_template(
        """
    You are a Korean terminology specialist following the CF Terminology Management Manual.
    
    Evaluate the following English name for proper Korean notation:
    
    Name: {name}
    
    {teamwork_info}
    
    CF GUIDELINES FOR ENGLISH TO KOREAN NAME VERIFICATION:
    
    1. Internal Data Verification:
       - Check CF's own Termbase in SmartCAT Glossary
       - Verify with CF Teamwork record (post-2019 only): https://cultureflipper.teamwork.com
       - Check NFLX Lucid TM for notation history: https://localization-lucid.netflix.com/translation/search/?targetLocales=ko
       - TM Depository: https://docs.google.com/spreadsheets/d/1A8QpynPg5rNJR2MPkPeyw7WDf5x-NiZauU5b2mN6NE0/edit#gid=0
       - CF Terminology Depository: https://docs.google.com/spreadsheets/d/1bktPGup6cixITi35RBtgZY41pGqguu93m8noGXQ5ffk/edit#gid=670266495&range=AA38
       - Follow verified notations from previous projects
    
    2. Netflix-Specific Resources:
       - NF Tiloc: https://localization-lucid.netflix.com/titles/search?cl=1
       - NF Original Credits (NOC): https://docs.google.com/spreadsheets/d/1AxXZfMZGmGMryaH4waVMvKoYps59owtyuBuTI2T_8pQ/edit#gid=554552356
       - NF Korean Ratings Trackers: https://docs.google.com/spreadsheets/d/1i7RFBjbHaqsLC4LZz50kdvp1bcWbO4eOILc1kml6Gcc/edit#gid=1190947542
       - NF LRT: https://lrt.netflix.net/
    
    3. External Data Verification:
       - For foreign author names, check Korean translated books
       - Verify with National Institute of Korean Language (NIKL): https://kornorms.korean.go.kr//example/exampleList.do?regltn_code=0003
       - Check multiple sources for consistency
       - For celebrity names, check official Korean notation in media
       - Cambridge Dictionary: https://dictionary.cambridge.org/dictionary/english/
       - YouTube (for pronunciation verification): https://www.youtube.com/
       - Look for consensus on Korean news sites
    
    4. Special Rules:
       - Distinguish between real person names and character names
       - Use different rules for stage names and group names
       - Consider phonetic challenges specific to Korean
       - Real person names may need stricter adherence to standards
       - Character names may have established translations from books/media
    
    Based on these guidelines, please:
    
    1. Recommend the proper Korean notation (Hangul) for this name
    2. Explain the verification process used
    3. Rate compliance with CF guidelines (0-100)
    4. Provide justification for your recommendation
    5. List sources that should be consulted
    """
    )

    # Get the evaluation from the model
    response = prompt.invoke(
        {"name": name, "teamwork_info": teamwork_info}
    ).to_messages()

    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"name": name, "teamwork_info": teamwork_info})

    # Parse important information from the result
    lines = result.split("\n")

    # Extract key information
    korean_notation = ""
    compliance_score = 0
    compliant = False
    verification_process = []
    recommendations = []
    sources = []

    for i, line in enumerate(lines):
        line = line.strip()

        # Extract Korean notation (usually near the beginning)
        if (
            "한글 표기" in line
            or "Korean notation" in line
            or "recommended notation" in line
            or "Hangul" in line
        ) and not korean_notation:
            # Try to extract the actual Hangul from this line or next line
            if ":" in line:
                korean_notation = line.split(":", 1)[1].strip()
            elif i + 1 < len(lines) and any(
                char for char in lines[i + 1] if "\uac00" <= char <= "\ud7a3"
            ):
                korean_notation = lines[i + 1].strip()

        # Extract compliance score
        if ("compliance" in line.lower() or "score" in line.lower()) and any(
            c.isdigit() for c in line
        ):
            for word in line.split():
                if word.isdigit() or (word.endswith("%") and word[:-1].isdigit()):
                    score_str = word.rstrip("%")
                    try:
                        compliance_score = int(score_str)
                        compliant = compliance_score >= 80  # CF standard
                        break
                    except ValueError:
                        pass

        # Extract verification process
        if "verification process" in line.lower() or "verified using" in line.lower():
            verification_process = []
            j = i + 1
            while (
                j < len(lines)
                and lines[j].strip()
                and not any(
                    k in lines[j].lower()
                    for k in ["justification", "recommendation", "sources"]
                )
            ):
                if lines[j].strip().startswith("-") or lines[j].strip().startswith("*"):
                    verification_process.append(lines[j].strip())
                j += 1

        # Extract recommendations
        if "recommend" in line.lower() or "suggestion" in line.lower():
            recommendations = []
            j = i + 1
            while (
                j < len(lines)
                and lines[j].strip()
                and not any(k in lines[j].lower() for k in ["sources", "verification"])
            ):
                if lines[j].strip().startswith("-") or lines[j].strip().startswith("*"):
                    recommendations.append(lines[j].strip())
                j += 1

        # Extract sources
        if "sources" in line.lower() or "references" in line.lower():
            sources = []
            j = i + 1
            while j < len(lines) and lines[j].strip():
                if lines[j].strip().startswith("-") or lines[j].strip().startswith("*"):
                    sources.append(lines[j].strip())
                j += 1

    # Construct the result dictionary
    evaluation_result = {
        "name": name,
        "korean_notation": korean_notation,
        "overall_score": compliance_score,
        "compliant": compliant,
        "verification_process": verification_process,
        "recommendations": recommendations,
        "sources": sources,
        "full_evaluation": result,
    }

    # Add Teamwork verification data if available
    if teamwork_verification:
        evaluation_result["teamwork_verification"] = teamwork_verification

    return evaluation_result


def evaluate_english_names(names: List[str], check_teamwork: bool = True) -> List[Dict]:
    """
    Evaluate multiple English names for proper Korean notation.

    Args:
        names: List of English names to evaluate
        check_teamwork: Whether to check Teamwork for previous translations

    Returns:
        List of dictionaries with evaluation results
    """
    results = []

    for name in names:
        print(f"Evaluating English name: {name}")
        try:
            result = evaluate_english_name(name, check_teamwork)
            results.append(result)
        except Exception as e:
            print(f"Error evaluating {name}: {e}")
            results.append(
                {"name": name, "error": str(e), "compliant": False, "overall_score": 0}
            )

    # Save results to file
    os.makedirs("reports", exist_ok=True)
    with open(
        "reports/english_name_evaluation_results.json", "w", encoding="utf-8"
    ) as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results


def generate_termbase_entries(
    results: List[Dict], output_file: str = "reports/en_ko_termbase_entries.txt"
):
    """
    Generates recommended Termbase entries from evaluation results.

    Args:
        results: List of evaluation results
        output_file: Path to the output text file
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# CF Terminology Management - Recommended Termbase Entries\n\n")

        for result in results:
            name = result.get("name", "Unknown")
            korean_notation = result.get("korean_notation", "")

            f.write(f"## {name} → {korean_notation}\n\n")

            # Add termbase entry details if available
            termbase_entry = result.get("termbase_entry", {})
            if termbase_entry:
                f.write("### Recommended Termbase Entry\n\n")
                for key, value in termbase_entry.items():
                    f.write(f"- **{key}**: {value}\n")
                f.write("\n")

            # Add verification sources
            verification_sources = result.get("verification_sources", [])
            if verification_sources:
                f.write("### Verification Sources\n\n")
                for source in verification_sources:
                    f.write(f"- {source}\n")
                f.write("\n")

            # Add pronunciation guide if available
            pronunciation = result.get("pronunciation_guide", "")
            if pronunciation:
                f.write(f"### Pronunciation Guide\n\n{pronunciation}\n\n")

            # Add reference links if available
            reference_links = result.get("reference_links", [])
            if reference_links:
                f.write("### Reference Links\n\n")
                for link in reference_links:
                    f.write(f"- {link}\n")
                f.write("\n")

            f.write("---\n\n")

    print(f"Termbase entries generated: {output_file}")


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


if __name__ == "__main__":
    # Sample English names for testing
    test_names = [
        "John Smith",
        "Emma Watson",
        "Robert Downey Jr.",
        "Jennifer Lawrence",
        "Chris Hemsworth",
    ]

    print("Starting English to Korean name evaluation...")
    results = evaluate_english_names(
        test_names, check_teamwork=False
    )  # Change to not check Teamwork by default

    # Generate Termbase entries
    generate_termbase_entries(results)

    print("\nEvaluation complete!")
    print("Results saved to: reports/english_name_evaluation_results.json")
    print("Termbase entries saved to: reports/en_ko_termbase_entries.txt")
