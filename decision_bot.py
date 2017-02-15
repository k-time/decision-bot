import sys
import praw
import string
import fight_finder
import user_info

fail_text = 'I couldn\'t find this fight! Try checking your spelling, or perhaps the ' \
            'fight didn\'t end in a decision. Please let me know if I\'ve made a mistake.'


def build_comment_reply(score_tables, fight_result, media_scores):
    comment = fight_result + '\n\n'

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
        media_text = '**MEDIA SCORES**\n\n'
        total = len(media_scores)
        covered = set()

        for score in media_scores:
            if score not in covered:
                count = media_scores.count(score)
                media_text += '* **' + str(count) + '/' + str(total) + \
                              '** media member(s) scored it **' + score[0] + ' ' + score[1] + '**.\n'
                covered.add(score)

        return media_text


def log_message(log_name, comment_body, message):
    try:
        with open(log_name, 'a') as f:
            f.write(comment_body + '\n' + message + '\n')
            f.write('-------------\n')
    except FileNotFoundError:
        print('File \'' + log_name + '\' not found!')
        print(comment_body + '\n' + message)


def log_error(log_name, comment_body, e):
    try:
        with open(log_name, 'a') as f:
            f.write(comment_body + '\n' + str(e) + '\n')
            f.write('-------------\n')
    except FileNotFoundError:
        print('File \'' + log_name + '\' not found!')
        print(comment_body + '\n' + str(e))


def log_comment(comment_log_name, comment_id):
    try:
        with open(comment_log_name, 'a') as f:
            f.write(comment_id + '\n')
    except FileNotFoundError:
        print('File \'' + comment_log_name + '\' not found!')
        print(comment_id)


def tester():
    print('Enter fight:')
    input_fight = input()
    print('Searching...')
    score_tables, fight_result, media_scores = fight_finder.get_score_cards_from_input(input_fight)
    if score_tables is None:
        print(fail_text)
    else:
        print(build_comment_reply(score_tables, fight_result, media_scores))


def main():
    # Authentication
    reddit = praw.Reddit(
            client_id=user_info.my_client_id,
            client_secret=user_info.my_client_secret,
            user_agent=user_info.my_user_agent,
            username=user_info.my_username,
            password=user_info.my_pw)

    log_name = '/home/ubuntu/decision_bot/log.txt'
    comment_log_name = '/home/ubuntu/decision_bot/commented.txt'

    # Open log of previous bot comments
    try:
        with open(comment_log_name, 'r') as f:
            commented_list = f.read().splitlines()
        # If over 100 comment ids are saved, remove half
        if len(commented_list) > 100:
            with open(comment_log_name, 'w') as f:
                f.write('\n'.join(commented_list[-50:]) + '\n')
    except FileNotFoundError as e:
        error_text = 'File \'' + comment_log_name + '\' not found!'
        print(error_text)
        log_error(log_name, error_text, e)
        sys.exit(1)

    # Monitoring incoming comment stream from r/mma
    subreddit = reddit.subreddit('bottesting')

    for comment in subreddit.stream.comments():
        text = comment.body.lower().strip()
        # Found a match
        if text.startswith('decisionbot') or text.startswith('decision bot'):
            try:
                # Make sure bot hasn't already commented
                if comment.id not in commented_list:
                    # Only take the first line of comment
                    if '\n' in text:
                        text = text.split('\n')[0]
                    # Remove 'decisionbot' string, whitespace, and punctuation
                    input_fight = text.replace('decisionbot', '')\
                        .replace('decision bot', ' ').strip(string.punctuation + ' ')
                    # Retrieve the score cards
                    score_tables, fight_result, media_scores = fight_finder.get_score_cards_from_input(input_fight)
                    if score_tables is None:
                        comment.reply(fail_text)
                        log_comment(comment_log_name, comment.id)
                    else:
                        comment.reply(build_comment_reply(score_tables, fight_result, media_scores))
                        log_comment(comment_log_name, comment.id)

            except Exception as e:
                log_error(log_name, comment.body, e)
                try:
                    comment.reply(fail_text)
                    log_comment(comment_log_name, comment.id)
                except praw.exceptions.PRAWException as e:
                    log_error(log_name, comment.body, e)
                    try:
                        if comment.author is not None:
                            reddit.redditor(comment.author.name).message(
                                'Sorry!', 'There was an error with DecisionBot- I will look into this issue ASAP.')
                    except praw.exceptions.PRAWException as e:
                        log_error(log_name, comment.body, e)


if __name__ == '__main__':
    main()
