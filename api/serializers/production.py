"""Serializer models for production optimization API"""

from flask_restx import fields
from api import api

# Models for API documentation
product_model = api.model('Product', {
    'name': fields.String(required=True, description='Product name'),
    'profit_per_unit': fields.Float(required=True, description='Profit per unit'),
    'cost_per_unit': fields.Float(required=True, description='Cost per unit')
})

resource_usage_model = api.model('ResourceUsage', {
    'product_name': fields.String(required=True, description='Product name'),
    'resource_name': fields.String(required=True, description='Resource name'),
    'usage_per_unit': fields.Float(required=True, description='Resource usage per unit of product')
})

resource_model = api.model('Resource', {
    'name': fields.String(required=True, description='Resource name'),
    'available_capacity': fields.Float(required=True, description='Available capacity')
})

demand_constraint_model = api.model('DemandConstraint', {
    'product_name': fields.String(required=True, description='Product name'),
    'min_demand': fields.Float(required=False, description='Minimum demand (optional)'),
    'max_demand': fields.Float(required=False, description='Maximum demand (optional)')
})

basic_optimization_model = api.model('BasicOptimizationInput', {
    'objective': fields.String(required=True, enum=['maximize_profit', 'minimize_cost'], 
                              description='Optimization objective'),
    'products': fields.List(fields.Nested(product_model), required=True, 
                           description='Products to be manufactured'),
    'resources': fields.List(fields.Nested(resource_model), required=True, 
                            description='Available resources'),
    'resource_usage': fields.List(fields.Nested(resource_usage_model), required=True, 
                                 description='Resource usage by products')
})

demand_constrained_model = api.model('DemandConstrainedInput', {
    'objective': fields.String(required=True, enum=['maximize_profit', 'minimize_cost'], 
                              description='Optimization objective'),
    'products': fields.List(fields.Nested(product_model), required=True, 
                           description='Products to be manufactured'),
    'resources': fields.List(fields.Nested(resource_model), required=True, 
                            description='Available resources'),
    'resource_usage': fields.List(fields.Nested(resource_usage_model), required=True, 
                                 description='Resource usage by products'),
    'demand_constraints': fields.List(fields.Nested(demand_constraint_model), required=True, 
                                     description='Demand constraints')
})

optimization_output_model = api.model('OptimizationOutput', {
    'status': fields.String(description='Optimization status'),
    'objective_value': fields.Float(description='Objective function value'),
    'production_plan': fields.Raw(description='Production quantities for each product'),
    'resource_utilization': fields.Raw(description='Resource utilization'),
    'solver_message': fields.String(description='Additional solver information')
})