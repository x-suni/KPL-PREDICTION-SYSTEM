import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime

class TeamPerformanceAnalyzer:
    def __init__(self, save_model=True, model_path='team_prediction_model.pkl'):
        """
        Initialize the Team Performance Analyzer.
        
        Args:
            save_model (bool): Whether to save the trained model
            model_path (str): Path to save or load the model
        """
        self.performance_categories = {
            'Excellent': {'min': 7.0, 'max': float('inf')},
            'Good': {'min': 6.0, 'max': 7.0},
            'Average': {'min': 5.0, 'max': 6.0},
            'Below Average': {'min': 4.0, 'max': 5.0},
            'Bad': {'min': 0, 'max': 4.0}
        }
        
        self.save_model = save_model
        self.model_path = model_path
        self.scaler = StandardScaler()
        
        # Try to load existing model
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                print(f"Loaded existing model from {model_path}")
            except:
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
                print(f"Failed to load model, initialized new RandomForest")
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            print("Initialized new RandomForest model")

    def categorize_performance(self, average_points):
        """
        Categorize team performance based on average points.
        
        Args:
            average_points (float): Average points from recent games
            
        Returns:
            str: Performance category
        """
        for category, thresholds in self.performance_categories.items():
            if thresholds['min'] <= average_points < thresholds['max']:
                return category
        return "Unknown"

    def prepare_features(self, team_a_points, team_b_points, h2h_points=None):
        """
        Prepare features for prediction.
        
        Args:
            team_a_points (list): Recent points for Team A
            team_b_points (list): Recent points for Team B
            h2h_points (list): Head-to-head game results
            
        Returns:
            array: Processed features for prediction
        """
        # Calculate basic statistics
        features = [
            np.mean(team_a_points),         # Average points Team A
            np.mean(team_b_points),         # Average points Team B
            np.std(team_a_points),          # Points variation Team A
            np.std(team_b_points),          # Points variation Team B
            np.max(team_a_points),          # Best performance Team A
            np.max(team_b_points),          # Best performance Team B
            np.min(team_a_points),          # Worst performance Team A
            np.min(team_b_points),          # Worst performance Team B
        ]
        
        # Calculate form (last 3 games trend)
        if len(team_a_points) >= 3:
            features.append(np.mean(team_a_points[-3:]))  # Recent form Team A
        else:
            features.append(np.mean(team_a_points))
            
        if len(team_b_points) >= 3:
            features.append(np.mean(team_b_points[-3:]))  # Recent form Team B
        else:
            features.append(np.mean(team_b_points))
        
        # Add H2H statistics if available
        if h2h_points:
            h2h_a = [game[0] for game in h2h_points]
            h2h_b = [game[1] for game in h2h_points]
            
            features.extend([
                np.mean(h2h_a),             # Average H2H points Team A
                np.mean(h2h_b),             # Average H2H points Team B
                len([1 for a, b in h2h_points if a > b]) / len(h2h_points),  # Team A win ratio
                len([1 for a, b in h2h_points if b > a]) / len(h2h_points),  # Team B win ratio
                len([1 for a, b in h2h_points if a == b]) / len(h2h_points)  # Draw ratio
            ])
        else:
            # Placeholder values if H2H not available
            features.extend([0, 0, 0.33, 0.33, 0.33])
        
        return np.array(features).reshape(1, -1)

    def train_model(self, historical_data):
        """
        Train the prediction model with historical match data.
        
        Args:
            historical_data (list): List of dictionaries with historical match data
            
        Returns:
            self: The trained model instance
        """
        features = []
        outcomes = []
        
        for match in historical_data:
            team_a_points = match['team_a_points']
            team_b_points = match['team_b_points']
            h2h_points = match.get('h2h_points', None)
            result = match['result']  # 0: Team A win, 1: Team B win, 2: Draw
            
            match_features = self.prepare_features(team_a_points, team_b_points, h2h_points).flatten()
            features.append(match_features)
            outcomes.append(result)
        
        # Scale features
        X = self.scaler.fit_transform(features)
        
        # Train model
        self.model.fit(X, outcomes)
        
        # Save model if requested
        if self.save_model:
            joblib.dump(self.model, self.model_path)
            print(f"Model saved to {self.model_path}")
            
        return self

    def predict_match(self, team_a_points, team_b_points, h2h_points=None):
        """
        Predict match outcome based on historical performance.
        
        Args:
            team_a_points (list): Recent points for Team A
            team_b_points (list): Recent points for Team B
            h2h_points (list): Head-to-head game results
            
        Returns:
            dict: Prediction results
        """
        # Prepare features
        features = self.prepare_features(team_a_points, team_b_points, h2h_points)
        
        # Scale features
        scaled_features = self.scaler.transform(features)
        
        # Get probabilities
        try:
            probabilities = self.model.predict_proba(scaled_features)[0]
            
            # Ensure we have probabilities for all outcomes
            if len(probabilities) < 3:
                full_probabilities = np.zeros(3)
                for i, prob in enumerate(probabilities):
                    if i < len(full_probabilities):
                        full_probabilities[i] = prob
                probabilities = full_probabilities
        except:
            # If model isn't trained yet, use simplified approach
            team_a_avg = np.mean(team_a_points)
            team_b_avg = np.mean(team_b_points)
            
            if team_a_avg > team_b_avg:
                probabilities = [0.6, 0.3, 0.1]  # Team A favored
            elif team_b_avg > team_a_avg:
                probabilities = [0.3, 0.6, 0.1]  # Team B favored
            else:
                probabilities = [0.4, 0.4, 0.2]  # Even match
        
        # Convert to 1-5 scale and round to 2 decimals
        scaled_probabilities = {
            'Team A': round(probabilities[0] * 5, 2),
            'Team B': round(probabilities[1] * 5, 2),
            'Draw': round(probabilities[2] * 5, 2)
        }
        
        # Determine predicted winner
        predicted_winner = max(scaled_probabilities, key=scaled_probabilities.get)
        
        return scaled_probabilities, predicted_winner

    def analyze_teams(self, team_a_points, team_b_points, h2h_points=None):
        """
        Analyze team performance and predict match outcome.
        
        Args:
            team_a_points (list): Recent points for Team A
            team_b_points (list): Recent points for Team B
            h2h_points (list): List of tuples with head-to-head results (optional)
            
        Returns:
            dict: Analysis results
        """
        # Calculate basic metrics
        team_a_avg = np.mean(team_a_points)
        team_b_avg = np.mean(team_b_points)
        
        team_a_performance = self.categorize_performance(team_a_avg)
        team_b_performance = self.categorize_performance(team_b_avg)
        
        # Calculate H2H metrics if available
        h2h_team_a_avg = None
        h2h_team_b_avg = None
        h2h_team_a_performance = None
        h2h_team_b_performance = None
        
        if h2h_points:
            h2h_team_a_points = [game[0] for game in h2h_points]
            h2h_team_b_points = [game[1] for game in h2h_points]
            
            h2h_team_a_avg = np.mean(h2h_team_a_points)
            h2h_team_b_avg = np.mean(h2h_team_b_points)
            
            h2h_team_a_performance = self.categorize_performance(h2h_team_a_avg)
            h2h_team_b_performance = self.categorize_performance(h2h_team_b_avg)
        
        # Predict match outcome
        win_probabilities, predicted_winner = self.predict_match(
            team_a_points, team_b_points, h2h_points
        )
        
        # Compile analysis results
        result = {
            'Team A': {
                'Recent Average': round(team_a_avg, 2),
                'Recent Performance': team_a_performance,
                'Win Probability': win_probabilities['Team A']
            },
            'Team B': {
                'Recent Average': round(team_b_avg, 2),
                'Recent Performance': team_b_performance,
                'Win Probability': win_probabilities['Team B']
            },
            'Draw Probability': win_probabilities['Draw'],
            'Predicted Winner': predicted_winner
        }
        
        # Add H2H analysis if available
        if h2h_points:
            result['Team A'].update({
                'H2H Average': round(h2h_team_a_avg, 2),
                'H2H Performance': h2h_team_a_performance,
                'H2H Win Rate': round(len([1 for a, b in h2h_points if a > b]) / len(h2h_points) * 100, 1)
            })
            
            result['Team B'].update({
                'H2H Average': round(h2h_team_b_avg, 2),
                'H2H Performance': h2h_team_b_performance,
                'H2H Win Rate': round(len([1 for a, b in h2h_points if b > a]) / len(h2h_points) * 100, 1)
            })
            
            result['Draw Rate'] = round(len([1 for a, b in h2h_points if a == b]) / len(h2h_points) * 100, 1)
        
        return result

    def analyze_multiple_teams(self, teams_data):
        """
        Analyze performance of multiple teams.
        
        Args:
            teams_data (dict): Dictionary with team names as keys and points lists as values
            
        Returns:
            dict: Analysis results for each team
        """
        results = {}
        rankings = []
        
        # Analyze each team
        for team_name, points in teams_data.items():
            avg_points = np.mean(points)
            performance = self.categorize_performance(avg_points)
            
            team_analysis = {
                'Average Points': round(avg_points, 2),
                'Performance': performance,
                'Standard Deviation': round(np.std(points), 2),
                'Best Performance': max(points),
                'Worst Performance': min(points),
                'Recent Form': round(np.mean(points[-3:]) if len(points) >= 3 else avg_points, 2)
            }
            
            results[team_name] = team_analysis
            rankings.append((team_name, avg_points))
        
        # Rank teams by average performance
        rankings.sort(key=lambda x: x[1], reverse=True)
        ranking_dict = {team: rank+1 for rank, (team, _) in enumerate(rankings)}
        
        # Add rankings to results
        for team in results:
            results[team]['Rank'] = ranking_dict[team]
        
        return results

    def visualize_performance(self, teams_data, output_path='team_performance.png'):
        """
        Create visualization of team performance.
        
        Args:
            teams_data (dict): Dictionary with team names as keys and points lists as values
            output_path (str): Path to save the visualization
            
        Returns:
            str: Path to saved visualization
        """
        plt.figure(figsize=(12, 8))
        
        # Create team averages bar chart
        averages = {team: np.mean(points) for team, points in teams_data.items()}
        teams = list(averages.keys())
        avg_values = list(averages.values())
        
        # Sort by average
        sorted_indices = np.argsort(avg_values)[::-1]
        sorted_teams = [teams[i] for i in sorted_indices]
        sorted_avgs = [avg_values[i] for i in sorted_indices]
        
        # Create bar colors based on performance category
        colors = []
        for avg in sorted_avgs:
            category = self.categorize_performance(avg)
            if category == 'Excellent':
                colors.append('darkgreen')
            elif category == 'Good':
                colors.append('lightgreen')
            elif category == 'Average':
                colors.append('yellow')
            elif category == 'Below Average':
                colors.append('orange')
            else:  # Bad
                colors.append('red')
        
        # Plot bars
        bars = plt.bar(sorted_teams, sorted_avgs, color=colors)
        
        # Add performance thresholds as horizontal lines
        plt.axhline(y=7, color='darkgreen', linestyle='--', alpha=0.7, label='Excellent threshold')
        plt.axhline(y=6, color='lightgreen', linestyle='--', alpha=0.7, label='Good threshold')
        plt.axhline(y=5, color='yellow', linestyle='--', alpha=0.7, label='Average threshold')
        plt.axhline(y=4, color='orange', linestyle='--', alpha=0.7, label='Below Average threshold')
        
        # Add labels and title
        plt.xlabel('Teams')
        plt.ylabel('Average Points')
        plt.title('Team Performance Analysis')
        plt.legend()
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                     f'{height:.2f}', ha='center', va='bottom')
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        return output_path

# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = TeamPerformanceAnalyzer()
    
    # Example data
    team_a_points = [8, 6, 7, 9, 8, 7, 6, 8, 9, 8]
    team_b_points = [5, 4, 6, 7, 5, 6, 4, 5, 6, 7]
    h2h_points = [(3, 1), (2, 2), (1, 0), (2, 1), (0, 2)]
    
    # Create some historical data for training the model
    historical_data = [
        {'team_a_points': [8, 7, 8, 9, 7], 'team_b_points': [5, 6, 4, 6, 5], 'result': 0},  # Team A win
        {'team_a_points': [6, 7, 6, 5, 6], 'team_b_points': [7, 8, 7, 6, 8], 'result': 1},  # Team B win
        {'team_a_points': [7, 6, 7, 8, 7], 'team_b_points': [7, 6, 8, 7, 8], 'result': 2},  # Draw
        {'team_a_points': [9, 8, 9, 8, 9], 'team_b_points': [4, 5, 4, 5, 4], 'result': 0},  # Team A win
        {'team_a_points': [4, 5, 4, 3, 4], 'team_b_points': [8, 7, 8, 7, 8], 'result': 1},  # Team B win
    ]
    
    # Train model
    analyzer.train_model(historical_data)
    
    # Analyze match
    result = analyzer.analyze_teams(team_a_points, team_b_points, h2h_points)
    
    # Print results
    print("=== Team Performance Analysis ===")
    print(f"Team A: {result['Team A']['Recent Performance']} (Avg: {result['Team A']['Recent Average']} points)")
    print(f"Team B: {result['Team B']['Recent Performance']} (Avg: {result['Team B']['Recent Average']} points)")
    
    if 'H2H Average' in result['Team A']:
        print("\n=== Head-to-Head Analysis ===")
        print(f"Team A H2H: {result['Team A']['H2H Performance']} (Avg: {result['Team A']['H2H Average']} points)")
        print(f"Team B H2H: {result['Team B']['H2H Performance']} (Avg: {result['Team B']['H2H Average']} points)")
        print(f"Team A Win Rate: {result['Team A']['H2H Win Rate']}%")
        print(f"Team B Win Rate: {result['Team B']['H2H Win Rate']}%")
        print(f"Draw Rate: {result['Draw Rate']}%")
    
    print("\n=== Win Prediction ===")
    print(f"Team A win probability: {result['Team A']['Win Probability']}/5")
    print(f"Team B win probability: {result['Team B']['Win Probability']}/5")
    print(f"Draw probability: {result['Draw Probability']}/5")
    print(f"Predicted winner: {result['Predicted Winner']}")
    
    # Example of multiple teams analysis
    multiple_teams_data = {
        'Team A': [8, 6, 7, 9, 8, 7, 6, 8, 9, 8],
        'Team B': [5, 4, 6, 7, 5, 6, 4, 5, 6, 7],
        'Team C': [7, 8, 7, 9, 8, 9, 7, 8, 9, 8],
        'Team D': [3, 4, 3, 5, 4, 3, 4, 5, 4, 3],
        'Team E': [6, 5, 6, 7, 6, 7, 6, 5, 6, 7],
    }
    
    multiple_results = analyzer.analyze_multiple_teams(multiple_teams_data)
    
    print("\n=== Multiple Teams Analysis ===")
    for team, analysis in sorted(multiple_results.items(), key=lambda x: x[1]['Rank']):
        print(f"Rank {analysis['Rank']}: {team} - {analysis['Performance']} (Avg: {analysis['Average Points']} points)")
    
    # Create visualization
    viz_path = analyzer.visualize_performance(multiple_teams_data)
    print(f"\nVisualization saved to {viz_path}")