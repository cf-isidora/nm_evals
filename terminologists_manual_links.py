#!/usr/bin/env python
"""
Verification Resources for CF Name Evaluation System.

This module centralizes all verification resources referenced in the CF Terminology
Management Manual into a single location. It provides organized access to the various
resources that terminologists need to consult when evaluating proper names for
Korean-English translation.

The module includes:
- Comprehensive lists of internal verification sources
- Netflix-specific verification resources
- External verification sources for names
- Specialized resources for Korean name romanization
- Resources for verification of different name types (people, places, organizations)
- Function to display resources in a formatted manner

Maintaining this central registry of resources ensures that all parts of the name
evaluation system reference consistent and up-to-date verification sources, and
makes it easy for terminologists to discover and access the appropriate resources
for their verification tasks.
"""

import os
from typing import Dict, List, Optional

# Path to data directory containing resources
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Path to manual files
MANUAL_FILE_PATH = os.path.join(
    DATA_DIR, "CF Terminology Management Manual_en excerpts (translated by ChatGPT).txt"
)
MANUAL_LINKS_PATH = os.path.join(DATA_DIR, "terminologists_manual_links.txt")

# Internal CF Resources
CF_INTERNAL_RESOURCES = {
    "teamwork": {
        "name": "CF Teamwork",
        "url": "https://cultureflipper.teamwork.com",
        "description": "Check existing submissions in CF Teamwork (do not trust records before 2019)",
    },
    "terminology_depository": {
        "name": "CF Terminology Depository",
        "local_file": os.path.join(DATA_DIR, "Terminologists' Depository.xlsx"),
        "url": "https://docs.google.com/spreadsheets/d/1bktPGup6cixITi35RBtgZY41pGqguu93m8noGXQ5ffk/edit#gid=670266495&range=AA38",
        "description": "CF Terminology depository for name verification",
    },
    "tm_depository": {
        "name": "TM Depository",
        "local_file": os.path.join(DATA_DIR, "TM Training Landscape.xlsx"),
        "url": "https://docs.google.com/spreadsheets/d/1A8QpynPg5rNJR2MPkPeyw7WDf5x-NiZauU5b2mN6NE0/edit#gid=0",
        "description": "Internal terminology management depository",
    },
    "tm_job_organizer": {
        "name": "TM Job Organizer",
        "local_file": os.path.join(DATA_DIR, "TM Job Organizer.xlsx"),
        "url": "https://docs.google.com/spreadsheets/d/1Ld3NOzPPua_XcodniDn2UaMr_ln_aDITgvdf4YHXizI/edit#gid=1174152703",
        "description": "Terminology job organization spreadsheet",
    },
    "tm_cellar": {
        "name": "TM Cellar",
        "url": "https://docs.google.com/spreadsheets/d/1z_DEkSTvmsgDMzWVUh2oZoBFVKQaGSKDpVw68vmHR3o/edit#gid=0",
        "description": "Terminology archive spreadsheet",
    },
    "cf_master_marketing": {
        "name": "CF Master Marketing Translations",
        "local_file": os.path.join(
            DATA_DIR, "MAIN MARKETING TRANSLATIONS (MMT - Source of Truth).xlsx"
        ),
        "url": "https://docs.google.com/spreadsheets/d/1ipJ3nxd2HAd16RGK6tIZLq3oVMXy9N5OFMAIhbGNtZA/edit#gid=678337773",
        "description": "CF Master Marketing Translations spreadsheet",
    },
    "cf_metadata": {
        "name": "CF Metadata – Container Word Translations",
        "url": "https://docs.google.com/spreadsheets/d/1ipJ3nxd2HAd16RGK6tIZLq3oVMXy9N5OFMAIhbGNtZA/edit#gid=0",
        "description": "CF Metadata: Container Word Translations",
    },
}

