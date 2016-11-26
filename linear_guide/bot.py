import telegram_config
import telebot
import cherrypy
import logging
import traceback
import StringIO
import os
import sys
from copy import copy
from urllib2 import urlopen


logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

def my_excepthook(excType, excValue, traceback, logger=logger):
    logger.error("Logging an uncaught exception",
                 exc_info=(excType, excValue, traceback))

sys.excepthook = my_excepthook

WEBHOOK_HOST = '78.47.79.238'
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (telegram_config.token)

bot = telebot.TeleBot(telegram_config.token)
#bot = telebot.AsyncTeleBot(telegram_config.token)
tree = telegram_config.guide_dict

class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
           'content-type' in cherrypy.request.headers and \
           cherrypy.request.headers['content-type'] == 'application/json':

            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})


last_question = 'Here are your products, please follow me'

class Guide:

	def __init__(self, init_msg):
		# find best category
		# TBD, now hardcoded 0th
		self.initialized = False
		best_match = tree.keys()[100]
		self.root = copy(tree[best_match])
		# results is the last node
		self.questions_number = len(self.root.keys()) - 1 
		self.current_question = 0
		self.results_imgs = []
                # found init guide category
                self.best_match = best_match

	def get_next_question(self):
		self.initialized = True
		if self.current_question == self.questions_number:
			results = []
			for i in [1, 10, 100]:
				results.append(self.root['Results']['Img_'+str(i)])
			self.results_imgs = results
                        #self.restart()
			return 'Here are your products, please follow me', results
        
		this_answers = self.root['Q_'+str(self.current_question)]
		# text is the last node
                #return this_answers['Text'], ['1']
		this_number_of_answers = len(this_answers.keys()) - 1
                #return this_answers['Text'], [str(this_number_of_answers)]
		variants = []
                #return this_answers['Text'], [this_answers['A_'+str(this_number_of_answers-1)]]
                for i_ans in range(this_number_of_answers):
			variants.append(this_answers['A_'+str(i_ans)])
		self.current_question += 1
		return this_answers['Text'], variants

	def restart(self):
		self.root = copy(tree[self.best_match])
		# results is the last node
		self.questions_number = len(self.root.keys()) - 1 
		self.current_question = 0
		self.results_imgs = []



# class GuidesArray:

#     chatid_to_guide = {}

#     def __init__(self):
#         self.chatid_to_guide = {}

#     def add_guide(self, chat_id):
# 	g = Guide()
# 	self.chatid_to_guide[int(chat_id)] = g

#     def does_guide_exist(self, chat_id):
# 	return int(chat_id) in self.chatid_to_guide

#     def get_guide(self, chat_id):   
#         if int(chat_id) in self.chatid_to_guide:
# 	        return self.chatid_to_guide[int(chat_id)]
#         else:
#             return None


# guides_array = GuidesArray()
g = Guide('hi')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	task = bot.get_me()
	# if not guides_array.does_guide_exist(message.chat.id):
	#     guides_array.add_guide(message.chat.id)
	# g = guides_array.get_guide(message.chat.id)
	if g.initialized:
		g.restart()
	g.initialized = True
	question, variants = g.get_next_question()
	#if variants == None:
	#	variants = ['1']
	#IMGS
	markup = telebot.types.ReplyKeyboardMarkup()
	for v in variants:
		markup.row(v)
        bot.send_message(message.chat.id, 'I think we should look in '+g.best_match+' category')
	bot.send_message(message.chat.id, question, reply_markup=markup)
	task.wait()


@bot.message_handler(func=lambda message: True, content_types=["text"])
def repeat_all_messages(message):
	task = bot.get_me()
	# if not guides_array.does_guide_exist(message.chat.id):
	#     guides_array.add_guide(message.chat.id)
	# g = guides_array.get_guide(message.chat.id)
	if not g.initialized:
		g.restart()
		markup = telebot.types.ReplyKeyboardMarkup()
		markup.row('/start')

		bot.send_message(message.chat.id, 
						 'Please press START', 
						 reply_markup=markup)
		task.wait()
                return

	question, variants = g.get_next_question()

        if question == last_question:
            for imgurl in variants:
                img_local_path = 'out_'+str(message.chat.id)+'.jpg'
                f = open(img_local_path,'w')
                f.write(urlopen(imgurl).read())
                f.close()
                #img = BytesIO(urlopen(imgurl).read())
                img = open(img_local_path, 'r')
                bot.send_chat_action(message.chat.id, 'upload_photo')
                bot.send_photo(message.chat.id, img)
                
            g.restart()
            variants = ['/start']
            question = 'Please press START'

	markup = telebot.types.ReplyKeyboardMarkup()
	for v in variants:
		markup.row(v)
	
	bot.send_message(message.chat.id, 
					 question, 
					 reply_markup=markup)
	task.wait()

if __name__ == '__main__':
	cherrypy.quickstart(WebhookServer(), 
						WEBHOOK_URL_PATH, 
						{'/': {}})


