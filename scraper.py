import requests
import praw
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

repo=[]
searchRequests=[]

cluster = MongoClient(os.getenv("mongo_url"))
db = cluster["linkrepo"]

credentials = {
    "client_id": os.getenv("client_id"),
    "client_secret": os.getenv("client_secret"),
    "user_agent": os.getenv("user_agent"),
    "username": os.getenv("username"),
    "password": os.getenv("password")
}

reddit = praw.Reddit(
    client_id=credentials["client_id"],
    client_secret=credentials["client_secret"],
    user_agent=credentials["user_agent"],
    username=credentials["username"],
    password=credentials["password"]
)

'''
    Utility function which checks if:
    x is a thing in a dict
    x is a string, thing is the name of a key in a dictionary,
    and _dict is a dict to search through
'''
def isXThingInDict(x, thing, _dict):
    for entry in _dict:
        if entry[thing] == x:
            return True
    return False



'''
    Go through all found Reddit comments with search requests and attempt to 
    reply to them. Calls the replyTo() function for each comment/reply.
'''
def sendReplies():
    #print(searchRequests)
    for content in searchRequests:
        replyTo(content)



'''
    Checks if a comment containing a search request has been replied to,
    if not: send reply
    otherwise: don't send duplicate reply
    Before ending, delete current comment from searchRequests array
    and recursiely call sendReplies to iterate through the new 
    searchRequests array.
'''
def replyTo(content):
    for reply in content.replies:
        if reply.author == "bot176":
            searchRequests.remove(content)
            sendReplies()
            #print("done")
            return False 
    #print("content")
    elements = content.body.split(" ")
    searchTerm = elements[2]
    results = []
    for entry in repo:
        if searchTerm in entry["keywords"]:
            results.append(entry)
    if len(results) == 0:
        content.reply("No results found.")
    else:
        replyString = ""
        for entry in results:
            replyString = replyString + str(entry["link"]) + "\n"
        content.reply(replyString)
    searchRequests.remove(content)
    sendReplies()
    return True


'''
    ADD:    [t|temp <#>h|d      -> auto removes link after # hours or days]
            [n|nsfw             -> lets everyone know and bot replies with tag]
    SEARCH: [l|link             -> searches for results matching the link ONLY]
            [a|all              -> searches for results matching the link OR keywords]
    BOTH:   [s|sub|subreddit    -> limits link or search to current sub only]
            [q|quiet            -> does not respond to comment & gives resuts in PM]
    MOD:    [n|nsfw]            -> enforces all links in sub to NSFW]
            [s|sub|subreddit    -> enforces all links/searches to be sub limited]
            [q|quiet            -> enforces all bot activity to be quiet]
            [b|ban              -> bans/blacklists subreddit from bot]
            [d|delete           -> deletes link made by parent comment (mod replies)]
            [r|reset            -> resets subreddit settings]
'''
def applyFlags(content, command, keywords, flags):
    pass



'''
    Searches Reddit comment for bot wake phrase and either:
    adds new link to DB or,
    adds searchRequest to array (searched after all comments are
    searched so that new links are also included in searchRequest reply)

    !linkrepo [add|search|mod] <link URL> [keywords] [-flags]*
'''
def searchForWake(content):
    if content.body.startswith("!linkrepo"):
        elements = content.body.split(" ", 3)
        keywords = []
        flags = []
        if len(elements) >= 4:
            flags = elements[3].split(" -")
            keywordsText = flags.pop(0)
            if "," in keywordsText:
                keywords = keywordsText.split(",")
            else:
                keywords = [keywordsText]
            for i in range (0,len(keywords)):
                keywords[i] = keywords[i].strip()
            applyFlags(content, elements[1], keywords, flags)
            print(flags)
        if "add" == elements[1] and not isXThingInDict(content.id, "id", repo):
            newLink = {
                "id": str(content.id),
                "link": str(elements[2]),
                "author": str(content.author),
                "keywords": keywords
            }
            repo.append(newLink)
            db["links"].insert_one(newLink)
            print (repo)
        elif "search" == elements[1] and content not in searchRequests:
            searchRequests.append(content)



'''
    TO-DO: make into loop
    MAIN FUNCTION
    Pulls current DB and stores locally
    Iterates through all recent comments and replies to comments
    Calls searchForWake for each comment
    Calls sendReplies for searchRequests after iterating through all comments
'''
x = 0
while x < 1:
    linksFromDB = db["links"].find()
    for link in linksFromDB:
        repo.append(link)
    #print(repo)
    subreddit = reddit.subreddit("cdwtesting")
    for submission in subreddit.new():
        for comment in submission.comments:
            searchForWake(comment)
            for reply in comment.replies:
                searchForWake(reply)
    #print(searchRequests)
    sendReplies()
    x = x + 1
    repo=[]







# URL = 'https://en.wikipedia.org/wiki/Mount_Funagata'
# headers = {"User-Agent": 'Mozilla/5.0 (X11; CrOS x86_64 12607.81.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.119 Safari/537.36'}
# page = requests.get(URL, headers=headers)
# soup = BeautifulSoup(page.content, 'html.parser').prettify()
# title = soup.find(id="productTitle").get_text()
# print(soup)