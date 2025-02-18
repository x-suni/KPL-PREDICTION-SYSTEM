import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

class KPLMatchPredictor:
    def __init__(self):
        # Initialize storage paths
        self.data_path = "kpl_match_data/"
        self.prediction_path = "kpl_predictions/"
        self.team_stats_path = "team_stats/"
        
        # Create directories if they don't exist
        for path in [self.data_path, self.prediction_path, self.team_stats_path]:
            if not os.path.exists(path):
                os.makedirs(path)
        
        # Initialize metrics weightings
        # CHANGE HERE: Adjust weightings based on which metrics you find more important
        self.metrics_weights = {
            'goals_scored': 1.5,
            'possession': 1.0,
            'shots_on_target': 1.2,
            'passes_completed': 0.8,
            'tackles_won': 0.7,
            'saves': 0.9,
            'cards': 0.7
        }
    
    def collect_match_data(self, match_id=None, season=None, team=None):
        """
        Collects data for Kenya Premier League matches.
        
        Args:
            match_id (str, optional): Specific match to collect data for.
            season (str, optional): Season to collect data for.
            team (str, optional): Team to collect data for.
            
        Returns:
            dict: Collected match data
        """
        # CHANGE HERE: Update URL to actual data source for KPL
        base_url = "https://example-kpl-data-source.com/api/matches"
        
        # Build parameters based on provided arguments
        params = {}
        if match_id:
            params['match_id'] = match_id
        if season:
            params['season'] = season
        if team:
            params['team'] = team
        
        try:
            # CHANGE HERE: Use appropriate authentication if required
            # response = requests.get(base_url, params=params, headers={'Authorization': 'YOUR_API_KEY'})
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                match_data = response.json()
                
                # Save raw data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.data_path}raw_data_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(match_data, f)
                
                return match_data
            else:
                print(f"Error fetching data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Exception occurred during data collection: {str(e)}")
            return None
    
    def process_match_data(self, match_data):
        """
        Processes raw match data into numerical metrics.
        
        Args:
            match_data (dict): Raw match data
            
        Returns:
            dict: Processed match metrics
        """
        processed_data = {}
        
        # CHANGE HERE: Modify this section based on the actual structure of your data
        for match in match_data.get('matches', []):
            match_id = match.get('id')
            processed_data[match_id] = {
                'date': match.get('date'),
                'home_team': {
                    'name': match.get('home_team', {}).get('name'),
                    'stats': self._calculate_team_metrics(match.get('home_team', {}).get('stats', {})),
                    'lineup': match.get('home_team', {}).get('lineup', [])
                },
                'away_team': {
                    'name': match.get('away_team', {}).get('name'),
                    'stats': self._calculate_team_metrics(match.get('away_team', {}).get('stats', {})),
                    'lineup': match.get('away_team', {}).get('lineup', [])
                },
                'result': match.get('result'),
                'venue': match.get('venue')
            }
            
            # Save processed match data
            with open(f"{self.data_path}match_{match_id}_processed.json", 'w') as f:
                json.dump(processed_data[match_id], f)
                
        return processed_data
    
    def _calculate_team_metrics(self, raw_stats):
        """
        Calculates numerical metrics from raw team statistics.
        
        Args:
            raw_stats (dict): Raw team statistics
            
        Returns:
            dict: Calculated metrics
        """
        metrics = {}
        
        # CHANGE HERE: Modify these calculations based on available stats and your preferences
        
        # Goals scored - direct value
        metrics['goals_scored'] = raw_stats.get('goals', 0)
        
        # Possession - percentage, scale to 0-10
        metrics['possession'] = raw_stats.get('possession', 50) / 10
        
        # Shots on target - scale to 0-10 (assuming max reasonable value is 20)
        shots_on_target = raw_stats.get('shots_on_target', 0)
        metrics['shots_on_target'] = min(shots_on_target / 2, 10)
        
        # Passes completed - scale to 0-10 (assuming 500 passes is excellent)
        passes = raw_stats.get('passes_completed', 0)
        metrics['passes_completed'] = min(passes / 50, 10)
        
        # Tackles - scale to 0-10 (assuming 30 tackles is excellent)
        tackles = raw_stats.get('tackles_won', 0)
        metrics['tackles_won'] = min(tackles / 3, 10)
        
        # Saves - scale to 0-10 (assuming 10 saves is excellent)
        saves = raw_stats.get('saves', 0)
        metrics['saves'] = min(saves, 13)
        
        # Cards - calculate penalty (more cards = worse)
        yellow_cards = raw_stats.get('yellow_cards', 0)
        red_cards = raw_stats.get('red_cards', 0)
        card_penalty = (yellow_cards + 3 * red_cards) / 3
        # Invert scale so 10 means no cards, 0 means many cards
        metrics['cards'] = max(10 - card_penalty, 0)
        
        # Calculate overall performance score
        total_score = sum(metric * self.metrics_weights.get(key, 1.0) 
                          for key, metric in metrics.items())
        total_weight = sum(self.metrics_weights.get(key, 1.0) 
                           for key in metrics.keys())
        
        metrics['overall_score'] = round(total_score / total_weight, 2)
        
        return metrics
    
    def calculate_team_average(self, team_name, num_previous_matches=5):
        """
        Calculates average performance metrics for a team based on previous matches.
        
        Args:
            team_name (str): Name of the team
            num_previous_matches (int): Number of previous matches to consider
            
        Returns:
            dict: Average performance metrics
        """
        # Get all processed match data for this team
        team_matches = []
        
        # CHANGE HERE: Implement proper file search/filter logic based on your storage structure
        for filename in os.listdir(self.data_path):
            if not filename.endswith("_processed.json"):
                continue
                
            with open(os.path.join(self.data_path, filename), 'r') as f:
                match_data = json.load(f)
                
                if match_data.get('home_team', {}).get('name') == team_name:
                    team_matches.append(('home_team', match_data))
                elif match_data.get('away_team', {}).get('name') == team_name:
                    team_matches.append(('away_team', match_data))
        
        # Sort by date, most recent first
        team_matches.sort(key=lambda x: x[1].get('date', ''), reverse=True)
        
        # Take only the specified number of previous matches
        team_matches = team_matches[:num_previous_matches]
        
        if not team_matches:
            return None
        
        # Calculate average metrics
        all_metrics = {}
        for team_key, match in team_matches:
            metrics = match.get(team_key, {}).get('stats', {})
            for key, value in metrics.items():
                if key not in all_metrics:
                    all_metrics[key] = []
                all_metrics[key].append(value)
        
        avg_metrics = {key: sum(values) / len(values) 
                       for key, values in all_metrics.items()}
        
        # Save team average data
        with open(f"{self.team_stats_path}{team_name}_avg.json", 'w') as f:
            json.dump({
                'team': team_name,
                'num_matches': len(team_matches),
                'avg_metrics': avg_metrics
            }, f)
            
        return avg_metrics
    
    def analyze_h2h(self, team_a, team_b):
        """
        Analyzes head-to-head matches between two teams.
        
        Args:
            team_a (str): First team name
            team_b (str): Second team name
            
        Returns:
            dict: Head-to-head analysis results
        """
        # Get all processed match data for matches between these teams
        h2h_matches = []
        
        # CHANGE HERE: Implement proper file search/filter logic
        for filename in os.listdir(self.data_path):
            if not filename.endswith("_processed.json"):
                continue
                
            with open(os.path.join(self.data_path, filename), 'r') as f:
                match_data = json.load(f)
                
                home_team = match_data.get('home_team', {}).get('name')
                away_team = match_data.get('away_team', {}).get('name')
                
                if (home_team == team_a and away_team == team_b) or \
                   (home_team == team_b and away_team == team_a):
                    h2h_matches.append(match_data)
        
        if not h2h_matches:
            return None
        
        # Sort by date, most recent first
        h2h_matches.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Calculate team performance in H2H matches
        team_a_metrics = []
        team_b_metrics = []
        
        for match in h2h_matches:
            if match['home_team']['name'] == team_a:
                team_a_metrics.append(match['home_team']['stats'])
                team_b_metrics.append(match['away_team']['stats'])
            else:
                team_a_metrics.append(match['away_team']['stats'])
                team_b_metrics.append(match['home_team']['stats'])
        
        # Calculate averages
        team_a_avg = {key: sum(m[key] for m in team_a_metrics) / len(team_a_metrics)
                      for key in team_a_metrics[0].keys()}
        
        team_b_avg = {key: sum(m[key] for m in team_b_metrics) / len(team_b_metrics)
                      for key in team_b_metrics[0].keys()}
        
        # Count wins
        team_a_wins = 0
        team_b_wins = 0
        draws = 0
        
        for match in h2h_matches:
            result = match.get('result', {})
            if result.get('winner') == team_a:
                team_a_wins += 1
            elif result.get('winner') == team_b:
                team_b_wins += 1
            else:
                draws += 1
        
        h2h_analysis = {
            'matches_count': len(h2h_matches),
            'team_a': {
                'name': team_a,
                'wins': team_a_wins,
                'avg_metrics': team_a_avg,
                'h2h_rating': self._rate_performance(team_a_avg['overall_score'])
            },
            'team_b': {
                'name': team_b,
                'wins': team_b_wins,
                'avg_metrics': team_b_avg,
                'h2h_rating': self._rate_performance(team_b_avg['overall_score'])
            },
            'draws': draws
        }
        
        # Save H2H analysis
        with open(f"{self.data_path}h2h_{team_a}_{team_b}.json", 'w') as f:
            json.dump(h2h_analysis, f)
            
        return h2h_analysis
    
    def _rate_performance(self, score):
        """
        Rates performance based on score.
        
        Args:
            score (float): Performance score
            
        Returns:
            str: Performance rating
        """
        if score < 4:
            return "bad"
        elif score < 5.5:
            return "average"
        else:
            return "excellent"
    
    def predict_match(self, team_a, team_b):
        """
        Predicts outcome of a match between two teams.
        
        Args:
            team_a (str): Home team name
            team_b (str): Away team name
            
        Returns:
            dict: Match prediction
        """
        # Get team averages
        team_a_avg = self.calculate_team_average(team_a)
        team_b_avg = self.calculate_team_average(team_b)
        
        if not team_a_avg or not team_b_avg:
            return None
        
        # Get H2H analysis
        h2h_analysis = self.analyze_h2h(team_a, team_b)
        
        # Calculate prediction factors
        prediction_factors = {
            'team_performance': {
                team_a: team_a_avg['overall_score'],
                team_b: team_b_avg['overall_score']
            },
            'h2h_advantage': 0
        }
        
        # Factor in H2H if available
        if h2h_analysis:
            # Give advantage to team with better H2H record
            team_a_h2h_factor = h2h_analysis['team_a']['wins'] / h2h_analysis['matches_count']
            team_b_h2h_factor = h2h_analysis['team_b']['wins'] / h2h_analysis['matches_count']
            
            h2h_diff = team_a_h2h_factor - team_b_h2h_factor
            prediction_factors['h2h_advantage'] = h2h_diff
        
        # Apply home advantage factor (typically around 0.1-0.3)
        # CHANGE HERE: Adjust home advantage factor based on league statistics
        home_advantage = 0.2
        prediction_factors['home_advantage'] = home_advantage
        
        # Calculate win probabilities
        # This is a simplified model - more sophisticated models would use
        # machine learning techniques like logistic regression, random forests, etc.
        base_team_a_prob = (team_a_avg['overall_score'] / 
                          (team_a_avg['overall_score'] + team_b_avg['overall_score']))
        
        # Apply factors
        team_a_prob = base_team_a_prob + home_advantage
        if h2h_analysis:
            team_a_prob += prediction_factors['h2h_advantage'] * 0.1
        
        # Ensure probabilities stay in valid range
        team_a_prob = max(0.05, min(0.95, team_a_prob))
        team_b_prob = 1 - team_a_prob
        
        # Draw probability is highest when teams are evenly matched
        draw_factor = 1 - abs(team_a_prob - 0.5) * 2
        draw_prob = 0.25 * draw_factor
        
        # Redistribute remaining probability
        team_a_prob = team_a_prob * (1 - draw_prob)
        team_b_prob = team_b_prob * (1 - draw_prob)
        
        # Round to 2 decimal places
        team_a_prob = round(team_a_prob, 2)
        team_b_prob = round(team_b_prob, 2)
        draw_prob = round(draw_prob, 2)
        
        # Create prediction result
        prediction = {
            'match': {
                'home_team': team_a,
                'away_team': team_b,
                'date': datetime.now().strftime("%Y-%m-%d")
            },
            'probabilities': {
                'home_win': team_a_prob,
                'away_win': team_b_prob,
                'draw': draw_prob
            },
            'factors': prediction_factors,
            'team_ratings': {
                team_a: self._rate_performance(team_a_avg['overall_score']),
                team_b: self._rate_performance(team_b_avg['overall_score'])
            }
        }
        
        # Save prediction
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.prediction_path}prediction_{team_a}_vs_{team_b}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(prediction, f)
            
        return prediction

# Usage example
if __name__ == "__main__":
    predictor = KPLMatchPredictor()
    
    # Collect data
    # CHANGE HERE: Use actual match IDs, seasons, or teams
    match_data = predictor.collect_match_data(season="2023-2024")
    
    if match_data:
        # Process collected data
        processed_data = predictor.process_match_data(match_data)
        
        # Example prediction
        # CHANGE HERE: Use actual team names
        prediction = predictor.predict_match("Gor Mahia", "AFC Leopards")
        
        if prediction:
            print("Match Prediction:")
            print(f"Home: {prediction['match']['home_team']} - {prediction['probabilities']['home_win'] * 100:.1f}%")
            print(f"Away: {prediction['match']['away_team']} - {prediction['probabilities']['away_win'] * 100:.1f}%")
            print(f"Draw: {prediction['probabilities']['draw'] * 100:.1f}%")
            
            print("\nTeam Ratings:")
            for team, rating in prediction['team_ratings'].items():
                print(f"{team}: {rating.capitalize()}")