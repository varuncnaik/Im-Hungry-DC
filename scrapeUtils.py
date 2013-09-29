"""
scrapeUtils.py

Created by Varun Naik on 2013-09-28.

"""

import datetime
import re
from bs4 import BeautifulSoup
from collections import OrderedDict
from urllib2 import urlopen

DC_DICTIONARY = OrderedDict([
    ('Crossroads', '01'),
    ('Cafe 3', '03'),
    ('CKC', '04'),
    ('Foothill', '06'),
])
VEGETARIAN_COLORS = {
    '#800040': 'Vegan',
    '#008000': 'Vegetarian',
}
KEY_INGREDIENTS_LIST = ['beef', 'pork', 'ham']

LABEL_URL_FORMAT = 'http://services.housing.berkeley.edu/FoodPro/dining/static/label.asp?RecNumAndPort={0}'
DC_URL_FORMAT = 'http://services.housing.berkeley.edu/FoodPro/dining/static/DiningMenus.asp?dtCurDate={0}/{1}/{2}&strCurLocation={3}'
TABLE_WIDTH = 670

def _add0(num):
    """
    Convert a single-digit number to a double-digit string, prepending 0 if
    necessary.
    """
    return '0' + str(num) if num < 10 else str(num)

def getDate():
    """
    Return the current date as a datetime.datetime object.
    """
    return datetime.datetime.now()

def getDateStr(date):
    """
    Return the string representation of date.
    """
    return _add0(date.month) + _add0(date.day) + _add0(date.year)

def _titlecase(s):
    """
    Convert a string to camel case, ignoring apostrophes as delimiters.
    Lifted from http://docs.python.org/2/library/stdtypes.html#str.title.
    """
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
                  lambda mo: mo.group(0)[0].upper() +
                             mo.group(0)[1:].lower(),
                  s)

def scrapeDC(date, dc):
    """
    Scrapes the information from the main DC page. Returns a list of (Dining
    Common, Meal, Station, Dish, Vegetarian, Url) tuples.
    """
    myList = []
    strLocation = DC_DICTIONARY[dc]
    url = DC_URL_FORMAT.format(date.month, date.day, date.year, strLocation)
    soup = BeautifulSoup(urlopen(url))
    table = soup.find('table', width=TABLE_WIDTH)
    trList = table.find_all('tr', recursive=False)
    fontList = trList[0].find_all('font')
    if len(fontList) == 0:
        return []
    tdList = trList[1].find_all('td')
    for font, td in zip(fontList, tdList):
        meal = _titlecase(font.text.strip())
        tag = td.find('font')
        while tag is not None:
            if tag.name == 'font' and tag['color'] == '':
                station = _titlecase(tag.text.strip())
            elif tag.name == 'a':
                font = tag.find('font')
                dish = font.text.strip()
                vegetarian = VEGETARIAN_COLORS.get(font['color'], 'Non-Veg')
                url = tag['href'].split('RecNumAndPort=')[1]
                myList += [[dc, meal, station, dish, vegetarian, url]]
            tag = tag.find_next_sibling()
    return myList

def _getTextForLabel(soup, s):
    """
    Returns the text from a label page corresponding to s.
    """
    b = soup.find('b', text=re.compile(r'\s*{0}:\s*'.format(s)))
    if b is None:
        return ''
    font = b.find_parent()
    b.extract()
    return font.text.strip()

def scrapeLabel(labelId):
    """
    Scrapes the information from the label page.
    """
    soup = BeautifulSoup(urlopen(LABEL_URL_FORMAT.format(labelId)))
    return [_getTextForLabel(soup, 'ALLERGENS'), _getTextForLabel(soup, \
        'INGREDIENTS')]

def getKeyIngredients(ingredients):
    """
    Returns which elements in KEY_INGREDIENTS_LIST appear in ingredients.
    """
    ingredients = ingredients.lower()
    return [_titlecase(ing) for ing in KEY_INGREDIENTS_LIST if ing in \
        re.split(r'[^\w]', ingredients)]
