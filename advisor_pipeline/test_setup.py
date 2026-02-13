#!/usr/bin/env python3
"""
Quick test to verify The Advisor pipeline setup.
Run this to check if all components are properly installed.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...")
    
    try:
        import anthropic
        print("✓ anthropic")
    except ImportError as e:
        print(f"✗ anthropic: {e}")
        return False
    
    try:
        import instructor
        print("✓ instructor")
    except ImportError as e:
        print(f"✗ instructor: {e}")
        return False
    
    try:
        import langchain
        print("✓ langchain")
    except ImportError as e:
        print(f"✗ langchain: {e}")
        return False
    
    try:
        from langchain_anthropic import ChatAnthropic
        print("✓ langchain_anthropic")
    except ImportError as e:
        print(f"✗ langchain_anthropic: {e}")
        return False
    
    try:
        import pymongo
        print("✓ pymongo")
    except ImportError as e:
        print(f"✗ pymongo: {e}")
        return False
    
    try:
        from pydantic import BaseModel
        print("✓ pydantic")
    except ImportError as e:
        print(f"✗ pydantic: {e}")
        return False
    
    print("\nAll core packages imported successfully!\n")
    return True


def test_project_structure():
    """Test that all project files are in place."""
    print("Testing project structure...")
    
    required_files = [
        "models/schemas.py",
        "config/settings.py",
        "agents/base_agent.py",
        "agents/logic_mapping_agent.py",
        "agents/evidence_finder_agent.py",
        "agents/figure_evaluator_agent.py",
        "agents/math_evaluator_agent.py",
        "agents/citation_checker_agent.py",
        "agents/results_compiler_agent.py",
        "database.py",
        "pipeline.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_present = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_present = False
    
    if all_present:
        print("\nAll required files present!\n")
    else:
        print("\nSome files are missing!\n")
    
    return all_present


def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    
    try:
        from config.settings import settings
        
        print(f"✓ Settings loaded")
        print(f"  Model: {settings.model_name}")
        print(f"  Temperature: {settings.temperature}")
        print(f"  Database: {settings.database_name}")
        
        if not settings.anthropic_api_key or settings.anthropic_api_key == "":
            print("\n⚠️  Warning: ANTHROPIC_API_KEY not set in .env")
            print("   Copy .env.example to .env and add your API key")
            return False
        else:
            print(f"  API Key: {'*' * 20}{settings.anthropic_api_key[-4:]}")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}\n")
        return False


def test_models():
    """Test Pydantic models can be loaded."""
    print("Testing Pydantic models...")
    
    try:
        from models.schemas import (
            PaperStructure,
            LogicalStep,
            Evidence,
            ValidationResult
        )
        
        # Try creating a simple model instance
        step = LogicalStep(
            step_number=1,
            description="Test step",
            section="Introduction"
        )
        
        print("✓ Models loaded and validated")
        print(f"  Created test LogicalStep: {step.step_number}\n")
        return True
        
    except Exception as e:
        print(f"✗ Model error: {e}\n")
        return False


def test_agents():
    """Test that agents can be instantiated."""
    print("Testing agent initialization...")
    
    try:
        # We'll test without API key to just check imports
        import os
        os.environ['ANTHROPIC_API_KEY'] = 'test-key-for-import-testing'
        
        from agents.logic_mapping_agent import PaperReaderAgent
        from agents.evidence_finder_agent import EvidenceFinderAgent
        
        print("✓ Agent classes can be imported")
        print("  Note: Full instantiation requires valid API key\n")
        return True
        
    except Exception as e:
        print(f"✗ Agent import error: {e}\n")
        return False


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("The Advisor Pipeline - Setup Verification")
    print("="*60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Project Structure", test_project_structure),
        ("Configuration", test_config),
        ("Pydantic Models", test_models),
        ("Agent Classes", test_agents)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Test '{name}' crashed: {e}\n")
            results.append((name, False))
    
    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("="*60)
    if all_passed:
        print("✓ All tests passed! Setup is complete.")
        print("\nNext steps:")
        print("1. Set ANTHROPIC_API_KEY in .env file")
        print("2. Start MongoDB (if using database features)")
        print("3. Run: python example_usage.py")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Run: pip install -r requirements.txt")
        print("2. Copy .env.example to .env and configure")
        print("3. Ensure all files were created correctly")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
