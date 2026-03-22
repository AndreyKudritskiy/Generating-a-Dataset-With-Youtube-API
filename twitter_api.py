import requests
import tweepy
import pandas as pd
import datetime
import time

from Query_Builder import Params

params = Params() #See Query_Builder.py; should be in working directory

keys = params.auth

# Quality of life refrences/"pointers"
media_outlets = params.media_outlets
media_outlets = [org.replace(" ","") for org in media_outlets] #twitter API does not like spaces in usernames
poi = params.people_of_intrest

# Initializing Client (using tweepy to handle authentication/API calls)
# https://docs.tweepy.org/en/stable/client.html#client
client = tweepy.Client(bearer_token=keys["twitter"])

# Getting direct id and follower count by and other useful user metrics for media outlets
# https://docs.tweepy.org/en/stable/client.html#tweepy.Client.get_users
# https://docs.tweepy.org/en/stable/expansions_and_fields.html#tweepy.user.USER_FIELDS
media_outlets_data = client.get_users(
    usernames=media_outlets,
    user_fields=['id',
                 'name',
                 'username',
                 'description',
                 'created_at',
                 'verified',
                 'public_metrics'])


#Peek at some of the data to make sure we are actually getting the correct accounts matched
for org in media_outlets_data.data[0:2]:
    print("----------------")
    print(f"id: {org.id},\n"
          f"Username: {org.username},\n"
          f"Description: {org.description},\n"
          f"Followers: {org.public_metrics['followers_count']},\n"
          f"Verified Status: {org.verified},\n"
          f"Created at: {org.created_at},\n"
          f"Tweet count: {org.public_metrics['tweet_count']},\n"
          f"Following: {org.public_metrics['following_count']},\n"
          f"Listed count: {org.public_metrics['listed_count']}"
          )

rows = []
skip_count = 0

#converting results to Pandas DataFrame
for org in media_outlets_data.data:
    rows.append({
        "id": org.id,
        "username": org.username,
        "description": org.description,
        "followers": org.public_metrics["followers_count"],
        "following": org.public_metrics["following_count"],
        "tweet_count": org.public_metrics["tweet_count"],
        "listed_count": org.public_metrics["listed_count"],
        "verified": org.verified,
        "created_at": org.created_at
        })

accounts_df = pd.DataFrame(rows)
accounts_df.to_csv("X_Media_Outlets.csv") #Saving results to csv file

id_list = [org.id for org in media_outlets_data.data]

#Getting datetime from a week ago for query.
now = datetime.datetime.utcnow().replace(microsecond=0)
start_time = now - datetime.timedelta(days=7) + datetime.timedelta(seconds=60)
end_time = now - datetime.timedelta(seconds=60)
#'end_time' must be a minimum of 10 seconds prior to the request time. Otherwise error 400 bad request.
# adding a buffer to both allows room for less time conflicts. (X API or tweepy handle close times poorly due to rounding or equivilant timestamps)

#Another set of queries, this time leveraging the id_list of user accounts that correspond to each media outlet.
for org_id in id_list:
    for name in poi:
        query_name = " OR ".join(name.split()) # Checking for either first or last name (or both) --> may recieve false positives
        query = f"({query_name} from:{org_id}) lang:en" #allowing for any language will introduce too much noise to the dataset

        #Very helpful for debugging without blowing up credits. (failed API calls can still cost money)
        try:
            tweets = client.search_recent_tweets(
                query=query,
                start_time=start_time,
                end_time=end_time,
                max_results=30,
                tweet_fields=["created_at",
                              "text",
                              "public_metrics"])
        except tweepy.TweepyException as e:
            print(f"Skipping query due to error: {e}")
            rows.append({key: None for key in ["Tweet_ID", "Created_at", "Text", "Retweets", "Replies_Count", "Likes_Count", "Quotes"]})
            skip_count += 1
            continue
        
        if not tweets.data:
            rows.append({key: None for key in ["Tweet_ID", "Created_at", "Text", "Retweets", "Replies_Count", "Likes_Count", "Quotes"]})
            skip_count += 1
            continue
        
        for tweet in tweets.data:
            rows.append({
                "Tweet_ID": tweet.id,
                "PoI": name,
                "Created_at": tweet.created_at,
                "Text": tweet.text,
                "Retweets": tweet.public_metrics['retweet_count'],
                "Replies_Count": tweet.public_metrics['reply_count'],
                "Likes_Count": tweet.public_metrics['like_count'],
                "Quotes": tweet.public_metrics['quote_count']
            })

print("Finished Dataset Generation")
print("Number of skips:",skip_count)
tweets_df = pd.DataFrame(rows)
tweets_df.to_csv("Tweets.csv")