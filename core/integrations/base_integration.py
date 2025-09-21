import abc
import logging
from typing import Dict, List, Optional
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseIntegration(abc.ABC):
    """Abstract base class for all enterprise tool integrations"""
    
    def __init__(self, base_url: str, auth_token: str = None, 
                 username: str = None, password: str = None):
        """
        Initialize integration with connection details
        
        Args:
            base_url (str): Base URL of the enterprise tool
            auth_token (str, optional): Authentication token
            username (str, optional): Username for basic auth
            password (str, optional): Password for basic auth
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.username = username
        self.password = password
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with authentication"""
        session = requests.Session()
        
        if self.auth_token:
            session.headers.update({
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json'
            })
        elif self.username and self.password:
            session.auth = (self.username, self.password)
            session.headers.update({'Content-Type': 'application/json'})
        
        return session
    
    @abc.abstractmethod
    def create_test_case(self, test_case: Dict, project: str = None) -> Dict:
        """
        Create a test case in the enterprise tool
        
        Args:
            test_case (Dict): Test case data
            project (str, optional): Project identifier
            
        Returns:
            Dict: Created test case with tool-specific ID
        """
        pass
    
    @abc.abstractmethod
    def update_test_case(self, test_case_id: str, updates: Dict) -> Dict:
        """
        Update an existing test case
        
        Args:
            test_case_id (str): ID of the test case to update
            updates (Dict): Updates to apply
            
        Returns:
            Dict: Updated test case
        """
        pass
    
    @abc.abstractmethod
    def get_test_case(self, test_case_id: str) -> Dict:
        """
        Get a test case by ID
        
        Args:
            test_case_id (str): Test case ID
            
        Returns:
            Dict: Test case data
        """
        pass
    
    @abc.abstractmethod
    def search_test_cases(self, query: str, project: str = None) -> List[Dict]:
        """
        Search for test cases
        
        Args:
            query (str): Search query
            project (str, optional): Project to search in
            
        Returns:
            List[Dict]: Matching test cases
        """
        pass
    
    def test_connection(self) -> bool:
        """
        Test the connection to the enterprise tool
        
        Returns:
            bool: True if connection is successful
        """
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request to the enterprise tool
        
        Args:
            method (str): HTTP method (get, post, put, delete)
            endpoint (str): API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response: Response object
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            method = method.lower()
            if method == 'get':
                response = self.session.get(url, **kwargs)
            elif method == 'post':
                response = self.session.post(url, **kwargs)
            elif method == 'put':
                response = self.session.put(url, **kwargs)
            elif method == 'delete':
                response = self.session.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def _map_test_case_to_tool_format(self, test_case: Dict) -> Dict:
        """
        Map generic test case format to tool-specific format
        
        Args:
            test_case (Dict): Generic test case data
            
        Returns:
            Dict: Tool-specific test case data
        """
        # This is a generic mapping that can be overridden by specific integrations
        return {
            'title': test_case.get('title', ''),
            'description': test_case.get('description', ''),
            'priority': test_case.get('priority', 'Medium'),
            'steps': test_case.get('steps', []),
            'expected_results': test_case.get('expected_results', ''),
            'custom_fields': {
                'compliance_checks': test_case.get('compliance_checks', []),
                'test_data': test_case.get('test_data', {})
            }
        }
    
    def _map_tool_format_to_generic(self, tool_test_case: Dict) -> Dict:
        """
        Map tool-specific test case format to generic format
        
        Args:
            tool_test_case (Dict): Tool-specific test case data
            
        Returns:
            Dict: Generic test case data
        """
        # This is a generic mapping that can be overridden by specific integrations
        return {
            'id': tool_test_case.get('id', ''),
            'title': tool_test_case.get('title', ''),
            'description': tool_test_case.get('description', ''),
            'priority': tool_test_case.get('priority', 'Medium'),
            'steps': tool_test_case.get('steps', []),
            'expected_results': tool_test_case.get('expected_results', ''),
            'compliance_checks': tool_test_case.get('custom_fields', {}).get('compliance_checks', []),
            'test_data': tool_test_case.get('custom_fields', {}).get('test_data', {})
        }
    
    def batch_import_test_cases(self, test_cases: List[Dict], project: str = None) -> List[Dict]:
        """
        Import multiple test cases in batch
        
        Args:
            test_cases (List[Dict]): List of test cases to import
            project (str, optional): Project identifier
            
        Returns:
            List[Dict]: List of imported test cases with tool-specific IDs
        """
        imported_cases = []
        
        for test_case in test_cases:
            try:
                imported_case = self.create_test_case(test_case, project)
                imported_cases.append(imported_case)
                logger.info(f"Successfully imported test case: {imported_case.get('id')}")
            except Exception as e:
                logger.error(f"Failed to import test case: {e}")
                # Continue with next test case
        
        return imported_cases
    
    def export_test_cases(self, query: str = None, project: str = None) -> List[Dict]:
        """
        Export test cases from the enterprise tool
        
        Args:
            query (str, optional): Search query for filtering
            project (str, optional): Project to export from
            
        Returns:
            List[Dict]: Exported test cases in generic format
        """
        test_cases = self.search_test_cases(query, project)
        return [self._map_tool_format_to_generic(tc) for tc in test_cases]