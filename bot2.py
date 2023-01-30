import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Message
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters
from telegram.ext.filters import MessageFilter
import math
import random
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
import json
import requests
import sys
import networkx as nx
import matplotlib.pyplot as plt


TOKEN = "5853516504:AAEsVh5WyxuEjthZYcKWSxP9aIEUjl5oMIQ"

# Setting up graph commands
graphs = {}

def load_graph(s):
    try:
        with open(s) as file:
            global graphs
            graphs = json.load(file)
    except FileNotFoundError:
        pass

def save_graph(context, s):
    for edge in context.user_data['graph']:
        edge["prev"] = ""
    context.user_data['mod_graphs'][context.user_data['class_type']] = context.user_data['graph']
    graphs[context.user_data['module']] = context.user_data['mod_graphs']
    with open(s, "w") as file:
        json.dump(graphs, file)

def get_class(element):
    return element["classNo"]

# Set up graphs
cs_modules = []
load_graph("graphs.json")
with open("2022-2023_moduleList.json", "r") as file:
    all_modules = json.load(file)
    cs_modules = list(filter(lambda module: module["moduleCode"].startswith("CS2"), all_modules))

# Add edge to graph
def add_edge(context, src, des, id, chat_id):
    context.user_data['graph'].append({"src": src, "des": des, "id": id, "prev": "", "chat_id": chat_id})

# Check for cycle
def contains_cycle(context, src, des, id):
    queue = [(des, id)]
    while len(queue) != 0:
        curr = queue.pop(0) 
        for edge in context.user_data['graph']:
            if edge["src"] == curr[0]:
                if edge["prev"] != "":
                    continue
                edge["prev"] = curr[1]
                queue.append((edge["des"], edge["id"]))
        if curr[0] == src:
            return True
    return False


# keyboards and bot setup
bot = telegram.Bot(TOKEN)
updater = Updater(token=TOKEN, use_context=True)

dispatcher = updater.dispatcher
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Tutorial Swapping Bot! Use /register to register a swap!")
    context.user_data['user_id'] = update.message.from_user['username']
    context.user_data['module'] = ""
    context.user_data['slot_had'] = ""
    context.user_data['slot_wanted'] = ""
    context.user_data['tut_list'] = ""
    context.user_data['temp_tut_list'] = ""
    context.user_data['class_type'] = ""
    context.user_data['class_types'] = ""
    context.user_data['mod_graphs'] = ""
    context.user_data['graph'] = ""

# Help function
def helper(update, context):
    update.message.reply_text("Type /register to register for a tutorial swap! Type /cancel at any time to cancel your registration. Note "
                              "that we ignore any invalid inputs (e.g. no such tutorial or module code)")

# Filters for all responses
class FilterModule(MessageFilter):
    def filter(self, message):
        return any(module["moduleCode"] == message.text for module in cs_modules)

class FilterTutHad(MessageFilter):
    def filter(self, message):
        return any(slot["classNo"] == message.text for slot in tut_list)

class FilterTutWanted(MessageFilter):
    def filter(self, message):
        return any(slot["classNo"] == message.text for slot in temp_tut_list)

class FilterClassType(MessageFilter):
    def filter(self, message):
        return message.text in class_types

# Initialise all filters
filter_module = FilterModule()
filter_tut_had = FilterTutHad()
filter_tut_wanted = FilterTutWanted()
filter_class_type = FilterClassType()

