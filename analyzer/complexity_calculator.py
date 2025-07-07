"""
Enhanced Position Complexity Calculator with PCS Formula

This module implements the improved Positional Complexity Score (PCS) based on
the Maia paper insights and top move evaluation differences.
"""

import chess
import chess.engine
import math
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import Counter

class ComplexityCalculator:
    """
    Calculate position complexity using the enhanced PCS formula.
    
    PCS Formula: max(0, score_2 - score_1) + max(0, score_3 - score_1) / 2
    
    This provides human-readable complexity that distinguishes high-decision
    fatigue positions and helps identify critical game moments.
    """
    
    def __init__(self, engine_path: str):
        self.engine_path = engine_path
        
        # PCS complexity thresholds based on centipawn differences
        self.pcs_thresholds = {
            'trivial': 30,      # < 30: Clear best move
            'balanced': 80,     # 30-80: Some choice but not critical
            'critical': 150,    # 80-150: Difficult decision
            'chaotic': float('inf')  # > 150: Many equally good options
        }
        
        # Enhanced weights for comprehensive analysis
        self.weights = {
            'pcs_score': 0.60,           # Primary: Top move evaluation gaps
            'tactical_density': 0.20,    # Secondary: Forcing moves present
            'choice_entropy': 0.15,      # Tertiary: Move variety
            'strategic_factors': 0.05    # Minor: Pawn structure, king safety
        }
    
    def calculate_complexity(self, board: chess.Board, engine_analysis: Dict, 
                           top_moves_analysis: List[Dict] = None) -> Dict:
        """
        Calculate enhanced position complexity using PCS formula.
        
        Args:
            board: Current chess position
            engine_analysis: Engine evaluation data
            top_moves_analysis: List of top 3 moves with evaluations
            
        Returns:
            Dictionary with enhanced complexity metrics
        """
        try:
            # Calculate PCS score from top moves
            pcs_score = self._calculate_pcs_score(top_moves_analysis or [])
            
            # Calculate supporting metrics
            tactical_density = self._calculate_tactical_density(board)
            choice_entropy = self._calculate_choice_entropy(board)
            strategic_factors = self._calculate_strategic_factors(board)
            
            # Determine PCS category
            pcs_category = self._get_pcs_category(pcs_score)
            
            # Calculate normalized complexity (0-1 scale)
            normalized_complexity = self._normalize_complexity(
                pcs_score, tactical_density, choice_entropy, strategic_factors
            )
            
            # Calculate decision difficulty score
            decision_difficulty = self._calculate_decision_difficulty(
                pcs_score, len(list(board.legal_moves))
            )
            
            return {
                'pcs_score': pcs_score,
                'pcs_category': pcs_category,
                'normalized_complexity': normalized_complexity,
                'decision_difficulty': decision_difficulty,
                'components': {
                    'pcs_score': pcs_score,
                    'tactical_density': tactical_density,
                    'choice_entropy': choice_entropy,
                    'strategic_factors': strategic_factors
                },
                'interpretation': self._get_complexity_interpretation(pcs_category, pcs_score),
                'legal_moves_count': len(list(board.legal_moves))
            }
            
        except Exception as e:
            print(f"Error calculating complexity: {e}")
            return self._get_default_complexity()
    
    def _calculate_pcs_score(self, top_moves_analysis: List[Dict]) -> float:
        """
        Calculate Positional Complexity Score using top 3 move evaluations.
        
        PCS = max(0, score_2 - score_1) + max(0, score_3 - score_1) / 2
        
        Args:
            top_moves_analysis: List of dictionaries with move evaluations
            
        Returns:
            PCS score in centipawns
        """
        if not top_moves_analysis or len(top_moves_analysis) < 2:
            return 0.0
        
        # Extract scores (assuming they're in centipawns)
        scores = []
        for move_data in top_moves_analysis[:3]:
            score = move_data.get('score', 0)
            # Handle mate scores
            if isinstance(score, dict):
                if score.get('mate'):
                    # Convert mate in N to large centipawn value
                    mate_moves = score['mate']
                    score = 1000 if mate_moves > 0 else -1000
                else:
                    score = score.get('cp', 0)
            scores.append(score)
        
        # Ensure we have at least 2 scores
        while len(scores) < 3:
            scores.append(scores[-1] if scores else 0)
        
        score_1, score_2, score_3 = scores[0], scores[1], scores[2]
        
        # Apply PCS formula
        pcs = max(0, score_1 - score_2) + max(0, score_1 - score_3) / 2
        
        print(f"Debug PCS: scores={scores}, pcs={pcs}")  # Debug line
        
        return float(pcs)
    
    def _get_pcs_category(self, pcs_score: float) -> str:
        """Get human-readable category for PCS score."""
        if pcs_score < self.pcs_thresholds['trivial']:
            return 'trivial'
        elif pcs_score < self.pcs_thresholds['balanced']:
            return 'balanced'
        elif pcs_score < self.pcs_thresholds['critical']:
            return 'critical'
        else:
            return 'chaotic'
    
    def _normalize_complexity(self, pcs_score: float, tactical_density: float,
                            choice_entropy: float, strategic_factors: float) -> float:
        """
        Normalize complexity to 0-1 scale using weighted components.
        """
        # Normalize PCS score (cap at 200 centipawns for scaling)
        normalized_pcs = min(1.0, pcs_score / 200.0)
        
        # Combine with weights
        complexity = (
            normalized_pcs * self.weights['pcs_score'] +
            tactical_density * self.weights['tactical_density'] +
            choice_entropy * self.weights['choice_entropy'] +
            strategic_factors * self.weights['strategic_factors']
        )
        
        return max(0.0, min(1.0, complexity))
    
    def _calculate_decision_difficulty(self, pcs_score: float, legal_moves: int) -> float:
        """
        Calculate decision difficulty based on PCS and move count.
        
        This metric helps identify positions requiring high cognitive load.
        """
        # Base difficulty from PCS
        base_difficulty = min(1.0, pcs_score / 150.0)
        
        # Adjust for number of legal moves
        move_factor = min(1.0, legal_moves / 40.0)
        
        # Combine factors
        difficulty = (base_difficulty * 0.8) + (move_factor * 0.2)
        
        return max(0.0, min(1.0, difficulty))
    
    def _calculate_tactical_density(self, board: chess.Board) -> float:
        """
        Calculate tactical density of position.
        
        Higher density indicates more forcing moves and tactical opportunities.
        """
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return 0.0
        
        tactical_moves = 0
        
        for move in legal_moves:
            # Count captures
            if board.is_capture(move):
                tactical_moves += 1
            
            # Count checks
            elif board.gives_check(move):
                tactical_moves += 1
            
            # Count promotions
            elif move.promotion:
                tactical_moves += 1
        
        # Calculate density as ratio
        density = tactical_moves / len(legal_moves)
        
        # Apply scaling for better distribution
        return min(1.0, density * 1.5)
    
    def _calculate_choice_entropy(self, board: chess.Board) -> float:
        """
        Calculate choice entropy based on move variety.
        
        More diverse move types indicate higher complexity.
        """
        legal_moves = list(board.legal_moves)
        if len(legal_moves) <= 1:
            return 0.0
        
        # Categorize moves
        move_categories = {
            'captures': 0,
            'checks': 0,
            'quiet': 0,
            'castling': 0,
            'promotions': 0
        }
        
        for move in legal_moves:
            if board.is_capture(move):
                move_categories['captures'] += 1
            elif board.gives_check(move):
                move_categories['checks'] += 1
            elif move.promotion:
                move_categories['promotions'] += 1
            elif board.is_castling(move):
                move_categories['castling'] += 1
            else:
                move_categories['quiet'] += 1
        
        # Calculate Shannon entropy
        total_moves = len(legal_moves)
        entropy = 0.0
        
        for count in move_categories.values():
            if count > 0:
                p = count / total_moves
                entropy -= p * math.log2(p)
        
        # Normalize to 0-1 (max entropy for 5 categories is log2(5) ≈ 2.32)
        return min(1.0, entropy / 2.32)
    
    def _calculate_strategic_factors(self, board: chess.Board) -> float:
        """
        Calculate strategic complexity factors.
        
        Includes pawn structure, king safety, and material considerations.
        """
        factors = 0.0
        
        # Pawn structure complexity
        pawn_complexity = self._analyze_pawn_structure(board)
        factors += pawn_complexity * 0.4
        
        # King safety considerations
        king_safety = self._analyze_king_safety(board)
        factors += king_safety * 0.3
        
        # Material imbalance
        material_factor = self._analyze_material_imbalance(board)
        factors += material_factor * 0.3
        
        return min(1.0, factors)
    
    def _analyze_pawn_structure(self, board: chess.Board) -> float:
        """Analyze pawn structure complexity."""
        complexity = 0.0
        
        # Count pawn islands and isolated pawns
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)
        
        # Simplified pawn structure analysis
        total_pawns = len(white_pawns) + len(black_pawns)
        if total_pawns == 0:
            return 0.0
        
        # More pawns generally mean more structure complexity
        base_complexity = min(1.0, total_pawns / 16.0)
        
        return base_complexity * 0.5  # Moderate influence
    
    def _analyze_king_safety(self, board: chess.Board) -> float:
        """Analyze king safety complexity."""
        complexity = 0.0
        
        # Check if kings are castled
        white_king_sq = board.king(chess.WHITE)
        black_king_sq = board.king(chess.BLACK)
        
        if white_king_sq and black_king_sq:
            # Kings in center are more complex
            white_center = chess.square_file(white_king_sq) in [3, 4]
            black_center = chess.square_file(black_king_sq) in [3, 4]
            
            if white_center or black_center:
                complexity += 0.5
        
        return min(1.0, complexity)
    
    def _analyze_material_imbalance(self, board: chess.Board) -> float:
        """Analyze material imbalance complexity."""
        # Simple material count
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        
        white_material = sum(
            len(board.pieces(piece_type, chess.WHITE)) * value
            for piece_type, value in piece_values.items()
        )
        
        black_material = sum(
            len(board.pieces(piece_type, chess.BLACK)) * value
            for piece_type, value in piece_values.items()
        )
        
        total_material = white_material + black_material
        if total_material == 0:
            return 0.0
        
        # Imbalance creates complexity
        imbalance = abs(white_material - black_material)
        return min(1.0, imbalance / (total_material * 0.2))
    
    def _get_complexity_interpretation(self, category: str, pcs_score: float) -> str:
        """Get human-readable interpretation of complexity."""
        interpretations = {
            'trivial': f"Clear best move (PCS: {pcs_score:.1f}). Low decision difficulty.",
            'balanced': f"Some choice available (PCS: {pcs_score:.1f}). Moderate complexity.",
            'critical': f"Difficult decision required (PCS: {pcs_score:.1f}). High complexity.",
            'chaotic': f"Many equally good options (PCS: {pcs_score:.1f}). Very high complexity."
        }
        return interpretations.get(category, f"Unknown complexity (PCS: {pcs_score:.1f})")
    
    def _get_default_complexity(self) -> Dict:
        """Return default complexity data in case of errors."""
        return {
            'pcs_score': 0.0,
            'pcs_category': 'trivial',
            'normalized_complexity': 0.3,
            'decision_difficulty': 0.3,
            'components': {
                'pcs_score': 0.0,
                'tactical_density': 0.0,
                'choice_entropy': 0.0,
                'strategic_factors': 0.0
            },
            'interpretation': "Unable to calculate complexity",
            'legal_moves_count': 0
        }
    
    def calculate_game_complexity_summary(self, position_complexities: List[Dict]) -> Dict:
        """
        Calculate game-level complexity statistics.
        
        Args:
            position_complexities: List of complexity data for each position
            
        Returns:
            Game-level complexity summary
        """
        if not position_complexities:
            return self._get_empty_game_summary()
        
        # Extract PCS scores and categories
        pcs_scores = [pos.get('pcs_score', 0) for pos in position_complexities]
        categories = [pos.get('pcs_category', 'trivial') for pos in position_complexities]
        
        # Calculate statistics
        avg_pcs = np.mean(pcs_scores) if pcs_scores else 0
        max_pcs = max(pcs_scores) if pcs_scores else 0
        
        # Count categories
        category_counts = Counter(categories)
        total_positions = len(position_complexities)
        
        # Calculate percentages
        category_percentages = {
            category: (count / total_positions) * 100
            for category, count in category_counts.items()
        }
        
        # Find complexity streaks
        critical_streak = self._find_longest_streak(categories, ['critical', 'chaotic'])
        
        return {
            'average_pcs': avg_pcs,
            'max_pcs': max_pcs,
            'category_distribution': category_counts,
            'category_percentages': category_percentages,
            'critical_chaotic_percentage': category_percentages.get('critical', 0) + 
                                         category_percentages.get('chaotic', 0),
            'longest_critical_streak': critical_streak,
            'total_positions': total_positions,
            'complexity_variance': np.var(pcs_scores) if len(pcs_scores) > 1 else 0
        }
    
    def _find_longest_streak(self, categories: List[str], target_categories: List[str]) -> int:
        """Find longest consecutive streak of target categories."""
        max_streak = 0
        current_streak = 0
        
        for category in categories:
            if category in target_categories:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _get_empty_game_summary(self) -> Dict:
        """Return empty game summary for error cases."""
        return {
            'average_pcs': 0.0,
            'max_pcs': 0.0,
            'category_distribution': {},
            'category_percentages': {},
            'critical_chaotic_percentage': 0.0,
            'longest_critical_streak': 0,
            'total_positions': 0,
            'complexity_variance': 0.0
        } 