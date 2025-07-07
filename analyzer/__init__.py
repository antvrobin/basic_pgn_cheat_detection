"""
Chess Analysis Package

This package provides comprehensive chess game analysis for cheat detection,
including PGN parsing, engine analysis, opening theory checking, and 
advanced positional complexity metrics.
"""

from .pgn_parser import PGNParser
from .engine_analyzer import EngineAnalyzer
from .opening_explorer import OpeningExplorer
from .complexity_calculator import ComplexityCalculator
from .metrics import MetricsCalculator

__version__ = "1.0.0"
__all__ = [
    'PGNParser',
    'EngineAnalyzer', 
    'OpeningExplorer',
    'ComplexityCalculator',
    'MetricsCalculator'
] 