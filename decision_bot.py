import sys
import praw
import pprint
import re
import string
import fight_finder


my_client_id = 'cl2sjC0O7UZ0Hg'
my_client_secret = 'xvD_JhO8g2Nbo26uGGXAK--Lc64'
my_user_agent = 'mac:com.example.testapp:v0.0.0 (by /u/DecisionBot)'
my_username = 'DecisionBot'
my_pw = 'american cheese father'

"""
my_client_id='f5eccy2vjdeWxw',
my_client_secret='JEdwRZ2bn4Fn-nNvwRVaUulRXO0',
my_user_agent='mac:com.example.myredditapp:v0.0.0',
my_username='KX2O',
my_pw='speedyx811')
"""

versus_list = ['v', 'v.', 'vs', 'vs.', 'versus', 'versus.']

def main():
    # Authentication
    reddit = praw.Reddit(
            client_id=my_client_id,
            client_secret=my_client_secret,
            user_agent=my_user_agent,
            username=my_username,
            password=my_pw)

    # Monitoring incoming comment stream from r/mma
    subreddit = reddit.subreddit('mma')
    for comment in subreddit.stream.comments():
        text = comment.body.lower()
        if 'decisionbot' in text:
            print(comment.body)
            # Remove decisionbot string, remove whitespace
            text = text.replace('decisionbot', '').strip(string.punctuation + ' ').strip()

            for word in versus_list:
                # Figure out regex
                #index = re.search(r'\b'+'word'+'\b', text)

                index = text.find(word)
                if index != -1:
                    fighter_1 = text[:index]
                    fighter_2 = text[index+3:]
                    print(fighter_1)
                    print(fighter_2)
                    fight_url = fight_finder.get_fight_url(fighter_1, fighter_2)
                    comment.reply(fight_finder.get_score_tables(fight_url))
                    print('Replying!')
                    break



if __name__ == '__main__':
    main()