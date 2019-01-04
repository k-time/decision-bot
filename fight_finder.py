import sys
from bs4 import BeautifulSoup
from unidecode import unidecode
from urllib.request import urlopen
import urllib.error
import requests
from pprint import pprint
from datetime import datetime
import logging
import yaml

# Set logging level to INFO for status output, CRITICAL for no output
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger('FIGHT_FINDER')

# Load configs
with open('config.yaml', 'r') as cfg_file:
    cfg = yaml.load(cfg_file)
home_url = cfg['home_url']


def get_fight_info(fighter_1, fighter_2):
    if fighter_1 and fighter_2 and len(fighter_1) > 1 and len(fighter_2) > 1:
        fight_urls = _get_fight_urls(fighter_1, fighter_2)
        return _get_fight_info_from_fight_page(fight_urls)
    return None


# There could be multiple fights due to rematches
def _get_fight_urls(fighter_1, fighter_2):
    # First, check if there's a fight url match for each search term
    fight_list_1 = _get_fight_url_list(unidecode(fighter_1).replace(' ', '+'))
    fight_list_2 = _get_fight_url_list(unidecode(fighter_2).replace(' ', '+'))
    return _find_fight_url_matches(fight_list_1, fight_list_2)


def _find_fight_url_matches(fight_list_1, fight_list_2):
    # Need to return a list of all matches, in case of rematches
    fight_urls = []
    if fight_list_1 is not None and fight_list_2 is not None:
        url_set = set()
        for fight_url_1 in fight_list_1:
            url_set.add(_sanitize_url(fight_url_1))

        for fight_url_2 in fight_list_2:
            url_2 = _sanitize_url(fight_url_2)
            if url_2 in url_set:
                fight_urls.append(url_2)
                if len(fight_urls) > 5:
                    logger.warning('Limiting number of fight url matches to 6.')
                    return fight_urls
    return fight_urls


def _get_fight_url_list(fighter):
    # Entering fighter as query on initial search page
    query_url = cfg['search_url'] + fighter
    try:
        page = urlopen(query_url)
        url = page.geturl()
    # Use requests.get() as backup if urlopen() fails
    except (urllib.error.HTTPError, UnicodeEncodeError):
        logger.info('urlopen() failed, trying requests.get()...')
        try:
            page = requests.get(query_url)
            url = page.url
            # Currently there is a search functionality issue with mmadecisions.com
            url = url.replace('mmadecisions/fighter', 'fighter')
        except requests.HTTPError:
            logger.exception('Could not open url {}'.format(query_url))
            return None

    # If page redirects to a fighter url
    if cfg['fighter_sub_url'] in url:
        logger.info('I\'m on a fighter page. Retrieving my fights...')
        return _get_fights_from_fighter_page(url)
    # If page redirects to a search url
    elif cfg['search_sub_url'] in url:
        logger.info('I\'m on a search page. Retrieving all fights, if any...')
        return _get_fights_from_search_page(url)
    # If page redirects to any other url
    else:
        logger.info('I\'m on an irrelevant page. Returning none...')
        return None


def _get_fights_from_fighter_page(fighter_page_url):
    # List of fight urls to be returned
    list_of_fights = []

    # Opening page
    soup = BeautifulSoup(urlopen(fighter_page_url).read(), "lxml")

    # Getting the list of fights from the table
    table = soup.find('td', attrs={'valign': 'top', 'align': 'center', 'width': '505px'})
    if table is None:
        return None
    fight_urls = table.find_all('a', href=True)
    if not fight_urls:
        return None
    for url in fight_urls:
        if 'decision/' in url['href']:
            clean_url = _sanitize_url(url['href'])
            logger.info('\t\t' + clean_url)
            list_of_fights.append(clean_url)

    return list_of_fights


