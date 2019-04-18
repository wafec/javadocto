from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
import logging

WEBSITE = 'https://select-statistics.co.uk/calculators/sample-size-calculator-population-proportion/'
LOGGER = logging.getLogger(__name__)


def sample_size(population_size):
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Firefox(firefox_options=options)
    LOGGER.info('Accessing website "%s"', WEBSITE)
    driver.get(WEBSITE)
    elem = driver.find_element_by_id('population')
    elem.clear()
    elem.send_keys(str(population_size))
    elem.send_keys(Keys.RETURN)
    driver.implicitly_wait(0.5)
    elem = driver.find_element_by_id('sample')
    size = elem.text
    elem = driver.find_element_by_id('margin')
    margin = str(elem.get_attribute('value'))
    elem = driver.find_element_by_id('confidence')
    confidence = str(elem.get_attribute('value'))
    LOGGER.info('Calculator [Margin=%s, Confidence=%s, Population=%s, Sample=%s]',
                margin, confidence, str(population_size), size)
    driver.close()

    return int(size)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(funcName)s: %(message)s')
    sample_size(1000)
