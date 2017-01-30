import sys
from urllib.request import urlopen
from bs4 import BeautifulSoup

home_url = 'http://mmadecisions.com/'
short_home_url = 'mmadecisions.com'
search_url = 'http://mmadecisions.com/search.jsp?s='
fighter_sub_url = 'mmadecisions.com/fighter/'
search_sub_url = 'mmadecisions.com/search'

def get_fight_url_list(fighter):
	
	# Opening first search page
	page = urlopen(search_url + fighter)
	soup = BeautifulSoup(page.read(), "lxml")
	url = page.geturl()

	# If page redirects to a fighter url
	if fighter_sub_url in url:
		print('Im a fighter')
		return get_fights_from_fighter_page(url)
	elif search_sub_url in url:
		print('Im in search')
		return get_fights_from_search_page(url)
	else:
		print('Im irrelevant')
		return None



def get_fights_from_fighter_page(fighter_page_url):
	# List of fight urls to be returned
	list_of_fights = []

	# Opening page
	soup = BeautifulSoup(urlopen(fighter_page_url).read(), "lxml")

	# Getting the list of fights from the table
	table = soup.find('td', attrs={'valign':'top', 'align':'center', 'width':'505px'})
	fight_urls = table.findAll('a', href=True)
	for url in fight_urls:
		if 'decision/' in url['href']:
			list_of_fights.append(url['href'])

	return list_of_fights


# MAKE SURE THAT IT'S NOT AN EMPTY SEARCH PAGE
def get_fights_from_search_page(search_page_url):
	# List of fight urls to be returned
	list_of_fights = []

	# Opening page
	soup = BeautifulSoup(urlopen(search_page_url).read(), "lxml")

	# Getting the list of all fights from all fighters in the table
	table = soup.find('div', attrs={'id':'pageFighters1'})

	if table is None:
		print('Nothing here!')
		return None

	fighter_urls = table.findAll('a', href=True)
	for url in fighter_urls:
		if url['href'].startswith('fighter/'):
			fights = get_fights_from_fighter_page(home_url + url['href'])
			list_of_fights.extend(fights)
			print(url['href'])

	return list_of_fights


def get_fight_url(fighter_1, fighter_2):

	print("hello")

	# first: check if theres a fight url match on each search page

	# second: if there's no match, check if there's a name match on each page

	# third, do a google search and find the first link


def get_tables(url):
	# Opening the page
	soup = BeautifulSoup(urlopen(url).read(), "lxml")
	
	# Finding the decision scores
	letters = soup.findAll('table', attrs={'cellspacing':'1', 'width':'100%'})

	# The final tables to be returned: list of (judge name, table rows) tuples
	tables = []

	# CHANGE RANGE TO 3 LATER
	for i in range(3):
		table = letters[i]
		judge = table.a.getText().replace(u'\xa0', u' ')

		# The rows of information to be returned
		rows = []

		# Getting fighter names
		fighters = table.findAll('td', attrs={'align':'center', 'class':'top-cell', 'width':'45%'})
		rows.append(['ROUND', fighters[0].getText(), fighters[1].getText()])
		
		# Getting round #s and scores
		rounds = table.findAll('tr', attrs={'class':'decision'})
		for r in rounds:
			cells = r.findAll('td', attrs={'class':'list', 'align':'center'})
			row = []
			for cell in cells: 
				row.append(cell.getText())
			rows.append(row)

		# Getting the totals
		totals = table.findAll('td', attrs={'class':'bottom-cell'})
		rows.append(['TOTAL', totals[0].getText(), totals[1].getText()])

		# Add tuple (judge, rows) to judge_list
		tables.append((judge, rows))

	return tables


def compare_fight_urls(url_1, url_2):
	i = 1
	# Need to truncate the jsessionid, and add mmadecision.com to front
	#fighter/2277/Michael-Diaz;jsessionid=E656A7A3B16F8AA71636E03B004CA74B 


def main():
	# STRIP WHITESPACE FROM BEFORE AND AFTER
	print(get_fight_url_list('glenn'.lower().replace(' ', '%20')));
	#print(get_fights_from_fighter_page('http://mmadecisions.com/fighter/635/Rafael-dos-Anjos'))
	#get_fights_from_search_page('http://mmadecisions.com/search.jsp?s=dsafasdfsadf')

	#tables = get_tables('http://mmadecisions.com/decision/7244/Conor-McGregor-vs-Nate-Diaz')
	#print(tables)



if __name__ == '__main__':
    main()