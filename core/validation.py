"""
Validation module for production optimization inputs.
This module provides functions to validate input data before optimization.
"""

from typing import Dict, Any, List, Tuple


def validate_optimization_input(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the input data for optimization
    
    Args:
        data: Dictionary containing optimization input data
            
    Returns:
        Tuple containing (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    required_fields = ['objective', 'products', 'resources', 'resource_usage']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Check objective
    if data['objective'] not in ['maximize_profit', 'minimize_cost']:
        errors.append("Objective must be either 'maximize_profit' or 'minimize_cost'")
    
    # Validate products
    product_names = set()
    for product in data['products']:
        # Check required product fields
        if 'name' not in product:
            errors.append("Each product must have a name")
            continue
            
        product_name = product['name']
        product_names.add(product_name)
        
        # Check for required product attributes
        if 'profit_per_unit' not in product:
            errors.append(f"Product '{product_name}' is missing profit_per_unit")
        elif product['profit_per_unit'] < 0:
            errors.append(f"Product '{product_name}' has negative profit_per_unit: {product['profit_per_unit']}")
            
        if 'cost_per_unit' not in product:
            errors.append(f"Product '{product_name}' is missing cost_per_unit")
        elif product['cost_per_unit'] < 0:
            errors.append(f"Product '{product_name}' has negative cost_per_unit: {product['cost_per_unit']}")
    
    # Validate resources
    resource_names = set()
    for resource in data['resources']:
        # Check required resource fields
        if 'name' not in resource:
            errors.append("Each resource must have a name")
            continue
            
        resource_name = resource['name']
        resource_names.add(resource_name)
        
        # Check for required resource attributes
        if 'available_capacity' not in resource:
            errors.append(f"Resource '{resource_name}' is missing available_capacity")
        elif resource['available_capacity'] < 0:
            errors.append(f"Resource '{resource_name}' has negative available_capacity: {resource['available_capacity']}")
    
    # Validate resource usage
    for ru in data['resource_usage']:
        # Check required resource usage fields
        if 'product_name' not in ru:
            errors.append("Each resource usage entry must specify a product_name")
        elif ru['product_name'] not in product_names:
            errors.append(f"Resource usage references unknown product: {ru['product_name']}")
            
        if 'resource_name' not in ru:
            errors.append("Each resource usage entry must specify a resource_name")
        elif ru['resource_name'] not in resource_names:
            errors.append(f"Resource usage references unknown resource: {ru['resource_name']}")
            
        if 'usage_per_unit' not in ru:
            errors.append(f"Resource usage for {ru.get('product_name', 'unknown')} and {ru.get('resource_name', 'unknown')} is missing usage_per_unit")
        elif ru['usage_per_unit'] < 0:
            errors.append(f"Resource usage for {ru['product_name']} and {ru['resource_name']} has negative usage_per_unit: {ru['usage_per_unit']}")
    
    # Check if any resource usage is defined for each product
    for product_name in product_names:
        has_resource_usage = any(ru['product_name'] == product_name for ru in data['resource_usage'])
        if not has_resource_usage:
            errors.append(f"Product '{product_name}' has no resource usage defined")
    
    # Validate demand constraints if present
    if 'demand_constraints' in data:
        for dc in data['demand_constraints']:
            if 'product_name' not in dc:
                errors.append("Each demand constraint must specify a product_name")
            elif dc['product_name'] not in product_names:
                errors.append(f"Demand constraint references unknown product: {dc['product_name']}")
            
            # Check if min_demand and max_demand are valid
            if 'min_demand' in dc and dc['min_demand'] < 0:
                errors.append(f"Product '{dc['product_name']}' has negative min_demand: {dc['min_demand']}")
                
            if 'max_demand' in dc and dc['max_demand'] < 0:
                errors.append(f"Product '{dc['product_name']}' has negative max_demand: {dc['max_demand']}")
                
            if 'min_demand' in dc and 'max_demand' in dc and dc['min_demand'] > dc['max_demand']:
                errors.append(f"Product '{dc['product_name']}' has min_demand ({dc['min_demand']}) greater than max_demand ({dc['max_demand']})")
    
    # Validate total constraints if present
    if 'total_constraints' in data and data['total_constraints']:
        total_constraints = data['total_constraints']
        
        if 'min_total' in total_constraints and total_constraints['min_total'] is not None:
            if total_constraints['min_total'] < 0:
                errors.append(f"Total constraints has negative min_total: {total_constraints['min_total']}")
        
        if 'max_total' in total_constraints and total_constraints['max_total'] is not None:
            if total_constraints['max_total'] < 0:
                errors.append(f"Total constraints has negative max_total: {total_constraints['max_total']}")
        
        if ('min_total' in total_constraints and total_constraints['min_total'] is not None and
            'max_total' in total_constraints and total_constraints['max_total'] is not None):
            if total_constraints['min_total'] > total_constraints['max_total']:
                errors.append(f"Total constraints has min_total ({total_constraints['min_total']}) " +
                             f"greater than max_total ({total_constraints['max_total']})")
    
    return len(errors) == 0, errors


def validate_solution_feasibility(result: Dict[str, Any], input_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the feasibility of the optimization solution
    
    Args:
        result: Dictionary containing optimization results
        input_data: Original input data
            
    Returns:
        Tuple containing (is_feasible, warnings)
    """
    warnings = []
    
    # If solution is not optimal, no need for further validation
    if result['status'] != 'optimal':
        return False, [f"Solution is not optimal: {result['solver_message']}"]
    
    # Check if any production values are extremely small (numerical precision issues)
    epsilon = 1e-6
    for product, quantity in result['production_plan'].items():
        if 0 < quantity < epsilon:
            warnings.append(f"Product '{product}' has very small production quantity ({quantity}), might be numerical precision issue")
            
    # Check resource constraints
    resources = {r['name']: r for r in input_data['resources']}
    resource_usage = {}
    
    # Create a dictionary to store resource usage by product and resource
    for ru in input_data['resource_usage']:
        product_name = ru['product_name']
        resource_name = ru['resource_name']
        if product_name not in resource_usage:
            resource_usage[product_name] = {}
        resource_usage[product_name][resource_name] = ru['usage_per_unit']
    
    # Calculate actual resource usage based on production plan
    calculated_usage = {r_name: 0.0 for r_name in resources}
    for product, quantity in result['production_plan'].items():
        if product in resource_usage:
            for resource, usage in resource_usage[product].items():
                calculated_usage[resource] += usage * quantity
    
    # Compare with reported resource utilization
    for resource, usage in calculated_usage.items():
        if resource in result['resource_utilization']:
            reported_usage = result['resource_utilization'][resource]['used']
            if abs(usage - reported_usage) > epsilon:
                warnings.append(f"Resource '{resource}' calculated usage ({usage}) differs from reported usage ({reported_usage})")
        
        # Check if usage exceeds capacity
        if usage > resources[resource]['available_capacity'] + epsilon:
            warnings.append(f"Resource '{resource}' usage ({usage}) exceeds available capacity ({resources[resource]['available_capacity']})")
    
    # Check demand constraints if they exist
    if 'demand_constraints' in input_data:
        demand_constraints = {dc['product_name']: dc for dc in input_data['demand_constraints']}
        
        for product, quantity in result['production_plan'].items():
            if product in demand_constraints:
                dc = demand_constraints[product]
                
                if 'min_demand' in dc and quantity < dc['min_demand'] - epsilon:
                    warnings.append(f"Product '{product}' production ({quantity}) violates minimum demand constraint ({dc['min_demand']})")
                
                if 'max_demand' in dc and quantity > dc['max_demand'] + epsilon:
                    warnings.append(f"Product '{product}' production ({quantity}) violates maximum demand constraint ({dc['max_demand']})")
    
    # Check total production constraints if they exist
    if 'total_constraints' in input_data and input_data['total_constraints']:
        total_constraints = input_data['total_constraints']
        total_production = sum(result['production_plan'].values())
        
        if 'min_total' in total_constraints and total_constraints['min_total'] is not None:
            if total_production < total_constraints['min_total'] - epsilon:
                warnings.append(f"Total production ({total_production}) violates minimum total constraint ({total_constraints['min_total']})")
        
        if 'max_total' in total_constraints and total_constraints['max_total'] is not None:
            if total_production > total_constraints['max_total'] + epsilon:
                warnings.append(f"Total production ({total_production}) violates maximum total constraint ({total_constraints['max_total']})")
    
    return len(warnings) == 0, warnings