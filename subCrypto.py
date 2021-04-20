import datetime
import requests
import json
import os
import time
import csv
import pandas
import math



#-----------------------------Edit these values -------------------------

#Including posts on start date but up to the end date i.e. not including posts on the end date
#Year, Month, Day
#Dont use extra zeros for the month like '02' that will throw an error
startDate = datetime.datetime(2021, 1, 1)
endDate = datetime.datetime(2021, 2, 27)
#Subreddit Name, this is case sensitive.
subreddit = "cryptocurrency"

#Find attributes from json request, only attributes, sub-attributes wont work here.
#Note id here is the post id.

#For example in this post url https://www.reddit.com/r/Bitcoin/comments/lqdd5u
# lqdd5u is the id of the post.
attributes = ['author', 'id', 'created_utc', 'is_submitter', 'body', 'link_id', 'parent_id', 'score', 'total_awards_received', 'banned_at_utc']
#------------------------------------------------------------------------




fileName = 'Comments-{}-{}-{}-CreatedOn-{}.csv'.format(subreddit,startDate.strftime('%d%m%y'),endDate.strftime('%d%m%y'),datetime.datetime.now().strftime("%d%m%y-%H%M%S"))
#Create empty csv file
with open(fileName, 'w+') as output:
    pass

print("Filename :" + fileName)
print("Subreddit :" + subreddit)
print("From {}  To {}".format(startDate.strftime('%A %d %B %Y'),endDate.strftime('%A %d %B %Y')))




#Get max server requests per minute
meta = json.loads(requests.get("https://api.pushshift.io/meta").text)
rateLimit = int(meta['server_ratelimit_per_minute'])
reqsPerSec = rateLimit/60
print("Current Rate Limit/min: " + str(rateLimit))

jsonEmpty = False
data = []
lastPostTS = startDate.timestamp()


counter = 0
postCount = 0

thousand = 1


def offload(data):
    #Append to end of csv file
    with open(fileName, 'a', newline='', encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerows(data)
        

#LoadCleanCSV
# dfCSV = pandas.read_csv("WallStreetBetsGoodPosts.csv")


#Loop until the get request has no more entries
while not jsonEmpty:
    time.sleep(0.45)
    print("\nGetting posts after {}".format(datetime.datetime.fromtimestamp(lastPostTS).strftime('%d-%m-%y - Time %H%M%S')))

    reqURL = "https://api.pushshift.io/reddit/search/comment/?size=500&subreddit={}&after={}&before={}&sort=asc&author=![deleted]".format(subreddit,int(lastPostTS), int(endDate.timestamp()))
    # print(reqURL)
    
    #Get Request
    req = requests.get(reqURL)
    print("Request Status : " + str(req.status_code))
    
    #Retry request until success with 5 second cooldown
    while req.status_code != requests.codes.ok:
        time.sleep(5)
        req = requests.get(reqURL)
        print("Request Status : " + str(req.status_code))


    #Count request
    counter += 1


    #Start Timer on first request.
    if counter == 1:
        start = time.time()
        time.sleep(0.5)
    #Get the total time
    timeElapsed = time.time() - start

    #If above half the rate limit then
    if (counter/timeElapsed) > reqsPerSec*0.5:    
        #Calculate the pause time to stay within the rate limit, plus 0.5 seconds safety.
        pauseTime = max(0,(counter*(1/reqsPerSec))-timeElapsed)+0.5
        print("Waiting {} seconds...".format(pauseTime))
        time.sleep(pauseTime)
        
    

    jsonReq = json.loads(req.text)
    #Check if json is empty
    jsonEmpty = len(jsonReq['data']) == 0
    postCount += len(jsonReq['data'])

    if not jsonEmpty:
        #Get time of last submission post in json
        lastPostTS = jsonReq['data'][-1]['created_utc']


        #Append new data
        #Only append the correct attributes.
        for item in jsonReq['data']:
            
            row = []
            for attribute in attributes:
                if attribute in item:
                    row.append(item[attribute])
                else:
                    row.append("")
            
            data.append(row)


        #Offload data into file every 1000 posts
        if math.ceil(postCount/1000) > thousand:
            thousand += 1
            offload(data)

            #Empty data array
            data = []


        print("Filesize MB: " + str(int(os.path.getsize(fileName))/1000000))
        print("Num of posts: " + str(postCount))


#Final offload
for item in jsonReq['data']:
            
    row = []
    for attribute in attributes:
        if attribute in item:
            row.append(item[attribute])
        else:
            row.append("")
            
    data.append(row)

offload(data)

print("Done!")
# from google.colab import files
# files.download(fileName)