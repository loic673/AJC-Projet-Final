import findspark

findspark.init("")
import pyspark
from pyspark.sql import functions as F
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr, udf, to_timestamp
from pyspark.sql.types import *
from textblob import TextBlob
import pymongo
import re
import time

time.sleep(200)

print("modules imported")

KAFKA_TOPIC_NAME_CONS = "twitter_topic"
KAFKA_BOOTSTRAP_SERVERS_CONS = "kafka:9092"

print("PySpark Structured Streaming with Kafka Application Started ...")

spark = (
    SparkSession.builder.master("spark://spark:7077")
    .appName("TwitterSentimentAnalysis")
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2") 
    .getOrCreate()
)

print("Now time to connect to Kafka broker to read Invoice Data")

spark.sparkContext.setLogLevel("ERROR")
print(" kafka Started ...")
# Construct a streaming DataFrame that reads from twitter
df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS_CONS)
    .option("subscribe", KAFKA_TOPIC_NAME_CONS)
    .load()
)

# retrieve date
def retrieve_date(tweet: str):
    dt_string = tweet[:20]
    dt_string = dt_string.replace('"','')
    return dt_string

def cleanTweet(tweet: str):
    tweet = str(tweet[21:])
    tweet = re.sub(r'http\S+', '', str(tweet)) # remove URLs
    tweet = re.sub(r'bit.ly/\S+', '', str(tweet)) #  remove URLs
    # tweet = re.sub(r'[link]', '', str(tweet)) # remove "[link]" text
 
    # remove @users
    tweet = re.sub(r'@\S+', '', str(tweet))

    #remove patterns "\X" X = letter or number
    tweet = re.sub(r'\\\w+', '', str(tweet))

    # remove numbers
    tweet = re.sub(r'[0-9]+', '', str(tweet))

    # remove hashtag symbol
    tweet = re.sub(r'#', '', str(tweet))

    # remove special characters
    tweet = re.sub(r'\W+', ' ', str(tweet))

    return tweet

# Create a function to get the subjectifvity
def getSubjectivity(tweet: str) -> float:
    return TextBlob(tweet).sentiment.subjectivity


# Create a function to get the polarity
def getPolarity(tweet: str) -> float:
    return TextBlob(tweet).sentiment.polarity


def getSentiment(polarityValue: int) -> str:
    if polarityValue < 0:
        return 'Negative'
    elif polarityValue == 0:
        return 'Neutral'
    else:
        return 'Positive'

class WriteRowMongo:
    def open(self, partition_id, epoch_id):
        #self.myclient = pymongo.MongoClient("db", username="root", password="secret")
        self.myclient = pymongo.MongoClient("mongodb://yohancaillau:KahlanAmnell1@mongo:27017/")
        self.mydb = self.myclient["project_twitter"]
        self.mycol = self.mydb["tweet_data"]
        return True

    def process(self, row):
        self.mycol.insert_one(row.asDict())

    def close(self, error):
        self.myclient.close()
        return True


# Get only the "text" from the information we receive from Kafka. The text is the tweet produce by a user
values = df.selectExpr("CAST(value AS STRING)").alias("tweet")

df1 = values.select("tweet.*")

# Here, we apply the functions on UDF (User Defined Function) and then create a new column with the new data.
retrieve_date = F.udf(retrieve_date, StringType())
date = df1.withColumn("date", retrieve_date(col("tweet.value")))
date = date.withColumn("date",to_timestamp(date.date,"dd/MM/yyyy HH:mm:ss"))

clean_tweets = F.udf(cleanTweet, StringType())
raw_tweets = date.withColumn('processed_text', clean_tweets(col("tweet.value")))

subjectivity = F.udf(getSubjectivity, FloatType())
polarity = F.udf(getPolarity, FloatType())
sentiment = F.udf(getSentiment, StringType())

subjectivity_tweets = raw_tweets.withColumn('subjectivity', subjectivity(col("processed_text")))
polarity_tweets = subjectivity_tweets.withColumn("polarity", polarity(col("processed_text")))
sentiment_tweets = polarity_tweets.withColumn("sentiment", sentiment(col("polarity")))

# query to see data
"""
query = sentiment_tweets.select("date", "processed_text", "polarity", "sentiment") \
    .writeStream.format("memory").queryName("memory_spark").start()

while (query.isActive):
    time.sleep(10)
    spark.sql("select * from memory_spark").show()

query.awaitTermination()
"""
# Query to send data to MongoDB
query = sentiment_tweets.writeStream.foreach(WriteRowMongo()).start().awaitTermination()
