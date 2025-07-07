// Chess Cheat Detection Pro - Complete Application
class ChessAnalysisApp {
    constructor() {
        this.currentAnalysis = null;
        this.selectedPlayer = 'white';
        this.charts = {};
        this.theme = 'dark';
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeTheme();
        
        // Wait for Chart.js to be fully loaded
        if (typeof Chart !== 'undefined') {
            console.log('Chart.js loaded successfully');
            this.setupChartDefaults();
        } else {
            console.error('Chart.js not loaded');
        }
    }

    setupEventListeners() {
        // Upload form
        const uploadForm = document.getElementById('uploadForm');
        uploadForm.addEventListener('submit', (e) => this.handleFileUpload(e));

        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        themeToggle.addEventListener('click', () => this.toggleTheme());

        // Tab switching
        document.addEventListener('click', (e) => {
            if (e.target.closest('.tab-btn')) {
                this.switchTab(e.target.closest('.tab-btn'));
            }
        });

        // Player selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.player-btn')) {
                this.selectPlayer(e.target.closest('.player-btn'));
            }
        });

        // Modal close
        document.addEventListener('click', (e) => {
            if (e.target.closest('.modal-close') || e.target.classList.contains('modal')) {
                this.hideModal();
            }
        });
    }

    setupChartDefaults() {
        if (typeof Chart === 'undefined') return;

        Chart.defaults.font.family = 'Inter, sans-serif';
        Chart.defaults.color = this.theme === 'dark' ? '#f0f6fc' : '#24292f';
        Chart.defaults.borderColor = this.theme === 'dark' ? '#30363d' : '#d0d7de';
        Chart.defaults.backgroundColor = this.theme === 'dark' ? 'rgba(88, 166, 255, 0.1)' : 'rgba(9, 105, 218, 0.1)';
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.setTheme(savedTheme);
    }

    toggleTheme() {
        const newTheme = this.theme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        const themeToggle = document.getElementById('themeToggle');
        themeToggle.innerHTML = theme === 'dark' 
            ? '<i class="fas fa-sun"></i>' 
            : '<i class="fas fa-moon"></i>';
        
        this.setupChartDefaults();
        this.refreshCharts();
    }

    async handleFileUpload(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showError('Please select a PGN file');
            return;
        }

        this.showLoading();
        
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            this.hideLoading();
            
            if (data.success) {
                this.currentAnalysis = data.analysis;
                this.displayResults(data.analysis);
            } else {
                this.showError(data.error || 'Analysis failed');
            }
        } catch (error) {
            this.hideLoading();
            this.showError('Network error: ' + error.message);
        }
    }

    showLoading() {
        document.getElementById('loadingSection').classList.remove('hidden');
        document.getElementById('resultsSection').classList.add('hidden');
        
        // Animate progress bar
        const progressFill = document.querySelector('.progress-fill');
        let width = 0;
        const interval = setInterval(() => {
            width += Math.random() * 10;
            if (width > 90) width = 90;
            progressFill.style.width = width + '%';
        }, 200);
        
        this.progressInterval = interval;
    }

    hideLoading() {
        document.getElementById('loadingSection').classList.add('hidden');
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
    }

    showError(message) {
        const modal = document.getElementById('errorModal');
        const messageEl = document.getElementById('errorMessage');
        messageEl.textContent = message;
        modal.classList.remove('hidden');
    }

    hideModal() {
        document.getElementById('errorModal').classList.add('hidden');
    }

    displayResults(analysis) {
        this.displayGameInfo(analysis.game_info);
        this.displayPlayerSelection(analysis);
        this.displayExecutiveSummary(analysis);
        this.createCharts(analysis);
        this.displayDetailedAnalysis(analysis);
        this.displayMoveAnalysis(analysis);
        
        document.getElementById('resultsSection').classList.remove('hidden');
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
    }

    displayGameInfo(gameInfo) {
        const html = `
            <div class="section-header">
                <h2><i class="fas fa-chess"></i> Game Information</h2>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">${gameInfo.white}</div>
                    <div class="metric-label">White Player</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${gameInfo.black}</div>
                    <div class="metric-label">Black Player</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${gameInfo.result}</div>
                    <div class="metric-label">Result</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${gameInfo.event}</div>
                    <div class="metric-label">Event</div>
                </div>
            </div>
        `;
        document.getElementById('gameInfo').innerHTML = html;
    }

    displayPlayerSelection(analysis) {
        const html = `
            <div class="section-header">
                <h2><i class="fas fa-users"></i> Select Player</h2>
                <p>Choose which player to analyze for potential engine assistance</p>
            </div>
            <div class="player-buttons">
                <button class="player-btn active" data-player="white">
                    <i class="fas fa-chess-king"></i>
                    ${analysis.white_player.name}
                </button>
                <button class="player-btn" data-player="black">
                    <i class="fas fa-chess-king"></i>
                    ${analysis.black_player.name}
                </button>
            </div>
        `;
        document.getElementById('playerSelection').innerHTML = html;
    }

    selectPlayer(button) {
        document.querySelectorAll('.player-btn').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        this.selectedPlayer = button.dataset.player;
        
        this.displayExecutiveSummary(this.currentAnalysis);
        this.createCharts(this.currentAnalysis);
        this.displayDetailedAnalysis(this.currentAnalysis);
        this.displayMoveAnalysis(this.currentAnalysis);
    }

    displayExecutiveSummary(analysis) {
        const playerData = analysis[this.selectedPlayer + '_player'];
        const metrics = playerData.metrics || {};
        const riskAssessment = this.calculateRiskAssessment(metrics);

        const html = `
            <div class="summary-header">
                <h2><i class="fas fa-clipboard-check"></i> Executive Summary - ${playerData.name}</h2>
                <div class="risk-badge risk-${riskAssessment.level.toLowerCase().replace(' ', '-')}">
                    ${riskAssessment.level} Risk
                </div>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">${(metrics.accuracy_score || 0).toFixed(1)}%</div>
                    <div class="metric-label">Accuracy Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${(metrics.best_move_rate || 0).toFixed(1)}%</div>
                    <div class="metric-label">Engine Match Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${(metrics.avg_centipawn_loss || 0).toFixed(0)}</div>
                    <div class="metric-label">Avg CP Loss</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.total_moves || 0}</div>
                    <div class="metric-label">Total Moves</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.opening_move_count || 0}</div>
                    <div class="metric-label">Opening Moves</div>
                </div>
            </div>
            
            <div class="insights-grid">
                <div class="insight-item">
                    <h5>🎯 Performance Analysis</h5>
                    <p>${this.getPerformanceInsight(metrics)}</p>
                </div>
                <div class="insight-item">
                    <h5>🤖 Engine Correlation</h5>
                    <p>${this.getEngineInsight(metrics)}</p>
                </div>
                <div class="insight-item">
                    <h5>⚠️ Risk Factors</h5>
                    <p>${riskAssessment.explanation}</p>
                </div>
            </div>
        `;
        document.getElementById('executiveSummary').innerHTML = html;
    }

    calculateRiskAssessment(metrics) {
        let riskScore = 0;
        let factors = [];

        const bestMoveRate = metrics.best_move_rate || 0;
        const accuracyScore = metrics.accuracy_score || 0;
        const avgCpLoss = metrics.avg_centipawn_loss || 0;
        const totalMoves = metrics.total_moves || 0;
        const blunderCount = metrics.blunder_count || 0;

        // Engine matching (40% weight)
        if (bestMoveRate >= 80) {
            riskScore += 40;
            factors.push('Extremely high engine matching (80%+)');
        } else if (bestMoveRate >= 60) {
            riskScore += 25;
            factors.push('High engine matching (60-80%)');
        } else if (bestMoveRate >= 40) {
            riskScore += 10;
            factors.push('Moderate engine matching (40-60%)');
        }

        // Accuracy (30% weight)
        if (accuracyScore >= 95) {
            riskScore += 30;
            factors.push('Exceptionally high accuracy (95%+)');
        } else if (accuracyScore >= 90) {
            riskScore += 20;
            factors.push('Very high accuracy (90-95%)');
        } else if (accuracyScore >= 85) {
            riskScore += 10;
            factors.push('High accuracy (85-90%)');
        }

        // Low error rate (20% weight)
        if (avgCpLoss <= 15 && totalMoves > 20) {
            riskScore += 20;
            factors.push('Very low centipawn loss (≤15)');
        } else if (avgCpLoss <= 25) {
            riskScore += 10;
            factors.push('Low centipawn loss (≤25)');
        }

        // Few blunders (10% weight)
        if (blunderCount === 0 && totalMoves > 20) {
            riskScore += 10;
            factors.push('No blunders in long game');
        }

        let level, explanation;
        if (riskScore >= 80) {
            level = 'VERY HIGH';
            explanation = 'Multiple strong indicators of engine assistance detected. ' + factors.join(', ') + '.';
        } else if (riskScore >= 60) {
            level = 'HIGH';
            explanation = 'Several concerning patterns identified. ' + factors.join(', ') + '.';
        } else if (riskScore >= 40) {
            level = 'MODERATE';
            explanation = 'Some elevated metrics but could indicate strong human play. ' + factors.join(', ') + '.';
        } else if (riskScore >= 20) {
            level = 'LOW';
            explanation = 'Metrics within normal ranges for strong human play.';
        } else {
            level = 'VERY LOW';
            explanation = 'Performance consistent with typical human play patterns.';
        }

        return { level, explanation, score: riskScore };
    }

    getPerformanceInsight(metrics) {
        const acc = metrics.accuracy_score || 0;
        if (acc >= 95) return `Exceptional accuracy of ${acc.toFixed(1)}% is extremely rare in human play and warrants investigation.`;
        if (acc >= 90) return `Very high accuracy of ${acc.toFixed(1)}% suggests either very strong play or potential assistance.`;
        if (acc >= 80) return `Good accuracy of ${acc.toFixed(1)}% indicates solid play but within human ranges.`;
        return `Accuracy of ${acc.toFixed(1)}% is typical for the playing level demonstrated.`;
    }

    getEngineInsight(metrics) {
        const rate = metrics.best_move_rate || 0;
        if (rate >= 80) return `${rate.toFixed(1)}% engine matching is extremely suspicious and indicates likely computer assistance.`;
        if (rate >= 60) return `${rate.toFixed(1)}% engine matching is very high and suggests possible computer help.`;
        if (rate >= 40) return `${rate.toFixed(1)}% engine matching shows strong play but could be natural talent.`;
        return `${rate.toFixed(1)}% engine matching is within normal human ranges.`;
    }

    createCharts(analysis) {
        const playerMoves = this.getPlayerMoves(analysis);
        
        this.createAccuracyChart(playerMoves);
        this.createComplexityChart(playerMoves);
        this.createTimingChart(playerMoves);
        this.createEngineChart(playerMoves);
    }

    getPlayerMoves(analysis) {
        const playerData = analysis[this.selectedPlayer + '_player'];
        return playerData ? playerData.moves || [] : [];
    }

    createAccuracyChart(moves) {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js not available');
            return;
        }

        const ctx = document.getElementById('accuracyChart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.accuracy) {
            this.charts.accuracy.destroy();
        }

        const data = moves.map((move, index) => ({
            x: index + 1,
            y: Math.max(0, 100 - ((move.centipawn_loss || 0) / 3.0)),
            move: move.move,
            moveNumber: move.move_number || (index + 1),
            cpLoss: move.centipawn_loss || 0,
            rank: move.move_rank
        }));

        const labels = data.map(d => d.x);
        const accuracyValues = data.map(d => d.y);

        const avgAccuracy = accuracyValues.reduce((sum, v) => sum + v, 0) / (accuracyValues.length || 1);

        this.charts.accuracy = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Move Accuracy',
                    data: accuracyValues,
                    borderColor: '#58a6ff',
                    backgroundColor: 'rgba(88, 166, 255, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.1,
                    pointBackgroundColor: data.map(point => {
                        const cpLoss = point.cpLoss || 0;
                        if (cpLoss >= 300) return '#f85149';
                        if (cpLoss >= 100) return '#d29922';
                        return '#2ea043';
                    })
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Accuracy Over Time',
                        font: { size: 18, weight: 'bold' }
                    },
                    tooltip: {
                        callbacks: {
                            title: (context) => {
                                const idx = context[0].dataIndex;
                                return `Move ${moves[idx]?.move_number || (idx + 1)}: ${moves[idx]?.move}`;
                            },
                            label: (context) => {
                                const idx = context.dataIndex;
                                const cpLoss = moves[idx]?.centipawn_loss || 0;
                                const rank = moves[idx]?.move_rank || 'N/A';
                                return [
                                    `Accuracy: ${context.parsed.y.toFixed(1)}%`,
                                    `CP Loss: ${cpLoss.toFixed(1)}`,
                                    `Rank: ${rank}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: { title: { display: true, text: 'Move Number' } },
                    y: { title: { display: true, text: 'Accuracy (%)' }, min: 0, max: 100 }
                }
            }
        });

        this.updateAccuracyInsights(data, avgAccuracy);
    }

    updateAccuracyInsights(data, avgAccuracy) {
        const blunders = data.filter(p => p.cpLoss >= 300).length;
        const mistakes = data.filter(p => p.cpLoss >= 100 && p.cpLoss < 300).length;
        const excellent = data.filter(p => p.cpLoss < 20).length;

        const html = `
            <h4><i class="fas fa-bullseye"></i> Accuracy Analysis</h4>
            <div class="insights-grid">
                <div class="insight-item">
                    <h5>Overall Performance</h5>
                    <p>Average accuracy: <strong>${avgAccuracy.toFixed(1)}%</strong><br>
                    Excellent moves (&lt;20 CP): <strong>${excellent}</strong><br>
                    Total moves analyzed: <strong>${data.length}</strong></p>
                </div>
                <div class="insight-item">
                    <h5>Error Analysis</h5>
                    <p>Blunders (300+ CP): <strong>${blunders}</strong><br>
                    Mistakes (100-299 CP): <strong>${mistakes}</strong><br>
                    Error rate: <strong>${((blunders + mistakes) / data.length * 100).toFixed(1)}%</strong></p>
                </div>
                <div class="insight-item">
                    <h5>Interpretation</h5>
                    <p>${this.getAccuracyInterpretation(avgAccuracy, blunders, data.length)}</p>
                </div>
            </div>
        `;
        document.getElementById('accuracyInsights').innerHTML = html;
    }

    getAccuracyInterpretation(avgAccuracy, blunders, totalMoves) {
        if (avgAccuracy >= 95) {
            return "🚨 Exceptionally high accuracy. This level of precision is extremely rare in human play and warrants investigation.";
        } else if (avgAccuracy >= 90) {
            return "⚠️ Very high accuracy. Could indicate either exceptional skill or potential computer assistance.";
        } else if (avgAccuracy >= 80) {
            return "✅ Good accuracy for strong human play. Performance within expected ranges for skilled players.";
        } else {
            return "📊 Average accuracy typical for the demonstrated playing level.";
        }
    }

    createComplexityChart(moves) {
        if (typeof Chart === 'undefined') return;

        const ctx = document.getElementById('complexityChart');
        if (!ctx) return;

        if (this.charts.complexity) {
            this.charts.complexity.destroy();
        }

        const data = moves.map((move, index) => {
            const complexity = move.complexity || {};
            const pcsScore = complexity.pcs_score || 0;
            const pcsCategory = complexity.pcs_category || 'trivial';
            const accuracy = Math.max(0, 100 - (move.centipawn_loss / 3.0));
            
            return {
                x: pcsScore,
                y: accuracy,
                move: move.move,
                moveNumber: move.move_number || (index + 1),
                sequentialIndex: index + 1,
                pcsCategory: pcsCategory,
                interpretation: complexity.interpretation || 'No complexity data',
                decisionDifficulty: complexity.decision_difficulty || 0
            };
        });

        // Enhanced color coding based on PCS categories
        const getCategoryColor = (category, alpha = 0.7) => {
            const colors = {
                'trivial': `rgba(46, 160, 67, ${alpha})`,      // Green
                'balanced': `rgba(121, 192, 255, ${alpha})`,   // Blue  
                'critical': `rgba(210, 153, 34, ${alpha})`,    // Orange
                'chaotic': `rgba(248, 81, 73, ${alpha})`       // Red
            };
            return colors[category] || `rgba(139, 148, 158, ${alpha})`;
        };

        this.charts.complexity = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'PCS vs Move Accuracy',
                    data: data,
                    backgroundColor: data.map(point => getCategoryColor(point.pcsCategory, 0.7)),
                    borderColor: data.map(point => getCategoryColor(point.pcsCategory, 1.0)),
                    borderWidth: 2,
                    pointRadius: data.map(point => {
                        // Larger points for more complex positions
                        switch(point.pcsCategory) {
                            case 'chaotic': return 12;
                            case 'critical': return 10;
                            case 'balanced': return 8;
                            default: return 6;
                        }
                    })
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Positional Complexity Score (PCS) vs Move Accuracy',
                        font: { size: 18, weight: 'bold' }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: (context) => `Move ${data[context[0].dataIndex]?.moveNumber}: ${data[context[0].dataIndex]?.move}`,
                            label: (context) => {
                                const point = data[context.dataIndex];
                                return [
                                    `PCS Score: ${point.x.toFixed(1)} cp (${point.pcsCategory})`,
                                    `Move Accuracy: ${point.y.toFixed(1)}%`,
                                    `Decision Difficulty: ${(point.decisionDifficulty * 100).toFixed(0)}%`,
                                    `${point.interpretation}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { 
                            display: true, 
                            text: 'Positional Complexity Score (Centipawns)'
                        },
                        min: 0,
                        max: Math.max(200, Math.max(...data.map(d => d.x)) * 1.1),
                        ticks: {
                            callback: function(value) {
                                if (value === 30) return '30 (Trivial)';
                                if (value === 80) return '80 (Balanced)';
                                if (value === 150) return '150 (Critical)';
                                return value;
                            }
                        }
                    },
                    y: {
                        title: { display: true, text: 'Move Accuracy (%)' },
                        min: 0,
                        max: 100
                    }
                }
            }
        });

        this.updateComplexityInsights(data);
    }

    updateComplexityInsights(data) {
        // Categorize moves by PCS category
        const categoryCounts = {
            trivial: data.filter(p => p.pcsCategory === 'trivial').length,
            balanced: data.filter(p => p.pcsCategory === 'balanced').length,
            critical: data.filter(p => p.pcsCategory === 'critical').length,
            chaotic: data.filter(p => p.pcsCategory === 'chaotic').length
        };

        const criticalAndChaotic = data.filter(p => p.pcsCategory === 'critical' || p.pcsCategory === 'chaotic');
        const criticalAccurate = criticalAndChaotic.filter(p => p.y > 80);
        const avgPCS = data.reduce((sum, p) => sum + p.x, 0) / data.length;
        const maxPCS = Math.max(...data.map(p => p.x));

        const html = `
            <h4><i class="fas fa-brain"></i> Enhanced Complexity Analysis (PCS)</h4>
            <div class="insights-grid">
                <div class="insight-item">
                    <h5>PCS Formula (Maia-Inspired)</h5>
                    <p><code>PCS = max(0, score₂ - score₁) + max(0, score₃ - score₁) / 2</code><br>
                    Average PCS: <strong>${avgPCS.toFixed(1)} cp</strong><br>
                    Maximum PCS: <strong>${maxPCS.toFixed(1)} cp</strong></p>
                </div>
                <div class="insight-item">
                    <h5>Complexity Distribution</h5>
                    <p>
                        Trivial (&lt;30cp): <strong>${categoryCounts.trivial}</strong> moves<br>
                        Balanced (30-80cp): <strong>${categoryCounts.balanced}</strong> moves<br>
                        Critical (80-150cp): <strong>${categoryCounts.critical}</strong> moves<br>
                        Chaotic (&gt;150cp): <strong>${categoryCounts.chaotic}</strong> moves
                    </p>
                </div>
                <div class="insight-item">
                    <h5>Performance in Critical Positions</h5>
                    <p>High accuracy in critical/chaotic positions: <strong>${criticalAccurate.length}</strong><br>
                    Success rate: <strong>${criticalAndChaotic.length > 0 ? (criticalAccurate.length / criticalAndChaotic.length * 100).toFixed(1) : 0}%</strong><br>
                    Critical+Chaotic %: <strong>${((criticalAndChaotic.length / data.length) * 100).toFixed(1)}%</strong></p>
                </div>
                <div class="insight-item">
                    <h5>Cheat Detection Pattern</h5>
                    <p>${this.getPCSInterpretation(criticalAndChaotic.length, criticalAccurate.length, data.length)}</p>
                </div>
            </div>
        `;
        document.getElementById('complexityInsights').innerHTML = html;
    }

    getPCSInterpretation(criticalCount, criticalAccurate, totalMoves) {
        if (criticalCount === 0) {
            return "✅ No critical/chaotic positions encountered. Normal game complexity.";
        }
        
        const criticalPercentage = (criticalCount / totalMoves) * 100;
        const accuracyRate = (criticalAccurate / criticalCount) * 100;
        
        let riskLevel = "LOW";
        let message = "✅ Normal human performance in critical positions.";
        
        if (criticalPercentage > 40 && accuracyRate > 85) {
            riskLevel = "CRITICAL";
            message = "🚨 CRITICAL: Consistently high accuracy in many critical positions suggests engine assistance.";
        } else if (criticalPercentage > 25 && accuracyRate > 80) {
            riskLevel = "HIGH";
            message = "⚠️ HIGH RISK: Excellent performance in critical positions. Investigate further.";
        } else if (accuracyRate > 75) {
            riskLevel = "MODERATE";
            message = "⚠️ MODERATE: Good performance in critical positions. Monitor for patterns.";
        }
        
        return `${message}<br><small>Risk Level: <strong>${riskLevel}</strong> | Critical Accuracy: ${accuracyRate.toFixed(1)}%</small>`;
    }

    getComplexityInterpretation(complexCount, complexAccurate) {
        if (complexCount === 0) {
            return "No highly complex positions encountered in this game.";
        }
        
        const rate = (complexAccurate / complexCount) * 100;
        if (rate >= 80) {
            return "🚨 Very high accuracy in complex positions is suspicious and may indicate engine assistance.";
        } else if (rate >= 60) {
            return "⚠️ Good performance in complex positions. Monitor for consistency across games.";
        } else {
            return "✅ Normal human performance in complex positions.";
        }
    }

    createTimingChart(moves) {
        if (typeof Chart === 'undefined') return;

        const ctx = document.getElementById('timingChart');
        if (!ctx) return;

        if (this.charts.timing) {
            this.charts.timing.destroy();
        }

        const timedMoves = moves.filter(move => move.move_time > 0);
        if (timedMoves.length === 0) {
            document.getElementById('timingInsights').innerHTML = `
                <h4><i class="fas fa-clock"></i> Timing Analysis</h4>
                <div class="insight-item">
                    <h5>No Timing Data</h5>
                    <p>This game does not contain move timing information. Upload a PGN with clock data for timing analysis.</p>
                </div>
            `;
            return;
        }

        const data = timedMoves.map((move, index) => {
            const complexity = move.complexity || {};
            const pcsScore = complexity.pcs_score || 0;
            const pcsCategory = complexity.pcs_category || 'trivial';
            
            return {
                x: index + 1,  // Sequential index for consistent x-axis
                y: move.move_time,
                move: move.move,
                moveNumber: move.move_number || (index + 1),
                pcsScore: pcsScore,
                pcsCategory: pcsCategory
            };
        });

        // Color based on PCS categories
        const getCategoryColor = (category, alpha = 0.7) => {
            const colors = {
                'trivial': `rgba(46, 160, 67, ${alpha})`,      // Green
                'balanced': `rgba(121, 192, 255, ${alpha})`,   // Blue  
                'critical': `rgba(210, 153, 34, ${alpha})`,    // Orange
                'chaotic': `rgba(248, 81, 73, ${alpha})`       // Red
            };
            return colors[category] || `rgba(139, 148, 158, ${alpha})`;
        };

        this.charts.timing = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Move Time (seconds)',
                    data: data,
                    backgroundColor: data.map(point => getCategoryColor(point.pcsCategory, 0.7)),
                    borderColor: data.map(point => getCategoryColor(point.pcsCategory, 1.0)),
                    pointRadius: data.map(point => {
                        switch(point.pcsCategory) {
                            case 'chaotic': return 10;
                            case 'critical': return 8;
                            case 'balanced': return 6;
                            default: return 5;
                        }
                    }),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Move Timing Patterns',
                        font: { size: 18, weight: 'bold' }
                    },
                    tooltip: {
                        callbacks: {
                            title: (context) => {
                                const idx = context[0].dataIndex;
                                return `Move ${data[idx]?.moveNumber}: ${data[idx]?.move}`;
                            },
                            label: (context) => {
                                const point = data[context.dataIndex];
                                return [
                                    `Time: ${point.y.toFixed(1)}s`,
                                    `PCS: ${point.pcsScore.toFixed(1)} cp (${point.pcsCategory})`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: { display: true, text: 'Move Number' },
                        ticks: { precision: 0 }
                    },
                    y: { title: { display: true, text: 'Time (seconds)' } }
                }
            }
        });

        this.updateTimingInsights(data);
    }

    updateTimingInsights(data) {
        const avgTime = data.reduce((sum, p) => sum + p.y, 0) / data.length;
        const consistency = this.calculateTimeConsistency(data);
        const correlation = this.calculateComplexityTimeCorrelation(data);

        const html = `
            <h4><i class="fas fa-clock"></i> Timing Analysis</h4>
            <div class="insights-grid">
                <div class="insight-item">
                    <h5>Timing Statistics</h5>
                    <p>Average time: <strong>${avgTime.toFixed(1)}s</strong><br>
                    Total timed moves: <strong>${data.length}</strong><br>
                    Time consistency: <strong>${consistency.toFixed(3)}</strong></p>
                </div>
                <div class="insight-item">
                    <h5>PCS-Time Correlation</h5>
                    <p>Time-PCS correlation: <strong>${correlation.toFixed(3)}</strong><br>
                    ${correlation > 0.3 ? 'Good correlation' : correlation > 0 ? 'Weak correlation' : 'Poor correlation'}<br>
                    <small>Higher PCS should correlate with longer thinking time</small></p>
                </div>
                <div class="insight-item">
                    <h5>Pattern Analysis</h5>
                    <p>${this.getTimingInterpretation(consistency, correlation)}</p>
                </div>
            </div>
        `;
        document.getElementById('timingInsights').innerHTML = html;
    }

    calculateTimeConsistency(data) {
        if (data.length < 2) return 0;
        const times = data.map(p => p.y);
        const mean = times.reduce((a, b) => a + b, 0) / times.length;
        const variance = times.reduce((sum, time) => sum + Math.pow(time - mean, 2), 0) / times.length;
        const stdDev = Math.sqrt(variance);
        return mean > 0 ? stdDev / mean : 0;
    }

    calculateComplexityTimeCorrelation(data) {
        if (data.length < 2) return 0;
        const pcsScores = data.map(p => p.pcsScore || 0);
        const times = data.map(p => p.y);
        
        const meanPCS = pcsScores.reduce((a, b) => a + b, 0) / pcsScores.length;
        const meanTime = times.reduce((a, b) => a + b, 0) / times.length;
        
        let numerator = 0, denomPCS = 0, denomTime = 0;
        
        for (let i = 0; i < data.length; i++) {
            const pcsDiff = pcsScores[i] - meanPCS;
            const timeDiff = times[i] - meanTime;
            numerator += pcsDiff * timeDiff;
            denomPCS += pcsDiff * pcsDiff;
            denomTime += timeDiff * timeDiff;
        }
        
        const denominator = Math.sqrt(denomPCS * denomTime);
        return denominator > 0 ? numerator / denominator : 0;
    }

    getTimingInterpretation(consistency, correlation) {
        if (consistency < 0.3 && correlation < 0.1) {
            return "🚨 Very consistent timing with poor PCS correlation suggests possible engine assistance.";
        } else if (consistency < 0.5 && correlation > 0.3) {
            return "✅ Consistent timing with good PCS correlation indicates natural human patterns.";
        } else if (correlation < 0.1) {
            return "⚠️ Poor correlation between thinking time and positional complexity may indicate external assistance.";
        } else {
            return "✅ Normal human timing patterns with appropriate PCS correlation.";
        }
    }

    createEngineChart(moves) {
        if (typeof Chart === 'undefined') return;

        const ctx = document.getElementById('engineChart');
        if (!ctx) return;

        if (this.charts.engine) {
            this.charts.engine.destroy();
        }

        const rankCounts = { 1: 0, 2: 0, 3: 0, '4-5': 0, '6+': 0 };
        moves.forEach(move => {
            const rank = move.move_rank;
            if (rank === 1) rankCounts[1]++;
            else if (rank === 2) rankCounts[2]++;
            else if (rank === 3) rankCounts[3]++;
            else if (rank >= 4 && rank <= 5) rankCounts['4-5']++;
            else rankCounts['6+']++;
        });

        this.charts.engine = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Best Move', '2nd Best', '3rd Best', '4th-5th', '6th+'],
                datasets: [{
                    data: [rankCounts[1], rankCounts[2], rankCounts[3], rankCounts['4-5'], rankCounts['6+']],
                    backgroundColor: ['#2ea043', '#79c0ff', '#d29922', '#f85149', '#8b949e'],
                    borderColor: '#0d1117',
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Engine Move Ranking Distribution',
                        font: { size: 18, weight: 'bold' }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} moves (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

        this.updateEngineInsights(rankCounts, moves.length);
    }

    updateEngineInsights(rankCounts, totalMoves) {
        const bestMoveRate = ((rankCounts[1] / totalMoves) * 100).toFixed(1);
        const top3Rate = (((rankCounts[1] + rankCounts[2] + rankCounts[3]) / totalMoves) * 100).toFixed(1);

        const html = `
            <h4><i class="fas fa-robot"></i> Engine Correlation</h4>
            <div class="insights-grid">
                <div class="insight-item">
                    <h5>Engine Matching Rates</h5>
                    <p>Best move rate: <strong>${bestMoveRate}%</strong><br>
                    Top-3 move rate: <strong>${top3Rate}%</strong><br>
                    Total moves analyzed: <strong>${totalMoves}</strong></p>
                </div>
                <div class="insight-item">
                    <h5>Distribution Analysis</h5>
                    <p>1st choice: <strong>${rankCounts[1]}</strong> moves<br>
                    2nd choice: <strong>${rankCounts[2]}</strong> moves<br>
                    3rd choice: <strong>${rankCounts[3]}</strong> moves</p>
                </div>
                <div class="insight-item">
                    <h5>Risk Assessment</h5>
                    <p>${this.getEngineRiskAssessment(parseFloat(bestMoveRate))}</p>
                </div>
            </div>
        `;
        document.getElementById('engineInsights').innerHTML = html;
    }

    getEngineRiskAssessment(bestMoveRate) {
        if (bestMoveRate >= 80) {
            return "🚨 CRITICAL: 80%+ engine matching is extremely suspicious and indicates likely computer assistance.";
        } else if (bestMoveRate >= 70) {
            return "🚨 HIGH RISK: 70-80% engine matching is very concerning and warrants investigation.";
        } else if (bestMoveRate >= 60) {
            return "⚠️ MODERATE RISK: 60-70% engine matching is elevated but could indicate very strong play.";
        } else if (bestMoveRate >= 40) {
            return "📊 ELEVATED: 40-60% engine matching shows strong play but within human ranges.";
        } else {
            return "✅ NORMAL: Below 40% engine matching is typical for human play.";
        }
    }

    displayDetailedAnalysis(analysis) {
        const playerData = analysis[this.selectedPlayer + '_player'];
        const metrics = playerData ? playerData.metrics || {} : {};
        const playerMoves = this.getPlayerMoves(analysis);

        const html = `
            <div class="section-header">
                <h2><i class="fas fa-microscope"></i> Detailed Statistical Analysis</h2>
            </div>
            <div class="insights-grid">
                <div class="insight-item">
                    <h5>📊 Performance Metrics</h5>
                    <p>
                        <strong>Accuracy Score:</strong> ${(metrics.accuracy_score || 0).toFixed(1)}%<br>
                        <strong>Average CP Loss:</strong> ${(metrics.avg_centipawn_loss || 0).toFixed(1)}<br>
                        <strong>Standard Deviation:</strong> ${(metrics.std_centipawn_loss || 0).toFixed(1)}<br>
                        <strong>Blunders:</strong> ${metrics.blunder_count || 0}<br>
                        <strong>Mistakes:</strong> ${metrics.mistake_count || 0}
                    </p>
                </div>
                <div class="insight-item">
                    <h5>🤖 Engine Analysis</h5>
                    <p>
                        <strong>Best Move Rate:</strong> ${(metrics.best_move_rate || 0).toFixed(1)}%<br>
                        <strong>Top-3 Move Rate:</strong> ${(metrics.top3_move_rate || 0).toFixed(1)}%<br>
                        <strong>Engine Correlation:</strong> ${this.getEngineCorrelationLevel(metrics.best_move_rate || 0)}<br>
                        <strong>Total Moves:</strong> ${metrics.total_moves || 0}<br>
                        <strong>PV-1 / PV-3 Counts:</strong> ${metrics.pv1_count || 0} / ${metrics.pv3_count || 0}
                    </p>
                </div>
                <div class="insight-item">
                    <h5>📚 Opening Theory</h5>
                    <p>
                        <strong>Opening moves in theory:</strong> ${metrics.opening_move_count || 0}
                    </p>
                </div>
                <div class="insight-item">
                    <h5>🧠 PCS Complexity Analysis</h5>
                    <p>
                        <strong>Average PCS:</strong> ${playerMoves.length > 0 ? (playerMoves.reduce((sum, m) => sum + (m.complexity?.pcs_score || 0), 0) / playerMoves.length).toFixed(1) : '0.0'} cp<br>
                        <strong>Max PCS:</strong> ${playerMoves.length > 0 ? Math.max(...playerMoves.map(m => m.complexity?.pcs_score || 0)).toFixed(1) : '0.0'} cp<br>
                        <strong>Critical+Chaotic:</strong> ${playerMoves.filter(m => ['critical', 'chaotic'].includes(m.complexity?.pcs_category)).length}<br>
                        <strong>Avg Legal Moves:</strong> ${playerMoves.length > 0 ? (playerMoves.reduce((sum, m) => sum + (m.legal_moves_count || 0), 0) / playerMoves.length).toFixed(1) : '0.0'}
                    </p>
                </div>
                <div class="insight-item">
                    <h5>⏱️ Timing Analysis</h5>
                    <p>
                        <strong>Average Move Time:</strong> ${(metrics.avg_move_time || 0).toFixed(1)}s<br>
                        <strong>Timed Moves:</strong> ${playerMoves.filter(m => (m.move_time || 0) > 0).length}<br>
                        <strong>Fastest Move:</strong> ${playerMoves.filter(m => (m.move_time || 0) > 0).length > 0 ? Math.min(...playerMoves.filter(m => (m.move_time || 0) > 0).map(m => m.move_time || 0)).toFixed(1) : '0.0'}s<br>
                        <strong>Slowest Move:</strong> ${playerMoves.filter(m => (m.move_time || 0) > 0).length > 0 ? Math.max(...playerMoves.filter(m => (m.move_time || 0) > 0).map(m => m.move_time || 0)).toFixed(1) : '0.0'}s
                    </p>
                </div>
            </div>
        `;
        document.getElementById('detailedAnalysis').innerHTML = html;
    }

    getEngineCorrelationLevel(rate) {
        if (rate >= 80) return 'EXTREME';
        if (rate >= 60) return 'HIGH';
        if (rate >= 40) return 'MODERATE';
        if (rate >= 20) return 'LOW';
        return 'MINIMAL';
    }

    displayMoveAnalysis(analysis) {
        const playerMoves = this.getPlayerMoves(analysis);
        const moves = playerMoves.slice(0, 30); // Show first 30 moves

        const html = `
            <div class="section-header">
                <h2><i class="fas fa-list"></i> Move-by-Move Analysis</h2>
                <p>Detailed breakdown of each move with complexity calculations and quality assessment</p>
            </div>
            <div style="overflow-x: auto;">
                <table class="move-table">
                    <thead>
                        <tr>
                            <th>Move</th>
                            <th>Notation</th>
                            <th>Legal Moves</th>
                            <th>Complexity</th>
                            <th>Engine Rank</th>
                            <th>CP Loss</th>
                            <th>Accuracy</th>
                            <th>Time</th>
                            <th>Quality</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${moves.map(move => {
                            const accuracy = Math.max(0, 100 - ((move.centipawn_loss || 0) / 3.0));
                            const quality = this.getMoveQuality(move.centipawn_loss || 0);
                            const complexity = move.complexity || {};
                            const pcsScore = complexity.pcs_score || 0;
                            const pcsCategory = complexity.pcs_category || 'trivial';
                            
                            return `
                                <tr>
                                    <td><strong>${move.move_number || 'N/A'}</strong></td>
                                    <td><strong>${move.move || 'N/A'}</strong></td>
                                    <td>${move.legal_moves_count || 0}</td>
                                    <td>
                                        ${pcsScore.toFixed(1)} cp<br>
                                        <small class="pcs-category pcs-${pcsCategory}">${pcsCategory}</small>
                                    </td>
                                    <td>${move.move_rank || 'N/A'}</td>
                                    <td>${(move.centipawn_loss || 0).toFixed(0)}</td>
                                    <td>${accuracy.toFixed(1)}%</td>
                                    <td>${(move.move_time || 0) > 0 ? (move.move_time || 0).toFixed(1) + 's' : 'N/A'}</td>
                                    <td><span class="move-badge badge-${quality.class}">${quality.label}</span></td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
            <div class="insight-item" style="margin-top: 24px;">
                <h5>📝 Enhanced Analysis Notes</h5>
                <p>
                    <strong>PCS Formula (Maia-Inspired):</strong> max(0, score₂ - score₁) + max(0, score₃ - score₁) / 2<br>
                    <strong>PCS Categories:</strong> Trivial (&lt;30cp), Balanced (30-80cp), Critical (80-150cp), Chaotic (&gt;150cp)<br>
                    <strong>Accuracy Calculation:</strong> max(0, 100 - centipawn_loss / 3.0)<br>
                    <strong>Quality Thresholds:</strong> Excellent (&lt;20 CP), Good (20-49 CP), Inaccuracy (50-99 CP), Mistake (100-299 CP), Blunder (300+ CP)
                </p>
            </div>
        `;
        document.getElementById('moveAnalysis').innerHTML = html;
    }

    getMoveQuality(cpLoss) {
        if (cpLoss >= 300) return { label: 'Blunder', class: 'blunder' };
        if (cpLoss >= 100) return { label: 'Mistake', class: 'mistake' };
        if (cpLoss >= 50) return { label: 'Inaccuracy', class: 'inaccuracy' };
        if (cpLoss >= 20) return { label: 'Good', class: 'good' };
        return { label: 'Excellent', class: 'excellent' };
    }

    switchTab(button) {
        const tab = button.dataset.tab;
        
        // Update button states
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        // Update panel visibility
        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
        document.getElementById(tab + 'Tab').classList.add('active');
    }

    refreshCharts() {
        if (this.currentAnalysis) {
            this.createCharts(this.currentAnalysis);
        }
    }

    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ChessAnalysisApp();
}); 