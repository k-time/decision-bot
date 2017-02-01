from urllib.request import urlopen
from bs4 import BeautifulSoup
from unidecode import unidecode
from pprint import pprint
import re

HOME_URL = 'http://mmadecisions.com/'
SEARCH_URL = 'http://mmadecisions.com/search.jsp?s='
FIGHTER_SUB_URL = 'mmadecisions.com/fighter/'
SEARCH_SUB_URL = 'mmadecisions.com/search'
VERSUS_LIST = ['v', 'v.', 'vs', 'vs.', 'versus', 'versus.']
DEBUG = False

def get_score_tables(fighter_1, fighter_2):
    fight_url = get_fight_url(unidecode(fighter_1), unidecode(fighter_2))
    return get_score_tables_from_fight_page(fight_url)


def get_fight_url(fighter_1, fighter_2):
    # First, check if there's a fight url match for each search term
    fight_list_1 = get_fight_url_list(fighter_1)
    fight_list_2 = get_fight_url_list(fighter_2)
    return find_fight_url_match(fight_list_1, fight_list_2)


def find_fight_url_match(fight_list_1, fight_list_2):
    if fight_list_1 is not None and fight_list_2 is not None:
        for fight_url_1 in fight_list_1:
            for fight_url_2 in fight_list_2:
                if sanitize_url(fight_url_1) == sanitize_url(fight_url_2):
                    return sanitize_url(fight_url_1)
    return None


def get_fight_url_list(fighter):
    # Entering fighter as query on initial search page
    page = urlopen(SEARCH_URL + fighter)
    url = page.geturl()

    # If page redirects to a fighter url
    if FIGHTER_SUB_URL in url:
        if DEBUG: print('Im on a fighter page. Retrieving my fights...')
        return get_fights_from_fighter_page(url)
    # If page redirects to a search url
    elif SEARCH_SUB_URL in url:
        if DEBUG: print('Im on a search page. Retrieving all fights, if any...')
        return get_fights_from_search_page(url)
    # If page redirects to any other url
    else:
        if DEBUG: print('Im on an irrelevant page. Returning none...')
        return None


def get_fights_from_fighter_page(fighter_page_url):
    # List of fight urls to be returned
    list_of_fights = []

    # Opening page
    soup = BeautifulSoup(urlopen(fighter_page_url).read(), "lxml")

    # Getting the list of fights from the table
    table = soup.find('td', attrs={'valign':'top', 'align':'center', 'width':'505px'})
    if table is None: return None
    fight_urls = table.find_all('a', href=True)
    if not fight_urls: return None
    for url in fight_urls:
        if 'decision/' in url['href']:
            clean_url = sanitize_url(url['href'])
            if DEBUG: print('\t\t' + clean_url)
            list_of_fights.append(clean_url)

    return list_of_fights


def get_fights_from_search_page(search_page_url):
    # List of fight urls to be returned
    list_of_fights = []

    # Opening page
    soup = BeautifulSoup(urlopen(search_page_url).read(), "lxml")

    # Getting the table of fighters on the search page
    table = soup.find('div', attrs={'id':'pageFighters1'})
    if table is None: return None

    # Getting the list of all fights from all fighters in the table
    fighter_urls = table.find_all('a', href=True)
    if not fighter_urls: return None
    for url in fighter_urls:
        if url['href'].startswith('fighter/'):
            clean_url = sanitize_url(url['href'])
            if DEBUG: print(clean_url)
            fights = get_fights_from_fighter_page(clean_url)
            if fights is not None: list_of_fights.extend(fights)

    return list_of_fights


def get_score_tables_from_fight_page(url):
    # The final tables to be returned: list of (judge name, table rows) tuples
    score_tables = []

    # Opening the page
    soup = BeautifulSoup(urlopen(url).read(), "lxml")

    # Finding the decision scores table
    html_tables = soup.find_all('table', limit=3, attrs={'cellspacing':'1', 'width':'100%'})
    if not html_tables: return None

    # Iterate over each judge's scorecards
    for i in range(len(html_tables)):
        current_table = html_tables[i]
        judge_name = current_table.a.getText().replace(u'\xa0', u' ')

        # The rows of information in the current table
        rows = []

        # Retrieving fighter names
        fighters = current_table.find_all('td', limit=2, attrs={'align':'center', 'class':'top-cell', 'width':'45%'})
        if len(fighters) != 2: return None
        rows.append(['ROUND', fighters[0].getText(), fighters[1].getText()])

        # Getting round numbers and scores
        rounds = current_table.find_all('tr', attrs={'class':'decision'})
        if not rounds: return None
        for r in rounds:
            cells = r.find_all('td', attrs={'class':'list', 'align':'center'})
            if not cells: return None
            row = []
            for cell in cells:
                row.append(cell.getText())
            rows.append(row)

        # Getting the total scores
        totals = current_table.find_all('td', limit=2, attrs={'class':'bottom-cell'})
        if len(totals) != 2: return None
        rows.append(['TOTAL', totals[0].getText(), totals[1].getText()])

        # Add tuple (judge, rows) to score_tables
        score_tables.append((judge_name, rows))

    return score_tables


def sanitize_user_input(input):
    input = input.strip()

    for word in VERSUS_LIST:
        index = re.search(r'\b' + re.escape(word) + r'\b', input)
        if index: print(index.start())

        """
        if index != -1:
            fighter_1 = input[:index]
            fighter_2 = input[index + 3:]
            print(fighter_1)
            print(fighter_2)
            comment.reply(get_score_tables(fighter_1, fighter_2))
            print('Replying!')
            break
        else:
            i=0
        """


def sanitize_url(url):
    # Check if the url is a valid url
    if 'decision/' not in url and 'fighter/' not in url:
        return None

    # Add home_url to the front of the url if needed
    if url.startswith('decision/') or url.startswith('fighter/'):
        url = HOME_URL + url

    # Remove the jsessionid from the url
    index = url.find('jsessionid')
    if index != -1:
        url = url[:index-1]

    # Replace accented characters in url
    return unidecode(url)


def main():

    print(sanitize_user_input('diaz vs mcgregor'))
    #get_fights_from_search_page('http://mmadecisions.com/search.jsp?s=diaz')

    """
    print('Enter fighter 1: ')
    fighter_1 = input()
    print('Enter fighter 2: ')
    fighter_2 = input()
    """

    """
    fighter_1 = 'dillashaw'
    fighter_2 = 'Assunção'

    score_tables = get_score_tables(fighter_1, fighter_2)

    if score_tables is None:
        print('Could not find fight, or perhaps this fight did not end in a decision.')
    else:
        pprint(score_tables)
    """


if __name__ == '__main__':
    main()
