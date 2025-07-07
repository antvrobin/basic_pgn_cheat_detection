#!/usr/bin/env python3
"""
Basic test script for Chess Cheat Detection System

This script verifies that all components are properly installed and configured.
Run this after installation to ensure everything is working correctly.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required libraries can be imported."""
    print("Testing imports...")
    
    try:
        import chess
        import chess.pgn
        print("✓ python-chess imported successfully")
    except ImportError as e:
        print(f"✗ python-chess import failed: {e}")
        return False
    
    try:
        from stockfish import Stockfish
        print("✓ stockfish library imported successfully")
    except ImportError as e:
        print(f"✗ stockfish library import failed: {e}")
        return False
    
    try:
        import numpy as np
        import pandas as pd
        import scipy
        print("✓ Scientific libraries imported successfully")
    except ImportError as e:
        print(f"✗ Scientific libraries import failed: {e}")
        return False
    
    try:
        import flask
        import requests
        print("✓ Web libraries imported successfully")
    except ImportError as e:
        print(f"✗ Web libraries import failed: {e}")
        return False
    
    return True

def test_stockfish():
    """Test Stockfish engine installation and configuration."""
    print("\nTesting Stockfish engine...")
    
    try:
        from stockfish import Stockfish
        
        # Try to initialize Stockfish
        sf = Stockfish()
        
        # Test a simple position
        sf.set_position(["e2e4", "e7e5"])
        evaluation = sf.get_evaluation()
        
        if evaluation is not None:
            print(f"✓ Stockfish working correctly. Evaluation: {evaluation}")
            return True
        else:
            print("✗ Stockfish evaluation failed")
            return False
            
    except Exception as e:
        print(f"✗ Stockfish test failed: {e}")
        print("  Make sure Stockfish is installed and in your PATH")
        return False

def test_analyzer_components():
    """Test the main analyzer components."""
    print("\nTesting analyzer components...")
    
    try:
        from analyzer import PGNParser, EngineAnalyzer, OpeningExplorer, ComplexityCalculator, MetricsCalculator
        print("✓ All analyzer components imported successfully")
        
        # Test PGN Parser
        parser = PGNParser()
        print("✓ PGN Parser initialized")
        
        # Test Engine Analyzer (this will also test Stockfish)
        engine = EngineAnalyzer()
        print("✓ Engine Analyzer initialized")
        engine.close()
        
        # Test other components
        explorer = OpeningExplorer()
        print("✓ Opening Explorer initialized")
        
        calculator = ComplexityCalculator()
        print("✓ Complexity Calculator initialized")
        
        metrics = MetricsCalculator()
        print("✓ Metrics Calculator initialized")
        metrics.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Analyzer components test failed: {e}")
        return False

def test_sample_pgn():
    """Test analysis with the sample PGN file."""
    print("\nTesting sample PGN analysis...")
    
    try:
        from analyzer import MetricsCalculator
        
        # Read sample PGN
        sample_path = Path("sample_data/sample_game.pgn")
        if not sample_path.exists():
            print("✗ Sample PGN file not found")
            return False
        
        with open(sample_path, 'r') as f:
            pgn_content = f.read()
        
        print("✓ Sample PGN file loaded")
        
        # Initialize analyzer
        metrics_calc = MetricsCalculator()
        
        # Perform a quick analysis (first few moves only for testing)
        # This is a simplified test to avoid long analysis times
        print("  Running quick analysis test...")
        
        # Parse the PGN
        game_data = metrics_calc.pgn_parser.parse_pgn_file(pgn_content)
        
        if game_data and game_data['moves']:
            print(f"✓ PGN parsed successfully. Found {len(game_data['moves'])} moves")
            
            # Test engine analysis on first move
            first_move = game_data['moves'][0]
            analysis = metrics_calc.engine_analyzer.analyze_move(
                first_move['fen_before'],
                first_move['uci_move'],
                depth=5  # Shallow depth for quick test
            )
            
            if analysis.get('is_legal', False):
                print("✓ Engine analysis working correctly")
            else:
                print("✗ Engine analysis failed")
                return False
        else:
            print("✗ PGN parsing failed")
            return False
        
        metrics_calc.close()
        print("✓ Sample analysis completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Sample PGN analysis failed: {e}")
        return False

def test_web_app():
    """Test that the Flask app can be initialized."""
    print("\nTesting Flask web application...")
    
    try:
        # Import app
        from app import app
        
        # Test configuration
        with app.app_context():
            print("✓ Flask app initialized successfully")
            print(f"  Upload folder: {app.config.get('UPLOAD_FOLDER', 'Not set')}")
            print(f"  Secret key: {'Set' if app.config.get('SECRET_KEY') else 'Not set'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Flask app test failed: {e}")
        return False

def test_directories():
    """Test that all required directories exist."""
    print("\nTesting directory structure...")
    
    required_dirs = [
        "analyzer",
        "templates", 
        "static/css",
        "static/js",
        "sample_data",
        "uploads"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path} exists")
        else:
            print(f"✗ {dir_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("Chess Cheat Detection System - Installation Test")
    print("=" * 50)
    
    # Configure logging to reduce noise during testing
    logging.getLogger().setLevel(logging.WARNING)
    
    tests = [
        ("Directory Structure", test_directories),
        ("Python Imports", test_imports),
        ("Stockfish Engine", test_stockfish),
        ("Analyzer Components", test_analyzer_components),
        ("Sample PGN Analysis", test_sample_pgn),
        ("Web Application", test_web_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The system is ready to use.")
        print("Run 'python app.py' to start the web interface.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the installation.")
        print("See the README.md for installation instructions.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 