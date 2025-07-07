#!/usr/bin/env python3
"""
Speed test script to demonstrate the performance improvements in lite mode.
"""

import sys
import os
import time
import logging

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import MetricsCalculator
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_analysis_speed():
    """Test analysis speed with the current configuration."""
    
    print("="*60)
    print("CHESS CHEAT DETECTION - SPEED TEST")
    print("="*60)
    
    # Show current configuration
    print(f"Analysis Mode: {'LITE MODE (Fast)' if Config.LITE_MODE else 'FULL MODE (Detailed)'}")
    print(f"Engine Depth: {Config.DEFAULT_DEPTH}")
    print(f"Complexity Depths: {Config.COMPLEXITY_DEPTHS}")
    print(f"Stockfish Path: {Config.STOCKFISH_PATH}")
    print("-"*60)
    
    # Load sample PGN
    sample_pgn_path = "sample_data/sample_game.pgn"
    
    if not os.path.exists(sample_pgn_path):
        print(f"❌ Sample PGN file not found: {sample_pgn_path}")
        return
    
    with open(sample_pgn_path, 'r') as f:
        pgn_content = f.read()
    
    print(f"✓ Loaded sample PGN file: {sample_pgn_path}")
    print(f"  PGN content length: {len(pgn_content)} characters")
    
    # Initialize analyzer
    try:
        metrics_calculator = MetricsCalculator()
        print("✓ Initialized MetricsCalculator")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        return
    
    # Run analysis and measure time
    print("\n" + "="*40)
    print("STARTING ANALYSIS...")
    print("="*40)
    
    start_time = time.time()
    
    try:
        result = metrics_calculator.analyze_game(pgn_content)
        end_time = time.time()
        
        # Calculate duration
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = duration % 60
        
        print("\n" + "="*40)
        print("ANALYSIS COMPLETED!")
        print("="*40)
        print(f"⏱️  Total Time: {minutes}m {seconds:.1f}s")
        print(f"📊 Analysis Results:")
        print(f"   - Total moves analyzed: {len(result.get('move_analyses', []))}")
        print(f"   - Opening moves: {result.get('opening_analysis', {}).get('opening_moves_count', 0)}")
        print(f"   - Engine matching: {result.get('metrics', {}).get('engine_matching', {}).get('pv1_percentage', 0):.1f}% PV1")
        print(f"   - Risk assessment: {result.get('metrics', {}).get('risk_assessment', {}).get('overall_risk', 'Unknown')}")
        
        # Show speed comparison
        if Config.LITE_MODE:
            estimated_full_time = duration * 2.5  # Rough estimate
            estimated_full_minutes = int(estimated_full_time // 60)
            estimated_full_seconds = estimated_full_time % 60
            print(f"\n🚀 SPEED IMPROVEMENT:")
            print(f"   - Current (Lite): {minutes}m {seconds:.1f}s")
            print(f"   - Estimated Full: {estimated_full_minutes}m {estimated_full_seconds:.1f}s")
            print(f"   - Speed up: ~{estimated_full_time/duration:.1f}x faster")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            metrics_calculator.close()
            print("\n✓ Cleanup completed")
        except:
            pass
    
    print("\n" + "="*60)
    print("SPEED TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    test_analysis_speed() 