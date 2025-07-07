#!/usr/bin/env python3
"""
Test script to verify the Lichess Opening Explorer API integration.
"""

import sys
import os
import logging

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer.opening_explorer import OpeningExplorer

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_opening_api():
    """Test the opening explorer API integration."""
    
    print("Testing Lichess Opening Explorer API integration...")
    
    # Create explorer instance
    explorer = OpeningExplorer()
    
    # Test 1: Check if basic opening moves work
    print("\n1. Testing basic opening moves...")
    basic_moves = ['e2e4', 'e7e5', 'g1f3', 'b8c6']
    
    try:
        opening_count = explorer.get_opening_moves_count(basic_moves)
        print(f"✓ Opening moves count for {basic_moves}: {opening_count}")
        
        if opening_count > 0:
            print("✓ Basic opening recognition working")
        else:
            print("✗ Basic opening recognition failed")
            
    except Exception as e:
        print(f"✗ Error in basic opening test: {e}")
    
    # Test 2: Test individual move checking
    print("\n2. Testing individual move checking...")
    try:
        single_move = ['e2e4']
        is_opening = explorer.is_opening_move(single_move)
        print(f"✓ Is 'e2e4' an opening move? {is_opening}")
        
        if is_opening:
            print("✓ Single move recognition working")
        else:
            print("✗ Single move recognition failed")
            
    except Exception as e:
        print(f"✗ Error in single move test: {e}")
    
    # Test 3: Test opening statistics
    print("\n3. Testing opening statistics...")
    try:
        stats = explorer.get_opening_statistics(['e2e4'])
        print(f"✓ Statistics for 'e2e4': {stats['total_games']} games")
        
        if stats['total_games'] > 0:
            print("✓ Opening statistics working")
        else:
            print("✗ Opening statistics failed")
            
    except Exception as e:
        print(f"✗ Error in statistics test: {e}")
    
    # Test 4: Test deviation analysis
    print("\n4. Testing deviation analysis...")
    try:
        test_moves = ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5']  # Spanish Opening
        deviation = explorer.analyze_opening_deviation(test_moves)
        print(f"✓ Deviation analysis: {deviation['opening_moves_count']} opening moves out of {len(test_moves)}")
        
        if deviation['opening_moves_count'] > 0:
            print("✓ Deviation analysis working")
        else:
            print("✗ Deviation analysis failed")
            
    except Exception as e:
        print(f"✗ Error in deviation test: {e}")
    
    # Test 5: Test API endpoints directly
    print("\n5. Testing API endpoints directly...")
    try:
        # Test masters database
        response = explorer._query_opening_api('e2e4', use_masters=True)
        if response:
            total_games = response.get('white', 0) + response.get('draws', 0) + response.get('black', 0)
            print(f"✓ Masters database response: {total_games} games")
        else:
            print("✗ Masters database failed")
            
        # Test lichess database
        response = explorer._query_opening_api('e2e4', use_masters=False)
        if response:
            total_games = response.get('white', 0) + response.get('draws', 0) + response.get('black', 0)
            print(f"✓ Lichess database response: {total_games} games")
        else:
            print("✗ Lichess database failed")
            
    except Exception as e:
        print(f"✗ Error in direct API test: {e}")
    
    print("\n" + "="*50)
    print("Opening Explorer API test completed!")
    print("If you see ✓ marks above, the integration is working correctly.")
    print("If you see ✗ marks, there may be issues with the API or network.")

if __name__ == "__main__":
    test_opening_api() 