def _get_fights_from_search_page(search_page_url):
    # List of fight urls to be returned
    list_of_fights = []

    # Opening page
    soup = BeautifulSoup(urlopen(search_page_url).read(), "lxml")

    # Getting the fighter column on the page
    fighter_column = soup.find('td', attrs={'width': '265px', 'valign': 'top', 'align': 'center'})
    if fighter_column is None:
        return None

    # Getting the fighters in the column
    fighter_names = fighter_column.find('div', attrs={'id': 'pageFighters1'})
    if fighter_names is None:
        return None

    fights_on_page = _get_fights_on_page(fighter_names)
    if fights_on_page is None:
        return None
    else:
        list_of_fights.extend(fights_on_page)

    # If there are additional pages, get all fighters from those fighters as well
    other_fighter_names = fighter_column.find_all('div', attrs={'style': 'display:none;'})
    for page_of_names in other_fighter_names:
        fights_on_page = _get_fights_on_page(page_of_names)
        if fights_on_page is None:
            return None
        else:
            list_of_fights.extend(fights_on_page)

    return list_of_fights


def _get_fights_on_page(fighter_names):
    # The list of fight urls on the current page
    fights_on_page = []

    fighter_urls = fighter_names.find_all('a', href=True)
    if not fighter_urls:
        return None
    for url in fighter_urls:
        if url['href'].startswith('fighter/'):
            clean_url = _sanitize_url(url['href'])
            logger.info(clean_url)
            fights = _get_fights_from_fighter_page(clean_url)
            if fights is not None:
                fights_on_page.extend(fights)

    return fights_on_page


def _get_fight_info_from_fight_page(fight_urls):
    if not fight_urls:
        return None

    # List of tuples representing each fight.
    # If there is one fight, there is one tuple.
    # If there was a rematch, there are two tuples, etc.
    fight_info = []

    for url in fight_urls:
        if not url or home_url not in url:
            return None

        # Opening the page
        soup = BeautifulSoup(urlopen(url).read(), "lxml")

        # Getting all the information from the page
        score_tables = _get_score_tables(soup)
        if not score_tables:
            return None
        fight_result = _get_fight_result(soup, url)
        event_info = _get_event_info(soup, url)
        media_scores = _get_media_scores(soup, url)

        # Add a tuple containing all fight info
        fight_info.append((score_tables, fight_result, media_scores, event_info))

    return fight_info


# Getting the score tables from the fight page
def _get_score_tables(soup):
    # The final tables to be returned: list of (judge name, table rows) tuples
    score_tables = []

    # Finding the decision scores table on the page
    html_tables = soup.find_all('table', limit=3, attrs={'cellspacing': '1', 'width': '100%'})
    if not html_tables:
        return None

    # Iterate over each judge's scorecards
    for i in range(len(html_tables)):
        current_table = html_tables[i]

        if current_table.a is None:
            judge_name = 'Unknown Judge'
        else:
            judge_name = current_table.a.getText().replace(u'\xa0', u' ')

        # The rows of information in the current table
        rows = []

        # Retrieving fighter names
        fighters = current_table.find_all('td', limit=2, attrs={'align': 'center', 'class': 'top-cell', 'width': '45%'})
        if len(fighters) != 2:
            return None
        rows.append(['ROUND', fighters[0].getText(), fighters[1].getText()])

        # Getting round numbers and scores
        rounds = current_table.find_all('tr', attrs={'class': 'decision'})
        if not rounds:
            return None
        for r in rounds:
            cells = r.find_all('td', attrs={'class': 'list', 'align': 'center'})
            if not cells:
                return None
            row = []
            for cell in cells:
                row.append(cell.getText())
            rows.append(row)

        # Getting the total scores
        totals = current_table.find_all('td', limit=2, attrs={'class': 'bottom-cell'})
        if len(totals) != 2:
            return None
        rows.append(['TOTAL', totals[0].getText(), totals[1].getText()])

        # Add tuple (judge, rows) to score_tables
        score_tables.append((judge_name, rows))

    return score_tables


