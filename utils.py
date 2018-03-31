import apiai
import json
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient


MONGODB_URI = "**********************************************"
client = MongoClient(MONGODB_URI)
db = client.get_database("*********************************")
wikisearchs = db.wikisearch
apisearchs = db.apisearch

# api.ai client
APIAI_ACCESS_TOKEN = "**************************************"
ai = apiai.ApiAI(APIAI_ACCESS_TOKEN)

key = "*************************************"

def wiki_scraping(wiki_url , location):
    r = requests.get(wiki_url)
    soup = BeautifulSoup(r.content , "html5lib")
    h = soup.findAll("h2")
    h.reverse()
    h.pop()
    h.reverse()
    count = 0
    contents = []
    for i in h:
        if count<10:
            kfc = i.text.split("[edit]")[0]
            contents.append((kfc , "show me "+kfc+" of "+location))
            count = count+1
        else:
            break
    return contents

def content_scraping(wiki_url):
    r = requests.get(wiki_url)
    soup = BeautifulSoup(r.content , "html5lib")
    table = soup.find("tbody")
    trs = table.findAll("tr")
    datas = "\n"
    for tr in trs:
        try:
            data = " "
            th = tr.find("th")
            td = tr.find("td")
            data = th.text + " -> " + td.text
        except:
            continue
        datas = datas + "\n " + data
    return datas

def get_place(params):
    """
    function to fetch place from google place finder API
    """
    GOOGLE_PLACE_FINDER_API = "**********************************************"
    params['key'] = key
    resp = requests.get(GOOGLE_PLACE_FINDER_API , params = params)
    return resp.json()

def apiai_response(query, session_id):
    """
    function to fetch api.ai response
    """
    request = ai.text_request()
    request.lang='en'
    request.session_id=session_id
    request.query = query
    response = request.getresponse()
    return json.loads(response.read().decode('utf8'))


def parse_response(response):
    """
    function to parse response and 
    return intent and its parameters
    """
    result = response['result']
    params=result.get("parameters")
    intent=result['metadata'].get('intentName')
    return intent,params
    
def fetch_reply(query, session_id):
    """
    main function to fetch reply for chatbot and 
    return a reply dict with reply 'type' and 'data'
    """
    response = apiai_response(query, session_id)
    intent, params = parse_response(response)
    reply = {}
    
    if response['result']['action'].startswith('smalltalk'):
        reply['type'] = 'smalltalk'
        reply['data'] = response['result']['fulfillment']['speech']

    elif intent == "wikipedia":
        reply['type'] = "wiki"
        wikisearch = wikisearchs.find_one({"placename":params.get('input') , "content_type":params.get("contents")})
        if wikisearch:
            reply["data"] = wikisearch["data"]
            if wikisearch.get("contents"):
                reply["contents"] = wikisearch["contents"]
            if wikisearch.get("url"):
                reply["url"] = wikisearch["url"]
        else:
            wiki1 = params.get('input').replace(" " , "_")
            wiki2 = "https://en.wikipedia.org/wiki/"+wiki1
            cont = params.get('contents')
            if cont.endswith(" "):
                wikilist = list(cont)
                wikilist.pop()
                cont = ''.join(str(z) for z in wikilist)
            if cont == "info":
                datas = content_scraping(wiki2)
                contents = wiki_scraping(wiki2, params.get('input'))
                reply['data'] = datas
                reply['contents'] = contents
                a = {}
                a["placename"] = params.get("input")
                a["content_type"]=params.get("contents")
                a["data"] = datas
                a["contents"] = contents
                wikisearchs.insert_one(a)
            else:
                # show some info about the content and a redirect button
                responseobject = requests.get(wiki2)
                cont = cont.capitalize()
                if responseobject:
                    soupobject = BeautifulSoup(responseobject.content , "html5lib")
                    if soupobject:
                        ph = soupobject.findAll(["h2" , "p"])
                        if ph:
                            flag = 0
                            for a in ph:
                                kfc = a.text.split("[edit]")[0]
                                if kfc == cont:
                                    flag = 1
                                    continue
                                elif flag == 1:
                                    reply['data'] = kfc
                                    break
                                else:
                                    continue
                                
                reply['url'] = wiki2+"#"+cont.replace(" " , "_")
                a = {}
                a["placename"] = params.get("input")
                a["content_type"]=params.get("contents")
                a["data"] = reply['data']
                a["url"] = reply["url"]
                wikisearchs.insert_one(a)
            
    elif intent == "places_autocomplete":
        reply['type'] = 'place'
        apisearch = apisearchs.find_one({"placename":params.get("input")})
        if apisearch:
            reply["data"] = apisearch["data"]
        else:
            places = get_place(params)
            predictions = places.get('predictions')
            # create generic template
            place_elements = []
            count=0
            for prediction in predictions:
                if count>5:
                        break
                urltemp = "***************************************************"
                place_id = prediction['place_id']
                partemp = {"key":key,
                           "placeid":place_id}
                rtemp = requests.get(urltemp , params = partemp)
                datatemp = rtemp.json()
                try:
                    photos = datatemp.get('result').get('photos')[0].get('photo_reference')
                except:
                    continue
                photourl = "*********************************************************?maxheight=800&key="+key+"&photoreference="+photos
                element = {}
                element['title'] = prediction['description']
                element['image_url'] = photourl
                place_elements.append(element)
                count+=1
            reply['data'] = place_elements
            a = {}
            a["placename"] = params.get("input")
            a["data"] = place_elements
            apisearchs.insert_one(a)
    else:
        reply['type'] ="none"
        reply['data'] = "sorry"
    return reply
