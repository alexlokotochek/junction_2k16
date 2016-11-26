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
from suggester import *


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

	def __init__(self):
		# find best category
		self.search_mode = True
		self.initialized = False

	def initialize(self, init_msg):
		self.suggester = SearchSuggester(init_msg)
		self.best_product = self.suggester.suggested_product
                if self.best_product:
                    self.best_product = str(self.best_product)
		self.best_category = self.suggester.suggested_category
                self.root = copy(tree.values()[0])
                if self.best_category:
                    self.best_category = str(self.best_category)
                    if self.best_category in tree:
                        self.root = copy(tree[self.best_category])
		self.initialized = False
		self.questions_number = len(self.root.keys())
		self.current_question = 0
		self.results_imgs = []

	def get_next_question(self):
		self.initialized = True
		if self.current_question == self.questions_number:
			results = []
                        results = ['http://public-qa.keskofiles.com/f/k-rauta/products/7314102030968']
			self.results_imgs = results
			return last_question, results
		this_answers = self.root['Q_'+str(self.current_question)]
		this_number_of_answers = len(this_answers.keys()) - 1
		variants = []
		for i_ans in range(this_number_of_answers):
			variants.append(this_answers['A_'+str(i_ans)])
		self.current_question += 1
		return this_answers['text'], variants


# guides_array = GuidesArray()
g = Guide()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.send_message(message.chat.id, 'Please enter what are you looking for')
	g.search_mode = True
        g.initialized = False


@bot.message_handler(func=lambda message: True, content_types=["text"])
def repeat_all_messages(message):

	if g.initialized and g.search_mode:
		g.search_mode = True
		markup = telebot.types.ReplyKeyboardMarkup()
		markup.row('/start')
		bot.send_message(message.chat.id, "Bye!", reply_markup=markup)
		return

	if g.search_mode:
		g.initialized = False
		# initial search query is recieved
		g.initialize(message.text)
		if g.best_product:
			markup = telebot.types.ReplyKeyboardMarkup()
			for v in ['Exactly! This is the product I wanted', '/start']:
				markup.row(v)
			bot.send_message(message.chat.id, str(g.best_product), reply_markup=markup)
		elif g.best_category:
			markup = telebot.types.ReplyKeyboardMarkup()
			for v in ['Exactly! This is the category I wanted', '/start']:
				markup.row(v)
			bot.send_message(message.chat.id, 'I suggest you category ' + str(g.best_category), reply_markup=markup)
                else:
                        markup = telebot.types.ReplyKeyboardMarkup()
                        markup.row('/start')
                        bot.send_message(message.chat.id, 'Sorry, try again', reply_markup=markup)
                
		g.search_mode = False
		return

	if message.text == 'Exactly! This is the product I wanted':
		markup = telebot.types.ReplyKeyboardMarkup()
		markup.row('/start')
		bot.send_message(message.chat.id, "Bye!", reply_markup=markup)
		return

	if message.text == 'Exactly! This is the category I wanted':
                if g.best_category not in tree:
                    markup = telebot.types.ReplyKeyboardMarkup()
                    markup.row('/start')
                    bot.send_message(message.chat.id, "Sorry, this category is not represented by Kesko API", reply_markup=markup)
                    return

		g.search_mode = False

	g.initialized = True

	question, variants = g.get_next_question()

	if question == last_question:
		for imgurl in variants:
                        bot.send_message(message.chat.id, imgurl)
			
		g.initialized = False
                g.search_mode = True
		variants = ['/start']
		question = 'Please press START'

	markup = telebot.types.ReplyKeyboardMarkup()
	for v in variants:
		markup.row(v)
	
	bot.send_message(message.chat.id, question, reply_markup=markup)

if __name__ == '__main__':
	cherrypy.quickstart(WebhookServer(), 
						WEBHOOK_URL_PATH, 
						{'/': {}})


