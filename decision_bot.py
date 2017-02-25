import sys
import traceback
import praw
import praw.exceptions
import string
import time
import random
import logging
import fight_finder
import config

FAIL_TEXT = 'I couldn\'t find this fight! Check your spelling, ' \
            'or maybe the fight didn\'t end in a decision.'
TROUBLESHOOT_TEXT = ' [Troubleshooting](https://s3.amazonaws.com/decisionbot/error_message.txt)'
DECISION_SPELLINGS = ['decision', 'decison', 'desicion', 'descision']
# Set logging level to INFO for status output, WARNING for no output
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger('DECISION_BOT')


def build_comment_reply(score_tables, fight_result, media_scores, event_info):
    comment = fight_result + '\n\n'
    if event_info is not None:
        comment += event_info + '\n\n'
        # Easter egg joke
        if '**CARLOS CONDIT** defeats **NICK DIAZ**' in fight_result:
            comment = '**DIAZ 1 2 5**\n\nI mean...\n\n' + comment

    # Building the first and second rows
    row_1 = 'ROUND'
    row_2 = ':-:'
    for i in range(len(score_tables)):
        row_1 += '|' + score_tables[0][1][0][1] + '|' + score_tables[0][1][0][2]
        if i != len(score_tables)-1:
            row_1 += '|'
        row_2 += '|:-:|:-:|:-:'
    comment += row_1 + '\n' + row_2 + '\n'

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
        comment += row + '\n'
    comment += total_row + '\n'

    # Adding judges
    comment += build_judge_text(score_tables) + '\n\n'

    # Adding media scores
    comment += build_media_scores_text(media_scores)

    return comment


def build_judge_text(score_tables):
    judge_text = 'Judges, in order: '
    for judge, table in score_tables:
        judge_text += judge + ', '
    return '*^(' + judge_text.strip(string.punctuation + ' ') + '.)*'


def build_media_scores_text(media_scores):
    if not media_scores:
        return 'No media scores available for this fight.'
    else:
        media_text = '**MEDIA MEMBER SCORES**\n\n'
        total = len(media_scores)
        covered = set()

        for score in media_scores:
            if score not in covered:
                count = media_scores.count(score)
                media_text += '- **' + str(count) + '/' + str(total) + \
                              '** people scored it **' + score[0] + ' ' + score[1] + '**.\n'
                covered.add(score)

        return media_text


# Replace nicknames and common name mistakes in user input
def create_nickname_dict(nickname_db):
    nickname_dict = {}
    try:
        with open(nickname_db) as f:
            for line in f:
                line = line.rstrip('\n')
                names = line.split(':')
                if len(names) == 2:
                    nickname_dict[names[0]] = names[1]
    except FileNotFoundError:
        print('File \'' + nickname_db + '\' not found!')

    return nickname_dict


def replace_nicknames(text, nickname_dict):
    for i, j in nickname_dict.items():
        text = text.replace(i, j)
    return text


def triggered(text):
    for word in DECISION_SPELLINGS:
        if text.startswith(word + 'bot') or text.startswith(word + ' bot'):
            return True
    return False


def remove_trigger_word(text):
    for word in DECISION_SPELLINGS:
        text = text.replace(word + 'bot', '').replace(word + ' bot', '')
    return text


def generate_fail_text():
    phrases = [
        'THOUGHT YOU HAD A FIGHT BOI!!',
        'I am not impressed by your search query.',
        'Sorry, my precision was not very precise.',
        'Who da fook are these guys?'  # Try again buddeh, Try again ya goof
    ]
    num = random.random()
    if num < .9:
        return random.choice(phrases) + TROUBLESHOOT_TEXT
    else:
        return 'I couldn\'t find this fight!' + TROUBLESHOOT_TEXT


def log_message(log_name, comment_body, message):
    try:
        with open(log_name, 'a') as f:
            f.write(comment_body + '\n' + message + '\n')
            f.write('-------------\n')
    except FileNotFoundError:
        print('File \'' + log_name + '\' not found!')
        print(comment_body + '\n' + message)


def log_error(log_name, comment_body, exc_info):
    try:
        with open(log_name, 'a') as f:
            f.write(comment_body + '\n')
            traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], file=f)
            f.write('-------------\n')
    except FileNotFoundError:
        print('File \'' + log_name + '\' not found!')
        print(comment_body + '\n')
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], file=sys.stdout)


def log_comment(comment_log_name, comment_id):
    try:
        with open(comment_log_name, 'a') as f:
            f.write(comment_id + '\n')
    except FileNotFoundError:
        print('File \'' + comment_log_name + '\' not found!')
        print(comment_id)


