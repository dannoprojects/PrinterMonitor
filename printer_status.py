import os
import time
import datetime
import re
import base64
import yaml

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def log_status(message, log_file=os.getenv("LOG_FILE_PATH")):
    """
    Append a status message to a log file with the current time and date.

    Args:
        message (str): The status message to log.
        log_file (str): Path to the log file. Default is 'script_log.txt'.
    """
    with open(log_file, "a") as file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - {message}\n")



def send_email(subject, body, recipient, sender, credentials_path=os.getenv("MAIL_CREDENTIALS_PATH"), token_path=os.getenv("MAIL_TOKEN_PATH")):
    """
    Send an email with the given subject and body.

    Args:
        subject (str): The subject of the email.
        body (str): The body content of the email.
        recipient (str): The recipient email address.
        sender (str): The sender email address.
        credentials_path (str): Path to the credentials.json file.
        token_path (str): Path to the token.json file.
    """
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    message = MIMEText(body)
    message['to'] = recipient
    message['from'] = sender
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        sent_message = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(f"Message sent! ID: {sent_message['id']}")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_mfp_toner_levels(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful
    soup = BeautifulSoup(response.text, 'html.parser')
    toner_levels = {}
    
    # Find all toner cartridges information blocks
    main_content = soup.find_all('table', class_='mainContentArea')

    for content in main_content:
        # Get cartridge name (e.g., Black Cartridge)
        cartridge_name_tag = content.find('td', class_='SupplyName width65')
        if cartridge_name_tag:
            cartridge_name = cartridge_name_tag.text.strip().split('\n')[0]
        else:
            continue

        # Get toner level (e.g., 70%)
        toner_level_tag = content.find('td', class_='SupplyName width35 alignRight')
        if toner_level_tag:
            toner_level_text = toner_level_tag.text.strip().replace('%', '').replace('*', '')  # Remove % and *
            try:
                toner_level = int(toner_level_text)
            except ValueError:
                toner_level = -1
        else:
            toner_level = -1

        toner_levels[cartridge_name] = toner_level
    return toner_levels

def find_toner_collection_status(url):
    # Fetch the webpage
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve webpage. Status code: {response.status_code}")

    content = response.text

    # Parse the HTML
    soup = BeautifulSoup(content, 'html.parser')

    # Look for the Toner Collection Unit status in the table
    tables = soup.find_all('table', class_='mainContentArea')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2 and cells[0].text.strip() == 'Status:':
                return cells[1].text.strip()

    return "Status not found"

def get_M402_toner_status(url, xpath):
    # Configure Selenium WebDriver
    options = Options()
    options.headless = True  # Run in headless mode
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Load the page
        driver.get(url)

        # Wait for the element to load and extract the text
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        toner_percentage_text = driver.find_element(By.XPATH, xpath).text.strip()
        
        # Clean the extracted text to retain only the numeric part
        toner_percentage_cleaned = re.search(r'\d+', toner_percentage_text)
        if toner_percentage_cleaned:
            return int(toner_percentage_cleaned.group())
        else:
            print("No numeric value found in the extracted text.")
            return None
    except Exception as e:
        print(f"Error fetching toner status: {e}")
        return None
    finally:
        driver.quit()

def get_M404dn_pages_remaining(url):
    # Set up Selenium with headless Chrome
    options = Options()
    options.headless = True  # Run Chrome in headless mode (no GUI)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Open the printer page
        driver.get(url)
        time.sleep(2)  # Wait for the page to load

        # Use querySelector to locate the element
        js_script = 'return document.querySelector("#appConsumable-inkCart-tbl-Tbl > tbody > tr:nth-child(8) > td:nth-child(2)").innerText;'
        pages_remaining = driver.execute_script(js_script)
        
        # Convert to integer
        return int(pages_remaining.strip())
    except Exception as e:
        raise ValueError(f"Error: {e}")
    finally:
        driver.quit()

def load_config(path="printers.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

# Main program
if __name__ == "__main__":
    config = load_config()
    email_body = "Order Printer Supplies:\n\n"
    mail_credentials = os.getenv("MAIL_CREDENTIALS_PATH")
    mail_token = os.getenv("MAIL_TOKEN_PATH")
    log_file = os.getenv("LOG_FILE_PATH")
    log_status("Supply monitor started.")

    for printer in config["printers"]:
        if printer["type"] == "pages_remaining":
            try:
                pages_remaining = get_M404dn_pages_remaining(printer["url"])
                if pages_remaining < printer["threshold"]:
                    email_body += f"{printer['name']} Approximate Pages Remaining: {pages_remaining}\n"
                    email_body += f"Order {printer['model']}\n\n"
                else:
                    log_status(f"{printer['name']} Approximate Pages Remaining: {pages_remaining}")
            except Exception as e:
                print(f"Error: {e}")
                email_body += f"{printer['name']} Error: {e}\n"
        elif printer["type"] == "toner":
            try:
                black_toner_percentage = get_M402_toner_status(printer["url"], printer["xpath"])
                if black_toner_percentage is not None:
                    if black_toner_percentage <= printer["threshold"]:
                        print(f"{printer['name']} Black toner percentage: {black_toner_percentage}%")
                        email_body +=f"{printer['name']} Black toner percentage: {black_toner_percentage}%\n"
                        email_body +=f"Order {printer['model']}\n\n"
                    else:
                        log_status(f"{printer['name']} Black toner percentage: {black_toner_percentage}%")
                else:
                    print("Unable to determine the black toner percentage.")
            except Exception as e:
                print(f"Error: {e}")
                email_body += f"{printer['name']} Error: {e}\n"
        elif printer["type"] == "mfp":
            status = find_toner_collection_status(printer["url"])
            if status != "Normal":
                email_body += f"MFP Toner Collection Unit Status: {status}\n"
                email_body += f"Order {printer['waste_toner_model']} for HP M570dn\n\n"
            else:
                log_status("Waste Toner is normal")
            toners = get_mfp_toner_levels(printer["url"])
            toners.popitem()
            for cartridge, level in toners.items():
                if level <= printer["toner_threshold"]:
                    model_number = printer["model_numbers"].get(cartridge.split()[0], "Unknown Model")
                    email_body += f"MFP {cartridge} ({model_number}): {level}%\n"
                else:
                    log_status(f"MFP {cartridge}: {level}")
    # Only send email if supplies are needed.
    if len(email_body.splitlines()) > 2:
        log_status("send email")
        send_email("Printer Monitoring Report: Order Supplies", email_body, 'drowe@projectp.com', 'drowe@projectp.com', mail_credentials, mail_token)
    else:
        log_status("no email sent")
    log_status("Supply monitor completed.")

