from selenium import webdriver
import unittest

import source_navigation_steps
import functional_test


class SourceInterfaceBannerWarnings(
        unittest.TestCase,
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps):

    def setUp(self):
        functional_test.FunctionalTest.setUp(self)

    def tearDown(self):
        functional_test.FunctionalTest.tearDown(self)

    def test_warning_appears_if_tor_browser_not_in_use(self):
        self.driver.get(self.source_location)

        warning_banner = self.driver.find_element_by_class_name('use-tor-browser')

        self.assertIn("We recommend using Tor Browser to access SecureDrop",
                      warning_banner.text)

    def test_turn_slider_to_high_in_warning(self):
        # Simulate Tor Browser
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override",
            "Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0")
        driver = webdriver.Firefox(profile)
        driver.delete_all_cookies()

        driver.get(self.source_location)

        warning_banner = driver.find_element_by_class_name('js-warning')

        self.assertIn("We recommend turning the Security Slider to High to protect your anonymity",
                      warning_banner.text)
