import scrython as scry
import nest_asyncio
import requests
from PIL import Image, ImageOps
from io import BytesIO
import re
from time import sleep
import os

SET_PATTERN = re.compile("\(.+\)")
DOUBLE_FACED_LAYOUTS = {"transform", "modal_dfc", "meld"}

nest_asyncio.apply()

def proxy_from_card_list(file, out_dir, img_size=(745, 1040), border_width=37):
    '''
    Generates proxied, serialized copies of cards according to a card list
    
    Inputs:
        file, String - filepath to text file containing card list
        out_dir, String - filepath to directory to store proxies
        img_size, (int, int) - width, height to resize images to
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    double_side_backlog = [] # list of tuples (quantity, card, name)
    i = 0
    for line in open(file, "r"):
        line = line.strip()
        quantity, name, set_id = parse_card_name(line)
        card = get_card(name, set_id)
        sleep(0.05) # 50 ms sleep for politeness
        if is_double_sided(card):
            # handle double sided cards at the end
            double_side_backlog.append((quantity, card, name))
        else:
            img = _add_border_to_image(get_card_image(card).resize(img_size), border_width)
            # make j copies of single card
            for j in range(quantity):
                _create_proxy(img, i, name, out_dir)
                i += 1
        
    _process_double_side_backlog(double_side_backlog, out_dir, i, img_size, border_width)

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
    return _get_image_from_uri(img_uri)

def get_double_faced_uris(card):
    faces = card.card_faces()
    front_img_uri = faces[0]["image_uris"]["png"]
    back_img_uri = faces[1]["image_uris"]["png"]
    return front_img_uri, back_img_uri

def get_double_faced_images(card):
    front_img_uri, back_img_uri = get_double_faced_uris(card)
    front_img = _get_image_from_uri(front_img_uri)
    back_img = _get_image_from_uri(back_img_uri)
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

def _process_double_side_backlog(backlog, out_dir, index, img_size, border_width):
    '''helper for handling double sided cards. Expects a list of double sided cards;
    proxies all front sides and then all back sides'''
    back_faces = []
    for quantity, card, name in backlog:
        name = name.split("//")[0]
        front_uri, back_uri = get_double_faced_uris(card) # uris instead imgs to reduce mem footprint
        back_faces.append((quantity, back_uri, name))
        front_img = _add_border_to_image(_get_image_from_uri(front_uri).resize(img_size), border_width)
        sleep(0.05) # 50 ms sleep for politeness
        for j in range(quantity):
            _create_proxy(front_img, index, name, out_dir)
            index += 1
    
    for quantity, uri, name in back_faces:
        back_img = _add_border_to_image(_get_image_from_uri(uri).resize(img_size), border_width)
        sleep(0.05) # 50 ms sleep for politeness
        for j in range(quantity):
            _create_proxy(back_img, index, name, out_dir)
            index += 1
    
def _get_image_from_uri(uri):
    request = requests.get(uri)
    return Image.open(BytesIO(request.content))

def _create_proxy(image, index, name, out_dir):
    path = os.path.join(out_dir, f"{index}_{name}.png")
    image.save(path)

def _add_border_to_image(image, border_width):
    return ImageOps.expand(image, border=border_width, fill='black')