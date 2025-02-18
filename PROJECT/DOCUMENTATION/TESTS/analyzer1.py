import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

def categorize_performance(average_points):
    """
    Categorize team performance based on average points.
    
    Args:
        average_points (float): Average points from recent games
        
    Returns:
        str: Performance category
    """
    if average_points > 7:
        return "Excellent"
    elif average_points < 5:
        return "Bad"
    else:
        return "Average"

def calculate_win_probability(team_a_points, team_b_points, h2h_points):
    """
    Calculate win probability using RandomForest classifier.
    
    Args:
        team_a_points (list): Last 10 game points for Team A
        team_b_points (list): Last 10 game points for Team B
        h2h_points (list): Points from head-to-head games between teams
        
    Returns:
        dict: Win probabilities for Team A, Team B, and Draw
    """
    # Create features for machine learning
    features = []
    outcomes = []
    
    # For each pair of historical points, create a training example
    # We'll use a simplified approach for demonstration
    for i in range(min(len(team_a_points), len(team_b_points))):
        features.append([
            team_a_points[i],
            team_b_points[i],
            np.mean(team_a_points[:i+1]) if i > 0 else team_a_points[i],
            np.mean(team_b_points[:i+1]) if i > 0 else team_b_points[i],
            np.std(team_a_points[:i+1]) if i > 0 else 0,
            np.std(team_b_points[:i+1]) if i > 0 else 0,
        ])
        
        # Determine historical outcome (simplified)
        if team_a_points[i] > team_b_points[i]:
            outcomes.append(0)  # Team A won
        elif team_b_points[i] > team_a_points[i]:
            outcomes.append(1)  # Team B won
        else:
            outcomes.append(2)  # Draw
    
    # Train a RandomForest classifier
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(features, outcomes)
    
    # Create prediction features using average metrics
    prediction_features = [[
        np.mean(team_a_points),
        np.mean(team_b_points),
        np.mean(team_a_points),
        np.mean(team_b_points),
        np.std(team_a_points),
        np.std(team_b_points),
    ]]
    
    # Get class probabilities
    probabilities = clf.predict_proba(prediction_features)[0]
    
    # If RandomForest wasn't able to predict all classes, adjust probabilities
    if len(probabilities) < 3:
        full_probabilities = np.zeros(3)
        for i, prob in enumerate(probabilities):
            if i < len(full_probabilities):
                full_probabilities[i] = prob
        probabilities = full_probabilities
    
    # Create win probability dictionary
    win_probabilities = {
        'Team A': round(probabilities[0] * 5, 2),
        'Team B': round(probabilities[1] * 5, 2),
        'Draw': round(probabilities[2] * 5, 2) if len(probabilities) > 2 else 0
    }
    
    return win_probabilities

def team_analysis(team_a_points, team_b_points, h2h_points):
    """
    Analyze team performance based on recent points and head-to-head games.
    
    Args:
        team_a_points (list): Last 10 game points for Team A
        team_b_points (list): Last 10 game points for Team B
        h2h_points (list): List of tuples containing (team_a_score, team_b_score)
                           for head-to-head games
    
    Returns:
        dict: Analysis results
    """
    # Calculate averages
    team_a_avg = np.mean(team_a_points)
    team_b_avg = np.mean(team_b_points)
    
    # Calculate H2H averages
    h2h_team_a_points = [game[0] for game in h2h_points]
    h2h_team_b_points = [game[1] for game in h2h_points]
    h2h_team_a_avg = np.mean(h2h_team_a_points)
    h2h_team_b_avg = np.mean(h2h_team_b_points)
    
    # Categorize performances
    team_a_performance = categorize_performance(team_a_avg)
    team_b_performance = categorize_performance(team_b_avg)
    h2h_team_a_performance = categorize_performance(h2h_team_a_avg)
    h2h_team_b_performance = categorize_performance(h2h_team_b_avg)
    
    # Calculate win probabilities
    win_probabilities = calculate_win_probability(
        team_a_points, team_b_points, h2h_points
    )
    
    # Determine predicted winner
    predicted_winner = max(win_probabilities, key=win_probabilities.get)
    
    # Return analysis results
    return {
        'Team A': {
            'Average Points': round(team_a_avg, 10),
            'Performance': team_a_performance,
            'H2H Average': round(h2h_team_a_avg, 2),
            'H2H Performance': h2h_team_a_performance,
            'Win Probability': win_probabilities['Team A']
        },
        'Team B': {
            'Average Points': round(team_b_avg, 10),
            'Performance': team_b_performance,
            'H2H Average': round(h2h_team_b_avg, 2),
            'H2H Performance': h2h_team_b_performance,
            'Win Probability': win_probabilities['Team B']
        },
        'Draw Probability': win_probabilities.get('Draw', 0),
        'Predicted Winner': predicted_winner,
    }

def multiple_teams_analysis(teams_data):
    """
    Analyze multiple teams' performance.
    
    Args:
        teams_data (dict): Dictionary containing team names as keys and lists of points as values
    
    Returns:
        dict: Analysis results for each team
    """
    results = {}
    
    for team_name, points in teams_data.items():
        avg_points = np.mean(points)
        performance = categorize_performance(avg_points)
        
        results[team_name] = {
            'Average Points': round(avg_points, 2),
            'Performance': performance,
        }
    
    return results

# Example usage
if __name__ == "__main__":
    # Example data for Team A and Team B's last 10 games
    team_a_points = [8, 6, 7, 9, 8, 7, 6, 8, 9, 8],[8, 6, 7, 9, 8, 7, 6, 8, 9, 8]

    team_b_points = [5, 4, 6, 7, 5, 6, 4, 5, 6, 7],[5, 4, 6, 7, 5, 6, 4, 5, 6, 7]
    
    # Example H2H data (Team A score, Team B score)
    h2h_points = [(3, 1), (2, 2), (1, 0), (2, 1), (0, 2)]
    
    # Run analysis
    result = team_analysis(team_a_points, team_b_points, h2h_points)
    
    # Print results
    print("=== Team Performance Analysis ===")
    print(f"Team A: {result['Team A']['Performance']} (Avg: {result['Team A']['Average Points']} points)")
    print(f"Team B: {result['Team B']['Performance']} (Avg: {result['Team B']['Average Points']} points)")
    print("\n=== Head-to-Head Analysis ===")
    print(f"Team A H2H: {result['Team A']['H2H Performance']} (Avg: {result['Team A']['H2H Average']} points)")
    print(f"Team B H2H: {result['Team B']['H2H Performance']} (Avg: {result['Team B']['H2H Average']} points)")
    print("\n=== Win Prediction ===")
    print(f"Team A win probability: {result['Team A']['Win Probability']}/5")
    print(f"Team B win probability: {result['Team B']['Win Probability']}/5")
    print(f"Draw probability: {result['Draw Probability']}/5")
    print(f"Predicted winner: {result['Predicted Winner']}")
    
    # Example usage for multiple teams analysis
    multiple_teams_data = {
        'Team A': [8, 6, 7, 9, 8, 7, 6, 8, 9, 8],
        'Team B': [5, 4, 6, 7, 5, 6, 4, 5, 6, 7],
        'Team C': [7, 8, 7, 9, 8, 9, 7, 8, 9, 8],
        'Team D': [3, 4, 3, 5, 4, 3, 4, 5, 4, 3],
    }
    
    multiple_results = multiple_teams_analysis(multiple_teams_data)
    
    print("\n=== Multiple Teams Analysis ===")
    for team, analysis in multiple_results.items():
        print(f"{team}: {analysis['Performance']} (Avg: {analysis['Average Points']} points)")