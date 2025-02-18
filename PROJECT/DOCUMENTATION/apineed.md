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
        self.metrics_weights = {
            'goals_scored': 1.5,
            'possession': 1.0,
            'shots_on_target': 1.2,
            'passes_completed': 0.8,
            'tackles_won': 1.0,
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
        base_url = "https://example-kpl-data-source.com/api/matches"
        
        params = {}
        if match_id:
            params['match_id'] = match_id
        if season:
            params['season'] = season
        if team:
            params['team'] = team
        
        try:
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                match_data = response.json()
                
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
    
    def get_upcoming_fixtures(self, days_ahead=7):
        """
        Gets upcoming fixtures for prediction.
        
        Args:
            days_ahead (int): Number of days to look ahead
            
        Returns:
            list: List of upcoming fixtures
        """
        fixtures = []
        
        try:
            url = f"https://example-kpl-data-source.com/api/fixtures?days={days_ahead}"
            response = requests.get(url)
            
            if response.status_code == 200:
                fixture_data = response.json()
                
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
        fixtures = self.get_upcoming_fixtures()
        
        if not fixtures:
            logger.warning("No upcoming fixtures found to predict")
            return []
        
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
    
    # Collect initial data
    match_data = predictor.collect_match_data(season="2023-2024")
    
    if match_data:
        # Process collected data
        processed_data = predictor.process_match_data(match_data)
        
        # Example prediction
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