"""
Production optimization API endpoints.
This module defines the REST API endpoints for production optimization.
"""

from flask import request
from flask_restx import Resource, Namespace, fields

from core.factory import OptimizerFactory
from api.serializers.production import (
    basic_optimization_model,
    demand_constrained_model,
    optimization_output_model
)
from api import api

# Create namespace
ns = Namespace('production', description='Production optimization operations')

# Model for optimizer list response
optimizer_list_model = api.model('OptimizerList', {
    'optimizers': fields.List(fields.String, description='Available optimizer types')
})

# Model for validation errors
validation_error_model = api.model('ValidationError', {
    'status': fields.String(description='Error status'),
    'solver_message': fields.String(description='Error message'),
    'validation_errors': fields.List(fields.String, description='List of validation errors')
})

# Enhanced optimization output model that includes warnings
enhanced_output_model = api.inherit('EnhancedOptimizationOutput', optimization_output_model, {
    'feasibility_warnings': fields.List(fields.String, description='Warnings about solution feasibility', required=False),
    'infeasible_constraints': fields.Raw(description='Information about infeasible constraints', required=False)
})


@ns.route('/optimizers')
class OptimizerList(Resource):
    @ns.doc('list_optimizers')
    @ns.marshal_with(optimizer_list_model)
    def get(self):
        """
        Get a list of all available optimizer types
        
        Returns:
            Dictionary with list of optimizer types
        """
        return {'optimizers': OptimizerFactory.list_available_optimizers()}


@ns.route('/optimize/<string:optimizer_type>')
@ns.param('optimizer_type', 'The optimizer type to use', enum=OptimizerFactory.list_available_optimizers())
class ProductionOptimization(Resource):
    @ns.doc('solve_optimization')
    @ns.expect(demand_constrained_model)  # Using the most comprehensive model
    @ns.response(200, 'Success', enhanced_output_model)
    @ns.response(400, 'Validation Error', validation_error_model)
    def post(self, optimizer_type):
        """
        Solve a production optimization problem using the specified optimizer
        
        Args:
            optimizer_type: String identifier for the optimizer to use
            
        Returns:
            Dictionary with optimization results
            
        Raises:
            400 Bad Request: If the optimizer type is unknown or validation fails
        """
        try:
            data = request.json
            result = OptimizerFactory.optimize(optimizer_type, data)
            
            if result['status'] == 'validation_error':
                return result, 400
                
            return result
            
        except Exception as e:
            return {'status': 'error', 'solver_message': str(e)}, 500


# For backward compatibility
@ns.route('/basic-optimization')
class BasicOptimization(Resource):
    @ns.doc('solve_basic_optimization')
    @ns.expect(basic_optimization_model)
    @ns.response(200, 'Success', enhanced_output_model)
    @ns.response(400, 'Validation Error', validation_error_model)
    def post(self):
        """
        Solve a basic production optimization problem
        
        Returns:
            Dictionary with optimization results
        """
        data = request.json
        result = OptimizerFactory.optimize('basic', data)
        
        if result['status'] == 'validation_error':
            return result, 400
            
        return result


@ns.route('/demand-constrained')
class DemandConstrained(Resource):
    @ns.doc('solve_demand_constrained')
    @ns.expect(demand_constrained_model)
    @ns.response(200, 'Success', enhanced_output_model)
    @ns.response(400, 'Validation Error', validation_error_model)
    def post(self):
        """
        Solve a production optimization problem with demand constraints
        
        Returns:
            Dictionary with optimization results
        """
        data = request.json
        result = OptimizerFactory.optimize('demand-constrained', data)
        
        if result['status'] == 'validation_error':
            return result, 400
            
        return result