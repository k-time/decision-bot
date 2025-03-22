import sys
import traceback
import praw
from praw.exceptions import PRAWException
import string
import time
import random
import logging
import yaml
import argparse
from retry import retry
from datetime import datetime
from scipy import stats
from typing import List, Tuple, Set, Optional, Union

import fight_finder as ff

# Set logging level to INFO for all output, CRITICAL for minimal output
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger('DECISION_BOT')

# Load configs
with open('config.yaml', 'r') as cfg_file:
    cfg = yaml.load(cfg_file, Loader=yaml.FullLoader)
log = cfg['log_name']
comment_log = cfg['comment_log_name']
troubleshoot_text = cfg['troubleshoot_text']
phrases = cfg['fail_phrases']
PHRASE_INDEX = 0


def is_substring(source: str, substring: str, chars_to_search: int = None) -> bool:
    if chars_to_search:
        return source.find(substring, 0, chars_to_search) != -1

    return source.find(substring) != -1


def build_comment_reply(
        score_tables,
        fight_result: str,
        media_scores: List[Tuple[str, str]],
        event_info: str,
        fan_scores: Optional[List[List[Union[str, int]]]],
        comment_author: str
):
    if is_substring(fight_result, "JON JONES", 100):
        fight_result = fight_result.replace("JON JONES", "JON JONES 👀👀", 1)
    if is_substring(fight_result, "DANIEL CORMIER", 100):
        fight_result = fight_result.replace("DANIEL CORMIER", "DANIEL CORMIER 🎂🍗", 1)
    if is_substring(fight_result, "ALEXANDER GUSTAFSSON", 100):
        fight_result = fight_result.replace("ALEXANDER GUSTAFSSON", "ALEXANDER GUSTAFSSON ♠️⧨", 1)
    elif is_substring(fight_result, "ARTEM LOBOV", 100):
        fight_result = fight_result.replace("ARTEM LOBOV", "THE GOAT", 1)
        if event_info is not None:
            event_info = event_info.replace("Lobov", "GOAT")
            # Replacing name in media scores
            new_media_scores = []
            for score in media_scores:
                new_media_scores.append((score[0], score[1].replace("Lobov", "GOAT")))
            media_scores = new_media_scores
            # Replacing name in scorecards
            score_tables[0][1][0][1] = score_tables[0][1][0][1].replace("Lobov", "GOAT")
            score_tables[0][1][0][2] = score_tables[0][1][0][2].replace("Lobov", "GOAT")

    comment = fight_result + '\n\n'
    if event_info is not None:
        comment += event_info + '\n\n'
        # Easter egg jokes. Note: these strings contain non-breaking space characters ('\xa0')
        for combo in cfg['easter_eggs']:
            if combo[0] in fight_result:
                comment = combo[1] + comment
                break

    # Adding scorecards
    comment += build_scorecard_text(score_tables)
    # Adding judges
    comment += build_judge_text(score_tables, comment_author) + '\n\n'
    # Adding media scores
    comment += build_media_scores_text(media_scores)
    # Adding fan scores
    # TODO: disabled for now
    # comment += build_fan_scores_text(fan_scores)

    return comment


def build_scorecard_text(score_tables):
    # Building the first and second rows
    row_1 = 'ROUND'
    row_2 = ':-:'
    for i in range(len(score_tables)):
        row_1 += '|' + score_tables[0][1][0][1] + '|' + score_tables[0][1][0][2]
        if i != len(score_tables)-1:
            row_1 += '|'
        row_2 += '|:-:|:-:|:-:'
    scorecard_text = row_1 + '\n' + row_2 + '\n'

    # Building the 'round' rows and 'total' row
    round_rows = [''] * (len(score_tables[0][1]) - 2)
    total_row = '**TOTAL**'

    for i in range(len(score_tables)):
        current_table = score_tables[i][1]
        for k in range(1, len(current_table)-1):
            current_row = current_table[k]
            # Adding the round numbers
            if i == 0:
                round_rows[k-1] += current_row[0]
            # Adding the round scores
            round_rows[k-1] += '|' + current_row[1] + '|' + current_row[2]
            if i != len(score_tables)-1:
                round_rows[k-1] += '|'

        total_row += '|**' + current_table[-1][1] + '**|**' + current_table[-1][2] + '**'
        if i != len(score_tables)-1:
            total_row += '|'

    for row in round_rows:
        scorecard_text += row + '\n'
    scorecard_text += total_row + '\n'

    return scorecard_text


