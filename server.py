import os
import uuid
import psycopg2
import psycopg2.extras
from flask import Flask, session
from flask.ext.socketio import SocketIO, emit


app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'
app.secret_key = os.urandom(24).encode('hex')

socketio = SocketIO(app)

messages = []
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
        
        
        
        
        
@socketio.on('search', namespace='/chat')
def new_search(term):
    query = "SELECT users.name, data.message FROM users INNER JOIN data ON users.id = data.id WHERE data.message LIKE '%%%s%%';"
    try:
        cur.execute(query % (term))
        results = cur.fetchall()
        print "successful search query"
        for result in results :
            result = {'name':result['name'], 'text' :result['message']}
            emit('search', result)
    except:
        print("Error executing query")
        print query
        
        
        
        
        
        
        
        
        
        
        
        

@socketio.on('message', namespace='/chat')
def new_message(message):
    tmp = {'text':message, 'name':users[session['uuid']]['username']}
    query = "insert into data (id, message) values (%s,%s);"
    try:
        cur.execute(query, (session['id'], message))
        print "successful message query"
        conn.commit()
        messages.append(tmp)
        emit('message', tmp, broadcast=True)
        print query
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
        session['id'] = 'none'
        cur.execute(query, (data['name'], data['password']))
        serialID = cur.fetchone()
        session['id'] = str(serialID[0])
        print session['id']
        emit('loginSuccess')
    except:
        print("Error executing query")
    query = "SELECT users.name, data.message FROM data INNER JOIN users ON data.id = users.id WHERE users.id = %s FETCH FIRST 10 ROWS ONLY;"
    try:
        cur.execute(query, (session['id']))
        messages = cur.fetchall()
        for message in messages:
            message = {'name':message['name'], 'text' :message['message']}
            emit('message', message)
        print "get user messages susscessful"
    except:
        print("ERROR getting user messages")
        print query
    #users[session['uuid']]={'username':message}
    #updateRoster()

@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    print 'disconnect'
    if session['uuid'] in users:
        del users[session['uuid']]
        updateRoster()
        session.pop('uuid', None)

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
     