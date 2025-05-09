# Production Optimization API

A flexible Flask-based API for solving production optimization problems using Gurobi. This API provides endpoints for both basic production optimization and demand-constrained optimization problems.

## Features

- Basic production optimization (maximize profit or minimize cost)
- Demand-constrained production optimization
- Swagger UI for API documentation and testing
- JSON input/output format
- Extensible architecture for adding new variants

## Requirements

- Python 3.7+
- Flask
- Flask-RestX
- Gurobi Optimizer (with valid license)

## Installation

1. Clone the repository
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure you have a valid Gurobi license installed

## Running the Application

```
python app.py
```

The API will be available at http://127.0.0.1:5000/ and the Swagger UI documentation at http://127.0.0.1:5000/

## API Endpoints

### Basic Production Optimization

**Endpoint:** `/production/basic-optimization`

**Method:** `POST`

This endpoint solves a basic production optimization problem where the objective is to maximize profit or minimize cost, subject to resource constraints.

### Demand-Constrained Optimization

**Endpoint:** `/production/demand-constrained`

**Method:** `POST`

This endpoint extends the basic optimization problem by adding minimum and maximum demand constraints for products.

## Example Usage

### Basic Optimization Example

```bash
curl -X POST "http://127.0.0.1:5000/production/basic-optimization" \
  -H "Content-Type: application/json" \
  -d @example_basic_optimization.json
```

### Demand-Constrained Example

```bash
curl -X POST "http://127.0.0.1:5000/production/demand-constrained" \
  -H "Content-Type: application/json" \
  -d @example_demand_constrained.json
```

## Extending the API

The API is designed to be extensible. To add new variants of the production optimization problem:

1. Create a new solver method in the `ProductionOptimizer` class
2. Define new API models for input/output as needed
3. Add a new endpoint that uses the solver method

## Input Format

The API accepts JSON input with the following structure:

### Basic Optimization

```json
{
  "objective": "maximize_profit", // or "minimize_cost"
  "products": [
    {
      "name": "Product A",
      "profit_per_unit": 100,
      "cost_per_unit": 60
    }
  ],
  "resources": [
    {
      "name": "Machine Hours",
      "available_capacity": 200
    }
  ],
  "resource_usage": [
    {
      "product_name": "Product A",
      "resource_name": "Machine Hours",
      "usage_per_unit": 2
    }
  ]
}
```

### Demand-Constrained Optimization

Extends the basic optimization with demand constraints:

```json
{
  // Same as basic optimization, plus:
  "demand_constraints": [
    {
      "product_name": "Product A",
      "min_demand": 20,
      "max_demand": 50
    }
  ]
}
```

## Output Format

The API returns JSON output with the following structure:

```json
{
  "status": "optimal",
  "objective_value": 12000,
  "production_plan": {
    "Product A": 50,
    "Product B": 30,
    "Product C": 40
  },
  "resource_utilization": {
    "Machine Hours": {
      "used": 190,
      "available": 200,
      "utilization_pct": 95
    }
  },
  "solver_message": "Optimal solution found"
}
```
