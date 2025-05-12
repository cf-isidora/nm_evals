# CF Name Evaluation System

This system evaluates proper name handling according to the CF Terminology Management Manual. It analyzes names in Korean-English translation contexts and provides detailed compliance reports.

## Features

- **Korean-to-English Name Evaluation**: Evaluate Korean names for proper English notation. This process takes Korean names as input and evaluates how they should be properly written in English (romanization). It follows specific rules for hyphenation, capitalization, and romanization according to the CF Terminology Management Manual.
- **English-to-Korean Name Evaluation**: Evaluate English names and recommend Korean notation. This is the reverse process, where English names are converted to proper Korean notation (Hangul). It analyzes the English name's pronunciation and determines the most appropriate Korean characters to represent the name according to Korean linguistic conventions.
- **Bidirectional Real Person Name Verification**: Integrated verification for real person names in both directions. This specialized module implements stricter verification requirements for real persons' names compared to fictional characters or other proper nouns. It combines both Korean-to-English and English-to-Korean verification processes with enhanced requirements for phonetician review, mandatory hyphenation, expert validation, and specialized recording in termbase.
- **Verification Process Analysis**: Check compliance with the multi-step verification process. This evaluates how well the verification steps were followed, analyzing whether proper verification sources were consulted in the correct order and assigning compliance scores based on adherence to the required verification process.
- **HTML Report Generation**: Create visual reports showing evaluation results
- **Termbase Entry Generation**: Generate properly formatted entries for the terminology database
- **Language Auto-detection**: Automatically identify if a name is primarily Korean or English
- **LangSmith Integration**: Optional tracing and evaluation through LangSmith platform
- **Comprehensive Verification Resources**: Direct access to all required verification resources from the CF Terminology Manual
- **Local Resource Files**: Access to reference files in the data directory for offline verification
- **Teamwork Integration**: Verify names against previous translations in Teamwork and post evaluation results

## Directory Structure

- `name_eval_system.py`: Unified system that combines both directions with auto-detection. This script integrates all evaluation capabilities into a single interface, automatically detecting name languages and routing them to the appropriate evaluator.
- `korean_to_english_evaluator.py`: Dedicated module for evaluating Korean names for proper English notation according to specific rules for hyphenation, capitalization, and romanization.
- `english_to_korean_evaluator.py`: Specialized evaluator for converting English names to proper Korean notation (Hangul) using phonetic analysis and Korean linguistic conventions.
- `korean_name_evaluator.py`: Core evaluation engine that works with both translation directions. It implements comprehensive rules based on the CF Terminology Management Manual and produces detailed HTML reports.
- `real_person_name_verifier.py`: Integrated bidirectional verification for real person names. This module combines both Korean-to-English and English-to-Korean functionalities with enhanced requirements specific to real person names.
- `korean_name_cli.py`: Command-line interface for quick name evaluations. It provides direct access to core evaluation functionality with support for both individual and batch processing.
- `terminologists_manual_links.py`: Centralized access to all verification resources from the CF Terminology Management Manual. It manages verification process documentation and provides appropriate references for each direction.
- `teamwork_integration.py`: Teamwork API integration for verifying names against previous translations and posting evaluation results back to Teamwork projects.
- `data/`: Directory containing reference files and manual excerpts:
  - `CF Terminology Management Manual_en excerpts (translated by ChatGPT).txt`: Main manual content
  - `terminologists_manual_links.txt`: Links from the Terminologists' Manual
  - Various Excel files for terminology verification and reference
- `reports/`: Directory for output reports and evaluation results:
  - HTML reports with color-coded evaluations
  - JSON result files with detailed evaluation data
  - Termbase entry text files for both directions

## Installation

1. Clone this repository
   ```
   git clone https://github.com/cf-isidora/nm_evals.git
   cd nm_evals
   ```
2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up environment variables:

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Required for LLM access
OPENAI_API_KEY=sk-...

# LangSmith integration (optional)
LANGCHAIN_API_KEY=ls-...
LANGCHAIN_PROJECT=cf_name_evaluation
LANGCHAIN_TRACING=true

# Teamwork integration (optional)
TEAMWORK_API_KEY=tw1-...
TEAMWORK_DOMAIN=cultureflipper

