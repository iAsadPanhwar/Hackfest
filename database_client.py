import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

class DatabaseClient:
    def __init__(self):
        """
        Initialize the Database client with PostgreSQL connection
        """
        self.conn = None
        self.connect()
    
    def connect(self):
        """Connect to the PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            print("Database connection successful")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise
    
    def _get_cursor(self):
        """Get a cursor with dictionary-like results"""
        if not self.conn or self.conn.closed:
            self.connect()
        return self.conn.cursor(cursor_factory=RealDictCursor)
    
    def get_employees(self):
        """Fetch all employees from the database"""
        try:
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM employees ORDER BY id")
            result = cursor.fetchall()
            cursor.close()
            # Convert RealDictRow objects to regular dictionaries
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Error fetching employees: {e}")
            return []
    
    def get_employee_by_id(self, employee_id):
        """
        Fetch an employee by ID
        
        Args:
            employee_id (int): The ID of the employee to fetch
            
        Returns:
            dict: Employee data or None if not found
        """
        try:
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            print(f"Error fetching employee by ID: {e}")
            return None
    
    def get_employees_by_condition(self, column, operator, value):
        """
        Fetch employees based on a condition
        
        Args:
            column (str): The column to filter on
            operator (str): The operator to use ('eq', 'gt', 'lt', 'lte', 'gte', 'like')
            value: The value to compare against
            
        Returns:
            list: List of matching employees
        """
        operator_map = {
            'eq': '=',
            'gt': '>',
            'lt': '<',
            'lte': '<=',
            'gte': '>=',
            'like': 'LIKE'
        }
        
        if operator not in operator_map:
            raise ValueError(f"Invalid operator: {operator}")
        
        sql_operator = operator_map[operator]
        
        try:
            cursor = self._get_cursor()
            # Use parameterized query to prevent SQL injection
            if operator == 'like':
                value = f"%{value}%"
                
            query = f"SELECT * FROM employees WHERE {column} {sql_operator} %s ORDER BY id"
            cursor.execute(query, (value,))
            result = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Error querying employees by condition: {e}")
            return []
    
    def insert_employee(self, employee_data):
        """
        Insert a new employee into the database
        
        Args:
            employee_data (dict): The employee data to insert
            
        Returns:
            dict: The inserted employee data or None if failed
        """
        try:
            cursor = self._get_cursor()
            columns = ', '.join(employee_data.keys())
            placeholders = ', '.join(['%s'] * len(employee_data))
            query = f"INSERT INTO employees ({columns}) VALUES ({placeholders}) RETURNING *"
            cursor.execute(query, list(employee_data.values()))
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting employee: {e}")
            return None
    
    def update_employee(self, employee_id, employee_data):
        """
        Update an existing employee in the database
        
        Args:
            employee_id (int): The ID of the employee to update
            employee_data (dict): The updated employee data
            
        Returns:
            dict: The updated employee data or None if failed
        """
        try:
            cursor = self._get_cursor()
            set_clause = ', '.join([f"{key} = %s" for key in employee_data.keys()])
            values = list(employee_data.values()) + [employee_id]
            query = f"UPDATE employees SET {set_clause} WHERE id = %s RETURNING *"
            cursor.execute(query, values)
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            self.conn.rollback()
            print(f"Error updating employee: {e}")
            return None
    
    def delete_employee(self, employee_id):
        """
        Delete an employee from the database
        
        Args:
            employee_id (int): The ID of the employee to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cursor = self._get_cursor()
            cursor.execute("DELETE FROM employees WHERE id = %s RETURNING id", (employee_id,))
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            return result is not None
        except Exception as e:
            self.conn.rollback()
            print(f"Error deleting employee: {e}")
            return False
    
    def get_refund_requests(self):
        """Fetch all refund requests from the database"""
        try:
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM refund_requests ORDER BY id")
            result = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Error fetching refund requests: {e}")
            return []
    
    def get_refund_request_by_id(self, request_id):
        """
        Fetch a refund request by ID
        
        Args:
            request_id (int): The ID of the refund request to fetch
            
        Returns:
            dict: Refund request data or None if not found
        """
        try:
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM refund_requests WHERE id = %s", (request_id,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            print(f"Error fetching refund request by ID: {e}")
            return None
    
    def update_refund_request(self, request_id, request_data):
        """
        Update an existing refund request in the database
        
        Args:
            request_id (int): The ID of the refund request to update
            request_data (dict): The updated refund request data
            
        Returns:
            dict: The updated refund request data or None if failed
        """
        try:
            cursor = self._get_cursor()
            set_clause = ', '.join([f"{key} = %s" for key in request_data.keys()])
            values = list(request_data.values()) + [request_id]
            query = f"UPDATE refund_requests SET {set_clause} WHERE id = %s RETURNING *"
            cursor.execute(query, values)
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            self.conn.rollback()
            print(f"Error updating refund request: {e}")
            return None
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None