from flask import Flask, render_template_string, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import datetime
import random

load_dotenv()

TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
PROXYMESH_USERNAME = os.getenv("PROXYMESH_USERNAME")
PROXYMESH_PASSWORD = os.getenv("PROXYMESH_PASSWORD")

app = Flask(__name__)

mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client['twitter_trends']
collection = db['trends']

def fetch_trending_topics():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        proxy = f"http://{PROXYMESH_USERNAME}:{PROXYMESH_PASSWORD}@proxy.proxy-mesh.com:8080"
        chrome_options.add_argument(f'--proxy-server={proxy}')
        
        service = Service("C:\\chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get("https://twitter.com/login")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
        ).send_keys(TWITTER_USERNAME)

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="LoginForm_Login_Button"]'))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "password"))
        ).send_keys(TWITTER_PASSWORD)

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="LoginForm_Login_Button"]'))
        ).click()

        trends = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@data-testid='trend']"))
        )

        trending_topics = [trend.text for trend in trends[:5]]

        now = datetime.datetime.now()

        unique_id = str(random.randint(100000, 999999))

        record = {
            "unique_id": unique_id,
            "trend1": trending_topics[0] if len(trending_topics) > 0 else None,
            "trend2": trending_topics[1] if len(trending_topics) > 1 else None,
            "trend3": trending_topics[2] if len(trending_topics) > 2 else None,
            "trend4": trending_topics[3] if len(trending_topics) > 3 else None,
            "trend5": trending_topics[4] if len(trending_topics) > 4 else None,
            "date_time": now,
            "ip_address": proxy.split('@')[0] if proxy else "No Proxy"
        }

        collection.insert_one(record)
        return record

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

    finally:
        driver.quit()

@app.route('/')
def index():
    return render_template_string('''
    <html>
    <body>
      <h1>Twitter Trends Scraper</h1>
      <button onclick="fetchTrends()">Click here to run the script</button>
      <div id="results"></div>
      <script>
          function fetchTrends() {
              fetch('/fetch-trends')
                  .then(response => response.json())
                  .then(data => {
                      if (data.error) {
                          document.getElementById('results').innerHTML = `<p style="color:red;">${data.error}</p>`;
                      } else {
                          document.getElementById('results').innerHTML =
                              `<p>These are the most happening topics as on ${data.date_time}:</p>
                               <ul>
                                 <li>${data.trend1 || 'N/A'}</li>
                                 <li>${data.trend2 || 'N/A'}</li>
                                 <li>${data.trend3 || 'N/A'}</li>
                                 <li>${data.trend4 || 'N/A'}</li>
                                 <li>${data.trend5 || 'N/A'}</li>
                               </ul>
                               <p>The IP address used for this query was ${data.ip_address}.</p>`;
                      }
                  })
                  .catch(error => {
                      document.getElementById('results').innerHTML = `<p style="color:red;">Error: ${error}</p>`;
                  });
          }
      </script>
    </body>
    </html>
    ''')

@app.route('/fetch-trends')
def fetch_trends():
    record = fetch_trending_topics()
    return jsonify(record)

if __name__ == '__main__':
    app.run(debug=True)
