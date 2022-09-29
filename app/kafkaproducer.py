import tweepy
from kafka import KafkaProducer
import time
import json

time.sleep(20)

#Tweepy setup
"""API ACCESS KEYS"""

apiKey = "RbbsuJ9myR7qKHJC4mPrlRklS"
apiKeySecret = "5kd4NtnpbISvLQJw8mru4divYEDEyqbxi871lCqAlF7VG11rDN"
accessToken = "90423687-noq5jGpy7aq9qxaInNoshzhSNqHx7aDSjm448ImaJ"
accessTokenSecret = "e5Q1FQJbPL2C6z21DKxDFPEbs87djvEIwkyX4xb8CpbF7"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAJNygwEAAAAA%2FWcguEkxtL8GwPn5JLzTAVjOy%2FY%3D5I3yMuM6LZZg9RPkJ8e1a9eOF3R7WbARqOrIT79qltSnCbN3zz"

auth = tweepy.OAuth1UserHandler(apiKey,apiKeySecret,accessToken,accessTokenSecret)
api = tweepy.API(auth)
client = tweepy.Client(bearer_token=BEARER_TOKEN)

#Initialisation du producer
producer= KafkaProducer(bootstrap_servers=["kafka:9092"], value_serializer=lambda v: json.dumps(v).encode('utf-8'))
topic_name = 'twitter_topic'

#Terms we want to filter
search_terms = ["#Qatar2022", "#WorldCup2022", "Qatar 2022", "worldcup2022"]

#Class to create the stream
class MyStream(tweepy.StreamingClient):
    def on_connect(self):
        print("Connected")
    
    def on_tweet(self, tweet):
        #Remove retweet and reply
        if tweet.referenced_tweets == None and tweet.lang =="en":
            tweet_data = tweet.created_at.strftime('%d/%m/%Y %H:%M:%S')+ ' ' + tweet.text
            producer.send(topic_name, value=tweet_data)
            producer.flush()
            print(tweet_data)
            
            #Just to not be overwhelmed
            time.sleep(0.2)

#Create the stream with the autentification    
stream = MyStream(bearer_token=BEARER_TOKEN)

#Looking for tweets that contains one of this terms
for term in search_terms:
    stream.add_rules(tweepy.StreamRule(term))

#Launch the stream with this argument to remove retweet and reply
stream.filter(tweet_fields=["referenced_tweets", "lang", "created_at"])
   