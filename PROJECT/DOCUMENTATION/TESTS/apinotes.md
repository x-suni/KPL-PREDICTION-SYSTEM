# SofaScore Scraper Documentation

## Overview
The **SofaScore Scraper** is a Python-based tool that extracts match results, team statistics, and performance trends from the **Kenyan Premier League (KPL)** section on **SofaScore**. This scraper collects structured football data using **Selenium** and **BeautifulSoup**, saving it in **JSON format** for further analysis, such as predictions and performance tracking.

## Features
- **Match Data Extraction**: Fetches match results, including team names, scores, and match date.
- **Team Performance Chart**: Retrieves team stats like possession, shots on target, and other relevant metrics.
- **Automated Data Storage**: Saves extracted data in structured JSON files.
- **Headless Scraping**: Uses Selenium in headless mode to load JavaScript-driven content.
- **Error Logging**: Implements logging to track errors and issues.

## Installation
Before running the scraper, install the required dependencies:

```bash
pip install selenium beautifulsoup4 requests pandas
```

You also need **ChromeDriver** for Selenium. Download it from:
[https://sites.google.com/chromium.org/driver/](https://sites.google.com/chromium.org/driver/)

## Project Structure
```
sofascore_scraper/
│── sofascore_scraper.py  # Main script
│── sofascore_data/        # Folder for storing JSON data
│── sofascore_scraper.log  # Log file
```

## Configuration
The script is set to scrape data from the following sources:
- **Match Data URL**: `https://www.sofascore.com/tournament/football/kenya/premier-league/`
- **Team Performance URL**: `https://www.sofascore.com/team/football/{team-name}/{team-id}`

## How the Scraper Works
### 1. Scraping Match Data
- The script navigates to the **Kenyan Premier League** page on **SofaScore**.
- Extracts match details such as:
  - Home Team
  - Away Team
  - Match Score
  - Match Date
- Saves this data in `sofascore_data/match_results.json`.

### 2. Scraping Team Performance
- The script visits each team's performance page.
- Extracts statistical metrics such as:
  - Possession Percentage
  - Shots on Target
  - Pass Accuracy
  - Expected Goals (xG)
- Saves performance data in `sofascore_data/{team_name}_stats.json`.

### 3. Data Storage
Extracted data is saved in JSON format inside the `sofascore_data/` folder:
```json
{
    "home_team": "Gor Mahia",
    "away_team": "AFC Leopards",
    "score": "2-1",
    "date": "2025-02-18"
}
```

### 4. Error Handling & Logging
- Logs errors and warnings in `sofascore_scraper.log`.
- Skips incomplete match entries to prevent corrupted data.

## Running the Scraper
To run the scraper, execute:
```bash
python sofascore_scraper.py
```

## Future Enhancements
- Automate daily scraping using a **cron job**.
- Store data in **CSV or a database** for better analysis.
- Implement **Selenium stealth mode** to avoid detection.

## Troubleshooting
| Issue | Solution |
|--------|------------|
| No matches found | Ensure the page structure hasn't changed. Update class names if necessary. |
| Selenium error | Verify that ChromeDriver is installed and up-to-date. |
| Scraper blocked | Reduce request frequency or implement stealth techniques. |

## Conclusion
This scraper automates data extraction from SofaScore, allowing you to analyze **Kenyan Premier League** match performance. Modify it further to integrate with prediction models or betting analytics systems.

---
For questions or enhancements, feel free to ask! 🚀

