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
    @ns.marshal_with(optimization_output_model, code=200)
    def post(self, optimizer_type):
        """
        Solve a production optimization problem using the specified optimizer
        
        Args:
            optimizer_type: String identifier for the optimizer to use
            
        Returns:
            Dictionary with optimization results
            
        Raises:
            400 Bad Request: If the optimizer type is unknown
        """
        try:
            data = request.json
            optimizer = OptimizerFactory.get_optimizer(optimizer_type)
            result = optimizer.solve(data)
            return result
        except ValueError as e:
            return {'status': 'error', 'solver_message': str(e)}, 400


# For backward compatibility
@ns.route('/basic-optimization')
class BasicOptimization(Resource):
    @ns.doc('solve_basic_optimization')
    @ns.expect(basic_optimization_model)
    @ns.marshal_with(optimization_output_model, code=200)
    def post(self):
        """
        Solve a basic production optimization problem
        
        Returns:
            Dictionary with optimization results
        """
        data = request.json
        optimizer = OptimizerFactory.get_optimizer('basic')
        result = optimizer.solve(data)
        return result


@ns.route('/demand-constrained')
class DemandConstrained(Resource):
    @ns.doc('solve_demand_constrained')
    @ns.expect(demand_constrained_model)
    @ns.marshal_with(optimization_output_model, code=200)
    def post(self):
        """
        Solve a production optimization problem with demand constraints
        
        Returns:
            Dictionary with optimization results
        """
        data = request.json
        optimizer = OptimizerFactory.get_optimizer('demand-constrained')
        result = optimizer.solve(data)
        return result