# Getting the fight result (ex. 'A defeats B (split decision)') from the fight page
def _get_fight_result(soup, url):
    try:
        top_section = soup.find('td', attrs={'class': 'decision-top', 'align': 'right'})
        first_fighter = top_section.a.getText().replace('&nbsp;', ' ').strip()
        middle_section = soup.find('td', attrs={'class': 'decision-middle', 'colspan': '2'})
        action = middle_section.i.getText().strip()
        bottom_section = soup.find('td', attrs={'class': 'decision-bottom', 'colspan': '2'})
        second_fighter = bottom_section.a.getText().replace('&nbsp;', ' ').strip()
        decision_section = soup.find('th', attrs={'class': 'event2', 'colspan': '2'})
        decision = decision_section.i.getText().strip()
        fight_result = '[**' + first_fighter.upper() + ' ' + action + ' ' + \
                       second_fighter.upper() + '** (*' + decision.lower() + '*)](' + url + ')'
    except AttributeError:
        logger.exception('Could not retrieve fight result from url {}'.format(url))
        return None

    return fight_result


# Getting the event info from the fight page
def _get_event_info(soup, url):
    try:
        event_section = soup.find('td', attrs={'class': 'decision-top2', 'colspan': '2'})
        info = event_section.getText().replace('\t', '').strip('\n').split('\n')
        if len(info) >= 1:
            # Getting the event name
            event_info = info[0].strip()
            if len(info) >= 2:
                # Adding the event date
                event_date = _get_full_date(info[1].strip(), url)
                event_info += ' — ' + event_date
                event_info = '^(' + event_info + ')'
        else:
            return None
    except AttributeError:
        logger.exception('Could not retrieve event info from url {}'.format(url))
        return None

    return event_info


# Getting the media scores from the fight page
def _get_media_scores(soup, url):
    try:
        media_section = soup.find('table', attrs={'cellspacing': '2', 'width': '100%'})
        media_rows = media_section.find_all('tr', attrs={'class': 'decision'})
        media_scores = []
        if media_rows:
            for row in media_rows:
                score = row.find('a', attrs={'class': 'external'}).getText().strip()
                fighter = row.find_all('td', attrs={'align': 'center'})[-1].getText()
                media_scores.append((score, fighter))
    except AttributeError:
        logger.exception('Could not retrieve media scores from url {}'.format(url))
        return None

    return media_scores


def _get_full_date(num_date, url):
    try:
        # Convert numerical date YYYY-mm-dd to full date (ex. January 1, 2000)
        d = datetime.strptime(num_date, '%Y-%m-%d')
        return d.strftime('%B %d, %Y')
        # return num_date
    except ValueError:
        logger.error('Could not convert date at url {}'.format(url))
        return num_date


def _sanitize_url(url):
    # Check if the url is a valid url
    if 'decision/' not in url and 'fighter/' not in url:
        return None

    if url.startswith('decision/'):
        url_sections = url.split('/')
        if len(url_sections) >= 2:
            url = 'decision/' + url_sections[1] + '/fight'
        url = home_url + url

    # Add home_url to the front of the url if needed
    elif url.startswith('fighter/'):
        url = home_url + url

    # Remove the jsessionid from the url
    index = url.find('jsessionid')
    if index != -1:
        url = url[:index-1]

    # Replace accented characters in url
    return unidecode(url)


# Check if a fight number is included in input, ex. Lawler vs. Hendricks 2.
# Used for rematch handling.
def _get_fight_num(input_fight):
    # Convert roman numerals to regular digits
    roman_numerals = ('i', 'ii', 'iii')
    for num in roman_numerals:
        if input_fight.endswith(' ' + num):
            fight_num = len(num)
            new_input_fight = input_fight[:-(len(num)+1)]
            return fight_num, new_input_fight

    # Handle regular digits
    last_char = input_fight[-1]
    if last_char.isdigit():
        fight_num = int(last_char)
        new_input_fight = input_fight[:-1].strip()
        return fight_num, new_input_fight

    return -1, input_fight