def build_judge_text(score_tables, comment_author):
    judge_text = 'Judges, in order: '
    for judge, table in score_tables:
        judge_text += judge + ', '
    return '\n*^({}.)*\n*^(Summoned by {}.)*'.format(judge_text.strip(string.punctuation + ' '), comment_author)
    # return '\n*^({}.)*'.format(judge_text.strip(string.punctuation + ' '))


def build_media_scores_text(media_scores) -> str:
    if not media_scores:
        return 'No media scores available for this fight.'
    else:
        media_text = '**MEDIA MEMBER SCORES**\n\n'
        total = len(media_scores)
        score_set = set()

        fighter_1_total = 0
        fighter_2_total = 0
        score_diff_list = []
        calculate_average = cfg['calculate_average_media_score']

        for score in media_scores:
            if score not in score_set:
                count = media_scores.count(score)
                media_text += '- **' + str(count) + '/' + str(total) + \
                              '** people scored it **' + score[0] + ' ' + score[1] + '**.\n'
                score_set.add(score)

            if calculate_average:
                try:
                    # Calculating average score
                    score_list = score[0].split('-')  # Convert score '30-27' to ['30, '27']
                    fighter_1_total += int(score_list[0])
                    fighter_2_total += int(score_list[1])
                    score_diff_list.append(int(score_list[0]) - int(score_list[1]))

                except Exception:
                    logger.exception("Error occurred adding scores at score {}".format(score))
                    calculate_average = False

        if calculate_average and total >= 6:  # Don't calculate averages if less than X media scores
            try:
                media_text += _get_average_media_score_text(media_scores, score_set, fighter_1_total, fighter_2_total,
                                                            score_diff_list, total)
            except Exception:
                logger.exception("Error occurred calculating avg media scorecard for media scores {}"
                                 .format(str(media_scores)))

        return media_text


def _get_average_media_score_text(media_scores: List[Tuple[str, str]], score_set: Set[Tuple[str, str]],
                                  fighter_1_total: int, fighter_2_total: int, score_diff_list: List[int],
                                  total: int) -> str:
    if len(score_set) == 1:
        winning_score = media_scores[0][0]
        winning_fighter = media_scores[0][1]
        return "\nAvg. media score: **{} {}**. Quick maths.\n".format(winning_score, winning_fighter)

    fighter_1_score = fighter_1_total / total
    fighter_2_score = fighter_2_total / total
    rounded_score_1 = round(fighter_1_score, 1)
    rounded_score_2 = round(fighter_2_score, 1)

    winning_score = "{}-{}".format(rounded_score_1, rounded_score_2)

    # One sample t-test; null hypothesis is a draw (score diff is 0)
    t, p = stats.ttest_1samp(score_diff_list, 0)
    if p is None:
        logger.error("p was null")
        return ""

    # Handling draws
    # if fighter_1_total == fighter_2_total or rounded_score_1 == rounded_score_2:
    if p > .2:
        winning_fighter = "DRAW"
        if p > .4:
            confidence_level = "high certainty"
        elif p > .3:
            confidence_level = "moderate certainty"
        else:
            confidence_level = "low certainty"
    # There was a winner
    else:
        if fighter_1_score > fighter_2_score:
            winning_fighter = "Fighter 1"
            for score in media_scores:
                if score[1] != "DRAW":
                    winning_fighter = score[1]
                    break
        else:
            winning_fighter = "Fighter 2"
            for score in reversed(media_scores):
                if score[1] != "DRAW":
                    winning_fighter = score[1]
                    break

        if p > .1:
            confidence_level = "low certainty"
        elif p > .05:
            confidence_level = "moderate certainty"
        else:
            confidence_level = "high certainty"

    explanation_url = 'https://redd.it/9p4xc7'
    return "\nAvg. media score: **{} {}** (*{}^[[1]]({})*).\n".format(winning_score, winning_fighter,
                                                                      confidence_level, explanation_url)

