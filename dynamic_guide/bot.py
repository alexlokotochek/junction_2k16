import telegram_config
import telebot
import cherrypy
import logging
import traceback
import StringIO
import os
import sys
from copy import copy


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

# bot = telebot.TeleBot(telegram_config.token, num_threads = 4)
bot = telebot.AsyncTeleBot(telegram_config.token)
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


last_question = "I have {0} items for you, please follow me"

class Guide:

	def __init__(self):
		self.initialized = False
		self.send_msg_question = ''
		self.send_msg_variants = []
		self.last = False
		self.current_node = copy(tree)
		self.root = copy(tree) 

	def restart(self):
		self.current_node = copy(self.root)

	def send_answer(self, answer, initial=False):
		if not initial:
			if answer not in self.current_node:
				print('error: answer not found')
				self.last = False
				return '', ''		
			self.current_node = self.current_node[answer]

		if len(self.current_node.keys()) == 1 and \
		self.current_node.keys()[0] == last_question:
			self.send_msg_question = last_question\
			.format(self.current_node.values()[0])
			self.last = True
			return self.send_msg_question, ''

		self.send_msg_question = self.current_node.keys()[0]
		self.send_msg_variants = []
		for k in self.current_node.values()[0].keys():
			self.send_msg_variants += [k]
		self.current_node = self.current_node.values()[0]
		self.last = False
		return self.send_msg_question, self.send_msg_variants



class GuidesArray:

    chatid_to_guide = {}

    def __init__(self):
        self.chatid_to_guide = {}

    def add_guide(self, chat_id):
	g = Guide()
	self.chatid_to_guide[int(chat_id)] = g

    def does_guide_exist(self, chat_id):
	return int(chat_id) in self.chatid_to_guide

    def get_guide(self, chat_id):   
        if int(chat_id) in self.chatid_to_guide:
	        return self.chatid_to_guide[int(chat_id)]
        else:
            return None


guides_array = GuidesArray()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	task = bot.get_me()
	if not guides_array.does_guide_exist(message.chat.id):
	    guides_array.add_guide(message.chat.id)
	g = guides_array.get_guide(message.chat.id)
	if g.initialized:
		g.restart()
	g.initialized = True
	question, variants = g.send_answer(answer='', initial=True)
	markup = telebot.types.ReplyKeyboardMarkup()
	for v in variants:
		markup.row(v)
	bot.send_message(message.chat.id, 
					 "Hi!"+'\n'+question, 
					 reply_markup=markup)
	task.wait()


@bot.message_handler(func=lambda message: True, content_types=["text"])
def repeat_all_messages(message):
	task = bot.get_me()
	if not guides_array.does_guide_exist(message.chat.id):
	    guides_array.add_guide(message.chat.id)
	g = guides_array.get_guide(message.chat.id)
	if not g.initialized:
		g.restart()
		markup = telebot.types.ReplyKeyboardMarkup()
		markup.row('/start')
		bot.send_message(message.chat.id, 
						 'Please press START', 
						 reply_markup=markup)
		task.wait()
		return

	question, variants = g.send_answer(message.text)

	if g.last:
		bot.send_message(message.chat.id, 
						 question)
		g.restart()
		markup = telebot.types.ReplyKeyboardMarkup()
		markup.row('/start')
		bot.send_message(message.chat.id, 
						 'Please press START', 
						 reply_markup=markup)
		task.wait()
		return

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


