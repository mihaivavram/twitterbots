import tweepy
import os
import sys
import random
import logging
import json

from multiprocessing import Queue, Process
"""
Retrieves a sample dataset of accounts from a file
"""

# DEFAULT_PERCENTAGE = 100
# DEFAULT_MIN_ID = 0
# DEFAULT_MAX_ID = 5000000000

logger = logging.getLogger(__name__)


def fetch_accounts_from_file(api,
                             account_queue,
                             account_provision_file):
    """Fetches accounts from a file

    Arguments:
        api {tweepy.API} -- The authenticated API instance
        min_id {int} -- The starting account ID
        max_id {int} -- The maximum max ID
        queue {Queue} -- The queue to send found accounts to

    Keyword Arguments:
        percentage {int} -- The percentage of accounts between min_id and
            max_id to fetch (default: {100})
    """
    logger.info('Account fetching from file started')

    account_ids = []
    with open(account_provision_file, 'r') as read_file:
        data = json.load(read_file)
        account_ids = data['account_ids']

    if len(account_ids) > 0:
        completed = False
        num_account_ids = len(account_ids) - 1
        for i in range(0, num_account_ids, 100):
            left_ix = i
            right_ix = i + 99
            if right_ix > num_account_ids:
                right_ix = num_account_ids
                completed = True
            try:
                results = api.lookup_users(
                    user_ids=account_ids[left_ix:right_ix],
                    include_entities=True)
            except Exception as e:
                logger.error(e)
            for result in results:
                user = result._json
                user['_tbsource'] = 'enum'
                account_queue.put(user)
            logger.debug('\t{} results found. Last account found: {}'.format(
                len(results), account_ids[right_ix]))

            if completed:
                break

def main():
    consumer_key = os.environ.get('TWEEPY_CONSUMER_KEY')
    consumer_secret = os.environ.get('TWEEPY_CONSUMER_SECRET')
    access_token = os.environ.get('TWEEPY_ACCESS_TOKEN')
    access_token_secret = os.environ.get('TWEEPY_ACCESS_TOKEN_SECRET')

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(
        auth, wait_on_rate_limit_notify=True, wait_on_rate_limit=True)

    q = Queue()

    if len(sys.argv) < 2:
        print('Usage: python3 accounts_from_file.py input-accounts.json')
        sys.exit()
    account_provision_file = sys.argv[1]

    try:
        p = Process(
            target=fetch_accounts_from_file,
            args=[api, q, account_provision_file])
        p.start()
        while True:
            try:
                elem = q.get()
                print(elem)
            except Exception as e:
                print(e)
    except KeyboardInterrupt:
        print('\nCtrl+C detected. Shutting down...')
        p.terminate()
        p.join()


if __name__ == '__main__':
    main()
