import os
import platform
from pathlib import Path

class Config:
    # Stockfish configuration (OPTIMIZED FOR SPEED)
    @staticmethod
    def get_stockfish_path():
        """Get Stockfish executable path based on platform."""
        # Try common installation paths
        possible_paths = [
            # Current directory
            Path("stockfish.exe") if platform.system() == "Windows" else Path("stockfish"),
            # User's Documents folder
            Path.home() / "Onedrive" /"Documents" / "stockfish" / "stockfish.exe",
            Path.home() / "Onedrive" / "Documents" / "stockfish-windows-x86-64-avx2" / "stockfish" / "stockfish.exe",
            Path.home() / "Onedrive" / "Documents" / "stockfish-windows-x86-64-avx2" / "stockfish",
            # System PATH
            Path("stockfish"),
        ]
        
        for path in possible_paths:
            if path.exists() or path.with_suffix('.exe').exists():
                return str(path)
        
        raise FileNotFoundError(
            "Stockfish not found. Please install Stockfish and ensure it's in your PATH "
            "or in one of the following locations:\n" + 
            "\n".join(str(p) for p in possible_paths)
        )
    
    STOCKFISH_PATH = get_stockfish_path.__func__()  # Get path at startup
    DEFAULT_DEPTH = 8  # Reduced from 15 for much faster analysis
    COMPLEXITY_DEPTHS = [5, 8, 10]  # Reduced from [10, 15, 20] for speed
    LITE_MODE = True  # Enable fast analysis mode
    
    # Lichess API configuration
    API_TIMEOUT = 10
    
    # Analysis settings
    MAX_OPENING_MOVES = 15  # Maximum moves to consider as opening
    MIN_GAME_LENGTH = 10    # Minimum game length for analysis
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True) 