# Netflix-Specific Resources
NETFLIX_RESOURCES = {
    "lucid_tm": {
        "name": "Lucid TM",
        "url": "https://localization-lucid.netflix.com/translation/search/?targetLocales=ko",
        "description": "NFLX Lucid TM Check for notation history",
    },
    "tiloc": {
        "name": "NF Tiloc",
        "url": "https://localization-lucid.netflix.com/titles/search?cl=1",
        "description": "NF title localization resource",
    },
    "lrt": {
        "name": "NF LRT",
        "url": "https://lrt.netflix.net/",
        "description": "Netflix Translation Resource Tool",
    },
    "lego": {
        "name": "LEGO subtitle search page",
        "url": "https://lego.netflix.com/#",
        "description": "Netflix subtitle search resource",
    },
    "nf_service": {
        "name": "NF Service Page",
        "url": "https://www.netflix.com/browse",
        "description": "Netflix streaming service",
    },
    "noc": {
        "name": "NF Original Credits (NOC)",
        "url": "https://docs.google.com/spreadsheets/d/1AxXZfMZGmGMryaH4waVMvKoYps59owtyuBuTI2T_8pQ/edit#gid=554552356",
        "description": "Netflix Original Credits resource",
    },
    "mmt": {
        "name": "NF Master Marketing Translations (MMT)",
        "url": "https://docs.google.com/spreadsheets/d/1oNJQBbfTCGBeziKjYftn-J5JU2KHFU7_CThZryQ_llg/edit?ts=5c1a9b19#gid=0",
        "description": "Netflix Master Marketing Translations",
    },
    "ratings_trackers": {
        "name": "NF Korean Ratings Trackers",
        "url": "https://docs.google.com/spreadsheets/d/1i7RFBjbHaqsLC4LZz50kdvp1bcWbO4eOILc1kml6Gcc/edit#gid=1190947542",
        "description": "Netflix Korean ratings tracking spreadsheet",
    },
    "cognito_form": {
        "name": "NF Cognito Form",
        "url": "https://netflix.jotform.com/200236257901044",
        "description": "Netflix error reporting form",
    },
}

# External Resource Links
EXTERNAL_RESOURCES = {
    "nikl": {
        "name": "NIKL (National Institute of Korean Language)",
        "url": "https://kornorms.korean.go.kr/",
        "description": "Official Korean language authority",
    },
    "nikl_examples": {
        "name": "NIKL Example Search",
        "url": "https://kornorms.korean.go.kr//example/exampleList.do?regltn_code=0003",
        "description": "Example Search on NIKL Korean Language Standards page",
    },
    "nikl_romanization": {
        "name": "NIKL Romanization Rules",
        "url": "https://kornorms.korean.go.kr//regltn/regltnView.do?regltn_code=0004#a",
        "description": "Official Korean Romanization Rules",
    },
    "romanization_converter": {
        "name": "Romanization Converter",
        "url": "http://roman.cs.pusan.ac.kr/",
        "description": "Tool for converting between Korean and romanized text",
    },
    "kofic_kobis": {
        "name": "KOFIC KOBIS",
        "url": "https://www.kobis.or.kr/kobis/business/main/main.do",
        "description": "Korean Film Council box office information system",
    },
    "kofic_kobiz": {
        "name": "KOFIC KoBiz",
        "url": "http://www.koreanfilm.or.kr/eng/main/main.jsp",
        "description": "Korean Film Council business portal",
    },
    "kmdb": {
        "name": "KMDb",
        "url": "https://www.kmdb.or.kr/main",
        "description": "Korean Movie Database",
    },
    "kmrb": {
        "name": "KMRB (Korea Media Rating Board)",
        "url": "https://www.kmrb.or.kr/kor/Main.do",
        "description": "Official Korean media rating authority",
    },
    "cambridge_dictionary": {
        "name": "Cambridge Dictionary",
        "url": "https://dictionary.cambridge.org/dictionary/english/",
        "description": "English language reference",
    },
    "playdb": {
        "name": "PlayDB",
        "url": "http://www.playdb.co.kr/Index.asp",
        "description": "Korean performing arts database",
    },
    "grac": {
        "name": "GRAC (Game Rating Committee)",
        "url": "https://www.grac.or.kr/",
        "description": "Game Rating and Administration Committee",
    },
    "national_library": {
        "name": "National Library of Korea",
        "url": "https://www.nl.go.kr/",
        "description": "National Library of Korea",
    },
    "imdb": {
        "name": "IMDb",
        "url": "https://www.imdb.com/",
        "description": "Internet Movie Database",
    },
    "youtube": {
        "name": "YouTube",
        "url": "https://www.youtube.com/",
        "description": "For pronunciation verification",
    },
}

# Combine all resources
ALL_RESOURCES = {**CF_INTERNAL_RESOURCES, **NETFLIX_RESOURCES, **EXTERNAL_RESOURCES}


def get_resources_by_category(category: str) -> Dict[str, Dict]:
    """
    Get resources filtered by category.

    Args:
        category: Category of resources ("internal", "netflix", "external", "all")

    Returns:
        Dictionary of resources in that category
    """
    if category.lower() == "internal":
        return CF_INTERNAL_RESOURCES
    elif category.lower() == "netflix":
        return NETFLIX_RESOURCES
    elif category.lower() == "external":
        return EXTERNAL_RESOURCES
    elif category.lower() == "all":
        return ALL_RESOURCES
    else:
        raise ValueError(f"Unknown category: {category}")


