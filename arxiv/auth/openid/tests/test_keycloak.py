import subprocess
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

@pytest.fixture(scope="module")
def web_driver() -> webdriver.Chrome:
    # Set up the Selenium WebDriver
    # You'd need
    # sudo apt-get update
    # sudo apt-get install -y chromium-browser chromium-chromedriver

    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    service = Service(executable_path="/usr/bin/chromedriver")
    _web_driver = webdriver.Chrome(service=service, options=options)
    _web_driver.implicitly_wait(10)  # Wait for elements to be ready
    yield _web_driver
    _web_driver.quit()  # Close the browser window after tests

@pytest.fixture(scope="module")
def toy_flask():
    flask_app = subprocess.Popen(["python3", "-m", "arxiv.auth.openid.tests.toy_flask"])
    time.sleep(5)  # Give the server time to start
    yield flask_app
    # Stop the Flask app
    flask_app.terminate()
    flask_app.wait()

def test_login(web_driver, toy_flask):
    web_driver.get("http://localhost:5101/login")  # URL of your Flask app's login route

    # Simulate user login on the IdP login page
    # Replace the following selectors with the actual ones from your IdP login form
    username_field = web_driver.find_element(By.ID, "username")  # Example selector
    password_field = web_driver.find_element(By.ID, "password")  # Example selector
    login_button = web_driver.find_element(By.ID, "kc-login")    # Example selector

    # Enter credentials
    username_field.send_keys("testuser")
    password_field.send_keys("testpassword")
    login_button.click()

    # Wait for the redirect back to the Flask app
    time.sleep(5)

    # Check if the login was successful by verifying the presence of a specific element or text
    web_driver.get("http://localhost:5101/protected")  # URL of your protected route
    body_text = web_driver.find_element(By.TAG_NAME, "body").text
    assert "Token is valid" in body_text