def build_fan_scores_text(fan_scores: Optional[List[List[Union[str, int]]]]) -> str:
    if not fan_scores:
        return ""

    if len(fan_scores) != 3:
        logger.error("Score array length must be 3. Score array {}".format(fan_scores))
        return ""

    fighter1_name = fan_scores[0][0]
    fighter1_num_votes = fan_scores[0][1]
    fighter2_name = fan_scores[1][0]
    fighter2_num_votes = fan_scores[1][1]
    draw_name = fan_scores[2][0]
    draw_num_votes = fan_scores[2][1]

    total_num_votes = fighter1_num_votes + fighter2_num_votes + draw_num_votes
    if total_num_votes < 10:
        return ""

    fighter1_percentage = round(fighter1_num_votes/total_num_votes * 100)
    fighter2_percentage = round(fighter2_num_votes/total_num_votes * 100)
    draw_percentage = round(draw_num_votes/total_num_votes * 100)

    valid_strings = []
    if fighter1_num_votes != 0:
        fighter_1_str = f"*{fighter1_num_votes} ({fighter1_percentage}%)* ***{fighter1_name}***"
        valid_strings.append(fighter_1_str)
    if fighter2_num_votes != 0:
        fighter_2_str = f"*{fighter2_num_votes} ({fighter2_percentage}%)* ***{fighter2_name}***"
        valid_strings.append(fighter_2_str)
    if draw_num_votes != 0:
        draw_str = f"*{draw_num_votes} ({draw_percentage}%)* ***{draw_name}***"
        valid_strings.append(draw_str)

    return f"\n*{total_num_votes} fan scores* — {', '.join(valid_strings)}."


# Replace nicknames and common name mistakes in user input
def create_nickname_dict(nickname_db):
    nickname_dict = {}
    try:
        with open(nickname_db, 'r') as f:
            for line in f:
                line = line.rstrip('\n')
                names = line.split(':')
                if len(names) == 2:
                    nickname_dict[names[0]] = names[1]
    except FileNotFoundError:
        logger.exception('File \'{}\' not found!'.format(nickname_db))

    return nickname_dict


def replace_nicknames(text, nickname_dict):
    for i, j in nickname_dict.items():
        text = text.replace(i, j)
    return text


# Find the index of the trigger word. Returns -1 if not found
def get_trigger_index(text):
    for word in cfg['decision_spellings']:
        index = text.find(word + 'bot')
        if index != -1:
            return index
        index = text.find(word + ' bot')
        if index != -1:
            return index
    return -1


# Reduce the input text to just the fight string
def sanitize_input(text):
    # Only take the first line of comment
    if '\n' in text:
        text = text.split('\n')[0]
    # Remove trigger word
    for word in cfg['decision_spellings']:
        text = text.replace(word + 'bot', '').replace(word + ' bot', '')

    return text.strip(string.punctuation + ' ')


# Cycle through the list of failure phrases
def get_failure_phrase(comment_author):
    global PHRASE_INDEX
    if PHRASE_INDEX >= len(phrases):
        PHRASE_INDEX = 0

    phrase = phrases[PHRASE_INDEX] + troubleshoot_text
    PHRASE_INDEX += 1
    if phrase.startswith('was never'):
        phrase = "{} {}".format(comment_author, phrase)
    elif phrase.startswith("I'm sitting on about"):
        phrase = "{} {}".format(comment_author, phrase)
    elif phrase.startswith("the piece of"):
        phrase = "{} {}".format(comment_author, phrase)

    return phrase


def generate_fail_text(input_fight, comment_author):
    num = random.random()
    if num < .5:  # Adjust this number to adjust the type of failure phrases
        return get_failure_phrase(comment_author)
    else:
        fighter_1, fighter_2, fight_num = ff.get_fighters_from_input(input_fight)
        if fighter_1 is None:
            return get_failure_phrase(comment_author)
        else:
            coin_flip = random.randint(0, 1)
            fighter = fighter_1 if coin_flip == 0 else fighter_2
            return 'I couldn\'t find this fight! Gonna guess... ' \
                   + string.capwords(fighter) + generate_victory_method() + troubleshoot_text


