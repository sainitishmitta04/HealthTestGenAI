import logging
from typing import Dict, List, Optional
from .base_integration import BaseIntegration

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraIntegration(BaseIntegration):
    """Integration with Atlassian Jira for test case management"""
    
    def __init__(self, base_url: str, auth_token: str = None, 
                 username: str = None, password: str = None):
        """
        Initialize Jira integration
        
        Args:
            base_url (str): Jira instance URL (e.g., https://your-domain.atlassian.net)
            auth_token (str, optional): Jira API token
            username (str, optional): Jira username for basic auth
            password (str, optional): Jira password for basic auth
        """
        super().__init__(base_url, auth_token, username, password)
        self.issue_api_url = f"{self.base_url}/rest/api/2/issue"
    
    def create_test_case(self, test_case: Dict, project: str = None) -> Dict:
        """
        Create a test case in Jira as a Test issue
        
        Args:
            test_case (Dict): Test case data
            project (str, optional): Jira project key (e.g., "PROJ")
            
        Returns:
            Dict: Created test case with Jira issue key
        """
        if not project:
            raise ValueError("Jira project key is required")
        
        # Map generic test case to Jira issue format
        jira_issue = self._map_to_jira_issue(test_case, project)
        
        try:
            response = self._make_request('post', self.issue_api_url, json=jira_issue)
            created_issue = response.json()
            
            logger.info(f"Created Jira test case: {created_issue['key']}")
            return self._map_from_jira_issue(created_issue)
            
        except Exception as e:
            logger.error(f"Failed to create Jira test case: {e}")
            raise
    
    def update_test_case(self, test_case_id: str, updates: Dict) -> Dict:
        """
        Update a Jira test case
        
        Args:
            test_case_id (str): Jira issue key (e.g., "PROJ-123")
            updates (Dict): Updates to apply
            
        Returns:
            Dict: Updated test case
        """
        issue_url = f"{self.issue_api_url}/{test_case_id}"
        jira_updates = self._map_updates_to_jira_format(updates)
        
        try:
            response = self._make_request('put', issue_url, json=jira_updates)
            updated_issue = response.json()
            
            logger.info(f"Updated Jira test case: {test_case_id}")
            return self._map_from_jira_issue(updated_issue)
            
        except Exception as e:
            logger.error(f"Failed to update Jira test case {test_case_id}: {e}")
            raise
    
    def get_test_case(self, test_case_id: str) -> Dict:
        """
        Get a Jira test case by issue key
        
        Args:
            test_case_id (str): Jira issue key
            
        Returns:
            Dict: Test case data
        """
        issue_url = f"{self.issue_api_url}/{test_case_id}"
        
        try:
            response = self._make_request('get', issue_url)
            jira_issue = response.json()
            
            return self._map_from_jira_issue(jira_issue)
            
        except Exception as e:
            logger.error(f"Failed to get Jira test case {test_case_id}: {e}")
            raise
    
    def search_test_cases(self, query: str = None, project: str = None) -> List[Dict]:
        """
        Search for test cases in Jira using JQL
        
        Args:
            query (str, optional): JQL query string
            project (str, optional): Jira project key
            
        Returns:
            List[Dict]: Matching test cases
        """
        search_url = f"{self.base_url}/rest/api/2/search"
        
        # Build JQL query
        jql_parts = ['issuetype = Test']
        if project:
            jql_parts.append(f'project = {project}')
        if query:
            jql_parts.append(f'text ~ "{query}"')
        
        jql = ' AND '.join(jql_parts)
        search_params = {
            'jql': jql,
            'maxResults': 100,
            'fields': 'summary,description,priority,status,customfield_10000'
        }
        
        try:
            response = self._make_request('get', search_url, params=search_params)
            search_results = response.json()
            
            test_cases = []
            for issue in search_results.get('issues', []):
                test_cases.append(self._map_from_jira_issue(issue))
            
            logger.info(f"Found {len(test_cases)} test cases in Jira")
            return test_cases
            
        except Exception as e:
            logger.error(f"Failed to search Jira test cases: {e}")
            raise
    
    def _map_to_jira_issue(self, test_case: Dict, project: str) -> Dict:
        """
        Map generic test case to Jira issue format
        
        Args:
            test_case (Dict): Generic test case data
            project (str): Jira project key
            
        Returns:
            Dict: Jira issue creation payload
        """
        return {
            'fields': {
                'project': {'key': project},
                'issuetype': {'name': 'Test'},
                'summary': test_case.get('title', 'Untitled Test Case'),
                'description': self._create_jira_description(test_case),
                'priority': {'name': test_case.get('priority', 'Medium')},
                'customfield_10000': self._create_test_steps_field(test_case.get('steps', [])),
                'customfield_10001': test_case.get('expected_results', ''),
                'labels': ['ai-generated', 'healthcare']
            }
        }
    
    def _map_from_jira_issue(self, jira_issue: Dict) -> Dict:
        """
        Map Jira issue to generic test case format
        
        Args:
            jira_issue (Dict): Jira issue data
            
        Returns:
            Dict: Generic test case data
        """
        fields = jira_issue.get('fields', {})
        
        return {
            'id': jira_issue.get('key', ''),
            'title': fields.get('summary', ''),
            'description': fields.get('description', ''),
            'priority': fields.get('priority', {}).get('name', 'Medium'),
            'steps': self._parse_test_steps_field(fields.get('customfield_10000', '')),
            'expected_results': fields.get('customfield_10001', ''),
            'status': fields.get('status', {}).get('name', ''),
            'created_date': fields.get('created', ''),
            'updated_date': fields.get('updated', '')
        }
    
    def _map_updates_to_jira_format(self, updates: Dict) -> Dict:
        """
        Map generic updates to Jira issue update format
        
        Args:
            updates (Dict): Generic updates
            
        Returns:
            Dict: Jira update payload
        """
        jira_updates = {}
        field_mapping = {
            'title': 'summary',
            'description': 'description',
            'priority': 'priority',
            'steps': 'customfield_10000',
            'expected_results': 'customfield_10001'
        }
        
        for generic_field, jira_field in field_mapping.items():
            if generic_field in updates:
                if jira_field == 'priority':
                    jira_updates[jira_field] = {'name': updates[generic_field]}
                else:
                    jira_updates[jira_field] = updates[generic_field]
        
        return {'fields': jira_updates}
    
    def _create_jira_description(self, test_case: Dict) -> str:
        """
        Create Jira-friendly description from test case data
        
        Args:
            test_case (Dict): Test case data
            
        Returns:
            str: Formatted description
        """
        description = test_case.get('description', '')
        
        if 'compliance_checks' in test_case:
            description += "\n\n*Compliance Checks:*"
            for check in test_case['compliance_checks']:
                status = "✅" if check.get('passed', False) else "❌"
                description += f"\n{status} {check.get('standard', 'Unknown')}: {check.get('requirement', '')}"
        
        if 'test_data' in test_case:
            description += "\n\n*Test Data:*"
            for key, value in test_case['test_data'].items():
                description += f"\n{key}: {value}"
        
        return description
    
    def _create_test_steps_field(self, steps: List[str]) -> str:
        """
        Format test steps for Jira custom field
        
        Args:
            steps (List[str]): Test steps
            
        Returns:
            str: Formatted test steps
        """
        if not steps:
            return "1. Execute test\n2. Verify results"
        
        formatted_steps = ""
        for i, step in enumerate(steps, 1):
            formatted_steps += f"{i}. {step}\n"
        
        return formatted_steps.strip()
    
    def _parse_test_steps_field(self, steps_field: str) -> List[str]:
        """
        Parse test steps from Jira custom field
        
        Args:
            steps_field (str): Formatted test steps
            
        Returns:
            List[str]: List of test steps
        """
        if not steps_field:
            return []
        
        steps = []
        for line in steps_field.split('\n'):
            line = line.strip()
            if line and any(char.isdigit() for char in line):
                # Remove numbering and keep the step text
                step_text = line.split('.', 1)[1].strip() if '.' in line else line
                steps.append(step_text)
        
        return steps if steps else ["Execute test", "Verify results"]
    
    def add_test_results(self, test_case_id: str, results: Dict) -> Dict:
        """
        Add test results to a Jira test case
        
        Args:
            test_case_id (str): Jira issue key
            results (Dict): Test results data
            
        Returns:
            Dict: Updated test case with results
        """
        # This would typically use Jira's test management add-ons or custom fields
        # For now, we'll add results as a comment
        comment_url = f"{self.issue_api_url}/{test_case_id}/comment"
        
        comment_text = f"""
        *Test Results:*
        - Status: {results.get('status', 'Unknown')}
        - Execution Date: {results.get('execution_date', 'N/A')}
        - Tester: {results.get('tester', 'Automated')}
        - Notes: {results.get('notes', 'No notes')}
        """
        
        comment_data = {'body': comment_text}
        
        try:
            self._make_request('post', comment_url, json=comment_data)
            logger.info(f"Added test results to {test_case_id}")
            return self.get_test_case(test_case_id)
            
        except Exception as e:
            logger.error(f"Failed to add test results to {test_case_id}: {e}")
            raise