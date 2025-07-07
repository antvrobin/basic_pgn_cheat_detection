"""
PGN Parser for extracting game data and move times from Lichess PGN files.
"""

import chess
import chess.pgn
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import io

class PGNParser:
    """
    Parses PGN files and extracts game information, moves, and timing data.
    Specifically designed to handle Lichess PGN format with clock annotations.
    """
    
    def __init__(self):
        self.game = None
        self.moves_data = []
        self.headers = {}
        
    def parse_pgn_file(self, pgn_content: str) -> Dict:
        """
        Parse PGN content and extract all relevant game information.
        
        Args:
            pgn_content: String content of the PGN file
            
        Returns:
            Dictionary containing parsed game data
        """
        try:
            pgn_io = io.StringIO(pgn_content)
            self.game = chess.pgn.read_game(pgn_io)
            
            if not self.game:
                raise ValueError("Invalid PGN format or empty file")
            
            # Extract headers
            self.headers = dict(self.game.headers)
            
            # Extract moves and timing data
            self.moves_data = self._extract_moves_and_times()
            
            return {
                'headers': self.headers,
                'moves': self.moves_data,
                'total_moves': len(self.moves_data),
                'game_result': self.headers.get('Result', '*'),
                'time_control': self.headers.get('TimeControl', 'Unknown'),
                'players': {
                    'white': self.headers.get('White', 'Unknown'),
                    'black': self.headers.get('Black', 'Unknown')
                },
                'ratings': {
                    'white': self._safe_int(self.headers.get('WhiteElo', 0)),
                    'black': self._safe_int(self.headers.get('BlackElo', 0))
                },
                'date': self.headers.get('Date', 'Unknown'),
                'site': self.headers.get('Site', 'Unknown')
            }
            
        except Exception as e:
            raise Exception(f"Error parsing PGN: {str(e)}")
    
    def _extract_moves_and_times(self) -> List[Dict]:
        """
        Extract moves and timing information from the game.
        
        Returns:
            List of move dictionaries with timing data
        """
        moves_data = []
        board = self.game.board()
        
        for move_num, node in enumerate(self.game.mainline(), 1):
            move = node.move
            
            # Get move in algebraic notation
            san_move = board.san(move)
            
            # Extract clock time from comment
            clock_time = self._extract_clock_time(node.comment)
            
            # Calculate move time (time spent on this move)
            move_time = self._calculate_move_time(moves_data, clock_time, move_num)
            
            # Get position info before the move
            fen_before = board.fen()
            legal_moves = len(list(board.legal_moves))
            
            # Make the move
            board.push(move)
            
            # Get position after the move
            fen_after = board.fen()
            
            move_data = {
                'move_number': move_num,
                'player': 'white' if move_num % 2 == 1 else 'black',
                'move': san_move,
                'uci_move': move.uci(),
                'fen_before': fen_before,
                'fen_after': fen_after,
                'clock_time': clock_time,
                'move_time': move_time,
                'legal_moves_count': legal_moves,
                'comment': node.comment.strip()
            }
            
            moves_data.append(move_data)
        
        return moves_data
    
    def _extract_clock_time(self, comment: str) -> Optional[float]:
        """
        Extract clock time from move comment.
        
        Args:
            comment: The move comment that may contain clock time
            
        Returns:
            Clock time in seconds, or None if not found
        """
        if not comment:
            return None
            
        # Look for clock time in format [%clk 0:01:23.4]
        clk_match = re.search(r'\[%clk\s+(\d+):(\d+):(\d+)(?:\.(\d+))?\]', comment)
        if clk_match:
            hours = int(clk_match.group(1))
            minutes = int(clk_match.group(2))
            seconds = int(clk_match.group(3))
            decimal = float(f"0.{clk_match.group(4)}") if clk_match.group(4) else 0.0
            
            return hours * 3600 + minutes * 60 + seconds + decimal
        
        # Alternative format [%clk 1:23.4]
        clk_match = re.search(r'\[%clk\s+(\d+):(\d+)(?:\.(\d+))?\]', comment)
        if clk_match:
            minutes = int(clk_match.group(1))
            seconds = int(clk_match.group(2))
            decimal = float(f"0.{clk_match.group(3)}") if clk_match.group(3) else 0.0
            
            return minutes * 60 + seconds + decimal
        
        return None
    
    def _calculate_move_time(self, moves_data: List[Dict], current_clock: Optional[float], move_num: int) -> Optional[float]:
        """
        Calculate the time spent on the current move.
        
        Args:
            moves_data: Previously processed moves
            current_clock: Current clock time
            move_num: Current move number
            
        Returns:
            Time spent on this move in seconds
        """
        if current_clock is None:
            return None
            
        # For the first move, we can't calculate move time
        if move_num <= 2:
            return None
            
        # Find the previous move by the same player
        same_player_moves = [m for m in moves_data if m['player'] == ('white' if move_num % 2 == 1 else 'black')]
        
        if not same_player_moves:
            return None
            
        last_move = same_player_moves[-1]
        if last_move['clock_time'] is None:
            return None
            
        # Move time = previous clock time - current clock time
        move_time = last_move['clock_time'] - current_clock
        
        # Ensure move time is positive (sometimes there are inconsistencies)
        return max(0, move_time) if move_time is not None else None
    
    def _safe_int(self, value: str) -> int:
        """
        Safely convert string to integer.
        
        Args:
            value: String value to convert
            
        Returns:
            Integer value or 0 if conversion fails
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    def get_game_summary(self) -> Dict:
        """
        Get a summary of the parsed game.
        
        Returns:
            Dictionary with game summary statistics
        """
        if not self.moves_data:
            return {}
            
        # Calculate timing statistics
        move_times = [m['move_time'] for m in self.moves_data if m['move_time'] is not None]
        
        white_moves = [m for m in self.moves_data if m['player'] == 'white']
        black_moves = [m for m in self.moves_data if m['player'] == 'black']
        
        return {
            'total_moves': len(self.moves_data),
            'white_moves': len(white_moves),
            'black_moves': len(black_moves),
            'avg_move_time': sum(move_times) / len(move_times) if move_times else 0,
            'min_move_time': min(move_times) if move_times else 0,
            'max_move_time': max(move_times) if move_times else 0,
            'moves_with_timing': len(move_times),
            'game_duration': self._calculate_game_duration()
        }
    
    def _calculate_game_duration(self) -> Optional[float]:
        """
        Calculate total game duration based on clock times.
        
        Returns:
            Game duration in seconds
        """
        if not self.moves_data:
            return None
            
        # Find initial time from time control
        time_control = self.headers.get('TimeControl', '')
        initial_time = self._parse_time_control(time_control)
        
        if initial_time is None:
            return None
            
        # Get final clock times
        final_white_clock = None
        final_black_clock = None
        
        for move in reversed(self.moves_data):
            if move['player'] == 'white' and final_white_clock is None:
                final_white_clock = move['clock_time']
            elif move['player'] == 'black' and final_black_clock is None:
                final_black_clock = move['clock_time']
            
            if final_white_clock is not None and final_black_clock is not None:
                break
        
        if final_white_clock is None or final_black_clock is None:
            return None
            
        # Calculate time used by each player
        white_time_used = initial_time - final_white_clock
        black_time_used = initial_time - final_black_clock
        
        return white_time_used + black_time_used
    
    def _parse_time_control(self, time_control: str) -> Optional[float]:
        """
        Parse time control string to get initial time.
        
        Args:
            time_control: Time control string from PGN headers
            
        Returns:
            Initial time in seconds
        """
        if not time_control:
            return None
            
        # Format: "600+0" (10 minutes + 0 increment)
        match = re.match(r'(\d+)\+(\d+)', time_control)
        if match:
            return float(match.group(1))
            
        return None 