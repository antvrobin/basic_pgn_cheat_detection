"""
Flask Web Application for Chess Cheat Detection System

This application provides a web interface for uploading PGN files and
displaying comprehensive chess analysis results including cheat detection metrics.
"""

import os
import logging
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import json
import traceback
from datetime import datetime
import numpy as np
import chess
import chess.engine
import chess.pgn
import io
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pgn', 'txt'}

def get_stockfish_path():
    """Get Stockfish executable path based on platform."""
    possible_paths = [
        Path("stockfish.exe"),
        Path("stockfish"),
        Path.home() / "OneDrive" / "Documents" / "stockfish" / "stockfish.exe",
        Path.home() / "OneDrive" / "Documents" / "stockfish-windows-x86-64-avx2" / "stockfish" / "stockfish.exe",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    raise FileNotFoundError("Stockfish not found. Please install Stockfish.")

def convert_numpy_types(obj):
    """Convert NumPy types to Python native types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_pgn(pgn_content):
    """Analyze a PGN file using the enhanced EngineAnalyzer."""
    try:
        # Import the EngineAnalyzer here to avoid circular imports
        from analyzer.engine_analyzer import EngineAnalyzer
        
        # Create analyzer instance and analyze the game
        analyzer = EngineAnalyzer()
        analysis_result = analyzer.analyze_game(pgn_content)
        
        if not analysis_result.get('success', False):
            return {
                'success': False,
                'error': analysis_result.get('error', 'Analysis failed')
            }
        
        # Process the analysis result to match expected frontend format
        game_info = analysis_result.get('game_info', {})
        move_analyses = analysis_result.get('move_analyses', [])
        metrics = analysis_result.get('metrics', {})
        
        # Separate moves by player for frontend compatibility
        white_moves = []
        black_moves = []
        
        for move_analysis in move_analyses:
            # Extract move data with enhanced complexity information
            move_data = {
                'move_number': move_analysis.get('move_number', 0),
                'player': move_analysis.get('player', 'white'),
                'move': move_analysis.get('move', ''),
                'move_time': move_analysis.get('move_time', 0),
                'clock_time': move_analysis.get('clock_time', 0),
                'centipawn_loss': move_analysis.get('engine_analysis', {}).get('centipawn_loss', 0),
                'move_rank': move_analysis.get('engine_analysis', {}).get('move_rank', 0),
                'evaluation': move_analysis.get('engine_analysis', {}).get('evaluation', 0),
                'legal_moves_count': move_analysis.get('legal_moves_count', 0),
                'complexity': move_analysis.get('complexity', {}),  # This now contains PCS data
                'engine_analysis': move_analysis.get('engine_analysis', {}),
                'opening_analysis': move_analysis.get('opening_analysis', {})
            }
            
            if move_data['player'] == 'white':
                white_moves.append(move_data)
            else:
                black_moves.append(move_data)
        
        # Extract player metrics
        def flatten_player_metrics(raw_metrics):
            """Flatten nested metrics (accuracy_metrics, engine_matching, temporal_metrics)"""
            if not raw_metrics:
                return {}
            accuracy = raw_metrics.get('accuracy_metrics', {})
            engine_match = raw_metrics.get('engine_matching', {})
            temporal = raw_metrics.get('temporal_metrics', {})
            flattened = {
                # Accuracy metrics
                'accuracy_score': accuracy.get('accuracy_score', 0),
                'avg_centipawn_loss': accuracy.get('avg_centipawn_loss', 0),
                'std_centipawn_loss': accuracy.get('std_centipawn_loss', 0),
                'blunder_count': accuracy.get('blunder_count', 0),
                'mistake_count': accuracy.get('mistake_count', 0),
                'total_moves': accuracy.get('total_moves', 0),
                # Engine matching (rename pv1_percentage -> best_move_rate)
                'best_move_rate': engine_match.get('pv1_percentage', 0),
                'pv1_count': engine_match.get('pv1_count', 0),
                'pv2_count': engine_match.get('pv2_count', 0),
                'pv3_count': engine_match.get('pv3_count', 0),
                'top2_match_rate': engine_match.get('pv2_percentage', 0),
                'top3_match_rate': engine_match.get('pv3_percentage', 0),
                # Alias for backward compatibility with frontend
                'top3_move_rate': engine_match.get('pv3_percentage', 0),
                # Temporal metrics (include mean move time, etc.)
                'move_time_mean': temporal.get('move_time_mean', 0),
                'avg_move_time': temporal.get('move_time_mean', 0),
                'move_time_std': temporal.get('move_time_std', 0),
                'move_time_cv': temporal.get('move_time_cv', 0),
                'total_moves_with_time': temporal.get('total_moves_with_time', 0),
                'time_consistency_score': temporal.get('time_consistency_score', 0),
                # Opening theory
                'opening_move_count': raw_metrics.get('opening_metrics_player', {}).get('opening_move_count', 0)
            }
            return flattened

        white_metrics = flatten_player_metrics(metrics.get('white_player', {}))
        black_metrics = flatten_player_metrics(metrics.get('black_player', {}))
        
        return {
            'success': True,
            'game_info': game_info,
            'white_player': {
                'name': game_info.get('white', 'Unknown'),
                'moves': white_moves,
                'metrics': white_metrics
            },
            'black_player': {
                'name': game_info.get('black', 'Unknown'),
                'moves': black_moves,
                'metrics': black_metrics
            },
            'metrics': metrics,  # Include overall game metrics
            'analysis_settings': analysis_result.get('analysis_settings', {})
        }
        
    except Exception as e:
        logger.error(f"Error analyzing PGN: {e}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    """Main page with file upload form."""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page with methodology and technical details."""
    return render_template('about.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PGN file upload and analysis."""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a PGN file.'}), 400
        
        # Read PGN content
        pgn_content = file.read().decode('utf-8')
        
        # Analyze the game
        logger.info("Starting game analysis...")
        analysis_result = analyze_pgn(pgn_content)
        
        if not analysis_result['success']:
            return jsonify({'error': analysis_result['error']}), 500
        
        logger.info("Analysis completed successfully")
        
        # Convert NumPy types to JSON-serializable types
        clean_result = convert_numpy_types(analysis_result)
        
        return jsonify({
            'success': True,
            'analysis': clean_result,
            'filename': file.filename
        })
        
    except Exception as e:
        logger.error(f"Error in file upload/analysis: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'error': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors."""
    return '', 204

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000) 