```python
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import Select
    from datetime import datetime
    import time
    import os
    import logging

    class VisaAppointmentBot:
        def __init__(self):
            self.setup_logging()
            self.driver = self.setup_driver()
            self.wait = WebDriverWait(self.driver, 30)
            self.base_url = "https://ais.usvisa-info.com/tr-tr/niv/groups/46114340"
            self.appointment_url = "https://ais.usvisa-info.com/tr-tr/niv/schedule/64807632/appointment"
            self.current_appointment_date = None
            self.screenshots_dir = "screenshots"
            os.makedirs(self.screenshots_dir, exist_ok=True)

        def setup_logging(self):
            logging.basicConfig(filename='visa_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            self.logger = logging

        def setup_driver(self):
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-notifications')
            service = Service('/usr/bin/chromedriver')
            return webdriver.Chrome(service=service, options=chrome_options)

        def take_screenshot(self, name):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.screenshots_dir}/{name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot saved: {filename}")

        def login(self):
            self.logger.info("Logging in...")
            self.driver.get("https://ais.usvisa-info.com/tr-tr/niv/users/sign_in")
            self.wait.until(EC.presence_of_element_located((By.ID, "user_email"))).send_keys("turhanhamza@gmail.com")
            self.driver.find_element(By.ID, "user_password").send_keys("7234459Qwee.")
            self.driver.execute_script("arguments[0].click();", self.driver.find_element(By.NAME, "policy_confirmed"))
            self.driver.find_element(By.NAME, "commit").click()
            self.logger.info("Login successful!")

        def get_current_date(self):
            self.logger.info("Retrieving current appointment date...")
            self.driver.get(self.base_url)
            date_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.consular-appt strong")))
            date_text_node = self.driver.execute_script('return arguments[0].nextSibling.textContent;', date_element).strip()
            date_str = date_text_node.split(" Ankara")[0].strip()

            tr_months = {
                'Ocak': 'January', 'Şubat': 'February', 'Mart': 'March',
                'Nisan': 'April', 'Mayıs': 'May', 'Haziran': 'June',
                'Temmuz': 'July', 'Ağustos': 'August', 'Eylül': 'September',
                'Ekim': 'October', 'Kasım': 'November', 'Aralık': 'December'
            }

            for tr, eng in tr_months.items():
                date_str = date_str.replace(tr, eng)

            self.current_appointment_date = datetime.strptime(date_str, "%d %B, %Y, %H:%M")
            self.logger.info(f"Current appointment date: {self.current_appointment_date.strftime('%d %B %Y, %H:%M')}")

        def find_earlier_date(self):
            self.logger.info("Checking for earlier appointment...")
            self.driver.get(self.appointment_url)
            self.wait.until(EC.presence_of_element_located((By.ID, "appointments_consulate_appointment_facility_id")))
            Select(self.driver.find_element(By.ID, "appointments_consulate_appointment_facility_id")).select_by_visible_text("Ankara")
            self.driver.find_element(By.ID, "appointments_consulate_appointment_date").click()

            months_checked = 0
            while months_checked < 24:
                active_dates = self.driver.find_elements(By.CSS_SELECTOR, "td.day:not(.disabled)")
                if active_dates:
                    first_date = active_dates[0]
                    date_str = first_date.get_attribute('data-date')
                    available_date = datetime.strptime(date_str, '%Y-%m-%d')

                    if available_date.date() < self.current_appointment_date.date():
                        first_date.click()
                        self.logger.info("Earlier date found and selected")
                        self.wait.until(EC.presence_of_element_located((By.ID, "appointments_consulate_appointment_time")))
                        Select(self.driver.find_element(By.ID, "appointments_consulate_appointment_time"))
                        self.driver.find_element(By.NAME, "commit").click()
                        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'button alert')]"))).click()
                        self.logger.info("New appointment successfully created!")
                        return True

                next_month_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ui-datepicker-next")))
                if "ui-state-disabled" in next_month_button.get_attribute("class"):
                    self.logger.info("Reached the last available month")
                    break

                next_month_button.click()
                time.sleep(1)
                months_checked += 1

            self.logger.info("No earlier appointment found within the next two years.")
            return False

        def run(self):
            try:
                self.login()
                self.get_current_date()
                attempt = 1
                while True:
                    self.logger.info(f"Attempt {attempt} starting...")
                    if self.find_earlier_date():
                        self.logger.info("Success! An earlier appointment was found and scheduled.")
                        break
                    self.logger.info("Retrying in 3 minutes...")
                    time.sleep(180)
                    attempt += 1
            except Exception as e:
                self.logger.error(f"Critical error: {str(e)}")
                self.take_screenshot("critical_error")
                raise

    if __name__ == "__main__":
        bot = VisaAppointmentBot()
        bot.run()

    ```
