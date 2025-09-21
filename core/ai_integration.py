import google.generativeai as genai
from typing import Dict, List, Optional
import json5
import json
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiAIClient:
    """Client for interacting with Google Gemini AI API"""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini AI client with API key
        
        Args:
            api_key (str): Google Gemini API key
        """
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.chat = self.model.start_chat(history=[])
            logger.info("Gemini AI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI client: {e}")
            raise
    
    def generate_content(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        Generate content using Gemini AI
        
        Args:
            prompt (str): The prompt to send to the AI
            temperature (float): Creativity temperature (0.0 to 1.0)
            max_tokens (int): Maximum tokens to generate
            
        Returns:
            str: Generated content
        """
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
    
    def generate_test_cases_prompt(self, requirements: str, custom_prompt: Optional[str] = None) -> str:
        """
        Create a specialized prompt for test case generation
        
        Args:
            requirements (str): The requirements text
            custom_prompt (str, optional): Custom prompt to use
            
        Returns:
            str: Formatted prompt for test case generation
        """
        base_prompt = f"""
        You are an expert QA engineer specializing in healthcare software testing.
        Your task is to generate comprehensive test cases based on the following requirements.

        REQUIREMENTS:
        {requirements}

        CRITICAL INSTRUCTION: You MUST return ONLY valid JSON format. Do not include any markdown formatting, code blocks, or additional text outside the JSON structure.

        Please generate test cases in JSON format with the following structure:
        {{
            "test_cases": [
                {{
                    "id": "TC-001",
                    "title": "Descriptive test case title",
                    "description": "Detailed description of what is being tested",
                    "priority": "High/Medium/Low/Critical",
                    "steps": [
                        "Step 1 description",
                        "Step 2 description",
                        ...
                    ],
                    "expected_results": "What should happen when the test passes",
                    "compliance_checks": [
                        {{
                            "standard": "FDA/ISO 13485/etc",
                            "requirement": "Specific requirement text",
                            "passed": true/false,
                            "issue": "If not passed, what's wrong",
                            "recommendation": "How to fix compliance issue"
                        }}
                    ],
                    "test_data": {{
                        "input_data": "Sample input data",
                        "expected_output": "Expected output data"
                    }}
                }}
            ]
        }}

        Important considerations for healthcare software:
        - Ensure compliance with FDA regulations, IEC 62304, ISO 13485, ISO 27001
        - Consider patient safety and data privacy (GDPR compliance)
        - Include edge cases and error conditions
        - Prioritize test cases based on risk assessment
        - Ensure traceability from requirements to test cases
        
        REMEMBER: Return ONLY valid JSON. No additional text, explanations, or markdown formatting.
        """
        
        if custom_prompt:
            return f"{base_prompt}\n\nAdditional instructions: {custom_prompt}"
        
        return base_prompt
    
    def generate_test_cases(self, requirements: str, custom_prompt: Optional[str] = None, 
                          temperature: float = 0.7, max_tokens: int = 2000) -> List[Dict]:
        """
        Generate test cases from requirements using AI
        
        Args:
            requirements (str): The requirements text
            custom_prompt (str, optional): Custom prompt instructions
            temperature (float): Creativity temperature
            max_tokens (int): Maximum tokens to generate
            
        Returns:
            List[Dict]: List of test case dictionaries
        """
        try:
            prompt = self.generate_test_cases_prompt(requirements, custom_prompt)
            
            logger.info("Generating test cases with Gemini AI...")
            response_text = self.generate_content(prompt, temperature, max_tokens)
            
            # Try to parse JSON response with enhanced error handling
            try:
                # First, try to extract JSON from the response text
                json_text = self._extract_json_from_response(response_text)
                parsed_response = json5.loads(json_text)
                
                if 'test_cases' in parsed_response:
                    test_cases = parsed_response['test_cases']
                    if isinstance(test_cases, list) and len(test_cases) > 0:
                        return test_cases
                    else:
                        logger.warning("No test cases found in response, falling back to text parsing")
                        return self._parse_text_response(response_text)
                else:
                    logger.warning("Response doesn't contain 'test_cases' key, falling back to text parsing")
                    return self._parse_text_response(response_text)
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response: {e}, falling back to text parsing")
                return self._parse_text_response(response_text)
                
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            raise
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """
        Extract JSON by finding the largest balanced {...} block in the text
        """
        stack = []
        start_idx = None
        largest_json = ''
        for i, char in enumerate(response_text):
            if char == '{':
                if not stack:
                    start_idx = i
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack and start_idx is not None:
                        candidate = response_text[start_idx:i+1]
                        if len(candidate) > len(largest_json):
                            largest_json = candidate
        if not largest_json:
            logger.warning("No JSON found, returning original text")
            return response_text
        return largest_json


    def _validate_and_fix_json(self, json_text: str) -> str:
        import json5
        try:
            json5.loads(json_text)
            return json_text
        except Exception as e:
            logger.warning(f"JSON invalid, returning original for fallback: {e}")
            return json_text


    def _parse_text_response(self, response_text: str) -> List[Dict]:
        """
        Parse text response when JSON parsing fails with enhanced logic

        Args:
            response_text (str): Raw text response from AI

        Returns:
            List[Dict]: Structured test cases
        """
        test_cases = []
        
        # First, try to extract multiple test cases using various patterns
        patterns = [
            r'(?i)(?:test case|tc)\s*\d+[:.-]?\s*(.*?)(?=(?:test case|tc)\s*\d+[:.-]?\s*|$)',
            r'(?i)##?\s*test case.*?(?=##?\s*test case|$)',
            r'(?i)\*\*test case.*?(?=\*\*test case|$)'
        ]
        
        sections = []
        for pattern in patterns:
            sections = re.split(pattern, response_text, flags=re.DOTALL)
            if len(sections) > 1:
                break
        
        # If no sections found, try to split by numbered items
        if len(sections) <= 1:
            sections = re.split(r'(?i)(?=\d+\.\s*test case)', response_text)
        
        for i, section in enumerate(sections):
            if not section.strip() or len(section.strip()) < 20:
                continue
                
            test_case = {
                'id': f"TC-{len(test_cases) + 1:03d}",
                'title': '',
                'description': '',
                'priority': 'Medium',
                'steps': [],
                'expected_results': '',
                'test_data': {},
                'compliance_checks': []
            }
            
            # Extract title - more flexible patterns
            title_patterns = [
                r'(?i)(?:test case|tc)\s*\d*[:.-]?\s*(.*?)(?:\n|$)',
                r'(?i)##?\s*(.*?)(?:\n|$)',
                r'(?i)\*\*(.*?)\*\*'
            ]
            
            for pattern in title_patterns:
                title_match = re.search(pattern, section)
                if title_match:
                    test_case['title'] = title_match.group(1).strip()
                    break
            
            # Extract description - look for paragraphs after title
            desc_match = re.search(r'(?i)(?:description|desc)[:.\s]*(.*?)(?=\n\s*(?:steps|expected|priority|test data|$))', section, re.DOTALL)
            if desc_match:
                test_case['description'] = desc_match.group(1).strip()
            else:
                # If no description found, use first few lines after title
                lines = section.split('\n')
                if len(lines) > 1:
                    desc_lines = []
                    for line in lines[1:]:
                        if line.strip() and not re.match(r'(?i)(steps|expected|priority|test data)', line):
                            desc_lines.append(line.strip())
                    if desc_lines:
                        test_case['description'] = ' '.join(desc_lines[:3])
            
            # Extract steps - more flexible pattern
            steps_patterns = [
                r'(?i)steps?[:.\s]*(.*?)(?=\n\s*(?:expected|priority|test data|$))',
                r'(?i)\d+\.\s*(.*?)(?=\n\s*\d+\.|\n\s*(?:expected|priority|$))'
            ]
            
            for pattern in steps_patterns:
                steps_matches = re.findall(pattern, section, re.DOTALL)
                if steps_matches:
                    if isinstance(steps_matches[0], str):
                        # Split by newlines if it's a block of text
                        steps = [step.strip() for step in steps_matches[0].split('\n') if step.strip()]
                    else:
                        steps = [step.strip() for step in steps_matches if step.strip()]
                    test_case['steps'] = steps
                    break
            
            # Extract expected results
            expected_patterns = [
                r'(?i)expected\s*(?:result|outcome)[:.\s]*(.*?)(?=\n\s*(?:priority|compliance|$))',
                r'(?i)expected[:.\s]*(.*?)(?=\n\s*(?:priority|compliance|$))'
            ]
            
            for pattern in expected_patterns:
                expected_match = re.search(pattern, section, re.DOTALL)
                if expected_match:
                    test_case['expected_results'] = expected_match.group(1).strip()
                    break
            
            # Extract priority
            priority_match = re.search(r'(?i)priority[:.\s]*(high|medium|low|critical)', section)
            if priority_match:
                test_case['priority'] = priority_match.group(1).capitalize()
            
            # Only add if we have meaningful content
            if (test_case['title'] and len(test_case['title']) > 5) or \
               (test_case['description'] and len(test_case['description']) > 20):
                test_cases.append(test_case)
        
        # If no structured test cases found, try to create multiple from the text
        if not test_cases and response_text.strip():
            # Split text into logical sections based on common patterns
            logical_sections = re.split(r'(?i)(?=\d+\.\s+|\* |\- |## )', response_text)
            
            for i, section in enumerate(logical_sections):
                if not section.strip() or len(section.strip()) < 30:
                    continue
                
                test_case = {
                    'id': f"TC-{i + 1:03d}",
                    'title': f"Test Case {i + 1}",
                    'description': section[:150] + '...' if len(section) > 150 else section,
                    'priority': 'Medium',
                    'steps': ['Execute the test scenario', 'Verify expected behavior'],
                    'expected_results': 'Test should pass with expected outcomes',
                    'test_data': {},
                    'compliance_checks': []
                }
                test_cases.append(test_case)
            
            # Limit to reasonable number of test cases
            test_cases = test_cases[:10]
            
        return test_cases
    
    def check_compliance(self, test_cases: List[Dict], standards: List[str]) -> Dict:
        """
        Check compliance of test cases against healthcare standards
        
        Args:
            test_cases (List[Dict]): Test cases to check
            standards (List[str]): Standards to check against
            
        Returns:
            Dict: Compliance check results
        """
        prompt = f"""
        You are a healthcare compliance expert. Analyze the following test cases 
        for compliance with these standards: {', '.join(standards)}.

        TEST CASES:
        {json.dumps(test_cases, indent=2)}

        Provide a compliance assessment in JSON format:
        {{
            "overall_score": 85,
            "standards": {{
                "FDA": [
                    {{
                        "requirement": "Specific FDA requirement",
                        "passed": true,
                        "issue": "If not passed, what's wrong",
                        "recommendation": "How to fix"
                    }}
                ],
                "ISO 13485": [
                    # ... similar structure
                ]
            }},
            "recommendations": "Overall recommendations for improvement"
        }}

        Focus on healthcare-specific compliance requirements including:
        - Patient safety and risk management
        - Data privacy and security (GDPR considerations)
        - Documentation and traceability requirements
        - Validation and verification processes
        - Quality management system requirements
        """
        
        try:
            response_text = self.generate_content(prompt, temperature=0.3, max_tokens=1500)
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            return {"error": str(e)}
    
    def enhance_test_cases(self, test_cases: List[Dict], enhancement_prompt: str) -> List[Dict]:
        """
        Enhance existing test cases based on specific prompts
        
        Args:
            test_cases (List[Dict]): Existing test cases
            enhancement_prompt (str): Prompt for enhancement
            
        Returns:
            List[Dict]: Enhanced test cases
        """
        prompt = f"""
        Enhance the following test cases based on this instruction: {enhancement_prompt}

        EXISTING TEST CASES:
        {json.dumps(test_cases, indent=2)}

        Return the enhanced test cases in the same JSON format with improvements applied.
        """
        
        try:
            response_text = self.generate_content(prompt, temperature=0.5, max_tokens=2000)
            enhanced_cases = json.loads(response_text)
            return enhanced_cases.get('test_cases', enhanced_cases)
        except Exception as e:
            logger.error(f"Error enhancing test cases: {e}")
            return test_cases  # Return original if enhancement fails