def tester():
    nickname_dict = create_nickname_dict(config.nickname_filename)
    print('Enter fight:')
    input_fight = input()
    input_fight = replace_nicknames(input_fight, nickname_dict)
    print('Searching...')
    fight_info = fight_finder.get_score_cards_from_input(input_fight)
    if not fight_info:
        print(FAIL_TEXT)
    else:
        for fight in fight_info:
            if fight[0] is None:
                print(FAIL_TEXT)
            else:
                print(build_comment_reply(fight[0], fight[1], fight[2], fight[3]))


def main():
    # Check for debug flag
    if '-d' in sys.argv:
        logger.setLevel(logging.INFO)
        fight_finder.logger.setLevel(logging.INFO)

    # Authentication
    reddit = praw.Reddit(
            client_id=config.my_client_id,
            client_secret=config.my_client_secret,
            user_agent=config.my_user_agent,
            username=config.my_username,
            password=config.my_pw)

    log_name = config.log_name
    comment_log_name = config.comment_log_name

    # Open log of previous bot comments
    try:
        with open(comment_log_name, 'r') as f:
            commented_list = f.read().splitlines()
        # If over 100 comment ids are saved, remove half
        if len(commented_list) > 100:
            with open(comment_log_name, 'w') as f:
                f.write('\n'.join(commented_list[-50:]) + '\n')
    except FileNotFoundError:
        error_text = 'File \'' + comment_log_name + '\' not found!'
        print(error_text)
        exc_info = sys.exc_info()
        log_error(log_name, error_text, exc_info)
        sys.exit(1)

    # Create the dictionary of nicknames to be replaced
    nickname_dict = create_nickname_dict(config.nickname_filename)

    # Monitoring incoming comment stream from subreddit
    subreddit = reddit.subreddit(config.target_subreddits)

    for comment in subreddit.stream.comments():
        text = comment.body.lower().strip()
        # Found a match
        if triggered(text):
            try:
                # Make sure bot hasn't already commented
                if comment.id not in commented_list:
                    # Only take the first line of comment
                    if '\n' in text:
                        text = text.split('\n')[0]

                    # Remove 'decisionbot' string, whitespace, and punctuation
                    input_fight = remove_trigger_word(text).strip(string.punctuation + ' ')

                    # Replace nicknames in input
                    input_fight = replace_nicknames(input_fight, nickname_dict)

                    # Retrieve the score cards
                    fight_info = fight_finder.get_score_cards_from_input(input_fight)

                    logger.info('Sending reply to initial comment...')
                    if not fight_info:
                        comment.reply(generate_fail_text())
                        log_comment(comment_log_name, comment.id)
                    else:
                        count = 0
                        for fight in fight_info:
                            if fight[0] is None:
                                comment.reply(generate_fail_text())
                                log_comment(comment_log_name, comment.id)
                                break
                            else:
                                # Make sure the bot isn't commenting too fast
                                if count != 0:
                                    time.sleep(2)
                                    logger.info('Sending reply with next fight...')
                                count += 1
                                comment.reply(build_comment_reply(fight[0], fight[1], fight[2], fight[3]))
                                log_comment(comment_log_name, comment.id)

                    logger.info('Success!')

                    # Let me know that the bot has been triggered.
                    # Permalink requires different formatting for desktop vs. mobile website.
                    permalink = 'www.reddit.com' + comment.permalink(fast=True)
                    reddit.redditor(config.personal_username).message(
                        'DecisionBot triggered',
                        comment.body
                        + '\n\nMobile: \n\n' + permalink.replace('//', '/')
                        + '\n\nDesktop: \n\n' + permalink)

            except Exception:
                logger.info('Error occurred.')
                exc_info = sys.exc_info()
                log_error(log_name, comment.body, exc_info)
                try:
                    comment.reply(FAIL_TEXT)
                    log_comment(comment_log_name, comment.id)
                except praw.exceptions.PRAWException:
                    exc_info = sys.exc_info()
                    log_error(log_name, comment.body, exc_info)
                    try:
                        if comment.author is not None:
                            reddit.redditor(comment.author.name).message(
                                'Sorry!', 'There was an error with DecisionBot- I will look into this issue ASAP.')
                            log_comment(comment_log_name, comment.id)
                    except praw.exceptions.PRAWException:
                        exc_info = sys.exc_info()
                        log_error(log_name, comment.body, exc_info)


if __name__ == '__main__':
    main()
