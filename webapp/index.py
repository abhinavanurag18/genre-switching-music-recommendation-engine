# mongo.py

from flask import Flask
from flask import jsonify
from flask import request, redirect
from flask_pymongo import PyMongo
import tensorflow as tf
import json
from flask import render_template
from flask import session
import os, errno
from distutils.dir_util import copy_tree
import tensorflow as tf
import tflearn
import numpy as np
import random
from bson.json_util import dumps

app = Flask(__name__)


#app configuration
app.config['MONGO_DBNAME'] = 'restdb'
#app.config['MONGO_URI'] = 'mongodb://localhost:27017/restdb'
app.config['MONGO_URI'] = 'mongodb://mad_men:madmen111@ds127564.mlab.com:27564/songo'
app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
mongo = PyMongo(app)


#app route - index
@app.route('/')
def index():
  if 'username' in session:
    return render_template("index.html",username=session['username'],song="1MoAdVyuEuU",genre="1")
  else:
    return render_template("login.html")

@app.route('/<song>')
def songplay(song):
  if 'username' in session:
    genre_id = get_genre_id_from_song_id(song)
    return render_template("index.html",username=session['username'],song=song,genre=genre_id)
  else:
    return render_template("login.html")

def get_genre_id_from_song_id(song_id):
    all_songs = get_all_songs()
    for song in all_songs["songs"]:
        if song["song_id"] == song_id:
            song_num = song["song_number"]
            genre_id = (int(song_num) / 5) + 1
            return genre_id

@app.route('/logout')
def logout():
  if 'username' in session:
    session.pop("username")
    return render_template("login.html")

@app.route('/', methods=['POST'])
def login():

  username = request.form['username']
  session['username'] = username
  user = mongo.db.users
  user_id = user.insert({"username":session["username"], "trail":[]})
  try:
    os.makedirs("users/" + session['username'])
  except OSError as e:
    if e.errno != errno.EEXIST:
        pass

  copy_tree("pre", "users/"+session['username'])

  return render_template("index.html",username=session['username'], song="nYh-n7EOtMA")

@app.route('/changegenre', methods=['GET'])
def change_genre():
    genre_id = request.args.get('genre','')
    song_number = random.randrange(int(genre_id) * 5 - 4 , int(genre_id) * 5, 1)
    all_songs = get_all_songs()
    for song in all_songs["songs"]:
        if song["song_number"] == str(song_number):
            return song["song_id"]

def get_all_songs():
    star = mongo.db.songo.find()
    print(type(star))
    output = {}
    for s in star:
        output = {'songs' : s['songs']}
    return output

@app.route('/star', methods=['GET'])
def get_all_stars():
    return get_all_songs()

@app.route('/star/', methods=['GET'])
def get_one_star(name):
  star = mongo.db.stars
  s = star.find_one({'name' : name})
  if s:
    output = {'name' : s['name'], 'distance' : s['distance']}
  else:
    output = "No such name"
  return jsonify({'result' : output})

@app.route('/songs', methods=['POST'])
def add_songs():
  songs_col = mongo.db.songs
  songs_json = request.json['songs']
  for song in songs_json:
    song_id = songs_col.insert(songs_json)
  output = []
  for s in songs_col.find():
    output.append(s)
  return jsonify({'result' : output})

@app.route('/update', methods=['POST'])
def update_songs():
  i = 1
  for song in mongo.db.songs.find():
    song['song_number'] = i
    i = i + 1

@app.route('/automode', methods=['POST'])
def automode():
  session["automode"] = "1"
  print("got it")
  return "Success"

@app.route('/next-song', methods=['GET'])
def nextsong():
    song = request.args.get('songid','')
    print(song)
    tf.reset_default_graph()
    net = tflearn.input_data(shape=[None, 30])
    net = tflearn.fully_connected(net, 60, activation='relu')
    net = tflearn.fully_connected(net, 90, activation='relu')
    net = tflearn.fully_connected(net, 12, activation='sigmoid')
    net = tflearn.regression(net, optimizer='adam', loss='categorical_crossentropy')

    model = tflearn.DNN(net)
    model.load('users/'+session['username']+'/model_v1.tflearn')
    song_from_db = get_all_songs()
    genre = 0
    length = 0
    
    for song_it in song_from_db["songs"]:
        length = length + 1
        if song_it["song_id"] == song:
            # genre = song_it["song_number"]
            genre = (int(song_it["song_number"]) % 5) + 1
            print(genre)
        


    prev_to_prev_genre = ""
    prev_length = 0
    user_data = mongo.db.users.find()
    for user_it in user_data:
        if user_it["username"] == session["username"]:
            print(user_it["username"])
            prev_to_prev_genre = user_data["prev_genre"]
            prev_length = user_data["length"]
  
    input_data_to_model = convert_to_one_hot_encoding(prev_to_prev_genre) + convert_to_one_hot_encoding_six(prev_length) + convert_to_one_hot_encoding(genre)
    output_from_model = model.predict([input_data_to_model])
    genre_returned = np.argmax(output_from_model)+1
    print(genre_returned)
    user_data = mongo.db.users.find()
    for user_it in user_data:
        if genre == user_it["prev_genre"]:
            user_data.update({"username":session["username"]},{"prev_genre":genre},{"$inc" : {"length":1}})
        else :
            user_data.update({"username":username},{"$set":{"prev_genre":genre,"length":1}})
  

    song_number_played = random.randrange(genre_returned * 5 - 4 , genre_returned * 5, 1)
    print(song_number_played)
    song_table = get_all_songs()
    song_id = "1MoAdVyuEuU"
    for song in song_table["songs"]:
        print("inside this")
        if song["song_number"] == str(song_number_played):
            song_id = song["song_id"]
            break
  # return str(input_data_to_model)
    return render_template('index.html', username=session["username"],song=song_id,genre=genre_returned)    


def convert_to_one_hot_encoding(number):
  if(number != ''):
    encoding = []
    for i in range(12):
      if i == (int(number) - 1):
        encoding.append(1)
      else:
        encoding.append(0)
    return encoding
  else :
    return [0,0,0,0,0,0,0,0,0,0,0,0]

def convert_to_one_hot_encoding_six(number):
  if(number != ''):
    encoding = []
    for i in range(6):
      if i == (int(number) - 1):
        encoding.append(1)
      else:
        encoding.append(0)
    return encoding
  else :
    return [0,0,0,0,0,0]

if __name__ == '__main__':
    app.run(debug=True)
