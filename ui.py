import gevent
import gevent.wsgi
from gevent import monkey;
import werkzeug.serving
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash, Response, copy_current_request_context, \
    stream_with_context
import flask
from contextlib import closing
from flask.ext.sqlalchemy import SQLAlchemy
import json
import redis

monkey.patch_all()

SQLALCHEMY_DATABASE_URI = "sqlite:///foostats.db"
DEBUG = True
SECRET_KEY = "fisk"
USERNAME = "admin"
PASSWORD = "dubblaskarmar"

app = Flask("fooshack")
app.config.from_object(__name__)
db = SQLAlchemy(app)
red = redis.StrictRedis()

current_players = [0, 0, 0, 0]
team_a = None
team_b = None
match = None
goals = []


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    tag = db.Column(db.Text)
    track = db.Column(db.Text)

    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return 'Player %d name %s tag %s' % (self.id, self.name, self.tag)

    def update(self, form):
        self.name = request.form['name']
        self.tag = request.form['tag']
        self.track = request.form['track']

    def json(self):
        return json.dumps({"player":{
            "id":self.id,
            "name":self.name,
            "tag":self.tag,
            "track:":self.track}})


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_a_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player_a = db.relationship("Player",
                               foreign_keys='Team.player_a_id',
                               backref=db.backref('Player A', lazy='dynamic'))
    player_b_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player_b = db.relationship("Player",
                               foreign_keys='Team.player_b_id',
                               backref=db.backref('Player B', lazy='dynamic'))

    def __init__(self, player_a, player_b):
        self.player_a = player_a
        self.player_b = player_b

    def __repr__(self):
        return 'Team %s, %s' % (self.player_a.name, self.player_b.name)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_a_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team_a = db.relationship("Team",
                             foreign_keys='Match.team_a_id',
                             backref=db.backref('team_a', lazy='dynamic'))
    team_b_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team_b = db.relationship("Team",
                             foreign_keys='Match.team_b_id',
                             backref=db.backref('team_b', lazy='dynamic'))
    goals = db.relationship("Goal", backref=db.backref('goal'))


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship("Team", backref=db.backref('team', lazy='dynamic'))
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    match = db.relationship("Match", backref=db.backref('match', lazy='dynamic'))
    speed = db.Column(db.Float)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/players")
def players():
    players = Player.query.all()
    return render_template("players.html", players=players)


@app.route("/player/<id>", methods=['GET'])
def player(id):
    p = db.session.query(Player).get(id)
    if p:
        return render_template("player.html", player=p)
    else:
        flash("no player " + id)
        return redirect(url_for('players'))


@app.route("/player_add", methods=['POST'])
def player_add():
    p = Player(request.form['name'])
    db.session.add(p)
    db.session.commit()
    flash('player ' + str(p) + " added")
    return redirect(url_for('players'))


@app.route("/player_update", methods=['POST'])
def player_update():
    player_id = request.form['id']
    p = db.session.query(Player).get(player_id)
    if p:
        p.update(request.form)
        db.session.add(p)
        db.session.commit()
        flash('player ' + str(p) + " updated")
    else:
        flash('no player with id ' + player_id)
    return redirect(url_for('players'))


@app.route("/register_player/<position>/<tag>")
def json_player(position, tag):
    print "registering player %s at position %s" % (tag, position)
    p = Player.query.filter_by(tag=tag).first()
    if not p:
        p = Player(tag)
        db.session.add(p)
        db.session.commit()
        db.session.refresh(p)
    current_players[int(position)-1] = p
    return Response(p.json(), mimetype="application/json")


def event_stream():
    pubsub = red.pubsub()
    pubsub.subscribe('fooshack')
    for message in pubsub.listen():
        if not type(message['data'] == str):
            continue
        yield 'data: %s\n\n' % message['data']


@app.route('/event-source')
def event_source():
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')


@app.route("/match/<id>")
def match(id):
    return render_template("match.html")


@app.route("/matches")
def matches():
    return render_template("matches.html")


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")


@werkzeug.serving.run_with_reloader
def runServer():
    db.create_all()
    app.debug = True
    server = gevent.wsgi.WSGIServer(("", 5000), app)
    server.serve_forever()


if __name__ == '__main__':
    runServer()