# Searches for variations of "versus" in the input
def get_fighters_from_input(input_fight):
    input_fight = input_fight.strip()
    if input_fight == '':
        return None, None, -1

    fight_num, input_fight = _get_fight_num(input_fight)

    for word in cfg['versus_list']:
        index = input_fight.find(word)
        if index != -1:
            fighter_1 = input_fight[:index].strip()
            fighter_2 = input_fight[index + len(word):].strip()
            return fighter_1, fighter_2, fight_num

    return None, None, -1


# Used when variations of "versus" are not found in the input
def _guess_fighters_from_input(input_fight):
    input_fight = input_fight.strip()
    if input_fight == '':
        return None, -1

    # TODO: Implement fight numbers
    fight_num, input_fight = _get_fight_num(input_fight)

    word_list = input_fight.split()
    word_count = len(word_list)
    name_combos = []

    if word_count < 2 or word_count > 6:
        return [], -1
    else:
        # For just even counts
        if word_count % 2 == 0:
            fighter_1 = ' '.join(word_list[:word_count//2])
            fighter_2 = ' '.join(word_list[word_count//2:])
            name_combos.append((fighter_1, fighter_2))
        # For both odd and even counts
        for i in range((word_count-1)//2, word_count//6, -1):
            fighter_1 = ' '.join(word_list[:i])
            fighter_2 = ' '.join(word_list[i:])
            name_combos.append((fighter_1, fighter_2))
            fighter_1 = ' '.join(word_list[:word_count-i])
            fighter_2 = ' '.join(word_list[word_count-i:])
            name_combos.append((fighter_1, fighter_2))

    return name_combos, fight_num


def get_fight_info_from_input(input_fight):
    # Try getting fighter names by looking for variations of "vs"
    fighter_1, fighter_2, fight_num = get_fighters_from_input(input_fight)
    fight_info = None

    # Input is blank
    if input_fight.strip() == '':
        logger.info('\nInput fight is blank! Please try again.')
    # One or both of the fighter names is whitespace
    elif fighter_1 == '' or fighter_2 == '':
        logger.info('\nOne or both of the fighter names is blank! Please try again.')
    # Fighter names found
    elif fighter_1 is not None and fighter_2 is not None:
        logger.info('Fighter 1: ' + fighter_1)
        logger.info('Fighter 2: ' + fighter_2)
        fight_info = get_fight_info(fighter_1, fighter_2)
    # Variations of "versus" were not found, so try to find the fighter names
    else:
        logger.info('No \'versus\' found in input, so guessing fighters...\n')
        name_combos, fight_num = _guess_fighters_from_input(input_fight)
        for combo in name_combos:
            logger.info('Trying fighter 1: ' + combo[0])
            logger.info('Trying fighter 2: ' + combo[1] + '\n')
            fight_info = get_fight_info(combo[0], combo[1])
            if fight_info:
                if fight_info[0]:
                    if fight_info[0][0] is not None:
                        break
            else:
                logger.info('\nCould not find fight- guessing names again...')

    if not fight_info:
        logger.info('Unable to find fight!')
    else:
        logger.info('Fight found!')

    return fight_info, fight_num


def main():
    print('Enter fight:')
    input_fight = input()
    print('Searching...')
    fight_info, fight_num = get_fight_info_from_input(input_fight)

    error_msg = 'Couldn\'t find this fight! Check your spelling, or maybe this fight didn\'t end in a decision.'

    if fight_info:
        for fight in fight_info:
            score_tables = fight[0]
            fight_result = fight[1]
            media_scores = fight[2]
            event_info = fight[3]

            if score_tables is None:
                print(error_msg)
            else:
                print('\n' + fight_result + '\n')
                if event_info:
                    print(event_info + '\n')
                else:
                    print('No event info available.\n')
                pprint(score_tables)
                print('\nMEDIA SCORES\n')
                if media_scores:
                    pprint(media_scores)
                else:
                    print('No scores available.')
    else:
        print(error_msg)


if __name__ == '__main__':
    main()
