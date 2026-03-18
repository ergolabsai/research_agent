"""
Symbolic equation solver.

Uses SymPy to rearrange equations and solve for any variable.
"""

from .db_config import get_engine
from .repository import FormulaRepository
import sympy as sp
from typing import Dict, Any, Optional


class FormulaCalculator:
    """
    Calculator that uses SQLite for formula storage.
    Integrates with the MCP server.
    """

    def __init__(self):
        """Initialize with SQLite engine."""
        self.repo = FormulaRepository(get_engine())

    def list_formulas(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        List available formulas
        MCP Tool: list_formulas

        Args:
            category: Optional category filter

        Returns:
            Dictionary of formulas with their details
        """
        formulas = self.repo.get_all_formulas(category=category)

        result = {}
        for formula in formulas:
            result[formula['formula_id']] = {
                'name': formula['name'],
                'description': formula['description'],
                'variables': formula['variables'],
                'category': formula['category'],
                'tags': formula.get('tags', [])
            }

        return {
            'formulas': result,
            'count': len(result),
            'usage': 'Call calculate with formula_name and known_values to solve equations.'
        }

    def describe_formula(self, formula_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a formula

        Args:
            formula_name: Formula ID to look up

        Returns:
            Formula details or None if not found
        """
        formula = self.repo.get_formula_by_id(formula_name)

        if not formula:
            return None

        return {
            'formula_id': formula['formula_id'],
            'name': formula['name'],
            'description': formula['description'],
            'equation': formula['equation'],
            'variables': formula['variables'],
            'variable_details': formula.get('variable_details', []),
            'category': formula['category'],
            'tags': formula.get('tags', [])
        }

    def solve_formula(
            self,
            formula_name: str,
            known_values: Dict[str, float],
            solve_for: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Solve for an unknown variable in a formula
        MCP Tool: solve_formula

        Args:
            formula_name: Name of the formula to use
            known_values: Dictionary of variable names to their values
            solve_for: Optional: explicitly specify which variable to solve for

        Returns:
            Dictionary with the solution or error message
        """
        # Get formula from database
        formula = self.repo.get_formula_by_id(formula_name)

        if not formula:
            return {
                'error': f"Formula '{formula_name}' not found",
                'available_formulas': list(self.list_formulas()['formulas'].keys())
            }

        equation_str = formula['equation']
        all_variables = formula['variables']

        # Determine which variable to solve for
        if solve_for:
            if solve_for not in all_variables:
                return {
                    'error': f"Variable '{solve_for}' not in formula",
                    'valid_variables': all_variables
                }
            unknown_var = solve_for
        else:
            # Auto-detect the missing variable
            provided_vars = set(known_values.keys())
            unknown_vars = set(all_variables) - provided_vars

            if len(unknown_vars) == 0:
                return {'error': 'All variables provided. Nothing to solve for.'}
            elif len(unknown_vars) > 1:
                return {
                    'error': f'Multiple unknowns: {list(unknown_vars)}. Specify solve_for.',
                    'unknown_variables': list(unknown_vars)
                }

            unknown_var = unknown_vars.pop()

        # Parse equation
        # Format: "result_var = expression"
        if '=' not in equation_str:
            return {'error': 'Invalid equation format. Expected "var = expression"'}

        lhs, rhs = equation_str.split('=', 1)
        lhs = lhs.strip()
        rhs = rhs.strip()

        try:
            # Create sympy symbols
            symbols = {var: sp.Symbol(var) for var in all_variables}

            # Parse the right-hand side expression
            expr = sp.sympify(rhs, locals=symbols)

            # Create equation: lhs - rhs = 0
            equation = sp.Eq(symbols[lhs], expr)

            # Substitute known values
            for var, value in known_values.items():
                equation = equation.subs(symbols[var], value)

            # Solve for unknown variable
            solution = sp.solve(equation, symbols[unknown_var])

            if not solution:
                return {'error': 'No solution found'}

            # Take the first solution (or all if multiple)
            if len(solution) == 1:
                result_value = float(solution[0])
                return {
                    'formula': formula['name'],
                    'solved_for': unknown_var,
                    'result': result_value,
                    'known_values': known_values,
                    'equation_used': formula['description']
                }
            else:
                # Multiple solutions
                results = [float(sol) for sol in solution]
                return {
                    'formula': formula['name'],
                    'solved_for': unknown_var,
                    'result': results,
                    'known_values': known_values,
                    'note': 'Multiple solutions found',
                    'equation_used': formula['description']
                }

        except Exception as e:
            return {
                'error': f'Calculation error: {str(e)}',
                'formula': formula_name,
                'equation': equation_str
            }

    def verify_formula(
            self,
            formula_name: str,
            values: Dict[str, float],
            tolerance: float = 1e-6
    ) -> Dict[str, Any]:
        """
        Check if a set of values satisfies a formula
        MCP Tool: verify_formula

        Args:
            formula_name: Name of formula to verify
            values: All variable values
            tolerance: Relative tolerance for equality check

        Returns:
            Dictionary with verification result
        """
        formula = self.repo.get_formula_by_id(formula_name)

        if not formula:
            return {'error': f"Formula '{formula_name}' not found"}

        equation_str = formula['equation']
        all_variables = formula['variables']

        # Check all variables are provided
        provided = set(values.keys())
        required = set(all_variables)

        if provided != required:
            missing = required - provided
            extra = provided - required
            return {
                'error': 'Variable mismatch',
                'missing': list(missing),
                'extra': list(extra),
                'required': list(required)
            }

        # Parse and evaluate equation
        if '=' not in equation_str:
            return {'error': 'Invalid equation format'}

        lhs_var, rhs = equation_str.split('=', 1)
        lhs_var = lhs_var.strip()
        rhs = rhs.strip()

        try:
            # Create namespace for evaluation
            namespace = dict(values)

            # Evaluate right-hand side
            calculated = eval(rhs, {"__builtins__": {}}, namespace)

            # Compare with provided value for LHS variable
            provided_value = values[lhs_var]

            # Check if they match within tolerance
            if calculated == 0:
                is_valid = abs(provided_value - calculated) < tolerance
            else:
                relative_error = abs(provided_value - calculated) / abs(calculated)
                is_valid = relative_error < tolerance

            return {
                'valid': is_valid,
                'formula': formula['name'],
                'provided_value': provided_value,
                'calculated_value': calculated,
                'difference': abs(provided_value - calculated),
                'equation': formula['description']
            }

        except Exception as e:
            return {
                'error': f'Verification error: {str(e)}',
                'formula': formula_name
            }

    def close(self):
        """No-op — SQLite connections are managed per-session."""
        pass
