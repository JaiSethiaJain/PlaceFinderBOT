from flask import Flask , request
from pymessenger import Bot
from utils import fetch_reply
import requests , json , os

app = Flask("my place finder bot")
FB_ACCESS_TOKEN = "******************************************************************************8"
bot = Bot(FB_ACCESS_TOKEN)
VERIFICATION_TOKEN = "********************************"
breaker = "super_secret_string"

@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFICATION_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200

@app.route('/' , methods = ['POST'])
def webhook():
    global breaker
    data = request.get_json()
    if data['object'] == "page":
        entries = data['entry']
        for entry in entries:
            messaging = entry['messaging']
            for messaging_event in messaging:
                sender_id = messaging_event['sender']['id']
                recipient_id = messaging_event['recipient']['id']
                if recipient_id == "1371250962979172":
                    pass
                elif messaging_event.get('message'):
                    if messaging_event['message'].get('text'):
                        query = messaging_event['message']['text']
                        bot.send_action(sender_id,"mark_seen")
                        bot.send_action(sender_id,"typing_on")
                        if query == breaker:
                            pass
                        else:
                            breaker = query
                            if messaging_event['message'].get('quick_reply'):
                                # HANDLE TEXT MESSAGE WITH QUICK REPLY
                                payload = messaging_event['message']['quick_reply']['payload']
                                query = payload
                            try :
                                reply = fetch_reply(query , sender_id)
                            except Exception as e:
                                reply = {}
                                reply['type'] = "none"
                                reply['data'] = "sorry"
                            try:
                                if reply['type'] == "place":
                                    if len(reply['data'])!=0:
                                        bot.send_generic_message(sender_id , reply['data'])
                                    else:
                                        bot.send_text_message(sender_id,"no such place exists ")
                                elif reply['type'] == "wiki":
                                    if reply.get("data"):
                                        if reply.get("contents"):
                                            bot.send_quickreply(sender_id , reply['data'] , reply['contents'])
                                        if reply.get("url"):
                                            button = [{"type":"web_url" ,
                                                       "title":"Wikipedia Search" ,
                                                       "url":reply["url"]}]
                                            bot.send_text_message(sender_id , reply['data'])
                                            bot.send_button_message(sender_id , "For more details" , button)

                                    else:
                                        bot.send_text_message(sender_id,"no such place exists ")
                                elif reply['type'] == "none":
                                    button=[{"type":"postback",
                                             "title":"Click here for help",
                                             "payload":"help"}]

                                    bot.send_button_message(sender_id, "Sorry, I didn't understand.",button)

                                else :
                                    bot.send_text_message(sender_id  , reply['data'])
                            except Exception as e :
                                bot.send_text_message(sender_id , "sorry")
                    elif messaging_event['message'].get('attachments'):
                            #HANDLE ATTACHMENTS
                        try:
                            image_url=messaging_event['message']['attachments'][0]['payload']['url']
                            bot.send_image_url(sender_id,image_url)
                        except Exception as e:
                            print(e)
                            print("sorry\n") 
                elif messaging_event.get("postback"):
                    payload=messaging_event['postback']['payload']
                    try:
                        if payload=='help':
                            bot.send_text_message(sender_id,"Hi, Friend . I am a place finder bot . I can show you pictures of a place name entered or some information about that place name.:)")
                            bot.send_text_message(sender_id,"For getting the pictures of any place , type 'find places near YourPlaceName ' and you will get 5 pictures of the best possible match of the place name you entered .")
                            bot.send_text_message(sender_id,"For getting some information about the place ,\n type 'show me info about YourPlaceName' and you will get basic information along with some quick replies for further details about the place .\n You can click any of the quick reply to fetch more details . ")
                            button=[{'type':'web_url',
                                     'title':"Meet the developer",
                                     'url':'https://www.facebook.com/jai.sethia.165'}]
                            bot.send_button_message(sender_id,"You can contact me for any further query , my facebook profile is :- ",button)
                    except Exception as e:
                        print(e)
                        button=[{"type":"postback",
                                 "title":"Click here for help",
                                 "payload":"help"}]
                        bot.send_button_message(sender_id, "Sorry, I didn't understand.",button)
    return "ok" , 200

def get_started():
    headers = {
        'Content-Type':'application/json'
        }
    data = {
        "setting_type":"call_to_actions",
        "thread_state" : "new_thread",
        "call_to_actions":[{
            "type":"postback",
            "payload":"help"
            }]
        }
    ENDPOINT = "https://graph.facebook.com/v2.8/me/thread_settings?access_token=%s"%(FB_ACCESS_TOKEN)
    r = requests.post(ENDPOINT, headers = headers, data = json.dumps(data))

def set_greeting_text():
	headers = {
		'Content-Type':'application/json'
		}
	data = {
		"setting_type":"greeting",
		"greeting":{
			"text":"Hi {{user_first_name}}! I am place finder bot"
			}
		}
	ENDPOINT = "https://graph.facebook.com/v2.8/me/thread_settings?access_token=%s"%(FB_ACCESS_TOKEN)
	r = requests.post(ENDPOINT, headers = headers, data = json.dumps(data))

def set_persistent_menu():
	headers = {
		'Content-Type':'application/json'
		}
	data = {
		"setting_type":"call_to_actions",
		"thread_state" : "existing_thread",
		"call_to_actions":[
                    {"type":"web_url",
                     "title":"Meet the developer",
                     "url":"https://www.facebook.com/jai.sethia.165"},
                    {"type":"postback",
                     "title":"Help",
                     "payload":"help"}]
                }
	ENDPOINT = "https://graph.facebook.com/v2.8/me/thread_settings?access_token=%s"%(FB_ACCESS_TOKEN)
	r = requests.post(ENDPOINT, headers = headers, data = json.dumps(data))

get_started()
set_persistent_menu()
set_greeting_text()

if __name__ == "__main__":
    app.run(port = 8000 , use_reloader = True , debug = True)
