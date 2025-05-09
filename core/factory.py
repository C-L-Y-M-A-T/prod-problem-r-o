"""
Factory module for creating optimizer instances.
This module provides a factory pattern implementation for creating appropriate optimizers.
"""

import importlib
import pkgutil
import inspect
from typing import Dict, Type, Any, List
from core.optimizers.base import ProductionOptimizerBase
import core.optimizers as optimizers_pkg
from core.validation import validate_optimization_input, validate_solution_feasibility


class OptimizerFactory:
    """
    Factory to create appropriate optimizer instances based on type
    """
    
    _optimizers: Dict[str, Type[ProductionOptimizerBase]] = {}
    
    @classmethod
    def register_optimizer(cls, optimizer_type: str, optimizer_class: Type[ProductionOptimizerBase]) -> None:
        """
        Register a new optimizer type
        
        Args:
            optimizer_type: String identifier for the optimizer
            optimizer_class: Class reference for the optimizer implementation
        """
        cls._optimizers[optimizer_type] = optimizer_class
    
    @classmethod
    def get_optimizer(cls, optimizer_type: str) -> ProductionOptimizerBase:
        """
        Get an optimizer instance by type
        
        Args:
            optimizer_type: String identifier for the desired optimizer type
            
        Returns:
            Instance of the requested optimizer type
            
        Raises:
            ValueError: If the optimizer type is not registered
        """
        optimizer_class = cls._optimizers.get(optimizer_type)
        if not optimizer_class:
            raise ValueError(f"Unknown optimizer type: {optimizer_type}")
        return optimizer_class()
    
    @classmethod
    def optimize(cls, optimizer_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input data and solve the optimization problem
        
        Args:
            optimizer_type: String identifier for the desired optimizer type
            data: Dictionary containing optimization input data
            
        Returns:
            Dictionary with optimization results and validation info
            
        Raises:
            ValueError: If the optimizer type is not registered
        """
        try:
            # Validate input data
            is_valid, validation_errors = validate_optimization_input(data)
            if not is_valid:
                return {
                    'status': 'validation_error',
                    'solver_message': 'Input validation failed',
                    'validation_errors': validation_errors
                }
            
            # Get the optimizer and solve
            optimizer = cls.get_optimizer(optimizer_type)
            result = optimizer.solve(data)
            
            # Validate solution feasibility if optimal
            if result['status'] == 'optimal':
                is_feasible, feasibility_warnings = validate_solution_feasibility(result, data)
                if not is_feasible:
                    result['status'] = 'solution_warning'
                    result['feasibility_warnings'] = feasibility_warnings
                elif feasibility_warnings:
                    # Solution is feasible but with warnings
                    result['feasibility_warnings'] = feasibility_warnings
            
            return result
        except ValueError as e:
            return {'status': 'error', 'solver_message': str(e)}
    
    @classmethod
    def discover_optimizers(cls) -> None:
        """
        Auto-discover and register all optimizer classes in the optimizers package
        """
        for _, name, _ in pkgutil.iter_modules(optimizers_pkg.__path__, optimizers_pkg.__name__ + '.'):
            module = importlib.import_module(name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                # Register only if it's a subclass of ProductionOptimizerBase but not the base class itself
                if (issubclass(obj, ProductionOptimizerBase) and 
                    obj is not ProductionOptimizerBase and
                    hasattr(obj, '__name__')):
                    
                    # Convert CamelCase class name to kebab-case type name
                    class_name = obj.__name__
                    if class_name.endswith('Optimizer'):
                        class_name = class_name[:-9]  # Remove 'Optimizer' suffix
                    
                    # Convert CamelCase to kebab-case
                    optimizer_type = ''.join(['-' + c.lower() if c.isupper() else c 
                                           for c in class_name]).lstrip('-')
                    
                    cls.register_optimizer(optimizer_type, obj)
    
    @classmethod
    def list_available_optimizers(cls) -> List[str]:
        """
        List all available optimizer types
        
        Returns:
            List of registered optimizer type names
        """
        return list(cls._optimizers.keys())


# Register standard optimizers explicitly
from core.optimizers.basic_production import BasicProductionOptimizer
from core.optimizers.demand_production import DemandConstrainedOptimizer

OptimizerFactory.register_optimizer('basic', BasicProductionOptimizer)
OptimizerFactory.register_optimizer('demand-constrained', DemandConstrainedOptimizer)

# Discover any additional optimizers
OptimizerFactory.discover_optimizers()