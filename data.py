
import datetime
import pymongo
from dateutil import parser


# the passwords needed to get access in the twitter api
consumer_key = "your consumer key here"
consumer_secret = "your consumer key secret here"
access_token = "your access token here"
access_token_secret = "your access token secret here"
bearer_token = "your bearer token here"


class TweetData(object):
    def __init__(self):
        self.db_link = self.get_connection()
        self.collections = {}
        self.db = self.db_link["twitter"]

    def stream_data(self):
        """
        search data from tweepy api through specific keywords
        :return: data-->dic
        """

    def get_connection(self):
        """
        get the connection with mongodb
        through the url link
        :return: client
        """
        client = pymongo.MongoClient(
                "mongodb+srv://wz2581:Zwxangel.72700@cluster0.xwejf.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
            )
        return client

    def init_db(self, movie):
        """
        initialize the database "twitter" with collection "records"
        with attributes: time, location, txt
        :return: records_collection
        """
        records_collection = self.db[movie]
        self.collections[movie] = records_collection
        return records_collection

    def insert_db(self, data, movie):
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
        date = data['data']['created_at']
        if type(date) != datetime.datetime:
            data['data']['created_at'] = parser.parse(date)

        if 'created_at' in user:
            data['data']['joined_at'] = parser.parse(user['created_at'])
        else:
            data['data']['joined_at'] = None

        if 'public_metrics' in user:
            data['data']['followers_count'] = user['public_metrics']['followers_count']
        else:
            data['data']['followers_count'] = 0

        if 'referenced_tweets' in data['data'] and data['data']['referenced_tweets'][0]['type']=='retweeted':
            data['data']['text'] = data['includes']['tweets'][0]['text']
            del data['data']['referenced_tweets']

        print(data['data'], '\n')
        self.collections[movie].insert_one(data['data'])

    def extract_db_bylocation(self, movie, country):
        """
        extract needed data records from database
        :return:
        """
        query = {"country": country}
        rst = self.db[movie].find(query)
        for i in rst:
            print(i)

    def extract_db_bytime(self, movie, start_time, end_time):
        """
        extract data from database by time range
        :param movie: the name of movie (string)
        :param start_time: the start time of the time range(datetime)
        :param end_time: the end time of the time range(datetime)
        :return: a dictionary of data records
        """
        query = {"created_at": {"$gte": start_time,
                                "$lt": end_time}}

        rst = self.db[movie].find(query)
        output = {}
        for i in rst:
            output[i['_id']] = i
        print(output)
        return output

    def clear_db(self, movie):
        """
        drop the specific movie collection from database
        :param movie: the collection name(string
        :return: None
        """
        if self.collections[movie].drop():
            print("Collection "+movie+" has been dropped...")


if __name__ == "__main__":
    d = TweetData()
    rst = d.extract_db_bytime("spider man", datetime.datetime(2022, 4, 23, 20, 3, 30),
                              datetime.datetime(2022, 4, 23, 20, 52, 58))