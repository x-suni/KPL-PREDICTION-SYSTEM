import json
import re
import pandas as pd
import sys

try:
    from google.colab import files  # Import Google Colab-specific module
except ImportError:
    files = None
import matplotlib.pyplot as plt
import seaborn as sns

data = """
{
    "standings": [
        {
            "tournament": {
                "name": "Premier League",
                "slug": "premier-league",
                "category": {
                    "name": "Kenya",
                    "slug": "kenya",
                    "sport": {
                        "name": "Football",
                        "slug": "football",
                        "id": 1
                    },
                    "id": 805,
                    "flag": "kenya",
                    "alpha2": "KE"
                },
                "uniqueTournament": {
                    "name": "Kenyan Premier League",
                    "slug": "premier-league",
                    "primaryColorHex": "#eb1a23",
                    "secondaryColorHex": "#3ebc7a",
                    "category": {
                        "name": "Kenya",
                        "slug": "kenya",
                        "sport": {
                            "name": "Football",
                            "slug": "football",
                            "id": 1
                        },
                        "id": 805,
                        "flag": "kenya",
                        "alpha2": "KE"
                    },
                    "userCount": 6271,
                    "id": 1644,
                    "hasPerformanceGraphFeature": true,
                    "displayInverseHomeAwayTeams": false
                },
                "priority": 0,
                "isGroup": false,
                "isLive": false,
                "id": 17654
            },
            "type": "total",
            "name": "Premier League 24/25",
            "descriptions": [],
            "tieBreakingRule": {
                "text": "In the event that two (or more) teams have an equal number of points, the following rules break the tie:\n1. Goal difference\n2. Goals scored",
                "id": 1238
            },
            "rows": [
                {
                    "team": {
                        "name": "Kenya Police",
                        "slug": "kenya-police",
                        "userCount": 1795,
                        "id": 291904,
                        "teamColors": {
                            "primary": "#374df5",
                            "secondary": "#374df5",
                            "text": "#ffffff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Tusker Football Club",
                        "slug": "tusker",
                        "userCount": 2793,
                        "id": 138496,
                        "teamColors": {
                            "primary": "#ffdf00",
                            "secondary": "#000000",
                            "text": "#000000"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Gor Mahia FC",
                        "slug": "gor-mahia-fc",
                        "userCount": 7219,
                        "id": 134306,
                        "teamColors": {
                            "primary": "#008000",
                            "secondary": "#000000",
                            "text": "#000000"
                        }
                    }
                },
                {
                    "team": {
                        "name": "AFC Leopards SC",
                        "slug": "afc-leopards-sc",
                        "userCount": 2381,
                        "id": 76433,
                        "teamColors": {
                            "primary": "#ffffff",
                            "secondary": "#0000ff",
                            "text": "#0000ff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Kenya Commercial Bank",
                        "slug": "kenya-commercial-bank",
                        "userCount": 1851,
                        "id": 138478,
                        "teamColors": {
                            "primary": "#00dd00",
                            "secondary": "#004165",
                            "text": "#004165"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Bandari FC",
                        "slug": "bandari-fc",
                        "userCount": 1536,
                        "id": 138474,
                        "teamColors": {
                            "primary": "#3050c6",
                            "secondary": "#ffffff",
                            "text": "#ffffff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Kakamega Homeboyz",
                        "slug": "kakamega-homeboyz",
                        "userCount": 1243,
                        "id": 213604,
                        "teamColors": {
                            "primary": "#fee34f",
                            "secondary": "#2b924d",
                            "text": "#2b924d"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Shabana FC",
                        "slug": "shabana-fc",
                        "userCount": 2156,
                        "id": 332880,
                        "teamColors": {
                            "primary": "#374df5",
                            "secondary": "#374df5",
                            "text": "#ffffff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Sofapaka",
                        "slug": "sofapaka",
                        "userCount": 1161,
                        "id": 138488,
                        "teamColors": {
                            "primary": "#ffffff",
                            "secondary": "#0000ff",
                            "text": "#0000ff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Ulinzi Stars",
                        "slug": "ulinzi-stars",
                        "userCount": 1082,
                        "id": 138498,
                        "teamColors": {
                            "primary": "#ff0000",
                            "secondary": "#ffffff",
                            "text": "#ffffff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Mara Sugar FC",
                        "slug": "mara-sugar-fc",
                        "userCount": 598,
                        "id": 815035,
                        "teamColors": {
                            "primary": "#374df5",
                            "secondary": "#374df5",
                            "text": "#ffffff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Kariobangi Sharks",
                        "slug": "kariobangi-sharks",
                        "userCount": 1118,
                        "id": 246032,
                        "teamColors": {
                            "primary": "#45c283",
                            "secondary": "#f8d815",
                            "text": "#f8d815"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Muranga Seal",
                        "slug": "muranga-seal",
                        "userCount": 1117,
                        "id": 332427,
                        "teamColors": {
                            "primary": "#374df5",
                            "secondary": "#374df5",
                            "text": "#ffffff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Mathare United",
                        "slug": "mathare-united",
                        "userCount": 805,
                        "id": 138482,
                        "teamColors": {
                            "primary": "#ffff00",
                            "secondary": "#006600",
                            "text": "#006600"
                        }
                    }
                },
                {
                    "team": {
                        "name": "FC Talanta",
                        "slug": "fc-talanta",
                        "userCount": 1174,
                        "id": 310815,
                        "teamColors": {
                            "primary": "#374df5",
                            "secondary": "#374df5",
                            "text": "#ffffff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Posta Rangers",
                        "slug": "posta-rangers",
                        "userCount": 1222,
                        "id": 213605,
                        "teamColors": {
                            "primary": "#c71328",
                            "secondary": "#ffffff",
                            "text": "#ffffff"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Bidco United",
                        "slug": "bidco-united",
                        "userCount": 1210,
                        "id": 258735,
                        "teamColors": {
                            "primary": "#ffffff",
                            "secondary": "#4ba7df",
                            "text": "#4ba7df"
                        }
                    }
                },
                {
                    "team": {
                        "name": "Nairobi City Stars FC",
                        "slug": "nairobi-city-stars-fc",
                        "userCount": 872,
                        "id": 138486,
                        "teamColors": {
                            "primary": "#273887",
                            "secondary": "#f74f00",
                            "text": "#f74f00"
                        }
                    }
                }
            ],
            "id": 132068,
            "updatedAtTimestamp": 1723025186
        }
    ]
}
"""
parsed_data = json.loads(data)

