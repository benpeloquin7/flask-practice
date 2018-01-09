import csv
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
import logging
import os
import pandas as pd
import sqlite3
from wtforms import Form, TextField, \
    SelectField, validators, StringField, SubmitField

CACHE = set()
DATABASE_INITIALIZED = False

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file, flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    TABLE_NAME='DATA',
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    DATABASE_INIT_FILE=os.path.join(app.root_path, 'practice-db.csv')

))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    con = sqlite3.connect(app.config['DATABASE'])
    con.row_factory = dict_factory
    df = pd.read_csv(app.config['DATABASE_INIT_FILE'])
    df.to_sql(app.config['TABLE_NAME'], con)
    con.commit()
    app.logger.info('initialized database')


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def show_entries():
    db = get_db()
    cur = db.execute('select title, text from {} order by id desc'.format(
        app.config['TABLE_NAME']))
    entries = cur.fetchall()
    return render_template('experiment.html', entries=entries)


def add_entry():
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
               [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('flaskr.show_entries'))


@app.route('/')
def intro():
    init_db()
    return render_template('intro.html')


class Response(Form):
    def __init__(self, sentence, candidate1, candidate2):
        super().__init__()
        self.sentence = sentence
        self.candidate1 = candidate1
        self.candidate2 = candidate2
        self.response = SelectField(label='Choice',
                                    choices=[self.candidate1, candidate2])


@app.route('/experiment', methods=["GET", "POST"])
def experiment():
    # If we've reached end go to conclusion
    if len(CACHE) == 1:
        return render_template('conclusion.html')

    db = get_db()
    cur = db.execute(
        'select sentence, candidate1, candidate2 from {} order by id desc'.format(
            app.config['TABLE_NAME']))
    data = cur.fetchone()
    app.logger.info("Current sentence:\t{}\nCurrent candidates:{}\t".format(
        data['sentence'], [data['candidate1'], data['candidate2']]))
    response = \
        Response(data['sentence'], data['candidate1'], data['candidate2'])

    return render_template('experiment.html', data=response)


@app.route('/conclusion')
def conclusion():
    return render_template('conclusion.html')


if __name__ == '__main__':
    app.run()
