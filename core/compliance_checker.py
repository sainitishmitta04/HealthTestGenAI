import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceChecker:
    """Check test cases for healthcare compliance standards"""
    
    # Predefined compliance requirements for various standards
    COMPLIANCE_STANDARDS = {
        "FDA": [
            {
                "id": "FDA-001",
                "requirement": "Software must be validated for its intended use",
                "description": "Ensure software functions as intended in the healthcare context"
            },
            {
                "id": "FDA-002",
                "requirement": "Risk management must be implemented",
                "description": "Identify and mitigate risks associated with software use"
            },
            {
                "id": "FDA-003",
                "requirement": "Design controls must be established",
                "description": "Maintain design history file and design validation"
            },
            {
                "id": "FDA-004",
                "requirement": "Quality system regulations must be followed",
                "description": "Comply with 21 CFR Part 820 Quality System Regulation"
            }
        ],
        "IEC 62304": [
            {
                "id": "IEC-001",
                "requirement": "Software development process must be established",
                "description": "Follow defined software development lifecycle"
            },
            {
                "id": "IEC-002",
                "requirement": "Risk management must be applied",
                "description": "Perform risk analysis and implement risk control measures"
            },
            {
                "id": "IEC-003",
                "requirement": "Software must be maintained properly",
                "description": "Establish software maintenance and configuration management"
            },
            {
                "id": "IEC-004",
                "requirement": "Software must be validated",
                "description": "Verify and validate software requirements"
            }
        ],
        "ISO 13485": [
            {
                "id": "ISO13485-001",
                "requirement": "Quality management system must be implemented",
                "description": "Establish and maintain quality management system"
            },
            {
                "id": "ISO13485-002",
                "requirement": "Risk-based approach must be used",
                "description": "Apply risk management to all processes"
            },
            {
                "id": "ISO13485-003",
                "requirement": "Design and development must be controlled",
                "description": "Maintain design and development records"
            },
            {
                "id": "ISO13485-004",
                "requirement": "Process validation must be performed",
                "description": "Validate processes where output cannot be verified"
            }
        ],
        "ISO 9001": [
            {
                "id": "ISO9001-001",
                "requirement": "Customer focus must be maintained",
                "description": "Meet customer requirements and enhance satisfaction"
            },
            {
                "id": "ISO9001-002",
                "requirement": "Leadership must be demonstrated",
                "description": "Establish unity of purpose and direction"
            },
            {
                "id": "ISO9001-003",
                "requirement": "Engagement of people must be ensured",
                "description": "Competent, empowered and engaged people"
            },
            {
                "id": "ISO9001-004",
                "requirement": "Process approach must be used",
                "description": "Systematic management of processes"
            }
        ],
        "ISO 27001": [
            {
                "id": "ISO27001-001",
                "requirement": "Information security policy must be established",
                "description": "Define and maintain information security policy"
            },
            {
                "id": "ISO27001-002",
                "requirement": "Risk assessment must be performed",
                "description": "Systematic assessment of information security risks"
            },
            {
                "id": "ISO27001-003",
                "requirement": "Access control must be implemented",
                "description": "Control access to information and systems"
            },
            {
                "id": "ISO27001-004",
                "requirement": "Cryptographic controls must be used",
                "description": "Protect information confidentiality and integrity"
            }
        ],
        "GDPR": [
            {
                "id": "GDPR-001",
                "requirement": "Lawful basis for processing must be established",
                "description": "Ensure valid legal basis for data processing"
            },
            {
                "id": "GDPR-002",
                "requirement": "Data subject rights must be respected",
                "description": "Enable data subject access, rectification, and erasure"
            },
            {
                "id": "GDPR-003",
                "requirement": "Data protection by design must be implemented",
                "description": "Integrate data protection into design phase"
            },
            {
                "id": "GDPR-004",
                "requirement": "Data breach notification must be prepared",
                "description": "Establish procedures for data breach notification"
            }
        ]
    }
    
    def __init__(self):
        self.compliance_cache = {}
    
    def check_compliance(self, test_cases: List[Dict], standards: List[str]) -> Dict:
        """
        Check test cases against specified compliance standards
        
        Args:
            test_cases (List[Dict]): List of test cases to check
            standards (List[str]): List of standards to check against
            
        Returns:
            Dict: Compliance check results with overall score and detailed checks
        """
        if not test_cases:
            return {"error": "No test cases provided for compliance check"}
        
        if not standards:
            return {"error": "No standards specified for compliance check"}
        
        logger.info(f"Checking compliance for {len(test_cases)} test cases against standards: {standards}")
        
        results = {
            "overall_score": 0,
            "standards": {},
            "total_checks": 0,
            "passed_checks": 0,
            "timestamp": datetime.now().isoformat(),
            "test_cases_count": len(test_cases)
        }
        
        total_checks = 0
        passed_checks = 0
        
        # Check each standard
        for standard in standards:
            if standard not in self.COMPLIANCE_STANDARDS:
                logger.warning(f"Standard {standard} not found in predefined standards")
                continue
                
            standard_checks = self.COMPLIANCE_STANDARDS[standard]
            standard_results = []
            
            for check in standard_checks:
                total_checks += 1
                check_result = self._check_single_requirement(test_cases, check)
                standard_results.append(check_result)
                
                if check_result["passed"]:
                    passed_checks += 1
            
            results["standards"][standard] = standard_results
        
        # Calculate overall score
        if total_checks > 0:
            results["overall_score"] = round((passed_checks / total_checks) * 100, 2)
            results["total_checks"] = total_checks
            results["passed_checks"] = passed_checks
        
        logger.info(f"Compliance check completed. Overall score: {results['overall_score']}%")
        return results
    
    def _check_single_requirement(self, test_cases: List[Dict], requirement: Dict) -> Dict:
        """
        Check a single compliance requirement against test cases
        
        Args:
            test_cases (List[Dict]): List of test cases
            requirement (Dict): Compliance requirement to check
            
        Returns:
            Dict: Check result with pass/fail status and details
        """
        # Simple heuristic: check if any test case mentions the requirement or related concepts
        requirement_text = requirement["requirement"].lower()
        description_text = requirement["description"].lower()
        
        # Keywords that might indicate compliance
        keywords = requirement_text.split() + description_text.split()
        keywords = [word for word in keywords if len(word) > 3]  # Filter short words
        
        passed = False
        evidence = []
        
        for test_case in test_cases:
            test_text = json.dumps(test_case).lower()
            
            # Check if test case contains any keywords
            for keyword in keywords:
                if keyword in test_text:
                    passed = True
                    evidence.append({
                        "test_case_id": test_case.get("id", "unknown"),
                        "title": test_case.get("title", "unknown"),
                        "matched_keyword": keyword
                    })
                    break
        
        return {
            "requirement_id": requirement["id"],
            "requirement": requirement["requirement"],
            "description": requirement["description"],
            "passed": passed,
            "evidence": evidence,
            "issue": "No test case addresses this requirement" if not passed else "",
            "recommendation": "Add test cases that cover this compliance requirement" if not passed else "Requirement adequately covered"
        }
    
    def get_available_standards(self) -> List[str]:
        """
        Get list of available compliance standards
        
        Returns:
            List[str]: List of standard names
        """
        return list(self.COMPLIANCE_STANDARDS.keys())
    
    def get_standard_details(self, standard: str) -> List[Dict]:
        """
        Get detailed requirements for a specific standard
        
        Args:
            standard (str): Standard name
            
        Returns:
            List[Dict]: List of requirements for the standard
        """
        return self.COMPLIANCE_STANDARDS.get(standard, [])
    
    def generate_compliance_report(self, results: Dict, format: str = "json") -> str:
        """
        Generate a compliance report in the specified format
        
        Args:
            results (Dict): Compliance check results
            format (str): Output format (json, text, html)
            
        Returns:
            str: Formatted compliance report
        """
        if format == "json":
            return json.dumps(results, indent=2)
        elif format == "text":
            return self._generate_text_report(results)
        elif format == "html":
            return self._generate_html_report(results)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_text_report(self, results: Dict) -> str:
        """Generate a text format compliance report"""
        report = []
        report.append("COMPLIANCE CHECK REPORT")
        report.append("=" * 50)
        report.append(f"Timestamp: {results.get('timestamp', 'N/A')}")
        report.append(f"Test Cases Analyzed: {results.get('test_cases_count', 0)}")
        report.append(f"Overall Compliance Score: {results.get('overall_score', 0)}%")
        report.append(f"Passed Checks: {results.get('passed_checks', 0)} / {results.get('total_checks', 0)}")
        report.append("")
        
        for standard, checks in results.get('standards', {}).items():
            report.append(f"STANDARD: {standard}")
            report.append("-" * 30)
            
            for check in checks:
                status = "PASS" if check.get('passed', False) else "FAIL"
                report.append(f"[{status}] {check.get('requirement_id', 'N/A')}: {check.get('requirement', 'N/A')}")
                
                if not check.get('passed', False):
                    report.append(f"   Issue: {check.get('issue', 'N/A')}")
                    report.append(f"   Recommendation: {check.get('recommendation', 'N/A')}")
                
                if check.get('evidence'):
                    report.append("   Evidence:")
                    for evidence in check.get('evidence', []):
                        report.append(f"     - Test Case {evidence.get('test_case_id', 'N/A')}: {evidence.get('title', 'N/A')}")
                
                report.append("")
        
        return "\n".join(report)
    
    def _generate_html_report(self, results: Dict) -> str:
        """Generate an HTML format compliance report"""
        html = []
        html.append("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Compliance Check Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; }
                .standard { margin-top: 20px; }
                .check { margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }
                .pass { border-left-color: green; background-color: #e8f5e8; }
                .fail { border-left-color: red; background-color: #fce8e8; }
                .evidence { margin-left: 20px; font-size: 0.9em; color: #666; }
            </style>
        </head>
        <body>
        """)
        
        html.append(f"""
        <div class="header">
            <h1>Compliance Check Report</h1>
            <p><strong>Timestamp:</strong> {results.get('timestamp', 'N/A')}</p>
            <p><strong>Test Cases Analyzed:</strong> {results.get('test_cases_count', 0)}</p>
            <p><strong>Overall Compliance Score:</strong> {results.get('overall_score', 0)}%</p>
            <p><strong>Passed Checks:</strong> {results.get('passed_checks', 0)} / {results.get('total_checks', 0)}</p>
        </div>
        """)
        
        for standard, checks in results.get('standards', {}).items():
            html.append(f"""
            <div class="standard">
                <h2>Standard: {standard}</h2>
            """)
            
            for check in checks:
                status_class = "pass" if check.get('passed', False) else "fail"
                html.append(f"""
                <div class="check {status_class}">
                    <h3>{check.get('requirement_id', 'N/A')}: {check.get('requirement', 'N/A')}</h3>
                    <p><strong>Status:</strong> {'PASS' if check.get('passed', False) else 'FAIL'}</p>
                    <p><strong>Description:</strong> {check.get('description', 'N/A')}</p>
                """)
                
                if not check.get('passed', False):
                    html.append(f"""
                    <p><strong>Issue:</strong> {check.get('issue', 'N/A')}</p>
                    <p><strong>Recommendation:</strong> {check.get('recommendation', 'N/A')}</p>
                    """)
                
                if check.get('evidence'):
                    html.append("<p><strong>Evidence:</strong></p>")
                    html.append("<ul class='evidence'>")
                    for evidence in check.get('evidence', []):
                        html.append(f"<li>Test Case {evidence.get('test_case_id', 'N/A')}: {evidence.get('title', 'N/A')}</li>")
                    html.append("</ul>")
                
                html.append("</div>")
            
            html.append("</div>")
        
        html.append("""
        </body>
        </html>
        """)
        
        return "\n".join(html)


# Utility function for standalone use
def check_compliance(test_cases: List[Dict], standards: List[str]) -> Dict:
    """
    Utility function to check compliance without instantiating the class
    
    Args:
        test_cases (List[Dict]): List of test cases
        standards (List[str]): List of standards to check
        
    Returns:
        Dict: Compliance check results
    """
    checker = ComplianceChecker()
    return checker.check_compliance(test_cases, standards)
