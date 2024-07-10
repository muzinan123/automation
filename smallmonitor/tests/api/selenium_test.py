import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time


class SmallMonitor(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()

    def test_search_in_python_org(self):
        self.driver.get("http://0.0.0.0:2332")
        time.sleep(2)
        self.assertIn("Small Monitor", self.driver.title)
        self.driver.find_element_by_id("filter").send_keys("test6")
        time.sleep(2)
        manager_url = self.driver.find_element_by_name("operation_app").get_attribute("href")
        self.driver.get(manager_url)
        self.assertIn("Manger", self.driver.title)

    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
    unittest.main()