# Optional: OpenAI model configuration
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.0
```

## Usage

### Basic Usage

```bash
# Comprehensive name evaluation with auto-detection
python name_eval_system.py --names "김지원" "John Smith" --auto-detect

# Evaluate Korean names for English notation using dedicated evaluator
python korean_to_english_evaluator.py --names "김지원" "박서준" "이종석"

# Evaluate Korean names using the CLI tool
python korean_name_cli.py --names "김지원" "박서준" "이종석" --direction KO-EN

# Evaluate English names and generate Korean notations
python english_to_korean_evaluator.py --names "John Smith" "Emma Watson"

# Verify real person names with specialized verification
python real_person_name_verifier.py --names "김지원" "John Smith" --auto-detect

# Display verification resources from the Terminologists' Manual
python name_eval_system.py --show-resources

# View available local resources in the data directory
python name_eval_system.py --show-local-resources

# Use only local resources for verification (offline mode)
python name_eval_system.py --names "김지원" "박서준" --local-only
```

### Advanced Usage

```bash
# Evaluate names from a file with specific direction
python name_eval_system.py --file names_list.txt --direction KO-EN --output-dir custom_reports

# Specialized real person name verification from file
python real_person_name_verifier.py --file celebrity_names.txt --auto-detect --verify-in-teamwork

# Batch processing with custom output
python korean_name_cli.py --file korean_names.txt --direction KO-EN --output custom_report.html

# Disable LangSmith tracing even if configured
python name_eval_system.py --names "김지원" "박서준" --disable-tracing

# Verify names in Teamwork (checks for previous translations)
python name_eval_system.py --names "김지원" "John Smith" --auto-detect --verify-in-teamwork

# Post evaluation results to Teamwork
python name_eval_system.py --names "김지원" "박서준" --post-to-teamwork --teamwork-project-id 123456

# Complete workflow with Teamwork integration
python name_eval_system.py --file names_list.txt --auto-detect --verify-in-teamwork --post-to-teamwork --teamwork-project-id 123456
```

## Real Person Name Verification

The system includes an integrated bidirectional verifier specifically for real person names, combining both Korean-to-English and English-to-Korean verification processes with enhanced rules specific to real people's names:

### Priority Verification Sources

1. KOFIC (Korean Film Council), including the KOFIC Integrated Ticketing System (Kobis)
2. Agency or Personal SNS, Official Media Channel Notations
3. Romanization Rules of Korean Language (NIKL's "Korean Romanization Rules")
4. Other References: Romanization Converter, Naver Labs Language Converter
5. For English to Korean: National Institute of Korean Language (NIKL) and translated publications

### Special Rules for Real Person Names

#### Korean to English Rules:
- Mandatory hyphenation between syllables (김지원 → Kim Ji-won)
- First letter capitalization with rest lowercase (unlike brand names)
- Strict NIKL romanization compliance
- Expert validation requirement for scores below 95
- If a North Korean name has spaces between syllables, replace spaces with hyphens, and lowercase first letter of second syllable
- For idol group/stage names in uppercase, capitalize first letter of each word, use lowercase for rest
- Animal names should be written without hyphens

#### English to Korean Rules:
- Phonetician review requirement for all real person names
- Kyonshik confirmation for Netflix-related projects 
- Recording of "HZ Original Notation" in the termbase
- Stricter transliteration standards than for fictional characters
- For newly confirmed real names (after 08/11/2020), confirm notation through Kyonshik for NF tasks
- For non-NF projects, confirm through Hazel (phonetician)

#### Getting Started with Real Person Verification
```bash
# Verify a mix of Korean and English real person names with auto-detection
python real_person_name_verifier.py --names "김지원,John Smith,박보검" --auto-detect

# Verify only Korean celebrity names for English notation
python real_person_name_verifier.py --names "김지원" "박서준" "이종석" --direction KO-EN

