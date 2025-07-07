"""
Opening Explorer for interfacing with Lichess Opening Explorer API.
"""

import requests
import chess
import chess.pgn
from typing import List, Dict, Optional, Set
import logging
import time
from config import Config

class OpeningExplorer:
    """
    Interfaces with Lichess Opening Explorer API to determine if moves
    are within known opening theory.
    """
    
    def __init__(self):
        """Initialize the opening explorer."""
        self.base_url = "https://explorer.lichess.ovh"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Chess-Analysis-Tool/1.0'
        })
        
    def is_opening_move(self, moves: List[str], position_fen: str = None) -> bool:
        """
        Check if a sequence of moves is within opening theory.
        
        Args:
            moves: List of moves in UCI notation
            position_fen: Optional FEN to start from (defaults to starting position)
            
        Returns:
            True if the move sequence is in opening theory
        """
        try:
            # Convert UCI moves to comma-separated string for API
            moves_string = ','.join(moves)
            
            # Query the Lichess API directly
            response = self._query_opening_api(moves_string, use_masters=False)
            
            if response:
                # Check total games in this position
                total_games = response.get('white', 0) + response.get('draws', 0) + response.get('black', 0)
                
                # Consider it opening theory if there are sufficient games
                return total_games >= 10  # Threshold for considering it opening theory
                
            return False
            
        except Exception as e:
            logging.error(f"Error checking opening move: {e}")
            return False
    
    def get_opening_moves_count(self, moves: List[str]) -> int:
        """
        Count how many moves from the beginning are in opening theory.
        
        This method keeps checking move sequences until it finds a position
        that's not in the database, indicating the end of opening theory.
        
        Args:
            moves: List of moves in UCI notation from the game
            
        Returns:
            Number of moves that are in opening theory
        """
        opening_moves = 0
        
        try:
            # Check moves incrementally until we find one not in database
            # In lite mode, check fewer moves and use faster API calls
            max_moves = 20 if Config.LITE_MODE else 40
            api_delay = 0.05 if Config.LITE_MODE else 0.1
            
            # Threshold for considering a position as still within opening theory
            game_threshold = 10  # Align with is_opening_move
            
            for i in range(1, min(len(moves) + 1, max_moves)):
                move_sequence = moves[:i]
                moves_string = ','.join(move_sequence)
                
                # Query the Lichess database directly
                response = self._query_opening_api(moves_string, use_masters=False)
                
                if response:
                    total_games = response.get('white', 0) + response.get('draws', 0) + response.get('black', 0)
                    
                    # If we have sufficient games, this is still opening theory
                    if total_games >= game_threshold:
                        opening_moves = i
                        logging.debug(f"Move {i} ({move_sequence[-1]}) still in opening theory: {total_games} games")
                    else:
                        # Not enough games, opening theory ends here
                        logging.debug(f"Move {i} ({move_sequence[-1]}) not in opening theory: {total_games} games")
                        break
                else:
                    # No response from API, assume opening theory ends here
                    logging.debug(f"Move {i} ({move_sequence[-1]}) not found in database")
                    break
                    
                # Add small delay to be respectful to API (shorter in lite mode)
                time.sleep(api_delay)
                
        except Exception as e:
            logging.error(f"Error counting opening moves: {e}")
            
        logging.info(f"Opening theory ends after {opening_moves} moves")
        return opening_moves
    
    def get_opening_statistics(self, moves: List[str]) -> Dict:
        """
        Get detailed opening statistics for a move sequence.
        
        Args:
            moves: List of moves in UCI notation
            
        Returns:
            Dictionary with opening statistics
        """
        try:
            moves_string = ','.join(moves)
            
            # Query the Lichess database directly
            response = self._query_opening_api(moves_string, use_masters=False)
            
            if response:
                total_games = response.get('white', 0) + response.get('draws', 0) + response.get('black', 0)
                
                opening_info = {
                    'total_games': total_games,
                    'white_wins': response.get('white', 0),
                    'black_wins': response.get('black', 0),
                    'draws': response.get('draws', 0),
                    'is_opening': total_games >= 10,
                    'top_continuations': []
                }
                
                # Get top continuations
                if 'moves' in response:
                    for move_info in response['moves'][:5]:  # Top 5 continuations
                        move_games = move_info.get('white', 0) + move_info.get('draws', 0) + move_info.get('black', 0)
                        opening_info['top_continuations'].append({
                            'move': move_info.get('uci', ''),
                            'san': move_info.get('san', ''),
                            'games': move_games,
                            'white_wins': move_info.get('white', 0),
                            'black_wins': move_info.get('black', 0),
                            'draws': move_info.get('draws', 0)
                        })
                
                return opening_info
                
        except Exception as e:
            logging.error(f"Error getting opening statistics: {e}")
            
        return {
            'total_games': 0,
            'white_wins': 0,
            'black_wins': 0,
            'draws': 0,
            'is_opening': False,
            'top_continuations': []
        }
    
    def _convert_uci_to_pgn(self, uci_moves: List[str], start_fen: str = None) -> str:
        """
        Convert UCI move notation to PGN format for API query.
        
        Args:
            uci_moves: List of moves in UCI notation
            start_fen: Optional starting FEN position
            
        Returns:
            Comma-separated string of moves for API query
        """
        try:
            # Start with initial position or provided FEN
            if start_fen:
                board = chess.Board(start_fen)
            else:
                board = chess.Board()
            
            pgn_moves = []
            
            for uci_move in uci_moves:
                # Convert UCI to move object
                move = chess.Move.from_uci(uci_move)
                
                # Check if move is legal
                if move not in board.legal_moves:
                    logging.warning(f"Illegal move encountered: {uci_move}")
                    break
                
                # Convert to SAN (Standard Algebraic Notation)
                san_move = board.san(move)
                pgn_moves.append(san_move)
                
                # Make the move
                board.push(move)
            
            return ','.join(pgn_moves)
            
        except Exception as e:
            logging.error(f"Error converting UCI to PGN: {e}")
            return ''
    
    def _query_opening_api(self, moves: str, use_masters: bool = True) -> Optional[Dict]:
        """
        Query the Lichess Opening Explorer API.
        
        Args:
            moves: Comma-separated string of moves in UCI notation
            use_masters: Whether to use masters database or lichess games
            
        Returns:
            API response as dictionary, or None if error
        """
        try:
            # Choose endpoint based on database preference
            endpoint = f"{self.base_url}/masters" if use_masters else f"{self.base_url}/lichess"
            
            params = {
                'variant': 'chess',
                'play': moves  # Use 'play' parameter for moves in UCI notation
            }
            
            # Add additional filters for lichess database
            if not use_masters:
                params.update({
                    'speeds': 'blitz,rapid,classical',
                    'modes': 'rated'
                })
            
            response = self.session.get(
                endpoint,
                params=params,
                timeout=Config.API_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited, wait and retry once
                logging.warning("Rate limited by API, waiting...")
                time.sleep(2)
                
                response = self.session.get(
                    endpoint,
                    params=params,
                    timeout=Config.API_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.json()
                    
            logging.error(f"API request failed with status {response.status_code}")
            return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in API query: {e}")
            return None
    
    def analyze_opening_deviation(self, moves: List[str]) -> Dict:
        """
        Analyze where a game deviates from opening theory.
        
        Args:
            moves: List of moves in UCI notation from the game
            
        Returns:
            Dictionary with opening deviation analysis
        """
        try:
            last_opening_move = self.get_opening_moves_count(moves)
            
            result = {
                'opening_moves_count': last_opening_move,
                'total_moves': len(moves),
                'deviation_move': last_opening_move + 1 if last_opening_move < len(moves) else None,
                'opening_percentage': (last_opening_move / len(moves)) * 100 if moves else 0,
                'is_mostly_opening': last_opening_move >= min(15, len(moves) // 2)
            }
            
            # Get opening name if available
            if last_opening_move > 0:
                opening_stats = self.get_opening_statistics(moves[:last_opening_move])
                result['opening_statistics'] = opening_stats
            
            # Analyze the deviation move
            if result['deviation_move'] and result['deviation_move'] <= len(moves):
                deviation_move = moves[result['deviation_move'] - 1]
                
                # Check what the popular continuations were
                if last_opening_move > 0:
                    opening_stats = self.get_opening_statistics(moves[:last_opening_move])
                    result['alternative_moves'] = opening_stats.get('top_continuations', [])
                
                result['actual_deviation_move'] = deviation_move
            
            return result
            
        except Exception as e:
            logging.error(f"Error analyzing opening deviation: {e}")
            return {
                'opening_moves_count': 0,
                'total_moves': len(moves),
                'deviation_move': None,
                'opening_percentage': 0,
                'is_mostly_opening': False
            }
    
    def get_opening_name(self, moves: List[str]) -> Optional[str]:
        """
        Attempt to get the opening name for a move sequence.
        
        Args:
            moves: List of moves in UCI notation
            
        Returns:
            Opening name if found, None otherwise
        """
        try:
            # This is a simplified approach - in a full implementation,
            # you might want to use a separate opening book database
            opening_moves = self.get_opening_moves_count(moves)
            
            if opening_moves >= 3:
                # Query for opening statistics to get more info
                stats = self.get_opening_statistics(moves[:opening_moves])
                
                # The Lichess API doesn't directly provide opening names,
                # but we can infer some common openings
                return self._infer_opening_name(moves[:opening_moves])
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting opening name: {e}")
            return None
    
    def _infer_opening_name(self, moves: List[str]) -> Optional[str]:
        """
        Infer opening name from move sequence.
        
        Args:
            moves: List of moves in UCI notation
            
        Returns:
            Inferred opening name
        """
        # This is a simplified mapping - a full implementation would use
        # a comprehensive opening database
        if len(moves) < 2:
            return None
            
        first_two = moves[:2]
        
        # Common opening patterns
        opening_patterns = {
            ('e2e4', 'e7e5'): 'King\'s Pawn Opening',
            ('e2e4', 'c7c5'): 'Sicilian Defense',
            ('e2e4', 'e7e6'): 'French Defense',
            ('e2e4', 'c7c6'): 'Caro-Kann Defense',
            ('d2d4', 'd7d5'): 'Queen\'s Pawn Opening',
            ('d2d4', 'g8f6'): 'Indian Defense',
            ('g1f3', 'd7d5'): 'Reti Opening',
            ('g1f3', 'g8f6'): 'King\'s Indian Attack',
            ('c2c4', 'e7e5'): 'English Opening',
        }
        
        key = tuple(first_two)
        return opening_patterns.get(key, 'Unknown Opening')
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close() 