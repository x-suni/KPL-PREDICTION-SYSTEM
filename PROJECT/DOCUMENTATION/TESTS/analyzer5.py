import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
import schedule
import logging

# Configure logging
logging.basicConfig(
    filename='kpl_predictor.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('KPLPredictor')

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
        
        # Initialize automated collection settings
        self.collection_frequency = 24  # hours
        self.auto_collection_enabled = False
        self.scheduler = None
    
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
        base_url = "https://www.sofascore.com/api/v1/unique-tournament/1644/season/65071/events/round/25"
        TEAM_STATS_URL = "https://www.sofascore.com/team/football/{team-name}/{team-id}"
        
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
                
                logger.info(f"Successfully collected data. Saved to {filename}")
                return match_data
            else:
                logger.error(f"Error fetching data: {response.status_code}")
                return None
                
        except Exception as e:
            logger.exception(f"Exception occurred during data collection: {str(e)}")
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
        metrics['saves'] = min(saves, 10)
        
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
            logger.warning(f"No match data found for team {team_name}")
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
            logger.warning(f"No H2H match data found for {team_a} vs {team_b}")
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
        logger.info(f"Generating prediction for {team_a} vs {team_b}")
        
        # Get team averages
        team_a_avg = self.calculate_team_average(team_a)
        team_b_avg = self.calculate_team_average(team_b)
        
        if not team_a_avg or not team_b_avg:
            logger.error(f"Cannot generate prediction: missing team average data")
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
        
        logger.info(f"Prediction saved to {filename}")    
        return prediction
    
    # Automated Data Collection Methods
    
    def _automated_collection_job(self):
        """
        Job that runs on schedule to collect latest match data.
        """
        logger.info("Starting automated data collection job")
        
        # Get current season
        current_year = datetime.now().year
        season = f"{current_year-1}-{current_year}" if datetime.now().month < 8 else f"{current_year}-{current_year+1}"
        
        # Collect data for current season
        match_data = self.collect_match_data(season=season)
        
        if match_data:
            # Process collected data
            processed_data = self.process_match_data(match_data)
            logger.info(f"Processed {len(processed_data)} matches in automated collection")
            
            # Update team averages for all teams
            teams = set()
            for match_id, match in processed_data.items():
                teams.add(match['home_team']['name'])
                teams.add(match['away_team']['name'])
            
            for team in teams:
                self.calculate_team_average(team)
            
            logger.info(f"Updated team averages for {len(teams)} teams")
        else:
            logger.warning("No data collected in automated job")
    
    def start_automated_collection(self, frequency_hours=24):
        """
        Starts automated data collection at specified frequency.
        
        Args:
            frequency_hours (int): How often to collect data (in hours)
        """
        if self.auto_collection_enabled:
            logger.warning("Automated collection already running")
            return
        
        self.collection_frequency = frequency_hours
        self.auto_collection_enabled = True
        
        # Create scheduler
        self.scheduler = schedule.every(frequency_hours).hours.do(self._automated_collection_job)
        
        # Run once immediately
        self._automated_collection_job()
        
        logger.info(f"Automated collection started with {frequency_hours}h frequency")
        
        # Start scheduler in a separate thread
        import threading
        def run_scheduler():
            while self.auto_collection_enabled:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler)
        self.scheduler_thread.daemon = True  # Daemon thread will shut down with main program
        self.scheduler_thread.start()
    
    def stop_automated_collection(self):
        """
        Stops the automated data collection.
        """
        if not self.auto_collection_enabled:
            logger.warning("Automated collection not running")
            return
        
        self.auto_collection_enabled = False
        if self.scheduler:
            schedule.cancel_job(self.scheduler)
            self.scheduler = None
        
        logger.info("Automated collection stopped")
    
    def get_upcoming_fixtures(self, days_ahead=7):
        """
        Gets upcoming fixtures for prediction.
        
        Args:
            days_ahead (int): Number of days to look ahead
            
        Returns:
            list: List of upcoming fixtures
        """
        # CHANGE HERE: Replace with actual API call to get fixtures
        # This is a placeholder implementation
        
        fixtures = []
        
        try:
            # Example URL - replace with actual endpoint
            url = f"https://example-kpl-data-source.com/api/fixtures?days={days_ahead}"
            response = requests.get(url)
            
            if response.status_code == 200:
                fixture_data = response.json()
                
                # Process fixture data
                for fixture in fixture_data.get('fixtures', []):
                    fixtures.append({
                        'date': fixture.get('date'),
                        'home_team': fixture.get('home_team'),
                        'away_team': fixture.get('away_team'),
                        'venue': fixture.get('venue')
                    })
                
                logger.info(f"Retrieved {len(fixtures)} upcoming fixtures")
            else:
                logger.error(f"Failed to get fixtures: {response.status_code}")
                
        except Exception as e:
            logger.exception(f"Error getting fixtures: {str(e)}")
        
        return fixtures
    
    def predict_upcoming_matches(self):
        """
        Predicts outcomes for all upcoming matches.
        
        Returns:
            list: Predictions for upcoming matches
        """
        # Get upcoming fixtures
        fixtures = self.get_upcoming_fixtures()
        
        if not fixtures:
            logger.warning("No upcoming fixtures found to predict")
            return []
        
        # Generate predictions for each fixture
        predictions = []
        for fixture in fixtures:
            home_team = fixture.get('home_team')
            away_team = fixture.get('away_team')
            
            prediction = self.predict_match(home_team, away_team)
            
            if prediction:
                predictions.append({
                    'fixture': fixture,
                    'prediction': prediction
                })
        
        logger.info(f"Generated predictions for {len(predictions)} upcoming matches")
        return predictions

# Usage example
if __name__ == "__main__":
    predictor = KPLMatchPredictor()
    
    # Start automated data collection
    predictor.start_automated_collection(frequency_hours=12)  # Collect data twice daily
    
    # Collect initial data
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
    
    # Get predictions for all upcoming matches
    upcoming_predictions = predictor.predict_upcoming_matches()
    print(f"\nPredicted {len(upcoming_predictions)} upcoming matches")
    
    # Keep running to allow the automated collection to continue
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        predictor.stop_automated_collection()
        print("Predictor stopped")