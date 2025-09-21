import streamlit as st
import os
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Import custom modules
from core.ai_integration import GeminiAIClient
from core.file_processing import FileProcessor
from core.compliance_checker import ComplianceChecker
from core.testcase_generator import TestCaseGenerator
from utils.config import load_config, save_config
from utils.database import DatabaseManager

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Healthcare TestGen AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'gemini_client' not in st.session_state:
    st.session_state.gemini_client = None
if 'file_processor' not in st.session_state:
    st.session_state.file_processor = FileProcessor()
if 'compliance_checker' not in st.session_state:
    st.session_state.compliance_checker = ComplianceChecker()
if 'testcase_generator' not in st.session_state:
    st.session_state.testcase_generator = TestCaseGenerator()
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()

def initialize_gemini_client():
    """Initialize Gemini AI client with API key"""
    api_key = os.getenv('GEMINI_API_KEY') or st.session_state.get('gemini_api_key')
    if not api_key:
        st.error("Gemini API key not found. Please configure it in the settings.")
        return None
    try:
        return GeminiAIClient(api_key)
    except Exception as e:
        st.error(f"Failed to initialize Gemini client: {e}")
        return None

def main():
    # Sidebar navigation
    st.sidebar.title("🏥 Healthcare TestGen AI")
    st.sidebar.markdown("---")
    app_mode = st.sidebar.radio(
        "Navigation",
        ["🏠 Dashboard", "📁 Upload Requirements", "⚙️ Generate Test Cases",
         "🛡️ Compliance Check", "🔗 Integrations", "⚙️ Settings"]
    )

    # API Key configuration
    st.sidebar.markdown("---")
    st.sidebar.subheader("API Configuration")
    gemini_api_key = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv('GEMINI_API_KEY', ''),
        help="Enter your Google Gemini API key"
    )
    if gemini_api_key:
        st.session_state.gemini_api_key = gemini_api_key
        st.session_state.gemini_client = initialize_gemini_client()

    # Main content
    if app_mode == "🏠 Dashboard":
        show_dashboard()
    elif app_mode == "📁 Upload Requirements":
        upload_requirements()
    elif app_mode == "⚙️ Generate Test Cases":
        generate_test_cases()
    elif app_mode == "🛡️ Compliance Check":
        compliance_check()
    elif app_mode == "🔗 Integrations":
        show_integrations()
    elif app_mode == "⚙️ Settings":
        show_settings()

def show_dashboard():
    st.title("🏠 Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Test Cases", len(st.session_state.get('generated_test_cases', [])))
    with col2:
        overall_score = st.session_state.get('compliance_results', {}).get('overall_score', 0)
        st.metric("Compliance Score", f"{overall_score}%")
    with col3:
        st.metric("Files Processed", 1 if 'uploaded_file_name' in st.session_state else 0)
    
    st.markdown("---")
    st.subheader("Recent Activity")
    st.info("No recent activity yet. Upload requirements to get started.")
    
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📁 Upload New Requirements", use_container_width=True):
            st.session_state.navigation = "📁 Upload Requirements"
            st.rerun()
    with col2:
        if st.button("⚙️ Generate Test Cases", use_container_width=True):
            st.session_state.navigation = "⚙️ Generate Test Cases"
            st.rerun()
    with col3:
        if st.button("🛡️ Check Compliance", use_container_width=True):
            st.session_state.navigation = "🛡️ Compliance Check"
            st.rerun()

def upload_requirements():
    st.title("📁 Upload Requirements")
    st.info("Supported formats: PDF, DOCX, XML, JSON, Markdown, Text")
    uploaded_file = st.file_uploader(
        "Choose a requirements file",
        type=['pdf', 'docx', 'xml', 'json', 'md', 'txt']
    )
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            file_path = tmp_file.name
        try:
            content = st.session_state.file_processor.process_file(file_path)
            st.success("✅ File uploaded successfully!")
            with st.expander("📄 File Content Preview"):
                st.text_area("Extracted Content", content, height=200)
            st.session_state.uploaded_file_content = content
            st.session_state.uploaded_file_name = uploaded_file.name
            if st.button("⚡ Generate Test Cases Now"):
                st.session_state.navigation = "⚙️ Generate Test Cases"
                st.rerun()
        except Exception as e:
            st.error(f"Error processing file: {e}")
        finally:
            os.unlink(file_path)

def generate_test_cases():
    st.title("⚙️ Generate Test Cases")
    if 'uploaded_file_content' not in st.session_state:
        st.warning("Please upload a requirements file first.")
        return
    requirements_content = st.text_area(
        "Edit requirements if needed:",
        st.session_state.uploaded_file_content,
        height=150
    )
    st.subheader("Generation Options")
    col1, col2 = st.columns(2)
    with col1:
        test_case_format = st.selectbox("Output Format", ["JSON", "XML", "Markdown", "CSV", "Excel"])
        priority_level = st.select_slider("Test Priority", options=["Low", "Medium", "High", "Critical"])
    with col2:
        include_compliance = st.checkbox("Include Compliance Checks", value=True)
        generate_test_data = st.checkbox("Generate Test Data", value=True)
    with st.expander("Advanced Options"):
        custom_prompt = st.text_area(
            "Custom Prompt",
            "Generate comprehensive test cases for healthcare software including test steps, expected results, and compliance considerations.",
            help="Customize the AI prompt for test case generation"
        )
    if st.button("🚀 Generate Test Cases", type="primary"):
        if not st.session_state.gemini_client:
            st.error("Gemini AI client not initialized. Please check API key in settings.")
            return
        with st.spinner("Generating test cases..."):
            try:
                test_cases = st.session_state.testcase_generator.generate_test_cases(
                    requirements_content,
                    st.session_state.gemini_client,
                    custom_prompt=custom_prompt,
                    include_compliance=include_compliance
                )
                st.session_state.generated_test_cases = test_cases
                st.success("✅ Test cases generated successfully!")
                display_test_cases(test_cases)
                st.subheader("Export Options")
                export_format = st.selectbox("Export as", ["JSON", "XML", "CSV", "Excel"])
                if st.button(f"💾 Export as {export_format}"):
                    export_test_cases(test_cases, export_format)
            except Exception as e:
                st.error(f"Error generating test cases: {e}")

