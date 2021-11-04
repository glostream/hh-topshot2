from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import common
import requests
import pandas as pd
import datetime
import time, sys, os, re, json
import threading


SALES_BATCH_SIZE = 5000	# number of rows to scrape per API request
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


def get_table(token, start_index, length, start_date='', end_date=''):
	headers = {
		'authority': 'api2.cryptoslam.io',
		'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
		'accept': 'application/json, text/javascript, */*; q=0.01',
		'sec-ch-ua-mobile': '?0',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
		'token': '',
		'content-type': 'application/json',
		'origin': 'https://www.cryptoslam.io',
		'sec-fetch-site': 'same-site',
		'sec-fetch-mode': 'cors',
		'sec-fetch-dest': 'empty',
		'referer': 'https://www.cryptoslam.io/',
		'accept-language': 'en-US,en;q=0.9',
	}

	headers['token'] = token

	data = '{"draw":1,"columns":[{"data":null,"name":"","searchable":true,"orderable":false,"search":{"value":"","regex":false}},{"data":null,"name":"TimeStamp","searchable":true,"orderable":true,"search":{"value":"","regex":false}},{"data":null,"name":"","searchable":true,"orderable":true,"search":{"value":"","regex":false}},{"data":null,"name":"","searchable":true,"orderable":true,"search":{"value":"","regex":false}},{"data":null,"name":"Tokens.Attributes.Set","searchable":true,"orderable":false,"search":{"value":"","regex":false}},{"data":null,"name":"Tokens.Attributes.Team","searchable":true,"orderable":false,"search":{"value":"","regex":false}},{"data":null,"name":"Tokens.Attributes.PlayCategory","searchable":true,"orderable":false,"search":{"value":"","regex":false}},{"data":null,"name":"Price","searchable":true,"orderable":true,"search":{"value":"","regex":false}},{"data":"priceUSD","name":"PriceUSDDoubleType","searchable":true,"orderable":true,"search":{"value":"","regex":false}},{"data":null,"name":"Tokens.Attributes.SerialNumber","searchable":true,"orderable":true,"search":{"value":"","regex":false}},{"data":null,"name":"","searchable":true,"orderable":true,"search":{"value":"","regex":false}},{"data":null,"name":"","searchable":true,"orderable":true,"search":{"value":"","regex":false}}],"order":[{"column":1,"dir":"asc"}],' \
		'"start":%(start)s,"length":%(length)s,' \
		'"search":{"value":"","regex":false},' \
		'"startdate":"%(start_date)s","enddate":"%(end_date)s",' \
		'"buyer":"","seller":"","attributesQuery":{},"marketplace":""}' \
		% {'start': start_index, 'length': length, 'start_date': start_date, 'end_date': end_date}

	response = requests.post('https://api2.cryptoslam.io/api/sales/NBA%20Top%20Shot/search',
		headers=headers, data=data)


	if response.status_code == 200:
		json_response = response.json()['data']
		print(len(json_response))
		return json_response
	elif response.status_code == 500:
		return ''
	else:
		print('ERROR {}, retrying in 5 seconds...'.format(response.status_code))
		time.sleep(5)
		token = read_token()
		return get_table(token, start_index, length, start_date, end_date)	


def process_table(response, rows):
	for k in response:
		seller = k['sellerDisplay']
		buyer = k['buyerDisplay']
		seller_address = k['seller']
		buyer_address = k['buyer']
		price = str(k['priceUSD']).replace('.0', '.00')
		time = k['timeStamp']
		token_ID = k['tokens'][0]['tokenId']
		link = 'https://www.cryptoslam.io/nba-top-shot/mint/{}'.format(token_ID)
		transaction_hash = k['transactionHash']
		sale_id = k['id']

		attr = k['tokens'][0]['attributes']
		if attr:
			try:
				player = attr['Name']
				category = attr['PlayCategory']
				season = attr['Season']
				sn = attr['SerialNumber']
				sets = attr['Set']
				team = attr['Team']
				moment_date = attr['MomentDate']
				mint_number = attr['MasterMint#']
				ed_size = attr['VariantRarity'].split('/')[1]
				jersey_number = attr['JerseyNumber']

				crypto = '{} {}'.format(season, player)

				new_row = (time, crypto, token_ID, mint_number, jersey_number, moment_date, sets, team, category,
					price, sn, seller, buyer, seller_address, buyer_address, transaction_hash, sale_id, ed_size, link)
				rows.append(new_row)
			except:
				continue
		else:
			continue
	return rows
	

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


