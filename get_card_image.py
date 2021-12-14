import scrython as scry
import nest_asyncio
import requests
from PIL import Image
from io import BytesIO
import re
from time import sleep

SET_PATTERN = re.compile("\(.+\)")
DOUBLE_FACED_LAYOUTS = {"transform", "modal_dfc", "meld"}

nest_asyncio.apply()

def proxy_from_card_list(file, out_dir):
    double_side_backlog = []
    i = 0
    for line in open(file, "r"):
        pass

def get_card_from_string(card_string):
    quantity, name, set_id = parse_card_name(card_string)
    return get_card(name, set_id)

def get_card(card_name, set_id=None):
    card = None
    if set_id is not None:
        card = scry.cards.Named(fuzzy=card_name, set=set_id)
    else:
        card = scry.cards.Named(fuzzy=card_name)
    return card

def get_card_image(card):
    img_uri = card.image_uris()["png"]
    img_request = requests.get(img_uri)
    img = Image.open(BytesIO(img_request.content))
    return img

def get_double_faced_images(card):
    faces = card.card_faces()
    front_img_uri = faces[0]["image_uris"]["png"]
    back_img_uri = faces[1]["image_uris"]["png"]
    
    front_request = requests.get(front_img_uri)
    sleep(0.05) # wait 50 ms, good behavior
    back_request = requests.get(back_img_uri)
    
    front_img = Image.open(BytesIO(front_request.content))
    back_img = Image.open(BytesIO(back_request.content))
    return front_img, back_img

def parse_card_name(card_name):
    tokens = card_name.split(' ')
    
    name_start_index = 0
    name_end_index = len(tokens)
    quantity = None
    set_id = None
    
    if tokens[0].isnumeric():
        quantity = int(tokens[0])
        name_start_index = 1
    else:
        quantity = 1
    
    if SET_PATTERN.search(tokens[-1]):
        set_id = tokens[-1][1:-1]
        name_end_index -= 1
    
    name = ' '.join(tokens[name_start_index:name_end_index])
    return quantity, name, set_id

def is_double_sided(card):
   return card.layout() in DOUBLE_FACED_LAYOUTS