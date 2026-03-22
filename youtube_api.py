import googleapiclient.discovery
import pandas as pd
import random

from Query_Builder import Params

params = Params()

# Quality of life refrences/"pointers"
media_outlets = params.media_outlets
poi = params.people_of_intrest

#API authetications
keys = params.auth
api_service_name = "youtube"
api_version = "v3"
developerKey = keys["youtube"]

youtube = googleapiclient.discovery.build(
    api_service_name,
    api_version,
    developerKey=developerKey
)

#Getting channel id's
def get_channel_id(channel_name):
  request = youtube.search().list(
    part = "snippet",
    q = channel_name,
    type = "channel",
    maxResults=1
  )

  response = request.execute()

  if response['items']:
    channel_id = response['items'][0]['id']['channelId']
    return channel_id

  else:
    return None

channel_ids = [get_channel_id(name) for name in media_outlets]

#Getting channel data
def get_channel_data(channel_id):
    channel_query = youtube.channels().list(
    part='statistics,snippet',
    id=channel_id)

    response = channel_query.execute()

    if not response['items']:
        print(f"No data found for channel ID: {channel_id}")
        return None

    stats = response['items'][0]['statistics']
    snippet = response['items'][0]['snippet']

    return {
        "Channel ID": channel_id,
        "Channel Name" : snippet.get('title', None),
        "Channel Description": snippet.get('description', None),
        "Subscriber Count": stats.get('subscriberCount', None),
        "Total Views": stats.get('viewCount', None),
        "Total Videos": stats.get('videoCount', None),
        "Country": snippet.get('country', None)
    }

rows = [get_channel_data(id) for id in channel_ids if id is not None]
#exporting results
channel_data_df = pd.DataFrame(rows)
channel_data_df.to_csv("youtube_channel_data.csv")

target_videos = []

#Getting Video data ids that match what we are looking for
def get_videos(chan_id,target):
    video_query = youtube.search().list(
        part = "id",
        channelId = chan_id,
        q = target,
        type = "video",
        order = "date",
        maxResults = 1
    )

    response = video_query.execute()

    video_ids = []
    for video in response['items']:
        video_ids.append(video['id']['videoId'])

    return video_ids

for channel in channel_ids:
    for person in poi:
        if random.random() < 0.25: #sampling only 75% of our videos to deal with Youtube V3 api call limit
            continue
        target_videos.extend(
           get_videos(channel,person)
        )

def get_video_meta_data(video_ids):
    response = youtube.videos().list(
        part='snippet,contentDetails,statistics',
        id=','.join(video_ids)
    ).execute()

    rows = []
    for item in response['items']:
        snippet = item['snippet']
        contentDetails = item['contentDetails']
        statistics = item['statistics']
        rows.append({
            "Title": snippet.get('title', None),
            "Published": snippet.get('publishedAt', None),
            "Channel": snippet.get('channelTitle', None),
            "Views": statistics.get('viewCount', None),
            "Likes": statistics.get('likeCount', None),
            "Comments": statistics.get('commentCount', None),
            "Shares": statistics.get('shareCount', None),
            "Description": snippet.get('description', None),
            "Tags": snippet.get('tags', 'No Tags'),
            "Captions": contentDetails.get('caption', None),
            "Duration": contentDetails.get('duration', None),
            "Default Language": snippet.get('defaultLanguage', 'No Default Language')
        })
    return rows

rows = []
chunk_size = 50
for i in range(0, len(target_videos), chunk_size):
    chunk = [v for v in target_videos[i:i+chunk_size] if v is not None]
    rows.extend(get_video_meta_data(chunk))

video_data_df = pd.DataFrame(rows)
video_data_df.to_csv("youtube_videos.csv")
print("Data Exported")