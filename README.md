# Printer Monitor

## Overview
The Printer Monitor is a Python-based project designed to monitor the status of printers, including toner levels, waste toner status, and approximate pages remaining. It automates the process of checking printer supplies and sends email notifications when supplies need to be ordered.

## Features
- Monitors multiple printers for:
  - Toner levels (Black, Cyan, Magenta, Yellow)
  - Waste toner status
  - Approximate pages remaining
- Sends email notifications when supplies are low.
- Logs all activities to a log file for tracking and debugging.
- Uses Selenium with WebDriver Manager for dynamic browser automation.
- Uses a YAML configuration file (`printers.yaml`) for easy management of printer details.

## Requirements
- Python 3.8 or higher
- Dependencies listed in `requirements.txt`:
  - `selenium`
  - `webdriver-manager`
  - `beautifulsoup4`
  - `google-api-python-client`
  - `google-auth`
  - `google-auth-oauthlib`
  - `python-dotenv`
  - `pyyaml`

## Setup
1. Clone the repository:
   ```bash
   git clone git@github.com:danr-pp/PrinterMonitor.git
   cd PrinterMonitor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Create a `.env` file in the project root.
   - Add the following variables:
     ```env
     MAIL_CREDENTIALS_PATH=path/to/credentials.json
     MAIL_TOKEN_PATH=path/to/token.json
     LOG_FILE_PATH=Logs/logfile.txt
     ```

4. Add your Google API credentials:
   - Place `credentials.json` in the project root.
   - Follow the [Google API setup guide](https://developers.google.com/gmail/api/quickstart/python) to enable Gmail API and download credentials.

5. Configure your printers in `printers.yaml`:
   - Edit the `printers.yaml` file to add, remove, or update printer details.
   - Example structure:
     ```yaml
     printers:
       - name: M404dn
         url: "http://randys/#hId-pgConsumables"
         model: "HP 58A (CF258A)"
         type: "pages_remaining"
         threshold: 1000

       - name: M402
         url: "http://npia601d3/info_suppliesStatus.html?tab=Home&menu=SupplyStatus"
         model: "26X (CF226X)"
         type: "toner"
         xpath: "/html/body/div[2]/table/tbody/tr[2]/td[2]/div[2]/table/tbody/tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[1]/td/table/tbody/tr/td[3]"
         threshold: 8

       - name: MFP
         url: "http://192.168.101.8/info_suppliesStatus.html?tab=Home&menu=SupplyStatus"
         model_numbers:
           Black: "CE400X"
           Cyan: "CE401A"
           Magenta: "CE403A"
           Yellow: "CE402A"
         type: "mfp"
         toner_threshold: 15
         waste_toner_model: "CE254A"
     ```

## Usage
Run the script to monitor printer supplies:
```bash
python printer_status.py
```

## Logging
All activities are logged in `Logs/logfile.txt`. The log includes timestamps and details about printer statuses and email notifications.

## Notes
- Ensure that the printers are accessible via the network.
- The script uses Selenium to scrape printer web pages for toner levels and statuses.
- You can easily update printer details in `printers.yaml` without modifying the code.

## License
This project is licensed under the MIT License. See the LICENSE file for details.