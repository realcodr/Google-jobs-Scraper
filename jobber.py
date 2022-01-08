import datetime
import logging
import os
import pprint
import random
import time
from pathlib import Path

from openpyxl import Workbook
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class GoogleSearchPageLocators:
	anchor_tags = 'g-card a'


class GoogleJobsPageLocators:
	clear_search_button = 'button[aria-label="Clear search"]'
	search_button = 'button[aria-label="Search"]'
	search_input_element = "hs-qsb"
	jobs_cards = 'li'
	result_title = '[role="heading"]'
	date_and_time = '[class*=KKh3md] span'
	publisher = '[class*=vNEEBe]'


class TimeKeeper:
	@property
	def now(self):
		'''
		return the current correct date and time using the format specified
		'''
		return f'{datetime.datetime.now():%d-%b-%Y T%I:%M}'


class Writer:
	def __init__(self, filename):
		self.filename = filename


class XlsxWriter(Writer):
	def __init__(self, filename='output'):
		super().__init__(filename)
		self.file_type = '.xlsx'
		self.fields = [
						"Date & time of search",
						"Keyword",
						"Publisher",
						"Result_Title",
						"Date/Time",
					]
		self.check_filename()
		self.open_an_active_sheet()
		self.write_sheet_headers()


	def __repr__(self):
		return self.filename


	def check_filename(self):
		if self.file_type not in self.filename:
			self.filename += self.file_type
	

	def open_an_active_sheet(self):
		self.workbook = Workbook()
		self.sheet = self.workbook.active


	def close_workbook(self):
		self.workbook.save(filename=self.filename)


	def write_sheet_headers(self):
		self.sheet['A1'].value = self.fields[0]
		self.sheet['B1'].value = self.fields[1]
		self.sheet['C1'].value = self.fields[2]
		self.sheet['D1'].value = self.fields[3]
		self.sheet['E1'].value = self.fields[4]


	def write_to_sheet(self, dictionary):
		try:
			value = self.sheet.max_row + 1
			self.sheet[f'A{value}'].value = dictionary.get("Date & time of search")
			self.sheet[f'B{value}'].value = dictionary.get("Keyword")
			self.sheet[f'C{value}'].value = dictionary.get("Publisher")
			self.sheet[f'D{value}'].value = dictionary.get("Result_Title")
			self.sheet[f'E{value}'].value = dictionary.get("Date/Time")
		finally:
			self.close_workbook()


class FileReader:	
	@staticmethod
	def accept_filename():
		# filename = input("\aEnter a valid filename: ")
		filename = 'keywords.txt'
		return filename


	@property
	def file_content(self):
		filename = self.accept_filename()
		path_object = Path(filename)
		if path_object.exists():
			print(f"{filename} found...")
			with path_object.open() as file_handler:
				content = [ line.strip() for line in file_handler.readlines() ]
				if content:
					return content
				else:
					print("\aNo keywords in the file specified")
		else:
			print("\aYou might have to check the file name.")


def set_windows_title():
	'''
	customizes the window title
	'''
	os.system('title Google Jobs Tool')


def create_driver_handler(driver_path="./chromedriver/chromedriver.exe"):
	'''
	creates a browser instance for selenium, 
	it adds some functionalities into the browser instance
	'''
	chrome_options = Options()
	chrome_options.add_argument("start-maximized")
	chrome_options.add_argument("log-level=3")
	# the following two options are used to take out the chrome browser infobar
	chrome_options.add_experimental_option("useAutomationExtension", False)
	chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
	driver_instance = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
	driver_instance.implicitly_wait(10)
	return driver_instance


def click_helper(selector):
	'''
	this is an helper function that collects a locator and 
	clicks that element with that locator 
	'''
	element = driver.find_element_by_css_selector(selector)
	element.click()


def clear_search_input_element(locator_class):
	'''
	clears the search input element
	'''
	click_helper(locator_class.clear_search_button)
	

def click_search_button_element(locator_class):
	'''
	clicks the search button
	'''
	click_helper(locator_class.search_button)


def nap(secs=random.randrange(1, 5)):
	'''
	sleeps the bot for a random number of seconds
	'''
	logging.info(f"Napping for {secs} seconds")
	time.sleep(secs)


def scroll_element_into_view(element):
	driver.execute_script("arguments[0].scrollIntoView();", element)


def fish_out_needed_data(card):
	datetime_of_search = timekeeper.now
	result_title = card.find_element_by_css_selector(GoogleJobsPageLocators.result_title).text
	date_and_time = card.find_element_by_css_selector(GoogleJobsPageLocators.date_and_time).text
	publisher = card.find_element_by_css_selector(GoogleJobsPageLocators.publisher).text

	data_to_send_to_writer = {
		"Date & time of search": datetime_of_search,
		"Date/Time": date_and_time,
		"Keyword": keyword,
		"Publisher": publisher,
		"Result_Title": result_title,
	}

	pprint.pprint(data_to_send_to_writer)
	excel_writer.write_to_sheet(data_to_send_to_writer)


def scroll_bar_solution(job_cards):
	# cap is the highest number of data the bot will fetch
	cnt, o, cap = 1, 10, 50

	while True:

		try:
			card = job_cards[cnt-1]
			scroll_element_into_view(card)		
		except IndexError as err:
			break

		fish_out_needed_data(card)

		if (cnt % o) == 0: # this will trigger on the 10th item 
			nap(15)
			job_cards = driver.find_elements_by_tag_name(GoogleJobsPageLocators.jobs_cards)

			if cnt == len(job_cards):
				logging.info("\aNew data isn't coming in.")
				break

		if cnt == cap:
			break
		
		cnt += 1


def load_google_jobs_page():
	search_page_url = "https://www.google.com/search?q=google+jobs"
	driver.get(search_page_url)
	# fish out the "/d+ more jobs" link on the g-card tag 
	anchor_tag_elements = driver.find_elements_by_css_selector(GoogleSearchPageLocators.anchor_tags)
	# first let's assume it's always going to be the last anchor tag
	more_jobs_element = anchor_tag_elements[-1]
	google_jobs_url = more_jobs_element.get_attribute('href')
	driver.get(google_jobs_url)


def keyword_jobsearch(keyword):
	# input the search word into the input element
	clear_search_input_element(GoogleJobsPageLocators)
	driver.find_element_by_id(GoogleJobsPageLocators.search_input_element).send_keys(keyword)
	click_search_button_element(GoogleJobsPageLocators)

	job_cards = driver.find_elements_by_tag_name(GoogleJobsPageLocators.jobs_cards)
	if job_cards:
		scroll_bar_solution(job_cards)
		excel_writer.close_workbook()
	else:
		print("No jobs match your search at the moment")


if __name__ == "__main__":
	set_windows_title()
	logging.basicConfig(format="## %(message)s", level=logging.INFO)
	driver = create_driver_handler()

	# these are our helper classes
	timekeeper = TimeKeeper()
	excel_writer = XlsxWriter()

	load_google_jobs_page()
	if (keywords := FileReader().file_content):
		for keyword in keywords:
			print(f"Working on keyword - {keyword}")
			keyword_jobsearch(keyword)
	
	driver.quit()
	input("\aPress Enter to quit...")