# Function to ask for module code
def module(update, context):
    tut_keyboard = [[str(module["moduleCode"])] for module in cs_modules]
    tut_markup = ReplyKeyboardMarkup(tut_keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text('Which module are you looking for?', reply_markup=tut_markup)
    return MODULE

# Function to ask for class type
def class_type(update, context):
    text = update.message.text.upper()
    context.user_data['module'] = text
    if context.user_data['module'] in graphs:
        context.user_data['mod_graphs'] = graphs[context.user_data['module']]
    else:
        context.user_data['mod_graphs'] = {}
    try:
        response = requests.get(f"https://api.nusmods.com/v2/2022-2023/modules/{context.user_data['module']}.json")
    except requests.RequestException:
        sys.exit()
    o = response.json()
    # If the module does not have any classes, end the command
    if len(o["semesterData"]) < 2:
        update.message.reply_text("This module has no valid lessons to swap! Ending command...")
        return ConversationHandler.END
    
    context.user_data['class_types'] = list(set([slot["lessonType"] for slot in o["semesterData"][1]["timetable"]]))
    context.user_data['class_types'].remove("Lecture")
    global class_types
    class_types = context.user_data['class_types']
    tut_keyboard = [[str(x)] for x in context.user_data['class_types']]
    tut_markup = ReplyKeyboardMarkup(tut_keyboard, one_time_keyboard=True, resize_keyboard=True)

    update.message.reply_text("Select your class type: ", reply_markup=tut_markup)
    return CLASS_TYPE
    
# Function to ask for current slot user has
def slot_had(update, context):
    text = update.message.text.upper()
    context.user_data['class_type'] = text
    if context.user_data['class_type'] in context.user_data['mod_graphs']:
        context.user_data['graph'] = context.user_data['mod_graphs'][context.user_data['class_type']]
    else:
        context.user_data['graph'] = []
    try:
        response = requests.get(f"https://api.nusmods.com/v2/2022-2023/modules/{context.user_data['module']}.json")
    except requests.RequestException:
        sys.exit()
    o = response.json()
    context.user_data['tut_list'] = list(filter(lambda slot: slot["lessonType"].upper() == context.user_data['class_type'], o["semesterData"][1]["timetable"]))
    context.user_data['tut_list'].sort(key=get_class)

    global tut_list
    tut_list = context.user_data['tut_list']

    tut_keyboard = [[str(x["classNo"])] for x in context.user_data['tut_list']]
    tut_markup = ReplyKeyboardMarkup(tut_keyboard, one_time_keyboard=True, resize_keyboard=True)

    update.message.reply_text("Select your current Tutorial slot (with the 0 in front if necessary): ", reply_markup=tut_markup)
    return SLOT_HAD

# Function to ask 
def slot_wanted(update, context):
    text = update.message.text.upper()
    context.user_data['slot_had'] = text

    context.user_data['temp_tut_list'] = list(filter(lambda slot: slot["classNo"] != context.user_data['slot_had'], context.user_data['tut_list']))
    global temp_tut_list
    temp_tut_list = context.user_data['temp_tut_list']
    tut_keyboard = [[str(x["classNo"])] for x in context.user_data['temp_tut_list']]
    tut_markup = ReplyKeyboardMarkup(tut_keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Select your desired Tutorial slot (with the 0 in front if necessary): ", reply_markup=tut_markup)
    return SLOT_WANTED

def conclude(update, context):
    text = update.message.text.upper()
    context.user_data['slot_wanted'] = text
    
    update.message.reply_text('Your data has been stored! Thank you!')
    if context.user_data['module'] not in graphs:
        graphs[context.user_data['module']] = []
    src = context.user_data['slot_had']
    dst = context.user_data['slot_wanted']
    user_id = context.user_data['user_id']
    chat_id = str(update.message.chat_id)
    add_edge(context, src, dst, user_id, chat_id)
    if contains_cycle(context, src, dst, user_id):
        temp = [f"{src}\n{user_id}"]
        temp4 = [chat_id]
        temp3 = [user_id]
        global graph
        next = list(filter(lambda edge: edge["prev"] == user_id, context.user_data['graph']))[0]
        while next["id"] != user_id:
            t1 = next["src"]
            t2 = next["id"]
            temp.append(f"{t1}\n{t2}")
            temp3.append(t2)
            temp4.append(next["chat_id"])
            next = list(filter(lambda edge: edge["prev"] == next["id"], context.user_data['graph']))[0]
        temp2 = []
        for edge in context.user_data['graph']:
            if edge["id"] not in temp3:
                temp2.append(edge)
        context.user_data['graph'] = temp2
        print(temp)
        generate_image(temp, context, temp4)
            
    else:
        print("No cycles found currently")
    save_graph(context, "graphs.json")
    return ConversationHandler.END

def generate_image(arr, context, temp4):
    plt.title(f"{context.user_data['module']} {context.user_data['class_type']}")
    arr2 = []
    for i in range(len(arr) - 1):
        arr2.append((arr[i], arr[i + 1]))
    arr2.append((arr[-1], arr[0]))
    DG = nx.DiGraph()
    DG.add_edges_from(arr2)
    nx.draw_networkx(DG, arrowsize=30, node_size=3000, node_color="#89CFF0")
    plt.savefig(f"{context.user_data['module']}.png")


    for chat_id in temp4:
        bot.send_photo(chat_id, open(f"{context.user_data['module']}.png", "rb"))

def cancel(update, context):
    update.message.reply_text('The command has been cancelled!')
    return ConversationHandler.END

    
MODULE,CLASS_TYPE, SLOT_HAD,SLOT_WANTED, CONCLUDE = range(5)
def main():
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    help_handler = CommandHandler('help', helper)
    dispatcher.add_handler(help_handler)

    #tutorial swap handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('register', module)],

        states={
            
            MODULE: [MessageHandler(filter_module, class_type)],

            CLASS_TYPE: [MessageHandler(filter_class_type, slot_had)],

            SLOT_HAD: [MessageHandler(filter_tut_had, slot_wanted)],

            SLOT_WANTED: [MessageHandler(filter_tut_wanted, conclude)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)



    updater.start_polling()

if __name__ == '__main__':
    main()
