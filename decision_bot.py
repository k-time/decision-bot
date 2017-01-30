import sys
import praw
import pprint


def main():
	reddit = praw.Reddit(
			client_id='cl2sjC0O7UZ0Hg',
			client_secret='xvD_JhO8g2Nbo26uGGXAK--Lc64',
			user_agent='mac:com.example.testapp:v0.0.0 (by /u/DecisionBot)',
			username='DecisionBot',
			password='american cheese father')

	subreddit = reddit.subreddit('mma')
	for comment in subreddit.stream.comments():
		text = comment.body.lower()
		if 'decisionbot' in text:
			print(text)






if __name__ == '__main__':
	main()