# The rematch_db is needed because mmadecisions.com does not have fights that end in
# finishes, which throws off the fight numbering. Each entry in rematch_db looks like:
# real fight #|fight # on mmadecisions.com (from bottom up)|fighter 1|fighter 2
# 0|0|... means fight decisions are in order
def create_rematch_list(rematch_db):
    rematch_list = []
    try:
        with open(rematch_db, 'r') as f:
            for line in f:
                line = line.rstrip('\n').lower()
                cells = line.split('|')
                rematch_list.append(tuple(cells))
    except FileNotFoundError:
        logger.exception('File \'{}\' not found!'.format(rematch_db))

    return rematch_list


def handle_rematch(fight_info, fight_num, rematch_list):
    if fight_num > 0 and fight_info and len(fight_info) > 0:
        # Reverse to get fights in chronological order
        fight_info.reverse()
        fight_result = fight_info[0][1].lower().replace(u'\xa0', u' ')
        for info in rematch_list:
            (real_fight_num, website_fight_num, fighter_1, fighter_2) = info
            real_fight_num = int(real_fight_num)
            website_fight_num = int(website_fight_num)
            if fighter_1 in fight_result and fighter_2 in fight_result:
                if real_fight_num == 0 and len(fight_info) >= fight_num:
                    return [fight_info[fight_num - 1]]
                elif real_fight_num == fight_num and len(fight_info) >= website_fight_num:
                    return [fight_info[website_fight_num - 1]]

    return fight_info


def get_commented_set() -> Set[str]:
    try:
        with open(comment_log, 'r') as f:
            commented_list = f.read().splitlines()
        # If over 100 comment ids are saved, remove half
        if len(commented_list) > 100:
            with open(comment_log, 'w') as f:
                f.write('\n'.join(commented_list[-50:]) + '\n')
    except FileNotFoundError:
        error_text = 'File \'' + comment_log + '\' not found!'
        logger.critical(error_text)
        log_error(error_text, sys.exc_info())
        sys.exit(1)

    return set(commented_list)


def log_message(comment_body, message):
    try:
        with open(log, 'a') as f:
            f.write(comment_body + '\n' + message + '\n')
            f.write('-------------\n')
    except FileNotFoundError:
        logger.exception('File \'{}\' not found!'.format(log))
        logger.error(comment_body + '\n' + message)


def log_error(text, exc_info):
    try:
        with open(log, 'a') as f:
            f.write(text + '\n')
            traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], file=f)
            f.write('-------------\n')
    except FileNotFoundError:
        logger.exception('File \'{}\' not found!'.format(log))
        logger.error(text + '\n')
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], file=sys.stdout)


def log_comment(comment_id):
    try:
        with open(comment_log, 'a') as f:
            f.write(comment_id + '\n')
    except FileNotFoundError:
        logger.exception('File \'{}\' not found!'.format(comment_log))
        logger.error('Comment ID being logged: {}'.format(comment_id))


def send_reply(fight_info, comment, input_fight):
    # Retrieved fight info
    if fight_info:
        count = 0
        for fight in fight_info:
            if fight[0] is None:
                log_and_reply(generate_fail_text(input_fight, comment.author.name), comment)
                break
            else:
                # Make sure the bot isn't commenting too fast
                if count != 0:
                    time.sleep(5)
                    logger.info('Sending reply with next fight...')
                log_and_reply(build_comment_reply(fight[0], fight[1], fight[2], fight[3], fight[4], comment.author.name), comment)
                count += 1
    # Easter egg jokes
    elif 'dana' in input_fight:
        log_and_reply('Dana defeats Goof' + generate_victory_method(), comment)
    elif 'usada' in input_fight:
        log_and_reply('USADA' + generate_victory_method(), comment)
    elif 'khabib' in input_fight or 'nurmagomedov' in input_fight:
        log_and_reply("Khabib by smesh." + troubleshoot_text, comment)
    else:
        log_and_reply(generate_fail_text(input_fight, comment.author.name), comment)


