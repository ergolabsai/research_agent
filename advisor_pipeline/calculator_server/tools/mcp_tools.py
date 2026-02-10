"""
MCP Tool definitions and handlers.

This module exposes just THREE tools that can handle all formula calculations:
1. calculate - solve for any variable in any formula
2. verify - check if values satisfy a formula
3. list_formulas - discover available formulas
"""

import json
from mcp.types import Tool, TextContent
if __name__ == '__main__':
    from solver import FormulaCalculator
else:
    from .solver import FormulaCalculator

def success_response(result: dict) -> list[TextContent]:
    """Wrap a result dict in a TextContent response."""
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# === Tool Definitions ===

TOOLS = [
    Tool(
        name="calculate",
        description="""Solve for an unknown variable in a physics/math equation.

Provide the formula name and n-1 of its variables - the tool solves for the remaining one.
Auto-detects which variable to solve for based on what's missing.

Examples:
- Wave equation: provide {speed, frequency} → get wavelength
- Kinetic energy: provide {mass, velocity} → get energy  
- Same formula works in reverse: provide {energy, mass} → get velocity

Use 'list_formulas' to see available formulas and their variables.""",
        inputSchema={
            "type": "object",
            "properties": {
                "formula_name": {
                    "type": "string",
                    "description": "Name of the formula to use (e.g., 'wave_equation', 'kinetic_energy')"
                },
                "known_values": {
                    "type": "object",
                    "description": "Dict of variable names to their numeric values. Provide n-1 variables.",
                    "additionalProperties": {"type": "number"}
                },
                "solve_for": {
                    "type": "string",
                    "description": "Optional: explicitly specify which variable to solve for. Auto-detected if omitted."
                }
            },
            "required": ["formula_name", "known_values"]
        }
    ),
    Tool(
        name="verify",
        description="""Check if a set of values satisfies a formula/equation.

Provide all variable values and the tool checks if they're consistent.
Useful for validating calculations or checking data from papers.

Example: verify wave_equation with {speed: 340, frequency: 500, wavelength: 0.68}
→ Returns whether these values actually satisfy v = f × λ""",
        inputSchema={
            "type": "object",
            "properties": {
                "formula_name": {
                    "type": "string",
                    "description": "Name of the formula to verify against"
                },
                "values": {
                    "type": "object",
                    "description": "Dict of ALL variable names to their values",
                    "additionalProperties": {"type": "number"}
                },
                "tolerance": {
                    "type": "number",
                    "description": "Relative tolerance for equality check (default: 1e-6)"
                }
            },
            "required": ["formula_name", "values"]
        }
    ),
    Tool(
        name="list_formulas",
        description="""List available formulas.""",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional: filter by category (not yet implemented)"
                }
            },
            "required": []
        }
    ),
    Tool(
        name="describe_formula",
        description="""Get details about a specific formula.""",
        inputSchema={
            "type": "object",
            "properties": {
                "formula_name": {
                    "type": "string",
                    "description": "Optional: get detailed info about a specific formula"
                },
            },
            "required": ["formula_name"]
        }
    ),
]


async def handle(name: str, arguments: dict) -> list[TextContent] | None:
    """Handle tool calls."""

    formula_calculator = FormulaCalculator()
    
    if name == "calculate":
        formula_name = arguments["formula_name"]
        known_values = arguments["known_values"]
        solve_for = arguments.get("solve_for")
        
        result = formula_calculator.solve_formula(formula_name, known_values, solve_for)
        return success_response(result)
    
    elif name == "verify":
        formula_name = arguments["formula_name"]
        values = arguments["values"]
        tolerance = arguments.get("tolerance", 1e-6)
        
        result = formula_calculator.verify_formula(formula_name, values, tolerance)
        return success_response(result)
    
    elif name == "list_formulas":
        category = arguments.get("category")
        
        result = formula_calculator.list_formulas(category)
        return success_response(result)

    elif name == "describe_formula":
        formula_name = arguments["formula_name"]

        result = formula_calculator.describe_formula(formula_name)
        return success_response(result)
    
    return None


def get_all_tools() -> list[Tool]:
    """Return all tools defined in this module."""
    return TOOLS


async def handle_tool(name: str, arguments: dict) -> list[TextContent]:
    """Main entry point for tool handling."""
    result = await handle(name, arguments)
    if result is None:
        return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]
    return result
