"""
Base abstract optimizer class for production optimization.
This module provides the foundation for all optimizer implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import gurobipy as gp
from gurobipy import GRB
from core.validation import validate_optimization_input, validate_solution_feasibility

class ProductionOptimizerBase(ABC):
    """
    Base abstract class for all production optimization variants
    """
    
    def __init__(self, model_name: str = "production_optimization"):
        self.model_name = model_name
    
    @abstractmethod
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method that all optimizer variants must implement
        
        Args:
            data: Dictionary containing optimization input data
            
        Returns:
            Dictionary with optimization results
        """
        # Get common data
        objective_type, products, resources, resource_usage = self._extract_common_data(data)
        
        # Create model
        model = self._create_model()
        
        # Create variables
        production_vars = self._create_production_variables(model, products)
        
        # Set objective
        self._set_objective(model, objective_type, products, production_vars)
        
        # Add constraints
        self._add_constraints(model, resources, products, production_vars, resource_usage, data)
        
        # Optimize
        model.optimize()
        
        # Return result
        return self._prepare_result(model, production_vars, resources, resource_usage)
    
    def validate_and_solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input data and solve the optimization problem
        
        Args:
            data: Dictionary containing optimization input data
            
        Returns:
            Dictionary with optimization results and validation info
        """
        # Validate input data
        is_valid, validation_errors = validate_optimization_input(data)
        if not is_valid:
            return {
                'status': 'validation_error',
                'solver_message': 'Input validation failed',
                'validation_errors': validation_errors
            }
        
        # If validation passed, solve the problem
        result = self.solve(data)
        
        # Validate solution feasibility
        if result['status'] == 'optimal':
            is_feasible, feasibility_warnings = validate_solution_feasibility(result, data)
            if not is_feasible:
                result['status'] = 'solution_warning'
                result['feasibility_warnings'] = feasibility_warnings
            elif len(feasibility_warnings) > 0:
                # Solution is feasible but with warnings
                result['feasibility_warnings'] = feasibility_warnings
        
        return result
    
    def _extract_common_data(self, data: Dict[str, Any]) -> tuple:
        """
        Extract common data elements from input
        
        Args:
            data: Dictionary containing optimization input data
            
        Returns:
            Tuple containing (objective_type, products, resources, resource_usage)
        """
        objective_type = data['objective']
        products = {p['name']: p for p in data['products']}
        resources = {r['name']: r for r in data['resources']}
        
        # Create a dictionary to store resource usage by product and resource
        resource_usage = {}
        for ru in data['resource_usage']:
            product_name = ru['product_name']
            resource_name = ru['resource_name']
            if product_name not in resource_usage:
                resource_usage[product_name] = {}
            resource_usage[product_name][resource_name] = ru['usage_per_unit']
            
        return objective_type, products, resources, resource_usage
    
    def _create_model(self) -> gp.Model:
        """
        Create a new Gurobi model with the given name
        
        Returns:
            Gurobi model instance
        """
        model = gp.Model(self.model_name)
        # Set some parameters to improve numerical stability
        model.setParam('NumericFocus', 3)  # Higher focus on numerical accuracy
        model.setParam('FeasibilityTol', 1e-6)  # Tighter feasibility tolerance
        return model
    
    def _set_objective(self, model: gp.Model, objective_type: str, 
                      products: Dict[str, Dict], production_vars: Dict[str, gp.Var]) -> None:
        """
        Set the objective function based on the objective type
        
        Args:
            model: Gurobi model instance
            objective_type: String specifying objective ('maximize_profit' or 'minimize_cost')
            products: Dictionary of product information
            production_vars: Dictionary of Gurobi variables for production quantities
        """
        objective = gp.LinExpr()
        
        if objective_type == 'maximize_profit':
            for product_name, product in products.items():
                objective += product['profit_per_unit'] * production_vars[product_name]
            model.setObjective(objective, GRB.MAXIMIZE)
        else:  # minimize_cost
            for product_name, product in products.items():
                objective += product['cost_per_unit'] * production_vars[product_name]
            model.setObjective(objective, GRB.MINIMIZE)
    
    def _add_resource_constraints(self, model: gp.Model, resources: Dict[str, Dict], 
                                 products: Dict[str, Dict], production_vars: Dict[str, gp.Var], 
                                 resource_usage: Dict[str, Dict]) -> None:
        """
        Add resource constraints to the model
        
        Args:
            model: Gurobi model instance
            resources: Dictionary of resource information
            products: Dictionary of product information
            production_vars: Dictionary of Gurobi variables for production quantities
            resource_usage: Dictionary of resource usage by products
        """
        for resource_name, resource in resources.items():
            constraint = gp.LinExpr()
            for product_name in products:
                if product_name in resource_usage and resource_name in resource_usage[product_name]:
                    constraint += resource_usage[product_name][resource_name] * production_vars[product_name]
            model.addConstr(constraint <= resource['available_capacity'], name=f"resource_{resource_name}")
    
    def _add_total_product_constraints(self, model: gp.Model, products: Dict[str, Dict],
                                    production_vars: Dict[str, gp.Var], 
                                    total_constraints: Dict[str, float]) -> None:
        """
        Add constraints on the total number of products to be manufactured
        
        Args:
            model: Gurobi model instance
            products: Dictionary of product information
            production_vars: Dictionary of Gurobi variables for production quantities
            total_constraints: Dictionary with min_total and/or max_total constraints
        """
        if not total_constraints:
            return
            
        # Create expression for the sum of all production variables
        total_production = gp.LinExpr()
        for product_name in products:
            total_production += production_vars[product_name]
        
        # Add minimum total constraint if specified
        if 'min_total' in total_constraints and total_constraints['min_total'] is not None:
            min_total = float(total_constraints['min_total'])  # Ensure it's a float
            if min_total > 0:  # Only add if positive
                model.addConstr(total_production >= min_total, name="min_total_production")
        
        # Add maximum total constraint if specified
        if 'max_total' in total_constraints and total_constraints['max_total'] is not None:
            max_total = float(total_constraints['max_total'])  # Ensure it's a float
            if max_total > 0:  # Only add if positive
                model.addConstr(total_production <= max_total, name="max_total_production")
    
    def _get_resource_utilization(self, model: gp.Model, resources: Dict[str, Dict], 
                                production_vars: Dict[str, gp.Var], resource_usage: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Calculate resource utilization from model solution and resource usage
        
        Args:
            model: Gurobi model instance
            resources: Dictionary of resource information
            production_vars: Dictionary of Gurobi variables for production quantities
            resource_usage: Dictionary of resource usage by products
            
        Returns:
            Dictionary containing resource utilization information
        """
        utilization = {}
        
        # Calculate actual resource usage based on production plan
        for resource_name, resource in resources.items():
            available = resource['available_capacity']
            used = 0.0
            
            # Calculate used amount for each resource
            for product_name, product_usage in resource_usage.items():
                if resource_name in product_usage and product_name in production_vars:
                    var = production_vars[product_name]
                    # Only add to usage if variable has a value (model is solved)
                    if var.x is not None:
                        used += product_usage[resource_name] * var.x
            
            utilization[resource_name] = {
                'used': used,
                'available': available,
                'utilization_pct': (used / available) * 100 if available > 0 else 0
            }
        
        return utilization
    
    def _calculate_total_production(self, production_vars: Dict[str, gp.Var]) -> float:
        """
        Calculate the total production quantity across all products
        
        Args:
            production_vars: Dictionary of Gurobi variables for production quantities
            
        Returns:
            Total production quantity
        """
        total = 0.0
        for _, var in production_vars.items():
            if var.x is not None:
                total += var.x
        return total
    
    def _prepare_result(self, model: gp.Model, production_vars: Dict[str, gp.Var], 
                    resources: Dict[str, Dict], resource_usage: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Prepare result dictionary based on optimization outcome
        
        Args:
            model: Gurobi model instance
            production_vars: Dictionary of Gurobi variables for production quantities
            resources: Dictionary of resource information
            resource_usage: Dictionary of resource usage by products
            
        Returns:
            Dictionary containing optimization results
        """
        if model.status == GRB.OPTIMAL:
            # Round small values to zero to handle numerical precision issues
            epsilon = 1e-8
            production_plan = {}
            for name, var in production_vars.items():
                value = var.x
                if abs(value) < epsilon:
                    value = 0.0
                production_plan[name] = value
                
            # Calculate total production
            total_production = self._calculate_total_production(production_vars)
                
            result = {
                'status': 'optimal',
                'objective_value': model.objVal,
                'production_plan': production_plan,
                'resource_utilization': self._get_resource_utilization(model, resources, production_vars, resource_usage),
                'total_production': total_production,
                'solver_message': 'Optimal solution found'
            }
        elif model.status == GRB.INFEASIBLE:
            # Try to get infeasibility analysis
            model.computeIIS()
            infeasible_constraints = []
            for c in model.getConstrs():
                if c.IISConstr:
                    infeasible_constraints.append(c.ConstrName)
            
            result = {
                'status': 'infeasible',
                'solver_message': 'The model is infeasible',
                'infeasible_constraints': infeasible_constraints if infeasible_constraints else "Unknown"
            }
        elif model.status == GRB.UNBOUNDED:
            result = {
                'status': 'unbounded',
                'solver_message': 'The model is unbounded (no finite optimal solution exists)'
            }
        else:
            result = {
                'status': 'error',
                'solver_message': f'Optimization status: {model.status}'
            }
        
        return result