def log_and_reply(text, comment):
    log_comment(comment.id)
    comment.reply(text)


def generate_victory_method():
    methods = cfg['victory_methods']
    return ' by ' + random.choice(methods) + '.'


def notify_myself(reddit, comment):
    # Permalink requires different formatting for desktop vs. mobile website
    permalink = 'www.reddit.com' + comment.permalink
    reddit.redditor(cfg['personal_username']).message(
        'DecisionBot triggered',
        comment.body
        + '\n\nMobile: \n\n' + permalink.replace('//', '/')
        + '\n\nDesktop: \n\n' + permalink)


# For testing locally with command line
def tester():
    nickname_dict = create_nickname_dict(cfg['nickname_db'])
    rematch_list = create_rematch_list(cfg['rematch_db'])
    fail_text = 'I couldn\'t find this fight! Check your spelling, or maybe the fight didn\'t end in a decision.'

    while True:
        print('Enter fight:')
        input_fight = input()
        input_fight = replace_nicknames(input_fight, nickname_dict)
        print('Searching...')
        fight_info, fight_num = ff.get_fight_info_from_input(input_fight)
        fight_info = handle_rematch(fight_info, fight_num, rematch_list)
        if not fight_info:
            print(fail_text)
        else:
            for fight in fight_info:
                if fight[0] is None:
                    print(fail_text)
                else:
                    print(build_comment_reply(fight[0], fight[1], fight[2], fight[3], fight[4], 'test_author'))


# Run the bot, retrying whenever there is an unavoidable connection reset
@retry(delay=30, logger=logger)
def run(nickname_dict, rematch_list):
    # Log date and time
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info('[' + now + '] Starting up DecisionBot...')

    # Authentication
    reddit = praw.Reddit(
        client_id=cfg['client_id'],
        client_secret=cfg['client_secret'],
        user_agent=cfg['user_agent'],
        username=cfg['username'],
        password=cfg['pw'])

    # Monitoring incoming comment stream from subreddit
    subreddit = reddit.subreddit(cfg['target_subreddits'])

    # Open log of previous bot comments
    commented_set = get_commented_set()

    for comment in subreddit.stream.comments():
        text = comment.body.lower().strip()
        index = get_trigger_index(text)
        # Found a match
        if index != -1:
            try:
                # Make sure bot hasn't already commented
                if comment.id not in commented_set:
                    # Let me know that the bot has been triggered
                    notify_myself(reddit, comment)
                    # Sanitize the input to just get the fight string
                    input_fight = sanitize_input(text[index:])
                    # Replace nicknames in input
                    input_fight = replace_nicknames(input_fight, nickname_dict)
                    # Retrieve all the fight info
                    fight_info, fight_num = ff.get_fight_info_from_input(input_fight)
                    # Handle if user entered a rematch number
                    fight_info = handle_rematch(fight_info, fight_num, rematch_list)
                    logger.info('Sending reply to initial comment...')
                    send_reply(fight_info, comment, input_fight)
                    logger.info('Success!\n')

            except (AttributeError, PRAWException):
                logger.exception('Error occurred...')
                log_error(comment.body, sys.exc_info())
                try:
                    log_and_reply('I couldn\'t find this fight!' + troubleshoot_text, comment)
                except PRAWException:
                    log_error('Error occurred at comment: ' + comment.body, sys.exc_info())


def main():
    # Command-line options parser
    parser = argparse.ArgumentParser(description='Reddit bot that searches and posts MMA scorecards.')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Print logging info to stdout.')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.INFO)
        ff.logger.setLevel(logging.INFO)

    # Create the dictionary of nicknames to be replaced
    nickname_dict = create_nickname_dict(cfg['nickname_db'])
    # Create the rematch list to narrow down searches
    rematch_list = create_rematch_list(cfg['rematch_db'])
    try:
        # Run bot, with retry (because of connection resets)
        run(nickname_dict, rematch_list)
    except (ConnectionResetError, PRAWException, AttributeError):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.exception('[' + now + '] Retrying failed, DecisionBot shutting down.')
        log_error('[' + now + '] Error stacktrace...', sys.exc_info())


if __name__ == '__main__':
    main()
