#!/usr/bin/python

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

current_match = None

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    tag = db.Column(db.Text)
    track = db.Column(db.Text)

    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return 'Player id %d name %s tag %s' % (self.id, self.name, self.tag)

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
    player_a_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player_a = db.relationship("Player",
                               foreign_keys='Team.player_a_id',
                               backref=db.backref('Player A', lazy='dynamic'))
    player_b_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player_b = db.relationship("Player",
                               foreign_keys='Team.player_b_id',
                               backref=db.backref('Player B', lazy='dynamic'))

    def __init__(self, player_a, player_b):
        self.player_a = player_a
        self.player_b = player_b

    def __repr__(self):
        return 'Team %s, %s' % (self.player_a, self.player_b)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_a_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team_a = db.relationship("Team",
                             foreign_keys='Match.team_a_id',
                             backref=db.backref('team_a', lazy='dynamic'))
    team_b_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team_b = db.relationship("Team",
                             foreign_keys='Match.team_b_id',
                             backref=db.backref('team_b', lazy='dynamic'))
    goals = db.relationship("Goal", backref=db.backref('goal'))

    def __init__(self, team_a, team_b):
        self.team_a = team_a
        self.team_b = team_b

    def __repr__(self):
        return "match with teams %s - %s, %d goals" % (
            self.team_a, self.team_b, len(self.goals))

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team = db.relationship("Team", backref=db.backref('team', lazy='dynamic'))
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    match = db.relationship("Match", backref=db.backref('match', lazy='dynamic'))
    speed = db.Column(db.Float)

    def __init__(self, match, team, speed):
        self.match = match
        self.team = team
        self.speed = speed
    def __repr__(self):
        return 'goal in match %d by team %s, speed %s' %(
            self.match_id, self.team_id, self.speed)

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


@app.route("/register_goal", methods=['POST'])
def register_goal():
    global current_match

    cp = map(db.session.query(Player).get, request.json['players'])
    team_a = Team.query.filter_by(player_a=cp[0],player_b=cp[1]).first()
    team_b = Team.query.filter_by(player_a=cp[2],player_b=cp[3]).first()
    if not team_a:
        team_a = Team(cp[0], cp[1])
    if not team_b:
        team_b = Team(cp[2], cp[3])

    if not current_match:
        current_match = Match(team_a, team_b)
        db.session.flush()
        db.session.refresh(current_match)
        
    goal = Goal(current_match, 
                team_a if request.json['team'] == 1 else team_b,
                int(request.json['spd']))
    db.session.flush()

    team_a_goals = Goal.query.filter_by(team=team_a,match=current_match).all()
    print 'team_a goals ',len(team_a_goals)
    for goal in team_a_goals:
        print '\t',goal

    team_b_goals = Goal.query.filter_by(team=team_b,match=current_match).all()
    print 'team_b goals ',len(team_b_goals)
    for goal in team_b_goals:
        print '\t',goal

    if len(team_a_goals) == 10:
        print 'team a wins!'
        current_match = None
    if len(team_b_goals) == 10:
        print 'team b wins!'
        current_match = None

    db.session.commit()
    return json.dumps({"data": {
                "current_match":current_match.id if current_match else 0}})

@app.route("/register_player/<position>/<tag>")
def json_player(position, tag):
    print "registering player %s at position %s" % (tag, position)
    p = Player.query.filter_by(tag=tag).first()
    if not p:
        p = Player(tag)
        db.session.add(p)
        db.session.commit()
        db.session.refresh(p)
    return Response(p.json(), mimetype="application/json")


def event_stream():
    pubsub = red.pubsub()
    pubsub.subscribe('fooshack')
    for message in pubsub.listen():
        if not type(message['data']) == str:
	    continue
        
        d = 'data: %s\n\n' % message['data']
	print d
	yield d


@app.route('/event-source')
def event_source():
    print 'event'
    return Response(stream_with_context(event_stream()), 
                    mimetype='text/event-stream')


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