def read_token():
	if os.path.exists('utils/token.cfg'):
		with open('utils/token.cfg', 'r') as f:
			token = f.read()
		return token
	else:
		time.sleep(1)
		return read_token()
	

def main(url):
	all_rows = []
	table_write_mode = 'w'
	write_header = True
	newest_entry = ''
	start_it = 0

	columns = ['Sold', 'Crypto', 'Token ID', 'Master Mint #', 'Jersey Number', 'Moment Date', 'Set', 'Team', 
		'Play Category', 'Price (USD)', 'SN#', 'Seller', 'Buyer', 'Sller Address', 'Buyer Address', 'Transaction Hash',
		'ID', 'Edition Size', 'Link']
	batch_size = SALES_BATCH_SIZE
	date1 = datetime.date(2020, 7, 28)
	# date1 = datetime.date(2021, 3, 18)

	if os.path.exists('data/sales.csv'):
		old_table = pd.read_csv('data/sales.csv', sep=',', usecols=[0])
		newest_entry = old_table.iloc[:,0].max()
		# print('newest entry:', newest_entry)
		date1 = datetime.datetime.strptime(newest_entry.split('T')[0], '%Y-%m-%d').date()
		number_entries_on_newest_day = len(old_table[old_table.iloc[:,0] > newest_entry.split('T')[0]])
		# print(number_entries_on_newest_day)
		start_it = number_entries_on_newest_day // batch_size
		# print('date 1:', date1)
		table_write_mode = 'a'
		write_header = False

	day = datetime.timedelta(days=1)
	end = datetime.date.today() + day
	# end = datetime.date(2020, 8, 1)

	i = start_it
	print('\nSearching {}...'.format(date1.strftime("%Y-%m-%d")))
	while date1 < end:
		date2 = date1 + day
		token = read_token()
		# print('start index:', i)
		json_response = get_table(token, i*batch_size, batch_size, date1.strftime("%Y-%m-%d"), date2.strftime("%Y-%m-%d"))
		# print('len response:', len(json_response))
		all_rows = process_table(json_response, all_rows)
		print('Have {} rows total.'.format(len(all_rows)))
		# time.sleep(1)
		if len(json_response) == batch_size:
			i += 1
			continue
		date1 += day
		date2 += day
		i = 0
		table = pd.DataFrame(all_rows, columns=columns)
		if newest_entry:
			table = table.drop(table[table.iloc[:,0] <= newest_entry].index)
			print('\nAdded {} new rows.'.format(len(table)))

		table.to_csv('data/sales.csv', sep=',', index=False, mode=table_write_mode, header=write_header)
		print('\nSearching {}...'.format(date1.strftime("%Y-%m-%d")))

	table = pd.DataFrame(all_rows, columns=columns)
	if newest_entry:
		table = table.drop(table[table.iloc[:,0] <= newest_entry].index)
		print('\nAdded {} new rows.'.format(len(table)))

	table.to_csv('data/sales.csv', sep=',', index=False, mode=table_write_mode, header=write_header)

	print('Scraping complete!')


if __name__ == '__main__':
	url = 'https://www.cryptoslam.io/nba-top-shot/sales'
	
	if os.path.exists('utils/token.cfg'):
		os.remove('utils/token.cfg')

	driver = launch_driver(url)

	refresh_thread = threading.Thread(target=refresh_token, args=(driver,))
	refresh_thread.start()

	main(url)

	os._exit(1)
