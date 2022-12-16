import os
import json
from google.cloud import pubsub_v1
from google.cloud import bigquery
from concurrent.futures import TimeoutError
import time
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from utils import clean
from dateutil import parser
import numpy as np

# environment variable setup for private key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/cengwenxin/Desktop/heroic-outpost-362100-d65845db5a1c.json"

# GCP topic, project & subscription ids
PUB_SUB_PROJECT = "heroic-outpost-362100"

# Pub/Sub consumer timeout
timeout = 5.0

client = bigquery.Client()


def process_payload(message):
    data = json.loads(message.data)
    message.ack()
    sentiment_score = (calculate_sentiment(data['text']).get('compound')*5)+5
    print(f"Received {data}." + 'score: ' + str(sentiment_score))
    created_at = data['created_at']
    text = data['text']
    row = [{"created_at": created_at, "text": text, "sentiment_score": sentiment_score}]
    errors = client.insert_rows_json(TABLE, row)
    if errors == []:
        print("New row has been added")
    else:
        print("Encounted errors: ", errors)


    # print('score: ', sentiment_score)
    # latest = model_sentiment(data['text'], self._sentiment, 0.99)


def calculate_sentiment(data):
    _data = data
    t = clean(_data)
    cal_sentiment = SentimentIntensityAnalyzer().polarity_scores(t)
    return cal_sentiment


# consumer function to consume messages from a topics for a given timeout period
def consume_payload(project, subscription, callback):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project, subscription)
    print(f"Listening for messages on {subscription_path}..\n")
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result()
            # time.sleep(5)
            # streaming_pull_future.cancel()
        except TimeoutError:
            streaming_pull_future.cancel()


# loop to test producer and consumer functions with a 3 second delay
if __name__ == "__main__":
    PUB_SUB_TOPIC = "GlassOnion"
    PUB_SUB_SUBSCRIPTION = PUB_SUB_TOPIC + "-sub"
    TABLE = "heroic-outpost-362100.movie_tweets." + PUB_SUB_TOPIC.lower()
    while True:
        print("===================================")
        consume_payload(PUB_SUB_PROJECT, PUB_SUB_SUBSCRIPTION, process_payload)
        time.sleep(5)
