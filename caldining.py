"""
caldining.py

Created by Varun Naik on 2013-09-28.

"""

import sqlite3
from collections import OrderedDict
from contextlib import closing
from flask import Flask, g, render_template
from scrapeUtils import getDate, getDateStr, scrapeDC, scrapeLabel, DC_DICTIONARY, LABEL_URL_FORMAT

# Configuration
DATABASE = 'C:/Users/varunnaik/Desktop/asdf/tmp/caldining.db'
DEBUG = True       # TODO: change this
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

TODAY = getDate()  # TODO: change this
TODAY_STR = getDateStr(TODAY)

app = Flask(__name__)
app.config.from_object(__name__)

def init_db():
    """
    Initialize the database (which must have already been created).
    """
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def connect_db():
    """
    Bind g.db to the database.
    """
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    """
    Set up the database before each request.
    """
    g.db = connect_db()

@app.teardown_request
def teardown_request(_):
    """
    Tear down the database after each request.
    """
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    """
    The 'home page' view of the app.
    """
    dcDict = OrderedDict([(dc, []) for dc in DC_DICTIONARY])
    cur = g.db.execute('SELECT DISTINCT dc, meal FROM Items ' \
                       "WHERE date1 IS '{0}' " \
                       'GROUP BY dc, meal'.format(TODAY_STR))
    for dc, meal in cur.fetchall():
        dcDict[dc] += [meal] # TODO: sort these
    return render_template('index.html', dcDict=dcDict)

@app.route('/refresh/')
def refresh():
    """
    Temporary view to scrape the Cal Dining site into the database manually.
    """
    cur1 = g.db.execute('SELECT dc, meal, station, label ' \
                        'FROM Items ' \
                        "WHERE date1='{0}'".format(TODAY_STR))
    fetched1 = {tuple(value) for value in cur1.fetchall()}
    for dc in DC_DICTIONARY:
        myList = scrapeDC(TODAY, dc)
        # TODO: prevent SQL injection here lol
        for value in myList:
            labelId = value[-1]
            if (value[0], value[1], value[2], labelId) in fetched1:
                fetched1.remove((value[0], value[1], value[2], labelId))
            else:
                g.db.execute('INSERT INTO Items (date1, dc, meal, station, ' \
                             'dish, vegetarian, label) VALUES ' \
                             '(?, ?, ?, ?, ?, ?, ?)', [TODAY_STR] + value)
                cur2 = g.db.execute('SELECT allergens, ingredients '
                                    "FROM Labels WHERE id='{0}'".format( \
                                    labelId))
                fetched2 = cur2.fetchall()
                if len(fetched2) >= 2:
                    raise Exception('Label ID repeated in database')
                if len(fetched2) == 0:
                    label = scrapeLabel(labelId)
                    g.db.execute('INSERT INTO Labels (id, allergens, ' \
                                 'ingredients) VALUES (?, ?, ?)', \
                                 [labelId] + label)
    for _, _, label in fetched1:
        g.db.execute('DELETE FROM Items ' \
                     "WHERE date1='{0}' " \
                     "AND label='{1}'".format(TODAY_STR, label))
#    g.db.execute("DELETE FROM Items WHERE date1='{0}'".format(TODAY_STR))
    g.db.commit()
    return 'Refreshed table'

@app.route('/<dc>/<meal>')
def dcAndMeal(dc, meal):
    """
    View to display a single meal for a single dining common.
    """
    cur1 = g.db.execute('SELECT station, dish, vegetarian, label ' \
                        'FROM Items ' \
                        "WHERE date1 IS '{0}' " \
                        "AND dc IS '{1}' " \
                        "AND meal IS '{2}'".format(TODAY_STR, dc, meal))
    stations = OrderedDict()
    for station, dish, vegetarian, labelId in cur1.fetchall():
        value = OrderedDict([('dish', dish)])
        cur2 = g.db.execute('SELECT allergens, ingredients ' \
                            "FROM Labels WHERE id IS '{0}'".format(labelId))
        fetched = cur2.fetchall()
        if len(fetched) >= 2:
            raise Exception('Label ID repeated in database')
        if len(fetched) == 0:
            raise Exception('Label ID not found')
        value['vegetarian'] = vegetarian
        value['allergens'], value['ingredients'] = fetched[0]
        value['url'] = LABEL_URL_FORMAT.format(labelId)
        if station not in stations:
            stations[station] = [value]
        else:
            stations[station] += [value]
    return render_template('dcAndMeal.html', dc=dc, meal=meal, \
        stations=stations)

@app.route('/labels/')
def labels():
    """
    Temporary view to display all rows in the Label table.
    """
    cur = g.db.execute('SELECT id, allergens, ingredients FROM Labels')
    return '<br>'.join(str(i) for i in cur.fetchall())

if __name__ == '__main__':
    app.run()
