import json
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestCaseGenerator:
    """Generate test cases from requirements using AI and templates"""
    
    def __init__(self):
        self.test_case_counter = 0
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load test case templates for different types of testing"""
        return {
            "functional": {
                "structure": {
                    "id": "TC-{counter}",
                    "title": "Test [functionality]",
                    "description": "Verify that [functionality] works as expected",
                    "priority": "Medium",
                    "steps": [
                        "Navigate to [screen/page]",
                        "Perform [action]",
                        "Verify [expected behavior]"
                    ],
                    "expected_results": "[Functionality] should work correctly without errors",
                    "test_data": {
                        "input_data": "Sample input data",
                        "expected_output": "Expected output data"
                    }
                },
                "placeholders": {
                    "[functionality]": "specific functionality being tested",
                    "[screen/page]": "relevant screen or page",
                    "[action]": "specific user action",
                    "[expected behavior]": "expected system response"
                }
            },
            "security": {
                "structure": {
                    "id": "SEC-{counter}",
                    "title": "Security Test: [vulnerability]",
                    "description": "Test for [vulnerability] vulnerability",
                    "priority": "High",
                    "steps": [
                        "Attempt to [malicious action]",
                        "Observe system response"
                    ],
                    "expected_results": "System should prevent [vulnerability] and respond appropriately",
                    "compliance_checks": [
                        {
                            "standard": "ISO 27001",
                            "requirement": "Security controls implementation",
                            "passed": True
                        }
                    ]
                }
            },
            "performance": {
                "structure": {
                    "id": "PERF-{counter}",
                    "title": "Performance Test: [metric]",
                    "description": "Test system performance for [metric]",
                    "priority": "Medium",
                    "steps": [
                        "Set up performance monitoring",
                        "Execute [scenario] with [load] load",
                        "Measure response times"
                    ],
                    "expected_results": "System should meet performance requirements: [requirements]",
                    "test_data": {
                        "load_level": "Specified load level",
                        "response_time_threshold": "Maximum acceptable response time"
                    }
                }
            },
            "compliance": {
                "structure": {
                    "id": "COMP-{counter}",
                    "title": "Compliance Test: [standard]",
                    "description": "Test compliance with [standard] requirements",
                    "priority": "High",
                    "steps": [
                        "Review [standard] requirements",
                        "Execute compliance verification steps",
                        "Document results"
                    ],
                    "expected_results": "System should comply with all [standard] requirements",
                    "compliance_checks": [
                        {
                            "standard": "[standard]",
                            "requirement": "Specific requirement",
                            "passed": True
                        }
                    ]
                }
            }
        }
    
    def generate_test_cases(self, requirements: str, ai_client, 
                          custom_prompt: Optional[str] = None,
                          include_compliance: bool = True,
                          test_type: str = "functional") -> List[Dict]:
        """
        Generate test cases from requirements using AI
        
        Args:
            requirements (str): Requirements text
            ai_client: Gemini AI client instance
            custom_prompt (str, optional): Custom prompt for AI
            include_compliance (bool): Whether to include compliance checks
            test_type (str): Type of test cases to generate
            
        Returns:
            List[Dict]: Generated test cases
        """
        try:
            if not ai_client:
                raise ValueError("AI client not provided")
            
            # Use AI to generate test cases
            ai_test_cases = ai_client.generate_test_cases(requirements, custom_prompt)
            
            # Enhance with templates and structure
            enhanced_cases = self._enhance_test_cases(ai_test_cases, test_type, include_compliance)
            
            logger.info(f"Generated {len(enhanced_cases)} test cases")
            return enhanced_cases
            
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            # Fallback to template-based generation
            return self._generate_from_template(requirements, test_type, include_compliance)
    
    def _enhance_test_cases(self, ai_test_cases: List[Dict], test_type: str, 
                          include_compliance: bool) -> List[Dict]:
        """
        Enhance AI-generated test cases with proper structure and compliance
        
        Args:
            ai_test_cases (List[Dict]): Raw AI-generated test cases
            test_type (str): Type of test cases
            include_compliance (bool): Whether to include compliance
            
        Returns:
            List[Dict]: Enhanced test cases
        """
        enhanced_cases = []
        
        for test_case in ai_test_cases:
            # Ensure basic structure
            enhanced_case = {
                "id": self._generate_test_case_id(test_type),
                "title": test_case.get("title", "Untitled Test Case"),
                "description": test_case.get("description", "No description provided"),
                "priority": test_case.get("priority", "Medium"),
                "steps": test_case.get("steps", []),
                "expected_results": test_case.get("expected_results", "No expected results specified"),
                "test_data": test_case.get("test_data", {}),
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
            
            # Add compliance checks if requested
            if include_compliance:
                enhanced_case["compliance_checks"] = test_case.get("compliance_checks", [])
            
            # Ensure steps are properly formatted
            if not enhanced_case["steps"]:
                enhanced_case["steps"] = ["Step 1: Execute test", "Step 2: Verify results"]
            
            enhanced_cases.append(enhanced_case)
        
        return enhanced_cases
    
    def _generate_from_template(self, requirements: str, test_type: str, 
                              include_compliance: bool) -> List[Dict]:
        """
        Generate test cases from template when AI fails
        
        Args:
            requirements (str): Requirements text
            test_type (str): Type of test cases
            include_compliance (bool): Whether to include compliance
            
        Returns:
            List[Dict]: Template-based test cases
        """
        template = self.templates.get(test_type, self.templates["functional"])
        
        # Simple extraction of key phrases from requirements
        key_phrases = self._extract_key_phrases(requirements)
        
        test_cases = []
        
        # Create basic test cases based on extracted phrases
        for i, phrase in enumerate(key_phrases[:5]):  # Limit to 5 test cases
            test_case = template["structure"].copy()
            
            # Replace placeholders
            for key, value in test_case.items():
                if isinstance(value, str):
                    test_case[key] = value.replace("[functionality]", phrase)
            
            test_case["id"] = test_case["id"].format(counter=self.test_case_counter + i + 1)
            test_case["title"] = test_case["title"].replace("[functionality]", phrase)
            test_case["description"] = test_case["description"].replace("[functionality]", phrase)
            
            test_cases.append(test_case)
        
        self.test_case_counter += len(test_cases)
        return test_cases
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases from requirements text
        
        Args:
            text (str): Requirements text
            
        Returns:
            List[str]: Extracted key phrases
        """
        # Simple extraction of potential testable functionalities
        phrases = []
        
        # Look for action verbs and their objects
        patterns = [
            r'(?:shall|should|must|will)\s+(\w+\s+\w+(?:\s+\w+)?)',
            r'(\w+ing\s+\w+(?:\s+\w+)?)',
            r'(\w+\s+function(?:ality)?)',
            r'(\w+\s+feature)',
            r'(\w+\s+module)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            phrases.extend(matches)
        
        # Remove duplicates and short phrases
        phrases = list(set(phrases))
        phrases = [p for p in phrases if len(p.split()) >= 2]
        
        return phrases[:10]  # Return top 10 phrases
    
    def _generate_test_case_id(self, test_type: str) -> str:
        """
        Generate a unique test case ID
        
        Args:
            test_type (str): Type of test case
            
        Returns:
            str: Unique test case ID
        """
        prefix_map = {
            "functional": "TC",
            "security": "SEC",
            "performance": "PERF",
            "compliance": "COMP"
        }
        
        prefix = prefix_map.get(test_type, "TC")
        self.test_case_counter += 1
        return f"{prefix}-{self.test_case_counter:04d}"
    
    def enhance_with_context(self, test_cases: List[Dict], context: str, 
                          enhancement_type: str = "general") -> List[Dict]:
        """
        Enhance existing test cases with additional context
        
        Args:
            test_cases (List[Dict]): Existing test cases
            context (str): Additional context or requirements
            enhancement_type (str): Type of enhancement
            
        Returns:
            List[Dict]: Enhanced test cases
        """
        enhanced_cases = []
        
        for test_case in test_cases:
            enhanced_case = test_case.copy()
            
            if enhancement_type == "edge_cases":
                enhanced_case = self._add_edge_cases(enhanced_case, context)
            elif enhancement_type == "negative_testing":
                enhanced_case = self._add_negative_tests(enhanced_case, context)
            elif enhancement_type == "performance":
                enhanced_case = self._add_performance_considerations(enhanced_case, context)
            else:
                enhanced_case = self._add_general_enhancements(enhanced_case, context)
            
            enhanced_case["last_modified"] = datetime.now().isoformat()
            enhanced_cases.append(enhanced_case)
        
        return enhanced_cases
    
    def _add_edge_cases(self, test_case: Dict, context: str) -> Dict:
        """Add edge case considerations to test case"""
        if "edge_cases" not in test_case:
            test_case["edge_cases"] = []
        
        # Add some generic edge cases based on context
        edge_cases = [
            "Test with maximum input values",
            "Test with minimum input values",
            "Test with invalid data formats",
            "Test with concurrent user access",
            "Test with system under high load"
        ]
        
        test_case["edge_cases"].extend(edge_cases[:2])  # Add 2 edge cases
        return test_case
    
    def _add_negative_tests(self, test_case: Dict, context: str) -> Dict:
        """Add negative testing scenarios to test case"""
        if "negative_tests" not in test_case:
            test_case["negative_tests"] = []
        
        negative_scenarios = [
            "Test with invalid user credentials",
            "Test with missing required fields",
            "Test with incorrect data types",
            "Test with permission violations"
        ]
        
        test_case["negative_tests"].extend(negative_scenarios[:2])
        return test_case
    
    def _add_performance_considerations(self, test_case: Dict, context: str) -> Dict:
        """Add performance considerations to test case"""
        if "performance_considerations" not in test_case:
            test_case["performance_considerations"] = []
        
        considerations = [
            "Measure response time under normal load",
            "Test scalability with increasing user count",
            "Monitor memory usage during execution",
            "Check for memory leaks"
        ]
        
        test_case["performance_considerations"].extend(considerations[:2])
        return test_case
    
    def _add_general_enhancements(self, test_case: Dict, context: str) -> Dict:
        """Add general enhancements to test case"""
        # Add context to description
        if context:
            test_case["description"] += f"\n\nAdditional context: {context}"
        
        return test_case
    
    def export_test_cases(self, test_cases: List[Dict], format: str = "json") -> str:
        """
        Export test cases in various formats
        
        Args:
            test_cases (List[Dict]): Test cases to export
            format (str): Export format (json, xml, csv, excel)
            
        Returns:
            str: Exported test cases in specified format
        """
        if format == "json":
            return json.dumps({"test_cases": test_cases}, indent=2)
        elif format == "xml":
            return self._export_to_xml(test_cases)
        elif format == "csv":
            return self._export_to_csv(test_cases)
        elif format == "excel":
            return self._export_to_excel(test_cases)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_to_xml(self, test_cases: List[Dict]) -> str:
        """Export test cases to XML format"""
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<testCases>']
        
        for tc in test_cases:
            xml_lines.append('  <testCase>')
            for key, value in tc.items():
                if isinstance(value, list):
                    xml_lines.append(f'    <{key}>')
                    for item in value:
                        if isinstance(item, dict):
                            xml_lines.append('      <item>')
                            for k, v in item.items():
                                xml_lines.append(f'        <{k}>{v}</{k}>')
                            xml_lines.append('      </item>')
                        else:
                            xml_lines.append(f'      <step>{item}</step>')
                    xml_lines.append(f'    </{key}>')
                else:
                    xml_lines.append(f'    <{key}>{value}</{key}>')
            xml_lines.append('  </testCase>')
        
        xml_lines.append('</testCases>')
        return '\n'.join(xml_lines)
    
    def _export_to_csv(self, test_cases: List[Dict]) -> str:
        """Export test cases to CSV format"""
        if not test_cases:
            return ""
        
        # Simple CSV export - for complex data, consider using pandas
        headers = ["ID", "Title", "Priority", "Description"]
        rows = []
        
        for tc in test_cases:
            row = [
                tc.get("id", ""),
                tc.get("title", ""),
                tc.get("priority", ""),
                tc.get("description", "").replace('"', '""')  # Escape quotes
            ]
            rows.append('"' + '","'.join(row) + '"')
        
        return ','.join(headers) + '\n' + '\n'.join(rows)
    
    def _export_to_excel(self, test_cases: List[Dict]) -> str:
        """Export test cases to Excel format (placeholder)"""
        # This would typically use a library like openpyxl or pandas
        # For now, return a message
        return f"Excel export would generate file with {len(test_cases)} test cases"


# Utility function for standalone use
def generate_test_cases(requirements: str, ai_client=None, **kwargs) -> List[Dict]:
    """
    Utility function to generate test cases without instantiating the class
    
    Args:
        requirements (str): Requirements text
        ai_client: Optional AI client
        **kwargs: Additional arguments for generate_test_cases
        
    Returns:
        List[Dict]: Generated test cases
    """
    generator = TestCaseGenerator()
    return generator.generate_test_cases(requirements, ai_client, **kwargs)
