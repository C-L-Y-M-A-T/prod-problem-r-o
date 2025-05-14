"""
Basic production optimization solver.
This module implements basic production optimization without demand constraints.
"""

from typing import Dict, Any
import gurobipy as gp
from gurobipy import GRB
from core.optimizers.base import ProductionOptimizerBase


class BasicProductionOptimizer(ProductionOptimizerBase):
    """
    Basic production optimization solver without demand constraints
    """
    
    def __init__(self):
        super().__init__("basic_production_optimization")
    
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve basic production optimization problem
        
        Args:
            data: Dictionary containing optimization input data
            
        Returns:
            Dictionary with optimization results
        """
        try:
            # Create a new model
            model = self._create_model()
            
            # Extract data
            objective_type, products, resources, resource_usage = self._extract_common_data(data)
            
            # Create variables
            production_vars = self._create_production_variables(model, products)
            
            # Set objective
            self._set_objective(model, objective_type, products, production_vars)
            
            # Add resource constraints
            self._add_resource_constraints(model, resources, products, production_vars, resource_usage)
            
            # Add total product constraints if specified
            if 'total_constraints' in data and data['total_constraints']:
                self._add_total_product_constraints(model, products, production_vars, data['total_constraints'])
            
            # Add non-negativity constraints (already included in variable definition)
            
            # Optimize the model
            model.optimize()
            
            # Prepare results
            return self._prepare_result(model, production_vars, resources, resource_usage)
        
        except Exception as e:
            return {
                'status': 'error',
                'solver_message': str(e)
            }

    
    def _create_production_variables(self, model: gp.Model, products: Dict[str, Dict]) -> Dict[str, gp.Var]:
        """
        Create production decision variables
        
        Args:
            model: Gurobi model instance
            products: Dictionary of product information
            
        Returns:
            Dictionary of Gurobi variables for production quantities
        """
        production_vars = {}
        for product_name in products:
            production_vars[product_name] = model.addVar(
                name=f"produce_{product_name}",
                vtype=GRB.CONTINUOUS,
                lb=0.0
            )
        return production_vars