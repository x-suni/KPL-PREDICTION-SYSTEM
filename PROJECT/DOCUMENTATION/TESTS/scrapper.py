import os
import json
import time
import logging
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    filename='sofascore_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SofaScoreScraper:
    def __init__(self):
        """Initialize the SofaScore scraper with necessary configurations."""
        # URLs
        self.base_url = "https://www.sofascore.com"
        self.kpl_url = f"https://www.sofascore.com/tournament/football/kenya/premier-league/"
        
        # Setup chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Run in headless mode
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        
        # User agent to mimic a real browser
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
        
        # Initialize the WebDriver
        service = Service()  # Assumes ChromeDriver is in PATH
        self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
        
        # Create data directory if it doesn't exist
        self.data_dir = "sofascore_data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Team IDs mapping (to be populated)
        self.team_ids = {}
        
        logging.info("SofaScore scraper initialized successfully")

    def get_team_ids(self):
        """Extract team IDs from the league page for individual team page navigation."""
        try:
            self.driver.get(self.kpl_url)
            time.sleep(5)  # Allow page to load
            
            # Wait for the standings table to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='standings-table']"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            standings_rows = soup.select("div[data-test-id='standings-table'] > div > a")
            
            for row in standings_rows:
                team_link = row.get('href')
                if team_link and '/team/football/' in team_link:
                    parts = team_link.split('/')
                    team_name = parts[-2]
                    team_id = parts[-1]
                    self.team_ids[team_name] = team_id
                    logging.info(f"Found team: {team_name} with ID: {team_id}")
            
            logging.info(f"Extracted IDs for {len(self.team_ids)} teams")
            return self.team_ids
        
        except Exception as e:
            logging.error(f"Error extracting team IDs: {str(e)}")
            return {}

    def scrape_match_results(self):
        """Scrape recent match results from the Kenyan Premier League."""
        try:
            # Navigate to the KPL page
            self.driver.get(f"{self.kpl_url}/results")
            time.sleep(5)  # Allow page to load
            
            # Wait for match results to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.sc-fqkvVR"))
            )
            
            # Extract match data
            match_data = []
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            match_containers = soup.select("div.sc-fqkvVR")  # Adjust selector based on actual page structure
            
            for container in match_containers:
                try:
                    # Extract match date
                    date_element = container.select_one("div.sc-gJjCVZ")
                    if date_element:
                        match_date = date_element.text.strip()
                    else:
                        match_date = "Unknown Date"
                    
                    # Extract individual matches
                    matches = container.select("a.sc-jXbUNg")
                    for match in matches:
                        try:
                            # Extract team names
                            teams = match.select("div.sc-iGgWBj")
                            if len(teams) >= 2:
                                home_team = teams[0].text.strip()
                                away_team = teams[1].text.strip()
                            else:
                                continue
                            
                            # Extract score
                            score_element = match.select_one("div.sc-fHjqPf")
                            if score_element:
                                score = score_element.text.strip()
                            else:
                                score = "0-0"  # Default if not found
                            
                            # Combine data
                            match_info = {
                                "home_team": home_team,
                                "away_team": away_team,
                                "score": score,
                                "date": match_date
                            }
                            match_data.append(match_info)
                            
                        except Exception as inner_e:
                            logging.warning(f"Error processing individual match: {str(inner_e)}")
                            continue
                
                except Exception as e:
                    logging.warning(f"Error processing match container: {str(e)}")
                    continue
            
            # Save match data to JSON
            self._save_to_json(match_data, "match_results.json")
            logging.info(f"Successfully scraped {len(match_data)} matches")
            return match_data
        
        except Exception as e:
            logging.error(f"Error scraping match results: {str(e)}")
            return []

    def scrape_team_performance(self, team_name, team_id):
        """Scrape detailed performance metrics for a specific team."""
        try:
            team_url = f"{self.base_url}/team/football/{team_name}/{team_id}"
            self.driver.get(team_url)
            time.sleep(5)  # Allow page to load
            
            # Wait for team stats to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.sc-fqkvVR"))
            )
            
            # Extract team stats
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Recent form
            form_data = []
            form_elements = soup.select("div.sc-jXbUNg")
            for form in form_elements[:5]:  # Get last 5 matches
                result_text = form.text.strip()
                form_data.append(result_text)
            
            # General statistics
            stats = {}
            stat_containers = soup.select("div.sc-gqUVxD")
            for container in stat_containers:
                stat_name_elem = container.select_one("div.sc-cyRTDc")
                stat_value_elem = container.select_one("div.sc-jWquRx")
                
                if stat_name_elem and stat_value_elem:
                    stat_name = stat_name_elem.text.strip()
                    stat_value = stat_value_elem.text.strip()
                    stats[stat_name] = stat_value
            
            # Combine all team performance data
            performance_data = {
                "team_name": team_name,
                "team_id": team_id,
                "recent_form": form_data,
                "statistics": stats,
                "scraped_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Save team performance data
            self._save_to_json(performance_data, f"{team_name}_stats.json")
            logging.info(f"Successfully scraped performance data for {team_name}")
            return performance_data
        
        except Exception as e:
            logging.error(f"Error scraping team performance for {team_name}: {str(e)}")
            return None

    def scrape_all_team_performances(self):
        """Scrape performance data for all teams in the league."""
        if not self.team_ids:
            self.get_team_ids()
        
        all_team_data = {}
        for team_name, team_id in self.team_ids.items():
            team_data = self.scrape_team_performance(team_name, team_id)
            if team_data:
                all_team_data[team_name] = team_data
            
            # Sleep to avoid overloading the server
            time.sleep(3)
        
        # Save combined data
        self._save_to_json(all_team_data, "all_teams_performance.json")
        logging.info(f"Completed scraping performance data for {len(all_team_data)} teams")
        return all_team_data

    def _save_to_json(self, data, filename):
        """Save data to a JSON file in the data directory."""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"Data saved successfully to {filepath}")
        except Exception as e:
            logging.error(f"Error saving data to {filepath}: {str(e)}")

    def run_full_scrape(self):
        """Run a complete scraping process for all available data."""
        try:
            logging.info("Starting full scrape process")
            
            # Get team IDs first
            self.get_team_ids()
            
            # Scrape match results
            match_data = self.scrape_match_results()
            
            # Scrape all team performances
            team_data = self.scrape_all_team_performances()
            
            logging.info("Full scrape completed successfully")
            return {
                "match_data": match_data,
                "team_data": team_data
            }
        
        except Exception as e:
            logging.error(f"Error during full scrape: {str(e)}")
            return None
        
        finally:
            # Always close the driver when done
            self.close()

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            logging.info("WebDriver closed successfully")


if __name__ == "__main__":
    try:
        # Initialize and run the scraper
        scraper = SofaScoreScraper()
        results = scraper.run_full_scrape()
        
        if results:
            print(f"Scrape completed successfully!")
            print(f"Collected data for {len(results['match_data'])} matches")
            print(f"Collected performance data for {len(results['team_data'])} teams")
        else:
            print("Scrape failed. Check logs for details.")
    
    except Exception as e:
        logging.critical(f"Critical error in main execution: {str(e)}")
        print(f"An error occurred: {str(e)}")