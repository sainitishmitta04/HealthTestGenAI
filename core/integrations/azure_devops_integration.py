import logging
import base64
from typing import Dict, List, Optional
from .base_integration import BaseIntegration

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureDevOpsIntegration(BaseIntegration):
    """Integration with Azure DevOps for test case management"""
    
    def __init__(self, base_url: str, auth_token: str = None, 
                 username: str = None, password: str = None):
        """
        Initialize Azure DevOps integration
        
        Args:
            base_url (str): Azure DevOps organization URL (e.g., https://dev.azure.com/your-organization)
            auth_token (str, optional): Personal Access Token (PAT)
            username (str, optional): Username (not typically used with PAT)
            password (str, optional): Password (not typically used with PAT)
        """
        super().__init__(base_url, auth_token, username, password)
        self.api_version = "7.1"
        
        # Setup authentication for Azure DevOps
        if self.auth_token:
            encoded_token = base64.b64encode(f":{self.auth_token}".encode()).decode()
            self.session.headers.update({
                'Authorization': f'Basic {encoded_token}',
                'Content-Type': 'application/json'
            })
    
    def create_test_case(self, test_case: Dict, project: str = None) -> Dict:
        """
        Create a test case in Azure DevOps Test Plans
        
        Args:
            test_case (Dict): Test case data
            project (str, optional): Azure DevOps project name
            
        Returns:
            Dict: Created test case with Azure DevOps ID
        """
        if not project:
            raise ValueError("Azure DevOps project name is required")
        
        # Map generic test case to Azure DevOps format
        azure_test_case = self._map_to_azure_format(test_case, project)
        
        test_case_url = f"{self.base_url}/{project}/_apis/testplan/plans/plans?api-version={self.api_version}"
        
        try:
            response = self._make_request('post', test_case_url, json=azure_test_case)
            created_case = response.json()
            
            logger.info(f"Created Azure DevOps test case: {created_case['id']}")
            return self._map_from_azure_format(created_case)
            
        except Exception as e:
            logger.error(f"Failed to create Azure DevOps test case: {e}")
            raise
    
    def update_test_case(self, test_case_id: str, updates: Dict) -> Dict:
        """
        Update an Azure DevOps test case
        
        Args:
            test_case_id (str): Azure DevOps test case ID
            updates (Dict): Updates to apply
            
        Returns:
            Dict: Updated test case
        """
        # Azure DevOps uses different endpoints for test cases in Test Plans vs Work Items
        # This is a simplified implementation
        update_url = f"{self.base_url}/_apis/wit/workitems/{test_case_id}?api-version={self.api_version}"
        azure_updates = self._map_updates_to_azure_format(updates)
        
        try:
            response = self._make_request('patch', update_url, json=azure_updates)
            updated_case = response.json()
            
            logger.info(f"Updated Azure DevOps test case: {test_case_id}")
            return self._map_from_azure_format(updated_case)
            
        except Exception as e:
            logger.error(f"Failed to update Azure DevOps test case {test_case_id}: {e}")
            raise
    
    def get_test_case(self, test_case_id: str) -> Dict:
        """
        Get an Azure DevOps test case by ID
        
        Args:
            test_case_id (str): Azure DevOps test case ID
            
        Returns:
            Dict: Test case data
        """
        get_url = f"{self.base_url}/_apis/wit/workitems/{test_case_id}?api-version={self.api_version}"
        
        try:
            response = self._make_request('get', get_url)
            azure_case = response.json()
            
            return self._map_from_azure_format(azure_case)
            
        except Exception as e:
            logger.error(f"Failed to get Azure DevOps test case {test_case_id}: {e}")
            raise
    
    def search_test_cases(self, query: str = None, project: str = None) -> List[Dict]:
        """
        Search for test cases in Azure DevOps
        
        Args:
            query (str, optional): Search query
            project (str, optional): Azure DevOps project name
            
        Returns:
            List[Dict]: Matching test cases
        """
        search_url = f"{self.base_url}/_apis/wit/wiql?api-version={self.api_version}"
        
        # Build WIQL query
        wiql_query = "SELECT [System.Id], [System.Title], [System.Description] FROM WorkItems "
        wiql_query += "WHERE [System.WorkItemType] = 'Test Case' "
        
        if project:
            wiql_query += f"AND [System.TeamProject] = '{project}' "
        if query:
            wiql_query += f"AND [System.Title] CONTAINS '{query}'"
        
        search_data = {'query': wiql_query}
        
        try:
            response = self._make_request('post', search_url, json=search_data)
            search_results = response.json()
            
            test_cases = []
            for work_item in search_results.get('workItems', []):
                # Get full work item details
                test_case = self.get_test_case(work_item['id'])
                test_cases.append(test_case)
            
            logger.info(f"Found {len(test_cases)} test cases in Azure DevOps")
            return test_cases
            
        except Exception as e:
            logger.error(f"Failed to search Azure DevOps test cases: {e}")
            raise
    
    def _map_to_azure_format(self, test_case: Dict, project: str) -> List[Dict]:
        """
        Map generic test case to Azure DevOps format using JSON Patch
        
        Args:
            test_case (Dict): Generic test case data
            project (str): Azure DevOps project name
            
        Returns:
            List[Dict]: Azure DevOps JSON Patch operations
        """
        return [
            {
                'op': 'add',
                'path': '/fields/System.Title',
                'value': test_case.get('title', 'Untitled Test Case')
            },
            {
                'op': 'add',
                'path': '/fields/System.Description',
                'value': self._create_azure_description(test_case)
            },
            {
                'op': 'add',
                'path': '/fields/Microsoft.VSTS.TCM.Steps',
                'value': self._format_test_steps(test_case.get('steps', []))
            },
            {
                'op': 'add',
                'path': '/fields/Microsoft.VSTS.TCM.Parameters',
                'value': self._format_test_data(test_case.get('test_data', {}))
            }
        ]
    
    def _map_from_azure_format(self, azure_case: Dict) -> Dict:
        """
        Map Azure DevOps work item to generic test case format
        
        Args:
            azure_case (Dict): Azure DevOps work item data
            
        Returns:
            Dict: Generic test case data
        """
        fields = azure_case.get('fields', {})
        
        return {
            'id': str(azure_case.get('id', '')),
            'title': fields.get('System.Title', ''),
            'description': fields.get('System.Description', ''),
            'priority': fields.get('Microsoft.VSTS.Common.Priority', '2'),
            'steps': self._parse_test_steps(fields.get('Microsoft.VSTS.TCM.Steps', '')),
            'expected_results': fields.get('Microsoft.VSTS.TCM.Parameters', ''),
            'status': fields.get('System.State', ''),
            'created_date': fields.get('System.CreatedDate', ''),
            'updated_date': fields.get('System.ChangedDate', '')
        }
    
    def _map_updates_to_azure_format(self, updates: Dict) -> List[Dict]:
        """
        Map generic updates to Azure DevOps JSON Patch format
        
        Args:
            updates (Dict): Generic updates
            
        Returns:
            List[Dict]: Azure DevOps JSON Patch operations
        """
        patch_operations = []
        field_mapping = {
            'title': 'System.Title',
            'description': 'System.Description',
            'steps': 'Microsoft.VSTS.TCM.Steps',
            'expected_results': 'Microsoft.VSTS.TCM.Parameters'
        }
        
        for generic_field, azure_field in field_mapping.items():
            if generic_field in updates:
                patch_operations.append({
                    'op': 'replace',
                    'path': f'/fields/{azure_field}',
                    'value': updates[generic_field]
                })
        
        return patch_operations
    
    def _create_azure_description(self, test_case: Dict) -> str:
        """
        Create Azure DevOps-friendly description from test case data
        
        Args:
            test_case (Dict): Test case data
            
        Returns:
            str: Formatted description
        """
        description = test_case.get('description', '')
        
        if 'compliance_checks' in test_case:
            description += "\n\n**Compliance Checks:**"
            for check in test_case['compliance_checks']:
                status = "✅" if check.get('passed', False) else "❌"
                description += f"\n{status} {check.get('standard', 'Unknown')}: {check.get('requirement', '')}"
        
        return description
    
    def _format_test_steps(self, steps: List[str]) -> str:
        """
        Format test steps for Azure DevOps
        
        Args:
            steps (List[str]): Test steps
            
        Returns:
            str: Formatted test steps in Azure DevOps XML format
        """
        if not steps:
            steps = ["Execute test", "Verify results"]
        
        xml_steps = '<steps id="0" last="{}">'.format(len(steps))
        for i, step in enumerate(steps, 1):
            xml_steps += f'''
            <step id="{i}" type="ActionStep">
                <parameterizedString isformatted="true">{step}</parameterizedString>
                <parameterizedString isformatted="true">Expected result</parameterizedString>
                <description/>
            </step>'''
        
        xml_steps += '</steps>'
        return xml_steps
    
    def _parse_test_steps(self, steps_xml: str) -> List[str]:
        """
        Parse test steps from Azure DevOps XML format
        
        Args:
            steps_xml (str): XML formatted test steps
            
        Returns:
            List[str]: List of test steps
        """
        if not steps_xml:
            return []
        
        # Simple XML parsing - in production, use proper XML parser
        steps = []
        lines = steps_xml.split('\n')
        for line in lines:
            if 'parameterizedString' in line and 'ActionStep' in line:
                # Extract step text between tags
                start = line.find('>') + 1
                end = line.find('</', start)
                if start > 0 and end > start:
                    step_text = line[start:end].strip()
                    if step_text and not step_text.startswith('Expected result'):
                        steps.append(step_text)
        
        return steps if steps else ["Execute test", "Verify results"]
    
    def _format_test_data(self, test_data: Dict) -> str:
        """
        Format test data for Azure DevOps
        
        Args:
            test_data (Dict): Test data
            
        Returns:
            str: Formatted test data
        """
        if not test_data:
            return "No test data specified"
        
        formatted_data = "Test Data:\n"
        for key, value in test_data.items():
            formatted_data += f"{key}: {value}\n"
        
        return formatted_data.strip()
    
    def create_test_plan(self, plan_name: str, project: str, description: str = "") -> Dict:
        """
        Create a test plan in Azure DevOps
        
        Args:
            plan_name (str): Name of the test plan
            project (str): Azure DevOps project name
            description (str): Test plan description
            
        Returns:
            Dict: Created test plan details
        """
        plan_url = f"{self.base_url}/{project}/_apis/testplan/plans?api-version={self.api_version}"
        
        plan_data = {
            'name': plan_name,
            'description': description,
            'areaPath': f"{project}\\Test",
            'iteration': f"{project}\\Iteration 1"
        }
        
        try:
            response = self._make_request('post', plan_url, json=plan_data)
            created_plan = response.json()
            
            logger.info(f"Created Azure DevOps test plan: {created_plan['id']}")
            return created_plan
            
        except Exception as e:
            logger.error(f"Failed to create Azure DevOps test plan: {e}")
            raise
    
    def add_test_cases_to_plan(self, plan_id: str, test_case_ids: List[str], project: str) -> Dict:
        """
        Add test cases to a test plan
        
        Args:
            plan_id (str): Test plan ID
            test_case_ids (List[str]): List of test case IDs to add
            project (str): Azure DevOps project name
            
        Returns:
            Dict: Operation result
        """
        add_url = f"{self.base_url}/{project}/_apis/testplan/plans/{plan_id}/suites/root/testcases?api-version={self.api_version}"
        
        test_cases_data = [{'id': case_id} for case_id in test_case_ids]
        
        try:
            response = self._make_request('post', add_url, json=test_cases_data)
            result = response.json()
            
            logger.info(f"Added {len(test_case_ids)} test cases to plan {plan_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to add test cases to plan {plan_id}: {e}")
            raise