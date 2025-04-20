import streamlit as st
import pandas as pd

class EmployeeManagement:
    def __init__(self, db_client):
        """
        Initialize the Employee Management component
        
        Args:
            db_client (DatabaseClient): The initialized Database client
        """
        self.db_client = db_client
    
    def display(self):
        """Display the employee management interface"""
        st.header("Employee Management")
        
        # Create tabs for different operations
        tabs = st.tabs(["View Employees", "Add Employee", "Update Employee", "Delete Employee", "Query Employees"])
        
        # View Employees tab
        with tabs[0]:
            self.display_employees()
        
        # Add Employee tab
        with tabs[1]:
            self.add_employee_form()
        
        # Update Employee tab
        with tabs[2]:
            self.update_employee_form()
        
        # Delete Employee tab
        with tabs[3]:
            self.delete_employee_form()
        
        # Query Employees tab
        with tabs[4]:
            self.query_employees_form()
    
    def display_employees(self):
        """Display all employees in a table"""
        st.subheader("All Employees")
        
        # Add refresh button
        if st.button("Refresh Employee Data", key="refresh_employees"):
            st.session_state.pop('employees', None)
        
        # Fetch employees if not already in session state
        if 'employees' not in st.session_state:
            with st.spinner("Fetching employees..."):
                st.session_state.employees = self.db_client.get_employees()
        
        # Display employees in a table
        if st.session_state.employees:
            df = pd.DataFrame(st.session_state.employees)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No employees found in the database.")
    
    def add_employee_form(self):
        """Display form to add a new employee"""
        st.subheader("Add New Employee")
        
        # Create a form
        with st.form("add_employee_form"):
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=18, max_value=100, step=1)
            salary = st.number_input("Salary", min_value=0.0, step=1000.0)
            
            submit = st.form_submit_button("Add Employee")
            
            if submit:
                if not name:
                    st.error("Name is required")
                else:
                    # Create employee data dictionary
                    employee_data = {
                        "name": name,
                        "age": age,
                        "salary": salary
                    }
                    
                    # Insert employee
                    with st.spinner("Adding employee..."):
                        result = self.db_client.insert_employee(employee_data)
                        
                        if result:
                            st.success(f"Employee {name} added successfully!")
                            # Refresh employees in session state
                            st.session_state.pop('employees', None)
                            # Rerun to show updated data
                            st.rerun()
                        else:
                            st.error("Failed to add employee")
    
    def update_employee_form(self):
        """Display form to update an existing employee"""
        st.subheader("Update Employee")
        
        # Fetch employees for selection
        if 'employees' not in st.session_state:
            with st.spinner("Fetching employees..."):
                st.session_state.employees = self.db_client.get_employees()
        
        if not st.session_state.employees:
            st.info("No employees available to update.")
            return
        
        # Create employee selection dropdown
        employee_options = {f"{emp['name']} (ID: {emp['id']})": emp['id'] for emp in st.session_state.employees}
        selected_employee_label = st.selectbox("Select Employee to Update", options=list(employee_options.keys()))
        selected_employee_id = employee_options[selected_employee_label]
        
        # Get current employee data
        current_employee = next((emp for emp in st.session_state.employees if emp['id'] == selected_employee_id), None)
        
        if current_employee:
            # Create update form
            with st.form("update_employee_form"):
                name = st.text_input("Name", value=current_employee['name'])
                age = st.number_input("Age", min_value=18, max_value=100, step=1, value=current_employee['age'])
                salary = st.number_input("Salary", min_value=0.0, step=1000.0, value=current_employee['salary'])
                
                submit = st.form_submit_button("Update Employee")
                
                if submit:
                    if not name:
                        st.error("Name is required")
                    else:
                        # Create updated employee data
                        updated_data = {
                            "name": name,
                            "age": age,
                            "salary": salary
                        }
                        
                        # Update employee
                        with st.spinner("Updating employee..."):
                            result = self.db_client.update_employee(selected_employee_id, updated_data)
                            
                            if result:
                                st.success(f"Employee {name} updated successfully!")
                                # Refresh employees in session state
                                st.session_state.pop('employees', None)
                                # Rerun to show updated data
                                st.rerun()
                            else:
                                st.error("Failed to update employee")
    
    def delete_employee_form(self):
        """Display form to delete an employee"""
        st.subheader("Delete Employee")
        
        # Fetch employees for selection
        if 'employees' not in st.session_state:
            with st.spinner("Fetching employees..."):
                st.session_state.employees = self.db_client.get_employees()
        
        if not st.session_state.employees:
            st.info("No employees available to delete.")
            return
        
        # Create employee selection dropdown
        employee_options = {f"{emp['name']} (ID: {emp['id']})": emp['id'] for emp in st.session_state.employees}
        selected_employee_label = st.selectbox("Select Employee to Delete", options=list(employee_options.keys()))
        selected_employee_id = employee_options[selected_employee_label]
        
        # Confirm deletion
        if st.button("Delete Employee", key="delete_employee_button"):
            confirm = st.checkbox("Are you sure you want to delete this employee? This action cannot be undone.")
            
            if confirm:
                # Delete employee
                with st.spinner("Deleting employee..."):
                    result = self.db_client.delete_employee(selected_employee_id)
                    
                    if result:
                        st.success(f"Employee deleted successfully!")
                        # Refresh employees in session state
                        st.session_state.pop('employees', None)
                        # Rerun to show updated data
                        st.rerun()
                    else:
                        st.error("Failed to delete employee")
    
    def query_employees_form(self):
        """Display form to query employees based on criteria"""
        st.subheader("Query Employees")
        
        query_type = st.selectbox(
            "Select Query Type",
            [
                "Fetch by ID",
                "Age Filter",
                "Name Contains",
                "Name Starts With",
                "Salary Range",
                "Get Specific Fields"
            ]
        )
        
        if query_type == "Fetch by ID":
            employee_id = st.number_input("Employee ID", min_value=1, step=1)
            
            if st.button("Fetch Employee", key="fetch_by_id"):
                with st.spinner("Fetching employee..."):
                    employee = self.db_client.get_employee_by_id(employee_id)
                    
                    if employee:
                        st.success("Employee found!")
                        st.json(employee)
                    else:
                        st.error(f"No employee found with ID {employee_id}")
        
        elif query_type == "Age Filter":
            operator = st.selectbox("Operator", ["Less than", "Greater than", "Equal to"])
            age_value = st.number_input("Age", min_value=18, max_value=100, step=1)
            
            if st.button("Fetch Employees", key="fetch_by_age"):
                with st.spinner("Fetching employees..."):
                    operator_map = {
                        "Less than": "lt",
                        "Greater than": "gt",
                        "Equal to": "eq"
                    }
                    
                    employees = self.db_client.get_employees_by_condition("age", operator_map[operator], age_value)
                    
                    if employees:
                        st.success(f"Found {len(employees)} employees")
                        df = pd.DataFrame(employees)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No employees match the criteria")
        
        elif query_type == "Name Contains":
            name_contains = st.text_input("Name Contains")
            
            if st.button("Fetch Employees", key="fetch_by_name_contains"):
                if name_contains:
                    with st.spinner("Fetching employees..."):
                        employees = self.db_client.get_employees_by_condition("name", "like", name_contains)
                        
                        if employees:
                            st.success(f"Found {len(employees)} employees")
                            df = pd.DataFrame(employees)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info(f"No employees found with name containing '{name_contains}'")
                else:
                    st.warning("Please enter a name to search for")
        
        elif query_type == "Name Starts With":
            starts_with = st.text_input("Name Starts With")
            
            if st.button("Fetch Employees", key="fetch_by_name_starts"):
                if starts_with:
                    with st.spinner("Fetching employees..."):
                        # For starts with, we use like but only append % at the end
                        employees = self.db_client.get_employees_by_condition("name", "like", f"{starts_with}%")
                        
                        if employees:
                            st.success(f"Found {len(employees)} employees")
                            df = pd.DataFrame(employees)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info(f"No employees found with name starting with '{starts_with}'")
                else:
                    st.warning("Please enter a starting letter or prefix")
        
        elif query_type == "Salary Range":
            col1, col2 = st.columns(2)
            with col1:
                min_salary = st.number_input("Minimum Salary", min_value=0.0, step=1000.0)
            with col2:
                max_salary = st.number_input("Maximum Salary", min_value=0.0, step=1000.0, value=50000.0)
            
            if st.button("Fetch Employees", key="fetch_by_salary"):
                with st.spinner("Fetching employees..."):
                    employees_min = self.db_client.get_employees_by_condition("salary", "gte", min_salary)
                    employees_max = self.db_client.get_employees_by_condition("salary", "lte", max_salary)
                    
                    # Find intersection of both results
                    employee_ids_min = {emp['id'] for emp in employees_min}
                    employees_in_range = [emp for emp in employees_max if emp['id'] in employee_ids_min]
                    
                    if employees_in_range:
                        st.success(f"Found {len(employees_in_range)} employees")
                        df = pd.DataFrame(employees_in_range)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info(f"No employees found with salary between {min_salary} and {max_salary}")
        
        elif query_type == "Get Specific Fields":
            # This is a custom example to show how to get specific fields
            st.markdown("This query will return only names and ages of employees with 'a' in their name")
            
            if st.button("Run Query", key="custom_query"):
                with st.spinner("Fetching data..."):
                    # First get employees with 'a' in their name
                    employees = self.db_client.get_employees_by_condition("name", "like", "a")
                    
                    if employees:
                        # Extract only the required fields
                        filtered_data = [{"name": emp["name"], "age": emp["age"]} for emp in employees]
                        st.success(f"Found {len(filtered_data)} employees")
                        df = pd.DataFrame(filtered_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No employees found with 'a' in their name")