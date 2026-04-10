# Fourth Work Schedule to Calendar

I have written a Python script that automatically fetches your work schedule from the Fourth schedule management system and syncs it to your calendar via a Dropbox hosted `.ics` file.

## What it does

1. Logs into Fourth using Selenium (handles the complex SSO authentication)
2. Grabs the session cookies from the browser and hands them to `requests`
3. Calls the Fourth API directly to fetch your upcoming shifts as JSON
4. Converts the shift data into a `.ics` calendar file
5. Uploads the file to Dropbox so your calendar app can subscribe to it and stay in sync automatically

## Requirements

- Python 3.9+
- Google Chrome 
- A Dropbox account

## Installation

**1. Clone the repository**


**2. Install dependencies(all conveniently stored in 'requirments.txt'**


## Configuration

**1. Create a `.env` file** in the project root:
```
USERNAME=your_fourth_email@example.com
PASSWORD=your_fourth_password
DROPBOX_TOKEN=your_dropbox_app_token
```


## Subscribing your calendar

Once the script has run and uploaded `schedule.ics` to Dropbox:

1. Get the public sharing link for the file from Dropbox
2. In Apple Calendar go to **File → New Calendar Subscription**
3. Paste the Dropbox link and set the refresh interval to whatever you see fit

Your calendar will now automatically update whenever the script runs.

## Automating with cron

To run the script at a certain interval, open your crontab:
```bash
crontab -e
```

Add this line (replace paths with your actual paths):
```
0 8 * * * /Users/yourname/fourth-schedule/.venv/bin/python /Users/yourname/fourth-schedule/main.py
```



## Important notes

- The script fetches shifts for the next **21 days** by default, adjust as you fit
- Shift times are stored in UTC by the Fourth API but displayed in **Europe/London** time (automatically handles GMT/BST switching)
