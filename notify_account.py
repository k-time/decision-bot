import praw
import yaml


def main():
    # Load configs
    with open('config.yaml', 'r') as cfg_file:
        cfg = yaml.load(cfg_file, yaml.FullLoader)

    # Authentication
    reddit = praw.Reddit(
        client_id=cfg['client_id'],
        client_secret=cfg['client_secret'],
        user_agent=cfg['user_agent'],
        username=cfg['username'],
        password=cfg['pw'])

    # Notify my account
    reddit.redditor(cfg['personal_username']).message(
        'DecisionBot starting', 'Attempting to start in background...')


if __name__ == '__main__':
    main()
