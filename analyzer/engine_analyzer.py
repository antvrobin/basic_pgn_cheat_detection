"""
Chess Engine Analyzer - Production Version

This module provides comprehensive chess position analysis using Stockfish engine.
Optimized for speed and accuracy with configurable parameters.
"""

import chess
import chess.engine
import chess.pgn
import requests
import time
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from .complexity_calculator import ComplexityCalculator
from config import Config

class EngineAnalyzer:
    """
    Production-ready chess engine analyzer with optimized performance.
    
    Features:
    - Stockfish engine integration with optimized settings
    - Position complexity calculation
    - Opening theory analysis via Lichess API
    - Comprehensive move evaluation and ranking
    - Robust error handling and fallback mechanisms
    """
    
    def __init__(self):
        """Initialize the engine analyzer with optimized settings."""
        self.engine_path = Config.get_stockfish_path()
        self.complexity_calculator = ComplexityCalculator(self.engine_path)
        
        # Optimized engine settings for production (deterministic)
        self.engine_config = {
            'Hash': 64,           # 64MB hash for better performance
            'Threads': 1,         # Single thread for deterministic results
            'Move Overhead': 5,   # Reduced overhead for faster analysis
            'Slow Mover': 50,     # Optimized time management
            'UCI_ShowWDL': False, # Disable WDL for speed
            'Syzygy Path': '',    # Disable tablebase for speed
            'MultiPV': 3,         # Force 3 PV lines for PCS calculation
        }
        
        # Enhanced analysis settings for better accuracy and determinism
        self.analysis_depth = 12          # Deeper analysis for better PCS calculation
        self.move_time_limit = None       # Use fixed depth for deterministic results
        self.max_pv_moves = 3             # Focus on top 3 moves for PCS calculation
        
        # Opening theory settings
        self.opening_api_url = "https://explorer.lichess.ovh/lichess"
        self.opening_api_delay = 0.05     # 50ms delay between requests
        self.max_opening_moves = 20       # Analyze first 20 moves for opening theory
        
        # Complexity thresholds
        self.complexity_thresholds = {
            'very_low': 0.25,
            'low': 0.40,
            'medium': 0.60,
            'high': 0.75,
            'very_high': 1.0
        }
    
    def analyze_game(self, pgn_content: str) -> Dict[str, Any]:
        """
        Analyze a complete chess game from PGN content.
        
        Args:
            pgn_content: PGN string containing the game
            
        Returns:
            Dictionary containing comprehensive game analysis
        """
        try:
            # Parse PGN
            game_info, moves = self._parse_pgn(pgn_content)
            
            if not moves:
                raise ValueError("No moves found in PGN")
            
            print(f"Analyzing game: {len(moves)} moves")
            
            # Analyze each position
            move_analyses = []
            board = chess.Board()
            
            with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
                # Configure engine
                for option, value in self.engine_config.items():
                    try:
                        engine.configure({option: value})
                    except Exception as e:
                        print(f"Warning: Could not set {option} to {value}: {e}")
                
                # Analyze each move
                for i, move_data in enumerate(moves):
                    try:
                        print(f"Analyzing move {i+1}/{len(moves)}: {move_data['move']}")
                        print(f"  Move data: player={move_data['player']}, move={move_data['move']}, uci={move_data.get('uci', 'N/A')}")
                        print(f"  Current board position: {board.fen()}")
                        
                        # Analyze position before move (this is the key fix)
                        analysis = self._analyze_position(
                            engine, board, move_data['move'], move_data.get('time', 0)
                        )
                        
                        # Add move metadata
                        analysis.update({
                            'move_number': move_data['move_number'],
                            'player': move_data['player'],
                            'move': move_data['move'],
                            'move_time': move_data.get('time', 0),
                            'clock_time': move_data.get('clock', 0)
                        })
                        
                        move_analyses.append(analysis)
                        
                        # Make the move on the board AFTER analysis
                        try:
                            chess_move = None
                            # Try SAN first
                            try:
                                chess_move = board.parse_san(move_data['move'])
                                print(f"  Successfully parsed SAN move: {move_data['move']} -> {chess_move.uci()}")
                            except (ValueError, AssertionError) as e:
                                print(f"  SAN parsing failed for {move_data['move']}: {e}")
                                # Try UCI
                                try:
                                    chess_move = chess.Move.from_uci(move_data['uci'])
                                    print(f"  Successfully parsed UCI move: {move_data['uci']} -> {chess_move}")
                                except (ValueError, AssertionError) as e2:
                                    print(f"  UCI parsing also failed for {move_data['uci']}: {e2}")
                                    pass
                            
                            if chess_move and chess_move in board.legal_moves:
                                board.push(chess_move)
                                print(f"  Successfully made move: {chess_move}, new position: {board.fen()}")
                            else:
                                if chess_move:
                                    print(f"  Move {chess_move} is not legal in current position")
                                    print(f"  Legal moves: {[board.san(move) for move in board.legal_moves]}")
                                else:
                                    print(f"  Could not parse move at all")
                                # Try to continue with remaining moves instead of breaking
                                continue
                                
                        except Exception as e:
                            print(f"Error processing move {move_data['move']}: {e}")
                            continue
                            
                    except Exception as e:
                        print(f"Error analyzing move {i+1}: {e}")
                        continue
            
            # Calculate comprehensive metrics
            metrics = self._calculate_game_metrics(move_analyses)
            
            return {
                'success': True,
                'game_info': game_info,
                'move_analyses': move_analyses,
                'metrics': metrics,
                'analysis_settings': {
                    'engine_depth': self.analysis_depth,
                    'move_time_limit': self.move_time_limit,
                    'engine_config': self.engine_config
                }
            }
            
        except Exception as e:
            print(f"Error analyzing game: {e}")
            return {
                'success': False,
                'error': str(e),
                'game_info': {},
                'move_analyses': [],
                'metrics': {}
            }
    
    def _parse_pgn(self, pgn_content: str) -> Tuple[Dict, List[Dict]]:
        """Parse PGN content and extract game information and moves."""
        try:
            import io
            pgn_io = io.StringIO(pgn_content)
            game = chess.pgn.read_game(pgn_io)
            
            if not game:
                raise ValueError("Could not parse PGN")
            
            # Extract game information
            game_info = {
                'white': game.headers.get('White', 'Unknown'),
                'black': game.headers.get('Black', 'Unknown'),
                'result': game.headers.get('Result', '*'),
                'date': game.headers.get('Date', 'Unknown'),
                'event': game.headers.get('Event', 'Unknown'),
                'site': game.headers.get('Site', 'Unknown'),
                'time_control': game.headers.get('TimeControl', 'Unknown'),
                'eco': game.headers.get('ECO', 'Unknown')
            }
            
            # Extract moves with timing information
            moves = []
            board = chess.Board()
            move_number = 1
            last_clock = {'white': None, 'black': None}  # track remaining clock for each side
            
            for node in game.mainline():
                try:
                    move = node.move
                    
                    # Verify move is legal before processing
                    if move not in board.legal_moves:
                        print(f"Warning: Illegal move {move} found in PGN, skipping")
                        continue
                    
                    san_move = board.san(move)
                    
                    # Determine player
                    player = 'white' if board.turn == chess.WHITE else 'black'
                    
                    # Extract timing information
                    move_time = 0
                    clock_time = 0
                    
                    if node.comment:
                        # Parse timing from comment (format: [%clk H:MM:SS] or [%eval ...])
                        comment = node.comment
                        if '%clk' in comment:
                            try:
                                clk_start = comment.find('%clk') + 5
                                clk_end = comment.find(']', clk_start)
                                if clk_end > clk_start:
                                    time_str = comment[clk_start:clk_end].strip()
                                    # Parse H:MM:SS format
                                    time_parts = time_str.split(':')
                                    if len(time_parts) == 3:
                                        hours = int(time_parts[0])
                                        minutes = int(time_parts[1])
                                        seconds = int(time_parts[2])
                                        clock_time = hours * 3600 + minutes * 60 + seconds
                            except Exception:
                                pass
                        
                        # Try to extract move time if available
                        if 'move_time' in comment.lower():
                            try:
                                import re
                                time_match = re.search(r'(\d+\.?\d*)\s*s', comment)
                                if time_match:
                                    move_time = float(time_match.group(1))
                            except Exception:
                                pass
                    
                    # Estimate move time using same-player previous clock if available
                    if clock_time > 0:
                        if last_clock[player] is not None and last_clock[player] > 0:
                            move_time = max(0, last_clock[player] - clock_time)
                        last_clock[player] = clock_time
                    
                    moves.append({
                        'move_number': move_number,
                        'player': player,
                        'move': san_move,
                        'uci': move.uci(),
                        'time': move_time,
                        'clock': clock_time
                    })
                    
                    board.push(move)
                    
                    # Increment move number after black's move
                    if player == 'black':
                        move_number += 1
                
                except Exception as e:
                    print(f"Error processing move in PGN: {e}")
                    continue
            
            return game_info, moves
            
        except Exception as e:
            print(f"Error parsing PGN: {e}")
            return {}, []
    
    def _analyze_position(self, engine: chess.engine.SimpleEngine, 
                         board: chess.Board, move: str, move_time: float) -> Dict:
        """Analyze a single position comprehensively."""
        try:
            # Get engine analysis
            engine_analysis = self._get_engine_analysis(engine, board, move)
            
            # Prepare top moves for PCS calculation
            top_moves_for_pcs = []
            top_moves_data = engine_analysis.get('top_moves', [])
            print(f"Debug: Top moves data: {top_moves_data}")  # Debug line
            
            for top_move in top_moves_data[:3]:
                top_moves_for_pcs.append({
                    'score': top_move.get('evaluation', 0),
                    'move': top_move.get('move', ''),
                    'rank': top_move.get('rank', 0)
                })
            
            print(f"Debug: PCS input data: {top_moves_for_pcs}")  # Debug line
            
            # Calculate position complexity using enhanced PCS formula
            complexity_analysis = self.complexity_calculator.calculate_complexity(
                board, engine_analysis, top_moves_analysis=top_moves_for_pcs
            )
            
            # Get opening theory data
            opening_analysis = self._get_opening_analysis(board)
            
            return {
                'engine_analysis': engine_analysis,
                'complexity': complexity_analysis,
                'opening_analysis': opening_analysis,
                'position_fen': board.fen(),
                'legal_moves_count': len(list(board.legal_moves))
            }
            
        except Exception as e:
            print(f"Error analyzing position: {e}")
            return {
                'engine_analysis': {'error': str(e)},
                'complexity': self.complexity_calculator._get_default_complexity(),
                'opening_analysis': {},
                'position_fen': board.fen() if board else '',
                'legal_moves_count': 0
            }
    
    def _get_engine_analysis(self, engine: chess.engine.SimpleEngine, 
                            board: chess.Board, move: str) -> Dict:
        """Get comprehensive engine analysis for a position."""
        try:
            # Analyze position with fixed depth for deterministic results
            limit = chess.engine.Limit(depth=self.analysis_depth)
            if self.move_time_limit:
                limit = chess.engine.Limit(depth=self.analysis_depth, time=self.move_time_limit)
            
            info = engine.analyse(
                board, 
                limit,
                multipv=self.max_pv_moves
            )
            
            # Extract primary evaluation
            primary_score = info[0]['score'].relative
            evaluation = primary_score.score(mate_score=10000) or 0
            
            # Get top moves - with better error handling
            top_moves = []
            for i, pv_info in enumerate(info[:self.max_pv_moves]):
                try:
                    if 'pv' in pv_info and pv_info['pv'] and len(pv_info['pv']) > 0:
                        first_move = pv_info['pv'][0]
                        
                        # Verify move is legal before converting
                        if first_move in board.legal_moves:
                            move_uci = first_move.uci()
                            move_san = board.san(first_move)
                            score = pv_info['score'].relative.score(mate_score=10000) or 0
                            
                            # Build PV line safely
                            pv_san = []
                            temp_board = board.copy()
                            for pv_move_obj in pv_info['pv'][:3]:
                                if pv_move_obj in temp_board.legal_moves:
                                    pv_san.append(temp_board.san(pv_move_obj))
                                    temp_board.push(pv_move_obj)
                                else:
                                    break
                            
                            top_moves.append({
                                'rank': i + 1,
                                'move': move_san,
                                'uci': move_uci,
                                'evaluation': score,
                                'pv': pv_san
                            })
                except Exception as e:
                    print(f"Error processing top move {i}: {e}")
                    continue
            
            # Find played move rank
            move_rank = 0
            centipawn_loss = 0
            
            try:
                print(f"  Engine analysis: Looking for move '{move}' in position {board.fen()}")
                
                # Parse move safely - try multiple methods
                played_move = None
                
                # Try SAN first
                try:
                    played_move = board.parse_san(move)
                    print(f"  Successfully parsed '{move}' as SAN -> {played_move.uci()}")
                except (ValueError, AssertionError) as e:
                    print(f"  SAN parsing failed for '{move}': {e}")
                    # Try UCI
                    try:
                        played_move = chess.Move.from_uci(move)
                        if played_move not in board.legal_moves:
                            print(f"  UCI move {move} parsed but not legal")
                            played_move = None
                        else:
                            print(f"  Successfully parsed '{move}' as UCI -> {played_move}")
                    except (ValueError, AssertionError) as e2:
                        print(f"  UCI parsing also failed for '{move}': {e2}")
                        played_move = None
                
                if played_move and played_move in board.legal_moves:
                    played_uci = played_move.uci()
                    print(f"  Looking for {played_uci} in top moves:")
                    
                    # Find rank of played move
                    for i, top_move in enumerate(top_moves):
                        print(f"    Top move {i+1}: {top_move['uci']} ({top_move['move']})")
                        if top_move['uci'] == played_uci:
                            move_rank = i + 1
                            print(f"    MATCH! Move rank = {move_rank}")
                            break
                    
                    if move_rank == 0:
                        print(f"    Move {played_uci} not found in top moves")
                    
                    # Calculate centipawn loss
                    if top_moves:
                        best_eval = top_moves[0]['evaluation']
                        
                        if move_rank > 0:
                            played_eval = top_moves[move_rank - 1]['evaluation']
                            print(f"    Best eval: {best_eval}, Played eval: {played_eval}")
                        else:
                            # Move not in top moves, analyze it separately
                            try:
                                board_copy = board.copy()
                                board_copy.push(played_move)
                                played_info = engine.analyse(board_copy, chess.engine.Limit(depth=self.analysis_depth))
                                played_eval = -played_info['score'].relative.score(mate_score=10000) or 0
                                print(f"    Separately analyzed eval: {played_eval}")
                            except Exception:
                                played_eval = best_eval  # Fallback
                                print(f"    Using fallback eval: {played_eval}")
                        
                        centipawn_loss = max(0, best_eval - played_eval)
                        print(f"    Centipawn loss: {centipawn_loss}")
                else:
                    print(f"  Could not parse or validate move '{move}' in position")
                    print(f"  Legal moves in position: {[board.san(m) for m in board.legal_moves]}")
                
            except Exception as e:
                print(f"Error analyzing played move '{move}': {e}")
                import traceback
                traceback.print_exc()
            
            return {
                'evaluation': evaluation,
                'move_rank': move_rank,
                'centipawn_loss': centipawn_loss,
                'top_moves': top_moves,
                'depth': self.analysis_depth,
                'nodes': info[0].get('nodes', 0),
                'time': info[0].get('time', 0),
                'is_valid': True
            }
            
        except Exception as e:
            print(f"Error in engine analysis: {e}")
            return {
                'evaluation': 0,
                'move_rank': 0,
                'centipawn_loss': 0,
                'top_moves': [],
                'depth': 0,
                'nodes': 0,
                'time': 0,
                'is_valid': False,
                'error': str(e)
            }
    
    def _get_opening_analysis(self, board: chess.Board) -> Dict:
        """Get opening theory analysis from Lichess API."""
        try:
            # Only analyze opening moves
            if len(board.move_stack) > self.max_opening_moves:
                return {'in_theory': False, 'popularity': 0}
            
            # Get position FEN
            fen = board.fen().split(' ')[0]  # Only piece positions
            
            # Query Lichess opening explorer
            url = f"{self.opening_api_url}?fen={fen}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                total_games = data.get('white', 0) + data.get('draws', 0) + data.get('black', 0)
                
                if total_games > 0:
                    # Position is in opening theory
                    return {
                        'in_theory': True,
                        'popularity': total_games,
                        'white_wins': data.get('white', 0),
                        'draws': data.get('draws', 0),
                        'black_wins': data.get('black', 0),
                        'total_games': total_games
                    }
            
            # Add delay to avoid rate limiting
            time.sleep(self.opening_api_delay)
            
        except Exception as e:
            print(f"Error getting opening analysis: {e}")
        
        return {'in_theory': False, 'popularity': 0}
    
    def _calculate_game_metrics(self, move_analyses: List[Dict]) -> Dict:
        """Calculate comprehensive game metrics from move analyses."""
        try:
            if not move_analyses:
                return {}
            
            # Separate by player
            white_moves = [m for m in move_analyses if m.get('player') == 'white']
            black_moves = [m for m in move_analyses if m.get('player') == 'black']
            
            # Calculate metrics for each player and combined
            white_metrics = self._calculate_player_metrics(white_moves)
            black_metrics = self._calculate_player_metrics(black_moves)
            combined_metrics = self._calculate_player_metrics(move_analyses)
            
            # Calculate complexity distribution using PCS data
            all_complexities = []
            position_complexities = []
            for move in move_analyses:
                complexity_data = move.get('complexity', {})
                pcs_score = complexity_data.get('pcs_score', 0)
                all_complexities.append(pcs_score)
                position_complexities.append(complexity_data)
            
            # Use new complexity summary calculation
            complexity_summary = self.complexity_calculator.calculate_game_complexity_summary(position_complexities)
            
            return {
                'white_player': white_metrics,
                'black_player': black_metrics,
                'combined': combined_metrics,
                'accuracy_metrics': combined_metrics.get('accuracy_metrics', {}),
                'engine_matching': combined_metrics.get('engine_matching', {}),
                'complexity_metrics': {
                    'average_pcs': complexity_summary.get('average_pcs', 0),
                    'max_pcs': complexity_summary.get('max_pcs', 0),
                    'category_distribution': complexity_summary.get('category_distribution', {}),
                    'category_percentages': complexity_summary.get('category_percentages', {}),
                    'critical_chaotic_percentage': complexity_summary.get('critical_chaotic_percentage', 0),
                    'longest_critical_streak': complexity_summary.get('longest_critical_streak', 0),
                    'complexity_variance': complexity_summary.get('complexity_variance', 0),
                    'complexity_trend': self._calculate_complexity_trend(all_complexities)
                },
                'temporal_metrics': combined_metrics.get('temporal_metrics', {}),
                'opening_metrics': self._calculate_opening_metrics(move_analyses)
            }
            
        except Exception as e:
            print(f"Error calculating game metrics: {e}")
            return {}
    
    def _calculate_player_metrics(self, moves: List[Dict]) -> Dict:
        """Calculate metrics for a specific player or combined."""
        try:
            if not moves:
                return {}
            
            # Extract engine analysis data
            valid_moves = []
            for move in moves:
                engine_data = move.get('engine_analysis', {})
                if engine_data.get('is_valid', False):
                    valid_moves.append(move)
            
            if not valid_moves:
                return {}
            
            # Accuracy metrics
            centipawn_losses = []
            move_ranks = []
            blunder_count = 0
            mistake_count = 0
            
            for move in valid_moves:
                engine_data = move.get('engine_analysis', {})
                cp_loss = engine_data.get('centipawn_loss', 0)
                move_rank = engine_data.get('move_rank', 0)
                
                centipawn_losses.append(cp_loss)
                if move_rank > 0:
                    move_ranks.append(move_rank)
                
                # Count blunders and mistakes
                if cp_loss >= 300:
                    blunder_count += 1
                elif cp_loss >= 100:
                    mistake_count += 1
            
            avg_cp_loss = np.mean(centipawn_losses) if centipawn_losses else 0
            accuracy_score = max(0, 100 - (avg_cp_loss / 3.0))  # Adjusted formula
            
            # Engine matching metrics
            pv1_count = sum(1 for move in valid_moves 
                           if move.get('engine_analysis', {}).get('move_rank') == 1)
            pv2_count = sum(1 for move in valid_moves 
                           if move.get('engine_analysis', {}).get('move_rank') <= 2)
            pv3_count = sum(1 for move in valid_moves 
                           if move.get('engine_analysis', {}).get('move_rank') <= 3)
            
            total_analyzed = len(valid_moves)
            
            pv1_percentage = (pv1_count / total_analyzed) * 100 if total_analyzed > 0 else 0
            pv2_percentage = (pv2_count / total_analyzed) * 100 if total_analyzed > 0 else 0
            pv3_percentage = (pv3_count / total_analyzed) * 100 if total_analyzed > 0 else 0

            # Opening moves count (within theory according to Lichess explorer)
            opening_move_count = 0
            for mv in moves:
                opening_data = mv.get('opening_analysis', {})
                if opening_data.get('in_theory', False):
                    opening_move_count += 1
                # Stop counting once out of opening theory window
                if len(mv.get('move', '')) > 0 and not opening_data.get('in_theory', False):
                    break
            
            # Timing metrics
            move_times = []
            for move in moves:
                move_time = move.get('move_time', 0)
                if move_time > 0:
                    move_times.append(move_time)
            
            timing_metrics = {}
            if move_times:
                timing_metrics = {
                    'move_time_mean': np.mean(move_times),
                    'move_time_std': np.std(move_times),
                    'move_time_cv': np.std(move_times) / np.mean(move_times) if np.mean(move_times) > 0 else 0,
                    'total_moves_with_time': len(move_times),
                    'time_consistency_score': max(0, 1 - (np.std(move_times) / np.mean(move_times))) if np.mean(move_times) > 0 else 0
                }
            
            return {
                'accuracy_metrics': {
                    'accuracy_score': accuracy_score,
                    'avg_centipawn_loss': avg_cp_loss,
                    'blunder_count': blunder_count,
                    'mistake_count': mistake_count,
                    'total_moves': total_analyzed
                },
                'engine_matching': {
                    'pv1_percentage': pv1_percentage,
                    'pv2_percentage': pv2_percentage,
                    'pv3_percentage': pv3_percentage,
                    'total_analyzed': total_analyzed,
                    'pv1_count': pv1_count,
                    'pv2_count': pv2_count,
                    'pv3_count': pv3_count,
                    'pv1_3_count': pv3_count  # alias
                },
                'temporal_metrics': timing_metrics,
                'opening_metrics_player': {
                    'opening_move_count': opening_move_count
                }
            }
            
        except Exception as e:
            print(f"Error calculating player metrics: {e}")
            return {}
    
    def _calculate_complexity_trend(self, complexities: List[float]) -> str:
        """Calculate complexity trend throughout the game."""
        if len(complexities) < 6:
            return 'insufficient_data'
        
        try:
            # Split into thirds
            third = len(complexities) // 3
            early = complexities[:third]
            middle = complexities[third:2*third]
            late = complexities[2*third:]
            
            early_avg = np.mean(early)
            middle_avg = np.mean(middle)
            late_avg = np.mean(late)
            
            # Determine trend
            if late_avg > middle_avg > early_avg:
                return 'increasing'
            elif early_avg > middle_avg > late_avg:
                return 'decreasing'
            elif middle_avg > early_avg and middle_avg > late_avg:
                return 'peak_middle'
            elif abs(late_avg - early_avg) < 0.1:
                return 'stable'
            else:
                return 'variable'
                
        except Exception:
            return 'unknown'
    
    def _calculate_opening_metrics(self, moves: List[Dict]) -> Dict:
        """Calculate opening theory metrics."""
        try:
            opening_moves = moves[:self.max_opening_moves]
            
            theory_moves = 0
            total_popularity = 0
            
            for move in opening_moves:
                opening_data = move.get('opening_analysis', {})
                if opening_data.get('in_theory', False):
                    theory_moves += 1
                    total_popularity += opening_data.get('popularity', 0)
            
            return {
                'moves_in_theory': theory_moves,
                'theory_percentage': (theory_moves / len(opening_moves)) * 100 if opening_moves else 0,
                'avg_popularity': total_popularity / theory_moves if theory_moves > 0 else 0,
                'total_opening_moves': len(opening_moves)
            }
            
        except Exception as e:
            print(f"Error calculating opening metrics: {e}")
            return {}
    
    def validate_engine(self) -> bool:
        """Validate that the engine is working correctly."""
        try:
            with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
                board = chess.Board()
                result = engine.play(board, chess.engine.Limit(time=0.1))
                return result.move is not None
        except Exception as e:
            print(f"Engine validation failed: {e}")
            return False
    
    def analyze_move(self, fen_before: str, uci_move: str, depth: int = None) -> Dict:
        """
        Analyze a single move in a position.
        
        Args:
            fen_before: FEN string of position before move
            uci_move: UCI notation of the move
            depth: Analysis depth (uses default if None)
            
        Returns:
            Dictionary with move analysis results
        """
        try:
            board = chess.Board(fen_before)
            move = chess.Move.from_uci(uci_move)
            
            if not move in board.legal_moves:
                return {
                    'is_legal': False,
                    'evaluation': 0,
                    'centipawn_loss': 0,
                    'move_rank': 0,
                    'best_move': '',
                    'pv_moves': []
                }
            
            with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
                # Configure engine
                for option, value in self.engine_config.items():
                    try:
                        engine.configure({option: value})
                    except Exception:
                        pass
                
                # Analyze position before move
                analysis_depth = depth or self.analysis_depth
                info = engine.analyse(board, chess.engine.Limit(depth=analysis_depth))
                
                # Get evaluation before move
                eval_before = info['score'].relative.score(mate_score=1000) or 0
                
                # Get top moves
                multipv_info = engine.analyse(board, chess.engine.Limit(depth=analysis_depth), multipv=5)
                top_moves = []
                move_rank = 0
                
                for i, pv_info in enumerate(multipv_info):
                    pv_move = pv_info['pv'][0] if pv_info['pv'] else None
                    if pv_move:
                        top_moves.append(pv_move)
                        if pv_move == move:
                            move_rank = i + 1
                
                # Calculate evaluation after move
                board.push(move)
                after_info = engine.analyse(board, chess.engine.Limit(depth=analysis_depth))
                eval_after = -(after_info['score'].relative.score(mate_score=1000) or 0)
                
                # Calculate centipawn loss
                centipawn_loss = max(0, eval_before - eval_after)
                
                # Safely convert moves to SAN notation
                board.pop()  # Go back to original position
                best_move_san = ''
                pv_moves_san = []
                
                try:
                    if top_moves:
                        best_move_san = board.san(top_moves[0])
                        for move_obj in top_moves[:3]:
                            if move_obj in board.legal_moves:
                                pv_moves_san.append(board.san(move_obj))
                except Exception as e:
                    print(f"Error converting moves to SAN: {e}")
                
                return {
                    'is_legal': True,
                    'evaluation': eval_after,
                    'centipawn_loss': centipawn_loss,
                    'move_rank': move_rank,
                    'best_move': best_move_san,
                    'pv_moves': pv_moves_san
                }
                
        except Exception as e:
            print(f"Error analyzing move: {e}")
            return {
                'is_legal': False,
                'evaluation': 0,
                'centipawn_loss': 0,
                'move_rank': 0,
                'best_move': '',
                'pv_moves': []
            }
    
    def analyze_at_multiple_depths(self, fen: str, depths: List[int]) -> Dict:
        """
        Analyze position at multiple depths for complexity calculation.
        
        Args:
            fen: FEN string of position
            depths: List of depths to analyze
            
        Returns:
            Dictionary with multi-depth analysis results
        """
        try:
            board = chess.Board(fen)
            results = {}
            
            with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
                # Configure engine
                for option, value in self.engine_config.items():
                    try:
                        engine.configure({option: value})
                    except Exception:
                        pass
                
                for depth in depths:
                    try:
                        info = engine.analyse(board, chess.engine.Limit(depth=depth))
                        evaluation = info['score'].relative.score(mate_score=1000) or 0
                        
                        # Safely convert moves to SAN
                        best_move_san = ''
                        pv_moves_san = []
                        
                        try:
                            if info['pv']:
                                best_move = info['pv'][0]
                                if best_move in board.legal_moves:
                                    best_move_san = board.san(best_move)
                                    for move_obj in info['pv'][:3]:
                                        if move_obj in board.legal_moves:
                                            pv_moves_san.append(board.san(move_obj))
                        except Exception as e:
                            print(f"Error converting PV moves to SAN at depth {depth}: {e}")
                        
                        results[f'depth_{depth}'] = {
                            'evaluation': evaluation,
                            'best_move': best_move_san,
                            'pv_moves': pv_moves_san
                        }
                    except Exception as e:
                        print(f"Error analyzing at depth {depth}: {e}")
                        results[f'depth_{depth}'] = {
                            'evaluation': 0,
                            'best_move': '',
                            'pv_moves': []
                        }
            
            return results
            
        except Exception as e:
            print(f"Error in multi-depth analysis: {e}")
            return {} 