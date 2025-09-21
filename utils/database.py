import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manage SQLite database operations for test cases and application data"""
    
    def __init__(self, db_path: str = "data/testgen.db"):
        """
        Initialize database manager
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self.connection = None
        self._initialize_database()
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _initialize_database(self) -> None:
        """Initialize database with required tables"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            # Create tables
            self._create_tables()
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_tables(self) -> None:
        """Create required database tables"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'Medium',
                steps TEXT,  -- JSON array of steps
                expected_results TEXT,
                test_data TEXT,  -- JSON object
                compliance_checks TEXT,  -- JSON array
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_file TEXT,
                project_name TEXT,
                status TEXT DEFAULT 'draft'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                content TEXT,
                source_file TEXT,
                file_format TEXT,
                extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                project_name TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                compliance_standards TEXT  -- JSON array
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS compliance_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case_id TEXT NOT NULL,
                standard TEXT NOT NULL,
                requirement_id TEXT NOT NULL,
                passed BOOLEAN DEFAULT FALSE,
                evidence TEXT,
                issue TEXT,
                recommendation TEXT,
                check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_case_id) REFERENCES test_cases (test_case_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                export_id TEXT UNIQUE NOT NULL,
                export_format TEXT NOT NULL,
                test_cases_count INTEGER DEFAULT 0,
                exported_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT,
                project_name TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS integration_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                integration_type TEXT NOT NULL,
                operation TEXT NOT NULL,
                target_id TEXT,
                status TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        cursor = self.connection.cursor()
        for table_sql in tables:
            cursor.execute(table_sql)
        self.connection.commit()
    
    def save_test_case(self, test_case: Dict) -> str:
        """
        Save a test case to the database
        
        Args:
            test_case (Dict): Test case data
            
        Returns:
            str: Database ID of the saved test case
        """
        try:
            cursor = self.connection.cursor()
            
            # Prepare data for insertion
            steps_json = json.dumps(test_case.get('steps', []))
            test_data_json = json.dumps(test_case.get('test_data', {}))
            compliance_checks_json = json.dumps(test_case.get('compliance_checks', []))
            
            cursor.execute("""
                INSERT OR REPLACE INTO test_cases 
                (test_case_id, title, description, priority, steps, expected_results, 
                 test_data, compliance_checks, source_file, project_name, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_case.get('id'),
                test_case.get('title'),
                test_case.get('description'),
                test_case.get('priority', 'Medium'),
                steps_json,
                test_case.get('expected_results'),
                test_data_json,
                compliance_checks_json,
                test_case.get('source_file'),
                test_case.get('project_name'),
                test_case.get('status', 'draft')
            ))
            
            self.connection.commit()
            db_id = str(cursor.lastrowid)
            logger.info(f"Saved test case {test_case.get('id')} to database")
            return db_id
            
        except Exception as e:
            logger.error(f"Failed to save test case: {e}")
            raise
    
    def get_test_case(self, test_case_id: str) -> Optional[Dict]:
        """
        Get a test case by ID
        
        Args:
            test_case_id (str): Test case ID
            
        Returns:
            Optional[Dict]: Test case data or None if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM test_cases WHERE test_case_id = ?
            """, (test_case_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_test_case(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get test case {test_case_id}: {e}")
            return None
    
    def get_all_test_cases(self, project_name: Optional[str] = None) -> List[Dict]:
        """
        Get all test cases, optionally filtered by project
        
        Args:
            project_name (str, optional): Filter by project name
            
        Returns:
            List[Dict]: List of test cases
        """
        try:
            cursor = self.connection.cursor()
            
            if project_name:
                cursor.execute("""
                    SELECT * FROM test_cases WHERE project_name = ? ORDER BY created_date DESC
                """, (project_name,))
            else:
                cursor.execute("SELECT * FROM test_cases ORDER BY created_date DESC")
            
            rows = cursor.fetchall()
            return [self._row_to_test_case(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get test cases: {e}")
            return []
    
    def search_test_cases(self, query: str, project_name: Optional[str] = None) -> List[Dict]:
        """
        Search test cases by title or description
        
        Args:
            query (str): Search query
            project_name (str, optional): Filter by project name
            
        Returns:
            List[Dict]: Matching test cases
        """
        try:
            cursor = self.connection.cursor()
            search_pattern = f"%{query}%"
            
            if project_name:
                cursor.execute("""
                    SELECT * FROM test_cases 
                    WHERE (title LIKE ? OR description LIKE ?) 
                    AND project_name = ?
                    ORDER BY created_date DESC
                """, (search_pattern, search_pattern, project_name))
            else:
                cursor.execute("""
                    SELECT * FROM test_cases 
                    WHERE title LIKE ? OR description LIKE ? 
                    ORDER BY created_date DESC
                """, (search_pattern, search_pattern))
            
            rows = cursor.fetchall()
            return [self._row_to_test_case(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to search test cases: {e}")
            return []
    
    def _row_to_test_case(self, row: sqlite3.Row) -> Dict:
        """Convert database row to test case dictionary"""
        return {
            'id': row['test_case_id'],
            'title': row['title'],
            'description': row['description'],
            'priority': row['priority'],
            'steps': json.loads(row['steps']) if row['steps'] else [],
            'expected_results': row['expected_results'],
            'test_data': json.loads(row['test_data']) if row['test_data'] else {},
            'compliance_checks': json.loads(row['compliance_checks']) if row['compliance_checks'] else [],
            'created_date': row['created_date'],
            'last_modified': row['last_modified'],
            'source_file': row['source_file'],
            'project_name': row['project_name'],
            'status': row['status']
        }
    
    def save_requirement(self, requirement: Dict) -> str:
        """
        Save a requirement to the database
        
        Args:
            requirement (Dict): Requirement data
            
        Returns:
            str: Database ID of the saved requirement
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO requirements 
                (requirement_id, title, description, content, source_file, file_format, project_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                requirement.get('id'),
                requirement.get('title'),
                requirement.get('description'),
                requirement.get('content'),
                requirement.get('source_file'),
                requirement.get('file_format'),
                requirement.get('project_name')
            ))
            
            self.connection.commit()
            db_id = str(cursor.lastrowid)
            logger.info(f"Saved requirement {requirement.get('id')} to database")
            return db_id
            
        except Exception as e:
            logger.error(f"Failed to save requirement: {e}")
            raise
    
    def get_requirement(self, requirement_id: str) -> Optional[Dict]:
        """
        Get a requirement by ID
        
        Args:
            requirement_id (str): Requirement ID
            
        Returns:
            Optional[Dict]: Requirement data or None if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM requirements WHERE requirement_id = ?
            """, (requirement_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get requirement {requirement_id}: {e}")
            return None
    
    def save_compliance_result(self, result: Dict) -> str:
        """
        Save compliance check result
        
        Args:
            result (Dict): Compliance result data
            
        Returns:
            str: Database ID of the saved result
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO compliance_results 
                (test_case_id, standard, requirement_id, passed, evidence, issue, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result.get('test_case_id'),
                result.get('standard'),
                result.get('requirement_id'),
                result.get('passed', False),
                result.get('evidence'),
                result.get('issue'),
                result.get('recommendation')
            ))
            
            self.connection.commit()
            db_id = str(cursor.lastrowid)
            logger.info(f"Saved compliance result for test case {result.get('test_case_id')}")
            return db_id
            
        except Exception as e:
            logger.error(f"Failed to save compliance result: {e}")
            raise
    
    def get_compliance_results(self, test_case_id: str) -> List[Dict]:
        """
        Get compliance results for a test case
        
        Args:
            test_case_id (str): Test case ID
            
        Returns:
            List[Dict]: Compliance results
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM compliance_results WHERE test_case_id = ? ORDER BY check_date DESC
            """, (test_case_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get compliance results for {test_case_id}: {e}")
            return []
    
    def create_project(self, name: str, description: str = "", standards: List[str] = None) -> str:
        """
        Create a new project
        
        Args:
            name (str): Project name
            description (str): Project description
            standards (List[str]): Compliance standards
            
        Returns:
            str: Database ID of the created project
        """
        try:
            cursor = self.connection.cursor()
            standards_json = json.dumps(standards or [])
            
            cursor.execute("""
                INSERT OR REPLACE INTO projects (name, description, compliance_standards)
                VALUES (?, ?, ?)
            """, (name, description, standards_json))
            
            self.connection.commit()
            db_id = str(cursor.lastrowid)
            logger.info(f"Created project: {name}")
            return db_id
            
        except Exception as e:
            logger.error(f"Failed to create project {name}: {e}")
            raise
    
    def get_projects(self) -> List[Dict]:
        """
        Get all projects
        
        Returns:
            List[Dict]: List of projects
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY created_date DESC")
            
            rows = cursor.fetchall()
            projects = []
            for row in rows:
                project = dict(row)
                project['compliance_standards'] = json.loads(project['compliance_standards']) if project['compliance_standards'] else []
                projects.append(project)
            
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the database
        
        Args:
            backup_path (str, optional): Path for backup file
            
        Returns:
            bool: True if backup successful
        """
        try:
            if not backup_path:
                backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f"testgen_backup_{timestamp}.db")
            
            # Create backup
            backup_conn = sqlite3.connect(backup_path)
            with backup_conn:
                self.connection.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"Database backup created at {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return False
    
    def close(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Utility functions for standalone use
def save_test_case_to_db(test_case: Dict, db_path: str = "data/testgen.db") -> str:
    """
    Utility function to save test case without instantiating the class
    
    Args:
        test_case (Dict): Test case data
        db_path (str): Database path
        
    Returns:
        str: Database ID
    """
    with DatabaseManager(db_path) as db:
        return db.save_test_case(test_case)

def get_test_case_from_db(test_case_id: str, db_path: str = "data/testgen.db") -> Optional[Dict]:
    """
    Utility function to get test case without instantiating the class
    
    Args:
        test_case_id (str): Test case ID
        db_path (str): Database path
        
    Returns:
        Optional[Dict]: Test case data
    """
    with DatabaseManager(db_path) as db:
        return db.get_test_case(test_case_id)