def display_test_cases(test_cases):
    st.subheader("Generated Test Cases")
    if isinstance(test_cases, list):
        for i, test_case in enumerate(test_cases, 1):
            with st.expander(f"Test Case #{i}: {test_case.get('title', 'Untitled')}"):
                st.write(f"**ID:** {test_case.get('id', 'N/A')}")
                st.write(f"**Description:** {test_case.get('description', 'No description')}")
                st.write(f"**Priority:** {test_case.get('priority', 'Medium')}")
                if 'steps' in test_case:
                    st.write("**Test Steps:**")
                    for j, step in enumerate(test_case['steps'], 1):
                        st.write(f"{j}. {step}")
                if 'expected_results' in test_case:
                    st.write("**Expected Results:**")
                    st.write(test_case['expected_results'])
                if 'compliance_checks' in test_case:
                    st.write("**Compliance Checks:**")
                    for check in test_case['compliance_checks']:
                        status = "✅" if check.get('passed', False) else "❌"
                        st.write(f"{status} {check.get('standard', 'Unknown')}: {check.get('requirement', '')}")

def export_test_cases(test_cases, format_type):
    st.info(f"Export functionality for {format_type} would be implemented here.")

def compliance_check():
    st.title("🛡️ Compliance Check")
    if 'generated_test_cases' not in st.session_state:
        st.warning("No test cases available for compliance check. Generate test cases first.")
        return
    st.subheader("Compliance Standards")
    standards = st.multiselect(
        "Select standards to check:",
        ["FDA", "IEC 62304", "ISO 9001", "ISO 13485", "ISO 27001", "GDPR"],
        default=["FDA", "ISO 13485"]
    )
    if st.button("🔍 Run Compliance Check", type="primary"):
        with st.spinner("Checking compliance..."):
            try:
                compliance_results = st.session_state.compliance_checker.check_compliance(
                    st.session_state.generated_test_cases,
                    standards
                )
                st.session_state.compliance_results = compliance_results
                display_compliance_results(compliance_results)
            except Exception as e:
                st.error(f"Error during compliance check: {e}")

def display_compliance_results(results):
    st.subheader("Compliance Check Results")
    if not results:
        st.warning("No compliance results to display.")
        return
    overall_score = results.get('overall_score', 0)
    st.metric("Overall Compliance Score", f"{overall_score}%")
    for standard, checks in results.get('standards', {}).items():
        with st.expander(f"{standard} Compliance"):
            passed = sum(1 for check in checks if check.get('passed', False))
            total = len(checks)
            st.write(f"**Score:** {passed}/{total} ({passed/total*100:.1f}%)")
            for check in checks:
                status = "✅" if check.get('passed', False) else "❌"
                st.write(f"{status} **{check.get('requirement', 'Unknown')}**")
                if not check.get('passed', False):
                    st.write(f"   *Issue:* {check.get('issue', 'No details')}")
                    st.write(f"   *Recommendation:* {check.get('recommendation', 'No recommendation')}")

def show_integrations():
    st.title("🔗 Integrations")
    st.subheader("Enterprise Tool Integration")
    integration_options = st.selectbox(
        "Select tool to integrate:",
        ["Jira", "Polarion", "Azure DevOps", "Custom API"]
    )
    if integration_options == "Jira":
        st.text_input("Jira URL", "https://your-jira-instance.atlassian.net")
        st.text_input("Jira Project Key", "PROJ")
        st.text_input("Username", type="password")
        st.text_input("API Token", type="password")
    elif integration_options == "Polarion":
        st.text_input("Polarion URL", "https://your-polarion-instance.com")
        st.text_input("Username", type="password")
        st.text_input("Password", type="password")
    elif integration_options == "Azure DevOps":
        st.text_input("Azure DevOps URL", "https://dev.azure.com/your-organization")
        st.text_input("Personal Access Token", type="password")
    elif integration_options == "Custom API":
        st.text_input("API Endpoint", "https://api.example.com")
        st.text_input("API Key", type="password")
        st.selectbox("Authentication Method", ["Bearer Token", "Basic Auth", "OAuth"])
    if st.button("💾 Save Integration Configuration"):
        st.success("Integration configuration saved!")

def show_settings():
    st.title("⚙️ Settings")
    st.subheader("Application Configuration")
    db_path = st.text_input("Database Path", "data/testgen.db")
    st.session_state.db_manager = DatabaseManager(db_path)
    max_file_size = st.slider("Maximum File Size (MB)", 1, 100, 10)
    model_temperature = st.slider("AI Model Temperature", 0.0, 1.0, 0.7)
    max_tokens = st.number_input("Max Tokens", 100, 4000, 1000)
    if st.button("💾 Save Settings"):
        config = {
            'database_path': db_path,
            'max_file_size_mb': max_file_size,
            'model_temperature': model_temperature,
            'max_tokens': max_tokens
        }
        save_config(config)
        st.success("Settings saved successfully!")

if __name__ == "__main__":
    main()
