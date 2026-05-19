#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test script for the symbolic calculator.

Demonstrates that ONE formula entry can solve for ANY of its variables.
"""

import sys
sys.path.insert(0, '/home/claude/calculator')

from solver import FormulaCalculator

formula = FormulaCalculator()


def test_wave_equation():
    """Demonstrate solving wave equation three ways from ONE stored formula."""
    print("=" * 60)
    print("WAVE EQUATION: v = f × λ")
    print("Stored once, solved three ways:")
    print("=" * 60)
    
    # Solve for wavelength
    result = formula.solve_formula("wave_equation", {"speed": 340, "frequency": 500})
    print(f"\n1. Given speed=340, frequency=500")
    print(f"   → {result['solved_for']} = {result['result']}")
    
    # Solve for frequency
    result = formula.solve_formula("wave_equation", {"speed": 340, "wavelength": 0.68})
    print(f"\n2. Given speed=340, wavelength=0.68")
    print(f"   → {result['solved_for']} = {result['result']}")
    
    # Solve for speed
    result = formula.solve_formula("wave_equation", {"frequency": 500, "wavelength": 0.68})
    print(f"\n3. Given frequency=500, wavelength=0.68")
    print(f"   → {result['solved_for']} = {result['result']}")


def test_kinetic_energy():
    """Demonstrate kinetic energy solved multiple ways."""
    print("\n" + "=" * 60)
    print("KINETIC ENERGY: KE = ½mv²")
    print("=" * 60)
    
    # Solve for energy
    result = formula.solve_formula("kinetic_energy", {"mass": 10, "velocity": 5})
    print(f"\n1. Given mass=10kg, velocity=5m/s")
    print(f"   → {result['solved_for']} = {result['result']}")
    
    # Solve for velocity (reverse!)
    result = formula.solve_formula("kinetic_energy", {"mass": 10, "energy": 125})
    print(f"\n2. Given mass=10kg, energy=125J")
    print(f"   → {result['solved_for']} = {result['result']}")
    
    # Solve for mass
    result = formula.solve_formula("kinetic_energy", {"velocity": 5, "energy": 125})
    print(f"\n3. Given velocity=5m/s, energy=125J")
    print(f"   → {result['solved_for']} = {result['result']}")


def test_plasma_physics():
    """Test plasma physics formulas."""
    print("\n" + "=" * 60)
    print("ALFVÉN SPEED: v_A = B/√(μ₀ρ)")
    print("=" * 60)
    
    # Solve for Alfvén speed
    result = formula.solve_formula("alfven_speed", {
        "magnetic_field": 1.0,  # 1 Tesla
        "mass_density": 1e-10   # kg/m³
    })
    print(f"\n1. Given B=1T, ρ=1e-10 kg/m³")
    print(f"   → {result['solved_for']} = {result['result']}")
    
    # Solve for magnetic field (reverse!)
    result = formula.solve_formula("alfven_speed", {
        "alfven_speed": 2.82e6,
        "mass_density": 1e-10
    })
    print(f"\n2. Given v_A=2.82e6 m/s, ρ=1e-10 kg/m³")
    print(f"   → {result['solved_for']} = {result['result']}")


def test_error_handling():
    """Demonstrate helpful error messages."""
    print("\n" + "=" * 60)
    print("ERROR HANDLING")
    print("=" * 60)
    
    # Too few variables
    result = formula.solve_formula("kinetic_energy", {"mass": 10})
    print(f"\n1. Only one variable provided:")
    print(f"   Error: {result.get('error')}")
    print(f"   Hint: {result.get('hint')}")
    
    # All variables provided
    result = formula.solve_formula("wave_equation", {"speed": 340, "frequency": 500, "wavelength": 0.68})
    print(f"\n2. All variables provided:")
    print(f"   Error: {result.get('error')}")
    print(f"   Hint: {result.get('hint')}")
    
    # Invalid variable name
    result = formula.solve_formula("wave_equation", {"speed": 340, "freq": 500})
    print(f"\n3. Invalid variable name:")
    print(f"   Error: {result.get('error')}")


def test_verification():
    """Test formula verification."""
    print("\n" + "=" * 60)
    print("VERIFICATION MODE")
    print("=" * 60)
    
    # Correct values
    result = formula.verify_formula("wave_equation", {
        "speed": 340,
        "frequency": 500,
        "wavelength": 0.68
    })
    print(f"\n1. Verify v=340, f=500, λ=0.68:")
    print(f"   {result['valid']}")
    
    # Incorrect values
    result = formula.verify_formula("wave_equation", {
        "speed": 340,
        "frequency": 500,
        "wavelength": 1.0  # Wrong!
    })
    print(f"\n2. Verify v=340, f=500, λ=1.0 (wrong):")
    print(f"   {result['valid']}")


def test_list_formulas():
    """Show available formulas."""
    print("\n" + "=" * 60)
    print("AVAILABLE FORMULAS")
    print("=" * 60)
    
    formulas = formula.list_formulas()
    for name, info in formulas['formulas'].items():
        print(f"\n  {name}:")
        print(f"    {info['description']}")
        print(f"    Variables: {', '.join(info['variables'])}")


def test_describe_formula():
    """Show detailed formula info."""
    print("\n" + "=" * 60)
    print("FORMULA DETAILS")
    print("=" * 60)
    
    info = formula.describe_formula("alfven_speed")
    print(f"\n  Name: {info['name']}")
    print(f"  Description: {info['description']}")
    print(f"  Equation: {info['equation']}")
    print(f"  Variables: {info['variables']}")


if __name__ == "__main__":
    test_wave_equation()
    test_kinetic_energy()
    test_plasma_physics()
    test_error_handling()
    test_verification()
    test_list_formulas()
    test_describe_formula()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)
