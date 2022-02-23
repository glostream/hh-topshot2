import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import os
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
import time
import threading


REFRESH_INTERVAL = 20	# seconds to wait between token refreshes


def refresh_token(driver):
	while True:
		browser_log = driver.get_log('performance')

		for item in browser_log:
			json_message = item['message']
			json_parsed = json.loads(json_message)
			try:
				token = json_parsed['message']['params']['headers']['token']
				print('Token refreshed!')
				break
			except:
				try:
					token = json_parsed['message']['params']['request']['headers']['token']
					print('Token refreshed!')
					break
				except Exception as e:
					pass

		with open('utils/token.cfg', 'w+') as f:
			f.write(token)
		
		time.sleep(REFRESH_INTERVAL)
		driver.refresh()


def read_token():
	if os.path.exists('utils/token.cfg'):
		with open('utils/token.cfg', 'r') as f:
			token = f.read()
		return token
	else:
		time.sleep(1)
		return read_token()


def launch_driver(url):
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('--disable-logging')
	chrome_options.add_argument("--log-level=3")

	caps = DesiredCapabilities.CHROME
	caps['goog:loggingPrefs'] = {'performance': 'ALL'}

	print('Initializing web driver...')

	driver = webdriver.Chrome(executable_path='utils/chromedriver', options=chrome_options, desired_capabilities=caps)
	driver.get(url)

	return driver


def get_url(token, id):
	headers = {
		'authority': 'api2.cryptoslam.io',
		'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
		'accept': 'application/json, text/javascript, */*; q=0.01',
		'sec-ch-ua-mobile': '?0',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
		'token': '{}'.format(token),
		'origin': 'https://cryptoslam.io',
		'sec-fetch-site': 'same-site',
		'sec-fetch-mode': 'cors',
		'sec-fetch-dest': 'empty',
		'referer': 'https://cryptoslam.io/',
		'accept-language': 'en-US,en;q=0.9',
	}

	url = 'https://api2.cryptoslam.io/api/mints/NBA%20Top%20Shot/{}'.format(id)
	response = requests.get(url, headers=headers)

	print(response.text)

	return response


def main():
	if os.path.exists('utils/token.cfg'):
		os.remove('utils/token.cfg')

	url = 'https://www.cryptoslam.io/nba-top-shot/sales'
	driver = launch_driver(url)

	refresh_thread = threading.Thread(target=refresh_token, args=(driver,))
	refresh_thread.start()

	time.sleep(10)
	token = read_token()
	
	get_url(token, '2214763')

	os._exit(1)


main()