import pandas as pd
from typing import List, Tuple, Dict

class TeamGameAnalyzer:
    def __init__(self):
        """
        Initialize the analyzer that will process multiple sets of game data.
        """
        self.all_results = []
    
    def calculate_averages(self, scores: List[int]) -> Tuple[float, float, float]:
        """
        Calculate averages for a single set of scores.
        
        Parameters:
            scores (List[int]): List of scores for a set of games
            
        Returns:
            Tuple[float, float, float]: last_6_avg, last_3_avg, weighted_avg
        """
        last_6_avg = sum(scores[-6:]) / 6
        last_3_avg = sum(scores[-3:]) / 3
        weighted_avg = (last_3_avg * 2 + last_6_avg) / 3
        return last_6_avg, last_3_avg, weighted_avg
    
    def calculate_odds(self, team_a_weighted: float, team_b_weighted: float, h2h_weighted: float) -> Dict[str, float]:
        """
        Calculate odds on a scale of 1-5 for each team and H2H.
        
        Parameters:
            team_a_weighted (float): Weighted average for Team A
            team_b_weighted (float): Weighted average for Team B
            h2h_weighted (float): Weighted average for head-to-head games
            
        Returns:
            Dict[str, float]: Odds for Team A, Team B, and H2H
        """
        # Normalize the weighted averages to a scale of 1-5
        total_avg = team_a_weighted + team_b_weighted + h2h_weighted
        
        if total_avg == 0:  # Avoid division by zero
            return {'team_a': 1.0, 'team_b': 1.0, 'h2h': 1.0}
        
        # Calculate odds proportional to weighted averages, scaled to 1-5
        team_a_odds = (team_a_weighted / total_avg) * 5
        team_b_odds = (team_b_weighted / total_avg) * 5
        h2h_odds = (h2h_weighted / total_avg) * 5
        
        return {
            'team_a': round(team_a_odds, 2),
            'team_b': round(team_b_odds, 2),
            'h2h': round(h2h_odds, 2)
        }
    
    def determine_winner(self, odds: Dict[str, float]) -> str:
        """
        Determine the likely winner based on odds.
        
        Parameters:
            odds (Dict[str, float]): Odds for Team A, Team B, and H2H
            
        Returns:
            str: Predicted winner
        """
        max_odds = max(odds.values())
        
        if odds['team_a'] == max_odds:
            return 'Team A'
        elif odds['team_b'] == max_odds:
            return 'Team B'
        else:
            return 'H2H (Draw likely)'
    
    def process_game_sets(self, team_a_sets: List[List[int]], 
                         team_b_sets: List[List[int]], 
                         h2h_sets: List[List[int]]) -> List[dict]:
        """
        Process multiple sets of games for each team.
        
        Parameters:
            team_a_sets: List of score sets for Team A
            team_b_sets: List of score sets for Team B
            h2h_sets: List of score sets for head-to-head games
            
        Returns:
            List[dict]: Analysis results for each set of games
        """
        results = []
        
        # Process each set of games
        for set_index in range(len(team_a_sets)):
            # Get the current set of scores for each team/category
            team_a_scores = team_a_sets[set_index]
            team_b_scores = team_b_sets[set_index]
            h2h_scores = h2h_sets[set_index]
            
            # Calculate averages for each team/category
            team_a_avg_6, team_a_avg_3, team_a_weighted = self.calculate_averages(team_a_scores)
            team_b_avg_6, team_b_avg_3, team_b_weighted = self.calculate_averages(team_b_scores)
            h2h_avg_6, h2h_avg_3, h2h_weighted = self.calculate_averages(h2h_scores)
            
            # Calculate combined averages
            combined_avg_6 = (team_a_avg_6 + team_b_avg_6) / 2
            combined_avg_3 = (team_a_avg_3 + team_b_avg_3) / 2
            combined_weighted = (team_a_weighted + team_b_weighted) / 2
            
            # Calculate final prediction
            final_prediction = (combined_weighted + h2h_weighted) / 2
            
            # Calculate odds
            odds = self.calculate_odds(team_a_weighted, team_b_weighted, h2h_weighted)
            
            # Determine predicted winner
            predicted_winner = self.determine_winner(odds)
            
            # Store results for this set
            set_results = {
                'set_number': set_index + 1,
                'team_a_analysis': {
                    'scores': team_a_scores,
                    'last_6_avg': team_a_avg_6,
                    'last_3_avg': team_a_avg_3,
                    'weighted_avg': team_a_weighted
                },
                'team_b_analysis': {
                    'scores': team_b_scores,
                    'last_6_avg': team_b_avg_6,
                    'last_3_avg': team_b_avg_3,
                    'weighted_avg': team_b_weighted
                },
                'h2h_analysis': {
                    'scores': h2h_scores,
                    'last_6_avg': h2h_avg_6,
                    'last_3_avg': h2h_avg_3,
                    'weighted_avg': h2h_weighted
                },
                'odds': odds,
                'predicted_winner': predicted_winner,
                'final_prediction': final_prediction
            }
            
            results.append(set_results)
        
        return results
    
    def categorize_performance(self, average_points: float) -> str:
        """
        Categorize team performance based on average points.
        
        Parameters:
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

    def print_analysis(self, results: List[dict]):
        """
        Print the analysis results in a readable format.
        
        Parameters:
            results (List[dict]): List of analysis results for each set
        """
        for result in results:
            print(f"\n=== Analysis for Set {result['set_number']} ===")
            
            # Team A Analysis
            print("\nTeam A Analysis:")
            print(f"Scores: {result['team_a_analysis']['scores']}")
            print(f"Last 6 Average: {result['team_a_analysis']['last_6_avg']:.2f}")
            print(f"Last 3 Average: {result['team_a_analysis']['last_3_avg']:.2f}")
            print(f"Weighted Average: {result['team_a_analysis']['weighted_avg']:.2f}")
            
            # Categorize Team A performance
            team_a_performance = self.categorize_performance(result['team_a_analysis']['weighted_avg'])
            print(f"Performance: {team_a_performance}")
            
            # Team B Analysis
            print("\nTeam B Analysis:")
            print(f"Scores: {result['team_b_analysis']['scores']}")
            print(f"Last 6 Average: {result['team_b_analysis']['last_6_avg']:.2f}")
            print(f"Last 3 Average: {result['team_b_analysis']['last_3_avg']:.2f}")
            print(f"Weighted Average: {result['team_b_analysis']['weighted_avg']:.2f}")
            
            # Categorize Team B performance
            team_b_performance = self.categorize_performance(result['team_b_analysis']['weighted_avg'])
            print(f"Performance: {team_b_performance}")
            
            # Head-to-Head Analysis
            print("\nHead-to-Head Analysis:")
            print(f"Scores: {result['h2h_analysis']['scores']}")
            print(f"Last 6 Average: {result['h2h_analysis']['last_6_avg']:.2f}")
            print(f"Last 3 Average: {result['h2h_analysis']['last_3_avg']:.2f}")
            print(f"Weighted Average: {result['h2h_analysis']['weighted_avg']:.2f}")
            
            # Categorize H2H performance
            h2h_performance = self.categorize_performance(result['h2h_analysis']['weighted_avg'])
            print(f"Performance: {h2h_performance}")
            
            # Odds and Prediction
            print("\nOdds (scale 1-5):")
            print(f"Team A: {result['odds']['team_a']}")
            print(f"Team B: {result['odds']['team_b']}")
            print(f"H2H: {result['odds']['h2h']}")
            print(f"Predicted Winner: {result['predicted_winner']}")
            
            print(f"\nFinal Prediction: {result['final_prediction']:.2f}")
            print("=" * 50)

# Example usage
if __name__ == "__main__":
    # Define multiple sets of game data
    team_a_sets = [
        [220, 215, 230, 225, 222, 218],  # First set
        [220, 215, 230, 225, 222, 218]   # Second set
    ]
    
    team_b_sets = [
        [212, 208, 218, 220, 224, 226],  # First set
        [220, 215, 230, 225, 222, 218]   # Second set
    ]
    
    h2h_sets = [
        [220, 225, 230, 215, 210, 220],  # First set
        [220, 225, 230, 215, 210, 220]   # Second set
    ]
    
    # Create analyzer and process the data
    analyzer = TeamGameAnalyzer()
    results = analyzer.process_game_sets(team_a_sets, team_b_sets, h2h_sets)
    
    # Print the results
    analyzer.print_analysis(results)