def get_resources_for_direction(direction: str) -> List[Dict]:
    """
    Get resources organized in priority order for a specific translation direction.

    Args:
        direction: Translation direction ("KO-EN" or "EN-KO")

    Returns:
        List of resource dictionaries in priority order
    """
    resources = []

    if direction.upper() == "KO-EN":
        # Korean to English verification resources in priority order
        priorities = [
            # Internal data verification
            "teamwork",
            "terminology_depository",
            "tm_depository",
            "lucid_tm",
            # Netflix resources
            "noc",
            "mmt",
            "ratings_trackers",
            "lrt",
            "lego",
            # External verification
            "nikl_romanization",
            "kofic_kobiz",
            "romanization_converter",
            "kmdb",
            "youtube",
            "imdb",
        ]
    elif direction.upper() == "EN-KO":
        # English to Korean verification resources in priority order
        priorities = [
            # Internal data verification
            "teamwork",
            "terminology_depository",
            "tm_depository",
            "lucid_tm",
            # Netflix resources
            "tiloc",
            "noc",
            "mmt",
            "ratings_trackers",
            "nf_service",
            "lrt",
            # External verification
            "nikl",
            "nikl_examples",
            "kmrb",
            "cambridge_dictionary",
            "youtube",
            "imdb",
        ]
    else:
        raise ValueError(f"Unknown direction: {direction}")

    # Add resources in priority order
    for key in priorities:
        if key in ALL_RESOURCES:
            resources.append(ALL_RESOURCES[key])

    return resources


def get_resource_url(resource_key: str) -> str:
    """
    Get URL for a specific resource by key.

    Args:
        resource_key: Key identifier for the resource

    Returns:
        URL string for the resource
    """
    resource = ALL_RESOURCES.get(resource_key)
    if resource:
        return resource["url"]
    else:
        raise ValueError(f"Unknown resource key: {resource_key}")


def get_verification_process_text(direction: str) -> str:
    """
    Get formatted text describing the verification process for a direction.

    Args:
        direction: Translation direction ("KO-EN" or "EN-KO")

    Returns:
        Formatted text with verification steps and resources
    """
    resources = get_resources_for_direction(direction)

    if direction.upper() == "KO-EN":
        text = "VERIFICATION PROCESS FOR KOREAN TO ENGLISH NAMES:\n\n"
    else:
        text = "VERIFICATION PROCESS FOR ENGLISH TO KOREAN NAMES:\n\n"

    # Add Internal Data Verification section
    text += "1. Internal Data Verification:\n"
    for resource in resources[:5]:  # First 5 resources are internal
        text += f"   - {resource['name']}: {resource['url']}\n"
        if resource.get("description"):
            text += f"     ({resource['description']})\n"

    # Add Netflix Resources section
    text += "\n2. Netflix-Specific Resources:\n"
    for resource in resources[5:10]:  # Next 5 resources are Netflix-specific
        text += f"   - {resource['name']}: {resource['url']}\n"
        if resource.get("description"):
            text += f"     ({resource['description']})\n"

    # Add External Verification section
    text += "\n3. External Data Verification:\n"
    for resource in resources[10:]:  # Remaining resources are external
        text += f"   - {resource['name']}: {resource['url']}\n"
        if resource.get("description"):
            text += f"     ({resource['description']})\n"

    return text


def load_manual_content() -> str:
    """
    Load the content of the CF Terminology Management Manual from the data directory.

    Returns:
        The content of the manual as a string
    """
    try:
        with open(MANUAL_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not load manual content: {e}")
        return "Manual content could not be loaded."


def load_manual_links() -> List[str]:
    """
    Load the links mentioned in the Terminologists' Manual.

    Returns:
        List of links from the manual
    """
    try:
        with open(MANUAL_LINKS_PATH, "r", encoding="utf-8") as f:
            links = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
            return links
    except Exception as e:
        print(f"Warning: Could not load manual links: {e}")
        return []


def get_local_file_path(resource_key: str) -> Optional[str]:
    """
    Get the local file path for a resource if available.

    Args:
        resource_key: Key identifier for the resource

    Returns:
        Local file path if available, None otherwise
    """
    resource = ALL_RESOURCES.get(resource_key)
    if resource and "local_file" in resource:
        return resource["local_file"]
    return None


if __name__ == "__main__":
    # Example usage
    print("Korean to English Verification Process:")
    print(get_verification_process_text("KO-EN"))
    print("\n")
    print("English to Korean Verification Process:")
    print(get_verification_process_text("EN-KO"))
