import os
import uuid
import psycopg2
import psycopg2.extras
from flask import Flask, session
from flask.ext.socketio import SocketIO, emit

serialID = 0

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'
app.secret_key = os.urandom(24).encode('hex')


socketio = SocketIO(app)

messages = [{'text':'test', 'name':'testName'}]
users = {}

def connectToDB():
  connectionString = 'dbname=irc user=postgres password=Amorroma host=localhost'
  try:
    print "connected to database IRC"
    return psycopg2.connect(connectionString)
  except:
    print("Can't connect to database")
    

def updateRoster():
    names = []
    for user_id in  users:
        print users[user_id]['username']
        if len(users[user_id]['username'])==0:
            names.append('Anonymous')
        else:
            names.append(users[user_id]['username'])
    print 'broadcasting names'
    emit('roster', names, broadcast=True)
    

@socketio.on('connect', namespace='/chat')
def test_connect():
    session['uuid']=uuid.uuid1()
    session['username']='starter name'
    print 'connected'
    users[session['uuid']]={'username':'New User'}
    updateRoster()


    for message in messages:
        emit('message', message)

@socketio.on('message', namespace='/chat')
def new_message(message):
    #tmp = {'text':message, 'name':'testName'}
    tmp = {'text':message, 'name':users[session['uuid']]['username']}
    messages.append(tmp)
    emit('message', tmp, broadcast=True)
    #######################################################start here with message sql queries
    query = "insert into data (id, message) values (%s, %s);"
    #query = "insert into data (id, message) values (" + serialID + ", " + message + ");"
    print serialID
    try:
        cur.execute(query, (serialID, message))
        #cur.execute(query)
    except:
        print("Error executing query")
        print query
    
    
@socketio.on('identify', namespace='/chat')
def on_identify(message):
    print 'identify' + message
    users[session['uuid']]={'username':message}
    updateRoster()


@socketio.on('login', namespace='/chat')
def on_login(data):
    print data['name'] + " " +  data['password']
    results = ''
    query = "select id from users WHERE name = %s AND password = crypt(%s, password);"
    try:
        cur.execute(query, (data['name'], data['password']))
        session['serialID'] = cur.fetchone()
        print session['serialID']
        print serialID
    except:
        print("Error executing query")
        print query
    #users[session['uuid']]={'username':message}
    #updateRoster()


    
@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    print 'disconnect'
    if session['uuid'] in users:
        del users[session['uuid']]
        updateRoster()

@app.route('/')
def hello_world():
    print 'in hello world'
    return app.send_static_file('index.html')

@app.route('/js/<path:path>')
def static_proxy_js(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('js', path))
    
@app.route('/css/<path:path>')
def static_proxy_css(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('css', path))
    
@app.route('/img/<path:path>')
def static_proxy_img(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('img', path))
    
if __name__ == '__main__':
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
     