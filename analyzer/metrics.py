"""
Metrics Calculator for comprehensive chess game analysis.

This module brings together all analysis components to compute a complete set
of metrics for cheat detection, including:
- Opening theory compliance
- Engine move matching (PV-1, PV-2, PV-3)
- Positional complexity analysis
- Temporal consistency (move times)
- Overall accuracy metrics
- Custom behavioral metrics
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging
from scipy import stats
import math

from .pgn_parser import PGNParser
from .engine_analyzer import EngineAnalyzer
from .opening_explorer import OpeningExplorer
from .complexity_calculator import ComplexityCalculator
from config import Config

class MetricsCalculator:
    """
    Comprehensive metrics calculator for chess cheat detection analysis.
    
    Combines PGN parsing, engine analysis, opening theory checking, and
    complexity calculation to provide a complete assessment of game patterns.
    """
    
    def __init__(self):
        """Initialize the metrics calculator with all required components."""
        self.pgn_parser = PGNParser()
        self.engine_analyzer = EngineAnalyzer()
        self.opening_explorer = OpeningExplorer()
        self.complexity_calculator = ComplexityCalculator(Config.get_stockfish_path())
        
    def analyze_game(self, pgn_content: str) -> Dict:
        """
        Perform complete analysis of a chess game.
        
        Args:
            pgn_content: String content of the PGN file
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            # Use the EngineAnalyzer to do the complete analysis
            analysis_result = self.engine_analyzer.analyze_game(pgn_content)
            
            if not analysis_result.get('success', False):
                raise ValueError(f"Engine analysis failed: {analysis_result.get('error', 'Unknown error')}")
            
            # Extract data from engine analysis
            game_data = analysis_result['game_info']
            move_analyses = analysis_result['move_analyses']
            engine_metrics = analysis_result['metrics']
            
            # Parse PGN for additional data if needed
            pgn_data = self.pgn_parser.parse_pgn_file(pgn_content)
            
            # Combine game data
            combined_game_data = {**game_data, **pgn_data}
            
            # Convert move analyses to expected format and add complexity
            formatted_move_analyses = []
            position_complexities = []
            
            for i, analysis in enumerate(move_analyses):
                try:
                    # Add complexity analysis
                    if 'complexity' in analysis:
                        complexity_result = analysis['complexity']
                    else:
                        # Calculate complexity if not present
                        import chess
                        board = chess.Board()
                        
                        # Replay moves up to this position
                        for j in range(i):
                            if j < len(move_analyses):
                                prev_move = move_analyses[j].get('move', '')
                                if prev_move:
                                    try:
                                        chess_move = board.parse_san(prev_move)
                                        board.push(chess_move)
                                    except:
                                        pass
                        
                        # Calculate complexity for current position
                        engine_analysis = {
                            'move_rank': analysis.get('move_rank', 0),
                            'evaluation': analysis.get('evaluation', 0),
                            'centipawn_loss': analysis.get('centipawn_loss', 0),
                            'is_legal': True
                        }
                        
                        complexity_result = self.complexity_calculator.calculate_complexity(
                            board, engine_analysis, lite_mode=Config.LITE_MODE
                        )
                    
                    # Format the analysis
                    formatted_analysis = {
                        'move_number': analysis.get('move_number', i + 1),
                        'player': analysis.get('player', 'white' if i % 2 == 0 else 'black'),
                        'move': analysis.get('move', ''),
                        'uci_move': analysis.get('uci_move', ''),
                        'move_time': analysis.get('move_time', 0),
                        'clock_time': analysis.get('clock_time', 0),
                        'legal_moves_count': analysis.get('legal_moves_count', 0),
                        'engine_analysis': {
                            'evaluation': analysis.get('evaluation', 0),
                            'centipawn_loss': analysis.get('centipawn_loss', 0),
                            'move_rank': analysis.get('move_rank', 0),
                            'is_legal': True,
                            'best_move': analysis.get('best_move', ''),
                            'pv_moves': analysis.get('pv_moves', [])
                        },
                        'complexity': complexity_result,
                        'fen_before': analysis.get('fen_before', '')
                    }
                    
                    formatted_move_analyses.append(formatted_analysis)
                    position_complexities.append(complexity_result)
                    
                except Exception as e:
                    logging.error(f"Error formatting move analysis {i + 1}: {e}")
                    continue
            
            # Analyze opening theory
            uci_moves = [move.get('uci_move', '') for move in formatted_move_analyses if move.get('uci_move')]
            opening_analysis = self.opening_explorer.analyze_opening_deviation(uci_moves)
            
            # Calculate all metrics using the formatted data
            metrics = self._calculate_all_metrics(
                combined_game_data, formatted_move_analyses, position_complexities, opening_analysis
            )
            
            return {
                'game_info': combined_game_data,
                'move_analyses': formatted_move_analyses,
                'opening_analysis': opening_analysis,
                'metrics': metrics,
                'analysis_metadata': {
                    'total_moves_analyzed': len(formatted_move_analyses),
                    'timestamp': pd.Timestamp.now().isoformat()
                }
            }
            
        except Exception as e:
            logging.error(f"Error in game analysis: {e}")
            raise Exception(f"Game analysis failed: {str(e)}")
    
    def _calculate_all_metrics(self, 
                             game_data: Dict,
                             move_analyses: List[Dict],
                             position_complexities: List[Dict],
                             opening_analysis: Dict) -> Dict:
        """
        Calculate all cheat detection metrics.
        
        Args:
            game_data: Parsed game data
            move_analyses: List of move analysis results
            position_complexities: List of position complexity results
            opening_analysis: Opening theory analysis
            
        Returns:
            Dictionary with all calculated metrics
        """
        metrics = {}
        
        # 1. Opening theory metrics
        metrics['opening_metrics'] = self._calculate_opening_metrics(opening_analysis)
        
        # 2. Engine move matching metrics
        metrics['engine_matching'] = self._calculate_engine_matching_metrics(move_analyses)
        
        # 3. Positional complexity metrics
        metrics['complexity_metrics'] = self.complexity_calculator.calculate_game_complexity_summary(
            position_complexities
        )
        
        # 4. Temporal consistency metrics
        metrics['temporal_metrics'] = self._calculate_temporal_metrics(move_analyses)
        
        # 5. Overall accuracy metrics
        metrics['accuracy_metrics'] = self._calculate_accuracy_metrics(move_analyses)
        
        # 6. Custom behavioral metrics
        metrics['behavioral_metrics'] = self._calculate_behavioral_metrics(
            move_analyses, game_data
        )
        
        # 7. Summary risk assessment
        metrics['risk_assessment'] = self._calculate_risk_assessment(metrics)
        
        return metrics
    
    def _calculate_opening_metrics(self, opening_analysis: Dict) -> Dict:
        """Calculate opening theory related metrics."""
        return {
            'opening_moves_count': opening_analysis.get('opening_moves_count', 0),
            'opening_percentage': opening_analysis.get('opening_percentage', 0),
            'deviation_move_number': opening_analysis.get('deviation_move', None),
            'is_mostly_opening': opening_analysis.get('is_mostly_opening', False),
            'opening_strength': self._assess_opening_strength(opening_analysis)
        }
    
    def _calculate_engine_matching_metrics(self, move_analyses: List[Dict]) -> Dict:
        """Calculate engine move matching metrics (PV-1, PV-2, PV-3)."""
        pv1_matches = 0
        pv2_matches = 0
        pv3_matches = 0
        total_analyzed = 0
        
        for analysis in move_analyses:
            engine_data = analysis.get('engine_analysis', {})
            if not engine_data.get('is_legal', False):
                continue
                
            move_rank = engine_data.get('move_rank', 0)
            if move_rank > 0:
                total_analyzed += 1
                
                if move_rank == 1:
                    pv1_matches += 1
                    pv2_matches += 1
                    pv3_matches += 1
                elif move_rank == 2:
                    pv2_matches += 1
                    pv3_matches += 1
                elif move_rank == 3:
                    pv3_matches += 1
        
        if total_analyzed == 0:
            return {
                'pv1_matches': 0,
                'pv2_matches': 0,
                'pv3_matches': 0,
                'pv1_percentage': 0,
                'pv2_percentage': 0,
                'pv3_percentage': 0,
                'total_analyzed': 0
            }
        
        return {
            'pv1_matches': pv1_matches,
            'pv2_matches': pv2_matches,
            'pv3_matches': pv3_matches,
            'pv1_percentage': (pv1_matches / total_analyzed) * 100,
            'pv2_percentage': (pv2_matches / total_analyzed) * 100,
            'pv3_percentage': (pv3_matches / total_analyzed) * 100,
            'total_analyzed': total_analyzed
        }
    
    def _calculate_temporal_metrics(self, move_analyses: List[Dict]) -> Dict:
        """Calculate temporal consistency metrics."""
        move_times = []
        white_times = []
        black_times = []
        
        for analysis in move_analyses:
            move_time = analysis.get('move_time')
            if move_time is not None and move_time > 0:
                move_times.append(move_time)
                
                if analysis['player'] == 'white':
                    white_times.append(move_time)
                else:
                    black_times.append(move_time)
        
        if not move_times:
            return {
                'move_time_std': 0,
                'move_time_mean': 0,
                'move_time_cv': 0,
                'white_time_std': 0,
                'black_time_std': 0,
                'time_consistency_score': 0
            }
        
        # Calculate statistics
        move_time_mean = np.mean(move_times)
        move_time_std = np.std(move_times)
        move_time_cv = move_time_std / move_time_mean if move_time_mean > 0 else 0
        
        white_time_std = np.std(white_times) if white_times else 0
        black_time_std = np.std(black_times) if black_times else 0
        
        # Time consistency score (lower is more consistent)
        time_consistency_score = move_time_cv
        
        return {
            'move_time_std': move_time_std,
            'move_time_mean': move_time_mean,
            'move_time_cv': move_time_cv,
            'white_time_std': white_time_std,
            'black_time_std': black_time_std,
            'time_consistency_score': time_consistency_score,
            'total_moves_with_time': len(move_times)
        }
    
    def _calculate_accuracy_metrics(self, move_analyses: List[Dict]) -> Dict:
        """Calculate overall accuracy metrics."""
        centipawn_losses = []
        total_moves = 0
        
        for analysis in move_analyses:
            engine_data = analysis.get('engine_analysis', {})
            if engine_data.get('is_legal', False):
                total_moves += 1
                cp_loss = engine_data.get('centipawn_loss', 0)
                centipawn_losses.append(cp_loss)
        
        if not centipawn_losses:
            return {
                'avg_centipawn_loss': 0,
                'total_centipawn_loss': 0,
                'accuracy_score': 0,
                'blunder_count': 0,
                'mistake_count': 0,
                'inaccuracy_count': 0
            }
        
        # Calculate accuracy metrics
        avg_cp_loss = np.mean(centipawn_losses)
        total_cp_loss = sum(centipawn_losses)
        
        # Count blunders, mistakes, inaccuracies
        blunders = sum(1 for loss in centipawn_losses if loss >= 300)
        mistakes = sum(1 for loss in centipawn_losses if 100 <= loss < 300)
        inaccuracies = sum(1 for loss in centipawn_losses if 50 <= loss < 100)
        
        # Calculate accuracy score (0-100, higher is better)
        # Based on average centipawn loss
        accuracy_score = max(0, 100 - (avg_cp_loss / 10))
        
        return {
            'avg_centipawn_loss': avg_cp_loss,
            'total_centipawn_loss': total_cp_loss,
            'accuracy_score': accuracy_score,
            'blunder_count': blunders,
            'mistake_count': mistakes,
            'inaccuracy_count': inaccuracies,
            'total_moves': total_moves
        }
    
    def _calculate_behavioral_metrics(self, move_analyses: List[Dict], game_data: Dict) -> Dict:
        """Calculate custom behavioral metrics."""
        # 1. Move time variance in critical positions
        critical_position_times = []
        normal_position_times = []
        
        for analysis in move_analyses:
            complexity = analysis.get('complexity', {}).get('total_complexity', 0)
            move_time = analysis.get('move_time')
            
            if move_time is not None and move_time > 0:
                if complexity > 0.6:  # High complexity threshold
                    critical_position_times.append(move_time)
                else:
                    normal_position_times.append(move_time)
        
        # Calculate time ratio for critical vs normal positions
        critical_time_ratio = 1.0
        if critical_position_times and normal_position_times:
            critical_avg = np.mean(critical_position_times)
            normal_avg = np.mean(normal_position_times)
            critical_time_ratio = critical_avg / normal_avg if normal_avg > 0 else 1.0
        
        # 2. Consistency in similar positions
        position_consistency = self._calculate_position_consistency(move_analyses)
        
        # 3. Endgame vs middlegame performance
        endgame_performance = self._calculate_phase_performance(move_analyses)
        
        return {
            'critical_time_ratio': critical_time_ratio,
            'position_consistency': position_consistency,
            'endgame_performance': endgame_performance,
            'critical_positions_count': len(critical_position_times),
            'normal_positions_count': len(normal_position_times)
        }
    
    def _calculate_position_consistency(self, move_analyses: List[Dict]) -> float:
        """Calculate consistency in handling similar position types."""
        # Group positions by complexity and calculate consistency
        complexity_groups = {'low': [], 'medium': [], 'high': []}
        
        for analysis in move_analyses:
            complexity = analysis.get('complexity', {}).get('total_complexity', 0)
            engine_data = analysis.get('engine_analysis', {})
            
            if engine_data.get('is_legal', False):
                cp_loss = engine_data.get('centipawn_loss', 0)
                
                if complexity < 0.4:
                    complexity_groups['low'].append(cp_loss)
                elif complexity < 0.7:
                    complexity_groups['medium'].append(cp_loss)
                else:
                    complexity_groups['high'].append(cp_loss)
        
        # Calculate consistency as inverse of coefficient of variation
        consistency_scores = []
        for group_name, losses in complexity_groups.items():
            if len(losses) > 1:
                mean_loss = np.mean(losses)
                std_loss = np.std(losses)
                cv = std_loss / mean_loss if mean_loss > 0 else 0
                consistency_scores.append(1 / (1 + cv))  # Higher is more consistent
        
        return np.mean(consistency_scores) if consistency_scores else 0.5
    
    def _calculate_phase_performance(self, move_analyses: List[Dict]) -> Dict:
        """Calculate performance in different game phases."""
        total_moves = len(move_analyses)
        if total_moves < 20:
            return {'opening': 0, 'middlegame': 0, 'endgame': 0}
        
        # Rough phase divisions
        opening_end = min(15, total_moves // 4)
        endgame_start = max(total_moves - 15, 3 * total_moves // 4)
        
        phases = {
            'opening': move_analyses[:opening_end],
            'middlegame': move_analyses[opening_end:endgame_start],
            'endgame': move_analyses[endgame_start:]
        }
        
        phase_performance = {}
        for phase_name, phase_moves in phases.items():
            if phase_moves:
                cp_losses = []
                for analysis in phase_moves:
                    engine_data = analysis.get('engine_analysis', {})
                    if engine_data.get('is_legal', False):
                        cp_losses.append(engine_data.get('centipawn_loss', 0))
                
                if cp_losses:
                    avg_loss = np.mean(cp_losses)
                    phase_performance[phase_name] = max(0, 100 - (avg_loss / 10))
                else:
                    phase_performance[phase_name] = 0
            else:
                phase_performance[phase_name] = 0
        
        return phase_performance
    
    def _assess_opening_strength(self, opening_analysis: Dict) -> str:
        """Assess opening knowledge strength."""
        opening_moves = opening_analysis.get('opening_moves_count', 0)
        opening_percentage = opening_analysis.get('opening_percentage', 0)
        
        if opening_moves >= 12 and opening_percentage >= 30:
            return 'strong'
        elif opening_moves >= 8 and opening_percentage >= 20:
            return 'moderate'
        elif opening_moves >= 4:
            return 'weak'
        else:
            return 'very_weak'
    
    def _calculate_risk_assessment(self, metrics: Dict) -> Dict:
        """Calculate overall risk assessment for cheating."""
        risk_factors = []
        
        # 1. Engine matching risk
        pv1_pct = metrics['engine_matching'].get('pv1_percentage', 0)
        if pv1_pct > 80:
            risk_factors.append(('very_high_pv1', 0.9))
        elif pv1_pct > 60:
            risk_factors.append(('high_pv1', 0.7))
        elif pv1_pct > 40:
            risk_factors.append(('moderate_pv1', 0.4))
        
        # 2. Temporal consistency risk
        time_cv = metrics['temporal_metrics'].get('move_time_cv', 0)
        if time_cv < 0.3:
            risk_factors.append(('very_consistent_timing', 0.8))
        elif time_cv < 0.5:
            risk_factors.append(('consistent_timing', 0.5))
        
        # 3. Accuracy risk
        accuracy = metrics['accuracy_metrics'].get('accuracy_score', 0)
        if accuracy > 95:
            risk_factors.append(('very_high_accuracy', 0.9))
        elif accuracy > 85:
            risk_factors.append(('high_accuracy', 0.6))
        
        # 4. Complexity handling risk
        avg_complexity = metrics['complexity_metrics'].get('average_complexity', 0)
        if avg_complexity > 0.7:
            risk_factors.append(('high_complexity_handling', 0.7))
        
        # Calculate overall risk score
        if risk_factors:
            risk_score = np.mean([score for _, score in risk_factors])
        else:
            risk_score = 0.1  # Low risk if no factors
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = 'very_high'
        elif risk_score >= 0.6:
            risk_level = 'high'
        elif risk_score >= 0.4:
            risk_level = 'moderate'
        elif risk_score >= 0.2:
            risk_level = 'low'
        else:
            risk_level = 'very_low'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'summary': f"Risk Level: {risk_level.upper()} (Score: {risk_score:.2f})"
        }
    
    def close(self):
        """Close all components."""
        if hasattr(self.engine_analyzer, 'close'):
            self.engine_analyzer.close()
        if hasattr(self.opening_explorer, 'close'):
            self.opening_explorer.close() 