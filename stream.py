import tweepy
from threading import Thread
import time
import json
from google.cloud import pubsub_v1
import datetime
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/cengwenxin/Desktop/heroic-outpost-362100-d65845db5a1c.json"


# the passwords needed to get access in the twitter api
bearer_token = "AAAAAAAAAAAAAAAAAAAAANxtbgEAAAAARqRWpqtsy3IMhXLObYOpMZPzMdE%3DGsndMQxD7HPC3R88LeLtpkBQ1DWvYIscOy95yBdPXIhB04fgLn"
class TweetStream(tweepy.StreamingClient):
    def __init__(self, bearer_token, **kwargs):
        super().__init__(bearer_token, **kwargs)
        self.publisher = pubsub_v1.PublisherClient()
        # self.buffer = deque()
        # self.buffer_limit = 10

    def create_rules(self, rules):
        for r in rules:
            new_rule = tweepy.StreamRule(value=rules[r], tag=r)
            self.add_rules(new_rule)

    def start_stream(self, autostop=None):
        """

        :param autostop: after "autostop" seconds the connection will stop automatically
        :param rules: the rules for filter streaming data
        :return:
        """
        def auto_stop():
            time.sleep(autostop)
            self.stop_stream()
            print("Auto-disconnecting after " + str(autostop) + " seconds....")

        if autostop is not None:
            t1 = Thread(target=auto_stop)
            t1.start()
        self.filter(tweet_fields=['created_at'], expansions=['author_id', 'referenced_tweets.id'], user_fields=['location', 'created_at', 'public_metrics'])

    def stop_stream(self):
        self.clean_rules()
        self.disconnect()

    def clean_rules(self):
        response = self.get_rules()
        for r in response.data:
            self.delete_rules(r.id)

    def insertPubsub(self, data, movie):
        """
        insert new tweets into the database
        :return:
        """
        users = {u["id"]: u for u in data['includes']['users']}
        user_id = data['data']['author_id']
        user = users[user_id]

        if 'location' in user:
            location = user['location']
        else:
            location = None

        data['data']['location'] = location
        # date = data['data']['created_at']
        # if type(date) != datetime.datetime:
        #     data['data']['created_at'] = datetime.datetime.fromtimestamp(data['data']["created_at"]).strftime('%Y-%m-%d %H:%M:%S')

        if 'created_at' not in user:
            data['data']['joined_at'] = None

        if 'public_metrics' in user:
            data['data']['followers_count'] = user['public_metrics']['followers_count']
        else:
            data['data']['followers_count'] = 0

        if 'referenced_tweets' in data['data'] and data['data']['referenced_tweets'][0]['type']=='retweeted':
            data['data']['text'] = data['includes']['tweets'][0]['text']
            del data['data']['referenced_tweets']

        print(data['data'], '\n')
        topic_path = self.publisher.topic_path('heroic-outpost-362100', movie)
        # publish to the topic, don't forget to encode everything at utf8!
        self.publisher.publish(topic_path, data=json.dumps(data['data'])
                               .encode("utf-8"))

    def on_data(self, raw_data):
        data = json.loads(raw_data)
        print(data)
        movies = data['matching_rules']  # movie names
        for i in movies:
            self.insertPubsub(data, i['tag'])
        # self.buffer.append(data)
        #
        # if len(self.buffer) > self.buffer_limit:
        #     t2 = Thread(target=self.clear_buffer)
        #     t2.start()

    def on_connection_error(self):
        print("Error: connection error!")
        self.disconnect()

    def on_errors(self, errors):
        print("Error detected, reconnecting in a few seconds...")
        self.start_stream()


if __name__ == "__main__":
    _rules = {'BlackPanther': 'black panther lang:en', 'WomanKing': 'woman king lang:en', 'BlackAdam': 'black adam lang:en', 'GlassOnion': 'glass onion lang:en', 'Slumberland': 'slumberland lang:en'}
    d = TweetStream(bearer_token)
    d.create_rules(_rules)
    d.start_stream(autostop=3600)