"""
Analysis module for interpreting optimization results.
This module provides utility functions to analyze and visualize optimization results.
"""

from typing import Dict, Any, List
import json


def format_optimization_result(result: Dict[str, Any]) -> str:
    """
    Format optimization result into a readable string
    
    Args:
        result: Dictionary containing optimization results
        
    Returns:
        Formatted string representation of results
    """
    output = []
    
    # Handle validation error
    if result['status'] == 'validation_error':
        output.append("VALIDATION ERROR")
        output.append(f"Message: {result['solver_message']}")
        output.append("\nValidation Errors:")
        for i, error in enumerate(result['validation_errors'], 1):
            output.append(f"  {i}. {error}")
        return "\n".join(output)
    
    # Handle solver error
    if result['status'] == 'error':
        output.append("SOLVER ERROR")
        output.append(f"Message: {result['solver_message']}")
        return "\n".join(output)
    
    # Handle infeasibility
    if result['status'] == 'infeasible':
        output.append("INFEASIBLE PROBLEM")
        output.append(f"Message: {result['solver_message']}")
        if 'infeasible_constraints' in result:
            output.append("\nInfeasible Constraints:")
            for constr in result['infeasible_constraints']:
                output.append(f"  - {constr}")
        return "\n".join(output)
    
    # Handle solution with warnings
    if result['status'] == 'solution_warning':
        output.append("WARNING: Solution found but with potential issues")
        if 'feasibility_warnings' in result:
            output.append("\nWarnings:")
            for i, warning in enumerate(result['feasibility_warnings'], 1):
                output.append(f"  {i}. {warning}")
        output.append("")  # Add blank line
    
    # Handle optimal solution
    if result['status'] in ['optimal', 'solution_warning']:
        output.append("OPTIMAL SOLUTION")
        output.append(f"Objective Value: {result['objective_value']:.4f}")
        
        # Production plan
        output.append("\nProduction Plan:")
        if 'production_plan' in result:
            sorted_products = sorted(result['production_plan'].items(), 
                                    key=lambda x: x[1], reverse=True)
            for product, quantity in sorted_products:
                if quantity > 0:
                    output.append(f"  {product}: {quantity:.4f}")
        
        # Resource utilization
        if 'resource_utilization' in result:
            output.append("\nResource Utilization:")
            for resource, details in result['resource_utilization'].items():
                output.append(f"  {resource}: {details['used']:.2f}/{details['available']:.2f} " +
                             f"({details['utilization_pct']:.1f}%)")
        
        # Warnings if any
        if 'feasibility_warnings' in result and result['feasibility_warnings']:
            output.append("\nWarnings:")
            for i, warning in enumerate(result['feasibility_warnings'], 1):
                output.append(f"  {i}. {warning}")
    
    return "\n".join(output)


def analyze_results(result: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform deeper analysis on optimization results
    
    Args:
        result: Dictionary containing optimization results
        data: Original input data
        
    Returns:
        Dictionary with additional analysis
    """
    if result['status'] not in ['optimal', 'solution_warning']:
        return result
    
    # Create a copy to avoid modifying the original
    analysis = {**result}
    analysis['analysis'] = {}
    
    # Extract relevant data
    objective_type = data['objective']
    products = {p['name']: p for p in data['products']}
    
    # Calculate financials
    if 'production_plan' in result:
        total_profit = 0
        total_cost = 0
        revenue = 0
        
        for product, quantity in result['production_plan'].items():
            if product in products and quantity > 0:
                profit = products[product]['profit_per_unit'] * quantity
                cost = products[product]['cost_per_unit'] * quantity
                total_profit += profit
                total_cost += cost
                revenue += profit + cost  # Assuming profit = revenue - cost
        
        analysis['analysis']['financials'] = {
            'total_profit': total_profit,
            'total_cost': total_cost,
            'revenue': revenue,
            'profit_margin_pct': (total_profit / revenue * 100) if revenue > 0 else 0
        }
    
    # Resource analysis
    if 'resource_utilization' in result:
        bottleneck_threshold = 0.95  # 95% utilization indicates a bottleneck
        bottlenecks = []
        underutilized = []
        
        for resource, details in result['resource_utilization'].items():
            utilization = details['utilization_pct'] / 100  # Convert from percentage
            
            if utilization >= bottleneck_threshold:
                bottlenecks.append({
                    'resource': resource,
                    'utilization': utilization * 100,
                    'margin': (1 - utilization) * details['available']
                })
            elif utilization < 0.5:  # Less than 50% utilized
                underutilized.append({
                    'resource': resource,
                    'utilization': utilization * 100,
                    'unused_capacity': (1 - utilization) * details['available']
                })
        
        analysis['analysis']['resources'] = {
            'bottlenecks': bottlenecks,
            'underutilized': underutilized
        }
    
    # Product analysis
    if 'production_plan' in result:
        unused_products = []
        for product in products:
            if product not in result['production_plan'] or result['production_plan'][product] <= 1e-6:
                unused_products.append(product)
        
        analysis['analysis']['products'] = {
            'unused_products': unused_products,
            'unused_count': len(unused_products),
            'total_products': len(products)
        }
    
    return analysis


def export_results_to_json(result: Dict[str, Any], filename: str) -> None:
    """
    Export optimization results to a JSON file
    
    Args:
        result: Dictionary containing optimization results
        filename: Name of the output file
    """
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)