# Extract the required information
teams_info = []
for row in parsed_data['standings'][0]['rows']:
    team = row['team']
    team_info = {
        'name': team['name'],
        'userCount': team['userCount'],
        'id': team['id'],
        'teamColors': team['teamColors']
    }
    teams_info.append(team_info)

# Convert the list of dictionaries to a pandas DataFrame for better visualization
teams_df = pd.DataFrame(teams_info)

# Display the extracted information as a DataFrame
print("Teams in the Kenyan Premier League:")
print(teams_df)

# Visualize the team popularity (userCount)
plt.figure(figsize=(12, 6))
sns.barplot(x='name', y='userCount', data=teams_df)
plt.title('Team Popularity in Kenyan Premier League')
plt.xlabel('Team')
plt.ylabel('User Count')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# Save the extracted information to a CSV file
teams_df.to_csv('kpl_teams_info.csv', index=False)
print("\nData saved to 'kpl_teams_info.csv'")

# Allow the user to download the CSV file
try:
    files.download('kpl_teams_info.csv')
    print("Download link for CSV file generated. Click to download.")
except:
    print("NOTE: File download works only in Google Colab. Run this in Colab to enable downloading.")

# If you want to save to Google Drive instead (uncomment if drive is mounted)
# teams_df.to_csv('/content/drive/My Drive/kpl_teams_info.csv', index=False)
# print("Data saved to Google Drive as 'kpl_teams_info.csv'")

# Function to export teams data to JSON file
def export_to_json(data, filename='kpl_teams_info.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"\nData saved to '{filename}'")
    
    # Allow the user to download the JSON file
    try:
        files.download(filename)
        print(f"Download link for {filename} generated. Click to download.")
    except:
        print(f"NOTE: File download works only in Google Colab. Run this in Colab to enable downloading.")

# Export the teams data to JSON
export_to_json(teams_info)

# Print summary statistics
print("\nSummary Statistics:")
print(f"Total number of teams: {len(teams_info)}")
print(f"Team with most followers: {teams_df.loc[teams_df['userCount'].idxmax()]['name']} ({teams_df['userCount'].max()} users)")
print(f"Team with least followers: {teams_df.loc[teams_df['userCount'].idxmin()]['name']} ({teams_df['userCount'].min()} users)")
print(f"Average number of followers per team: {teams_df['userCount'].mean():.2f}")

# Function to get team IDs for further scraping
def get_team_ids():
    return {team['name']: team['id'] for team in teams_info}

team_ids = get_team_ids()
print("\nTeam IDs for API requests:")
for name, id in team_ids.items():
    print(f"{name}: {id}")

# Note: The actual web scraping with Selenium requires additional setup in Colab
print("\nNOTE: To use Selenium in Google Colab, you need to install the Chrome webdriver")
print("Run this command to install webdriver and selenium: !pip install selenium webdriver-manager")
print("Then use the following code to initialize the driver:")
print("""
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
""")