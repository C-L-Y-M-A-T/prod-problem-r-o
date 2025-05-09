"""
Base abstract optimizer class for production optimization.
This module provides the foundation for all optimizer implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import gurobipy as gp
from gurobipy import GRB

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
        pass
    
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
        return gp.Model(self.model_name)
    
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
    
    def _get_resource_utilization(self, model: gp.Model, resources: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Calculate resource utilization from model constraints
        
        Args:
            model: Gurobi model instance
            resources: Dictionary of resource information
            
        Returns:
            Dictionary containing resource utilization information
        """
        utilization = {}
        for resource_name in resources:
            constr_name = f"resource_{resource_name}"
            if constr_name in model.getConstrs():
                constr = model.getConstrByName(constr_name)
                utilization[resource_name] = {
                    'used': constr.getRHS() - constr.getSlack(),
                    'available': constr.getRHS(),
                    'utilization_pct': ((constr.getRHS() - constr.getSlack()) / constr.getRHS()) * 100 
                                      if constr.getRHS() > 0 else 0
                }
        return utilization
    
    def _prepare_result(self, model: gp.Model, production_vars: Dict[str, gp.Var], 
                       resources: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Prepare result dictionary based on optimization outcome
        
        Args:
            model: Gurobi model instance
            production_vars: Dictionary of Gurobi variables for production quantities
            resources: Dictionary of resource information
            
        Returns:
            Dictionary containing optimization results
        """
        if model.status == GRB.OPTIMAL:
            result = {
                'status': 'optimal',
                'objective_value': model.objVal,
                'production_plan': {name: var.x for name, var in production_vars.items()},
                'resource_utilization': self._get_resource_utilization(model, resources),
                'solver_message': 'Optimal solution found'
            }
        elif model.status == GRB.INFEASIBLE:
            result = {
                'status': 'infeasible',
                'solver_message': 'The model is infeasible'
            }
        else:
            result = {
                'status': 'error',
                'solver_message': f'Optimization status: {model.status}'
            }
        
        return result