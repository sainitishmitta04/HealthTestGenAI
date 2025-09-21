# Healthcare TestGen AI

An AI-powered system that automatically converts healthcare software requirements into compliant, traceable test cases integrated with enterprise toolchains.

## Features

- **Automated Test Case Generation**: Convert natural language and structured specifications into test cases
- **Multi-format Support**: PDF, Word, XML, Markdown, and more
- **Healthcare Compliance**: FDA, IEC 62304, ISO 9001, ISO 13485, ISO 27001 standards
- **Enterprise Integration**: Jira, Polarion, Azure DevOps integration
- **GDPR Compliance**: Ready for GDPR-compliant Proof of Concepts
- **No-code Test Authoring**: Create test cases without scripting
- **API Testing**: OpenAPI/Swagger integration for API testing
- **Traceability**: Full requirement-to-test traceability

## Tech Stack

- **AI**: Google Gemini API
- **Backend**: Python 3.11.13
- **File Processing**: Various Python libraries
- **Database**: SQLite (for demo purposes)
- **Integration**: REST APIs for enterprise tools

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`
4. Run the application: `streamlit run app/main.py`

## Configuration

Create a `.env` file with your Gemini API key:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

## Project Structure

```
healthcare-testgen/
├── app/
│   ├── main.py                 # Main application
│   ├── components/             # UI components
│   └── pages/                 # Multi-page application
├── core/
│   ├── ai_integration.py      # Gemini AI integration
│   ├── file_processing.py     # File format handling
│   ├── compliance_checker.py  # Healthcare compliance
│   ├── testcase_generator.py  # Test case generation logic
│   └── integrations/          # Enterprise tool integrations
├── utils/
│   ├── config.py              # Configuration management
│   ├── database.py           # Database operations
│   └── helpers.py           # Utility functions
├── data/
│   └── templates/           # Test case templates
├── tests/                  # Test files
├── requirements.txt       # Python dependencies
└── .env.example          # Environment template