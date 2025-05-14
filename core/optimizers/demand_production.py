"""
Demand-constrained production optimization solver.
This module implements production optimization with minimum and maximum demand constraints.
"""

from typing import Dict, Any
import gurobipy as gp
from gurobipy import GRB
from core.optimizers.basic_production import BasicProductionOptimizer


class DemandConstrainedOptimizer(BasicProductionOptimizer):
    """
    Production optimization with demand constraints
    """
    
    def __init__(self):
        super().__init__()
        self.model_name = "demand_constrained_optimization"
    
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve production optimization problem with demand constraints
        
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
            
            # Process demand constraints or use empty dict if not provided
            demand_constraints = {}
            if 'demand_constraints' in data:
                demand_constraints = {d['product_name']: d for d in data['demand_constraints']}
            
            # Create variables with demand constraints
            production_vars = self._create_production_variables_with_demand(model, products, demand_constraints)
            
            # Set objective
            self._set_objective(model, objective_type, products, production_vars)
            
            # Add resource constraints
            self._add_resource_constraints(model, resources, products, production_vars, resource_usage)
            
            # Add total product constraints if specified
            if 'total_constraints' in data and data['total_constraints']:
                self._add_total_product_constraints(model, products, production_vars, data['total_constraints'])
            
            # Optimize the model
            model.optimize()
            
            # Prepare results
            return self._prepare_result(model, production_vars, resources, resource_usage)
        
        except Exception as e:
            return {
                'status': 'error',
                'solver_message': str(e)
            }
    
    def _create_production_variables_with_demand(self, model: gp.Model, products: Dict[str, Dict], 
                                              demand_constraints: Dict[str, Dict]) -> Dict[str, gp.Var]:
        """
        Create production decision variables with demand constraints
        
        Args:
            model: Gurobi model instance
            products: Dictionary of product information
            demand_constraints: Dictionary of demand constraints
            
        Returns:
            Dictionary of Gurobi variables for production quantities
        """
        production_vars = {}
        for product_name in products:
            lb = 0.0
            ub = float('inf')
            
            # Apply demand constraints if they exist
            if product_name in demand_constraints:
                constraint = demand_constraints[product_name]
                
                if 'min_demand' in constraint and constraint['min_demand'] is not None:
                    lb = max(0.0, constraint['min_demand'])  # Ensure non-negative
                
                if 'max_demand' in constraint and constraint['max_demand'] is not None:
                    ub = constraint['max_demand']
                    # If min > max, use min as both (will be caught in validation but prevent solver error)
                    if lb > ub:
                        ub = lb
            
            production_vars[product_name] = model.addVar(
                name=f"produce_{product_name}",
                vtype=GRB.CONTINUOUS,
                lb=lb,
                ub=ub
            )
        return production_vars