# Process celebrity names from a file with Teamwork integration
python real_person_name_verifier.py --file celebrity_names.txt --auto-detect --verify-in-teamwork
```

## Verification Resources

The system includes direct access to all verification resources from the CF Terminology Management Manual:

### Internal Resources
- CF Teamwork
- CF Terminology Depository (available locally in data/ directory)
- TM Depository (available locally in data/ directory)
- Terminology Management tools

### Netflix Resources
- Lucid TM
- NF Tiloc
- NF LRT
- LEGO subtitle search
- NF Service Page
- Various tracking spreadsheets (some available locally in data/ directory)

### External Resources
- NIKL (National Institute of Korean Language)
- KOFIC KoBiz
- Romanization resources
- Reference databases
- Media verification sources

To view all available resources with detailed links:
```bash
python name_eval_system.py --show-resources
```

## LangSmith Integration

The system optionally integrates with [LangSmith](https://smith.langchain.com/) for enhanced tracing, evaluation, and monitoring. If LangSmith is not available, the system will still work using fallback functions.

### Setup

1. Sign up for a LangSmith account at [smith.langchain.com](https://smith.langchain.com/)
2. Obtain your API key from the LangSmith dashboard
3. Add the API key to your `.env` file as `LANGCHAIN_API_KEY`
4. Tracing is automatically enabled when the API key is present

After running evaluations, you can view traces of each name evaluation process and analyze compliance scores and recommendations on the LangSmith dashboard.

## Teamwork Integration

The system integrates with [Teamwork](https://www.teamwork.com/) for enhanced name verification and evaluation tracking:

### Setup

1. Obtain your Teamwork API key from your profile page
2. Add the API key to your `.env` file as `TEAMWORK_API_KEY`
3. Verify your Teamwork domain (default is "cultureflipper") in your `.env` file as `TEAMWORK_DOMAIN`

### Using Teamwork Integration

The following features are available when Teamwork integration is enabled:

1. **Name Verification**: Check if a name has been previously evaluated or used in Teamwork tasks
   ```
   python name_eval_system.py --names "김지원" --verify-in-teamwork
   ```

2. **Posting Results**: Create tasks with evaluation results in a Teamwork project
   ```
   python name_eval_system.py --names "김지원" --post-to-teamwork --teamwork-project-id YOUR_PROJECT_ID
   ```

This will create a task in the specified Teamwork project containing the evaluation results for each name, including:
- Compliance status
- Overall score
- Individual rule scores
- Recommendations

## Output Files

The system generates several output files in the `reports/` directory:

- **HTML Reports**: Visual summaries of name evaluations with color-coded scores
- **JSON Results**: Structured data containing full evaluation details
- **Termbase Entries**: Markdown-formatted files with recommended database entries for each direction:
  - `ko_en_termbase_entries.txt`: Korean to English termbase entries
  - `en_ko_termbase_entries.txt`: English to Korean termbase entries

## Using Local Resources

The system supports using local reference files stored in the `data/` directory for offline verification when internet access is limited or when you need to work with specific versions of reference materials.

### Available Local Resources

The following resources can be accessed locally when properly configured:

- **Terminology Management Manual**: Core guidelines for name verification
- **Terminologists' Depository**: Excel file containing verified terminology entries
- **TM Training Landscape**: Training and reference material for terminology management
- **Master Marketing Translations**: Source of truth for marketing terminology
- **TM Job Organizer**: Excel file tracking terminology verification jobs
- **Task Tracker**: Detailed task tracking with notation history

### Options for Local Resources

```bash
# View available local resources in your data directory
python name_eval_system.py --show-local-resources

# Run in local-only mode (will only use resources available in data directory)
python name_eval_system.py --names "김지원" "박서준" --local-only

# Combine with other options
python name_eval_system.py --file names.txt --direction KO-EN --local-only
```

## Recent Updates

- **Integrated Real Person Name Verifier**: Added new module `real_person_name_verifier.py` that combines both Korean-to-English and English-to-Korean name evaluation with specialized rules for real person names
- **Enhanced Directory Structure**: Organized output files into the `reports/` directory
- **Improved Teamwork Integration**: Fixed authentication issues and added better error handling
- **LangSmith Integration**: Made LangSmith integration optional with proper fallbacks

## Contributing

Contributions to the CF Name Evaluation System are welcome. Here's how you can contribute:

1. Fork the repository on GitHub
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Submit a pull request with a clear description of the changes

### Guidelines

- Follow the existing code style and conventions
- Add tests for new features
- Update documentation to reflect your changes
- Ensure your changes don't break existing functionality

## License

This project is licensed for internal use only and is not available for public distribution.