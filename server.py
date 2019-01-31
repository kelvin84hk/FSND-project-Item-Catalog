from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
import os
app = Flask(__name__)


from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
GOOGLE_CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']


from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, catalogItem
from sqlalchemy import func
from sqlalchemy import desc
engine = create_engine('sqlite:///catalog.db') 
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):  # force to refresh css
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.route('/',methods=['GET','POST'])
@app.route('/catalog', methods=['GET','POST'])
def loadMain():  # show all items
    if request.method == 'GET':
    	categories = session.query(Category).all()
    	items = session.query(catalogItem).order_by(desc(catalogItem.id))
        if 'username' not in login_session:
            state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
            login_session['state'] = state
            return render_template('allobjects.html',
            	STATE=state,
            	IsLogedIn = False,
            	categories=categories,
            	items=items,
            	rightmsg ="All items showing the latest first",
            	getCategoryName=getCategoryName)
        else:
            return render_template('allobjectsPrivate.html',
            	IsLogedIn = True,
            	username=login_session['username'],
            	user_id=login_session['user_id'],
            	imgPath=login_session['picture'],
            	categories=categories,items=items,
            	rightmsg ="All items showing the latest first",
            	getCategoryName=getCategoryName)
    else:
    	newItem()
    	return redirect(url_for('loadMain'))


@app.route('/catalog/<int:catalog_id>', methods=['GET'])
def loadCategoryItems(catalog_id):
    categories = session.query(Category)
    category = session.query(Category).filter_by(id = catalog_id).one()
    items = session.query(catalogItem).filter_by(category_id = catalog_id).order_by(desc(catalogItem.id))
    if 'username' not in login_session:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['state'] = state
        return render_template('allobjects.html',
        	STATE=state,
        	IsLogedIn = False,
        	categories=categories,
        	items=items,
        	rightmsg ="Category " + category.name +" items showing the latest first",
        	getCategoryName=getCategoryName)
    else:
        return render_template('allobjectsPrivate.html',
        	IsLogedIn = True,
        	username=login_session['username'],
        	user_id=login_session['user_id'],
        	imgPath=login_session['picture'],
        	categories=categories,
        	items=items,
        	rightmsg = "Category " + category.name +" items showing the latest first",
        	getCategoryName=getCategoryName)


@app.route('/item/<int:item_id>', methods=['GET'])
def loadItem(item_id):
    item = session.query(catalogItem).filter_by(id = item_id).one()
    if 'username' not in login_session:
        return render_template('showobject.html',
        	item = item,
        	IsLogedIn=False)
    else:
        return render_template('showobject.html',
        	username=login_session['username'],
        	user_id=login_session['user_id'],
        	imgPath=login_session['picture'],
        	item = item,
        	IsLogedIn=True)

@app.route('/catalog/allitems/JSON')
def loadItemJSON():
    items = session.query(catalogItem).all()
    return jsonify(Items= [i.serialize for i in items])


@app.route('/catalog/allcategories/JSON')
def loadCategoryJSON():
    categories = session.query(Category).all()
    return jsonify(Categories= [c.serialize for c in categories])


@app.route('/edititem/<int:item_id>', methods=['GET','POST'])
def editItem(item_id):
    if 'username' not in login_session:
        response = make_response(json.dumps('Security breach!!! You are trying to edit item without login!!!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    item = session.query(catalogItem).filter_by(id = item_id).one()
    if login_session['user_id'] != item.user_id:
        response = make_response(json.dumps('Security breach!!! You are trying to edit item which was not created by you!!!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if request.method == 'GET':
        categories = session.query(Category)
        return render_template('editobject.html',
        	username=login_session['username'],
        	user_id=login_session['user_id'],
        	imgPath=login_session['picture'],
        	categories=categories,
        	item = item,
        	IsLogedIn=True)
    else:
        editItem(item)
        return redirect(url_for('loadMain'))


@app.route('/deleteItem/<int:item_id>', methods=['GET','POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        response = make_response(json.dumps('Security breach!!! You are trying to delete item without login!!!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    item = session.query(catalogItem).filter_by(id = item_id).one()
    if login_session['user_id'] != item.user_id:
        response = make_response(json.dumps('Security breach!!! You are trying to delete item which was not created by you!!!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    item = session.query(catalogItem).filter_by(id = item_id).one()
    if request.method == 'GET':
        return render_template('deleteobject.html',
        	username=login_session['username'],
        	user_id=login_session['user_id'],
        	imgPath=login_session['picture'],
        	item = item,
        	IsLogedIn=True)
    else:
        deleteItem(item)
        return redirect(url_for('loadMain'))



@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
      response = make_response(json.dumps('Invalid state parameter'), 401)
      response.headers['Content-Type'] = 'application/json'
      return response

    code = request.data
    try:
      oauth_flow = flow_from_clientsecrets('client_secrets.json',scope='')
      oauth_flow.redirect_uri = 'postmessage'
      credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
      response = make_response(json.dumps('Failed to upgrade the authorization code.'),401)
      response.headers['Content-Type'] = 'application/json'
      return response 
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    if result.get('error') is not None:
      response = make_response(json.dumps(result.get('error')),500)  
      response.headers['Content-Type'] = 'application/json'
      return response 
      
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
      response = make_response(json.dumps("Token's user ID dosen't match given user ID."), 401)
      response.headers['Content-Type'] = 'application/json'
      return response

     # Verify that the access token is valid for this app.
    if result['issued_to'] != GOOGLE_CLIENT_ID:
      response = make_response(
          json.dumps("Token's client ID does not match app's."), 401)
      print "Token's client ID does not match app's."
      response.headers['Content-Type'] = 'application/json'
      return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token  is not None and gplus_id == stored_gplus_id:
      response = make_response(json.dumps('<h5>Current user is already connected</h5>'),200)
      response.headers['Content-Type'] = 'application/json'
      return response
    
    login_session['provider'] = 'google'  
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url ="https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token,'alt':'json'}
    answer = requests.get(userinfo_url,params=params)
    data = answer.json()
    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    userID= getUserID(login_session['email'])

    if userID is None:
        userID = createUser(login_session)
    login_session['user_id']=userID
      
    output=''
    output += '<h5>Welcome, '
    output += login_session['username']
    output +=  '!</h5>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    return output


@app.route('/gdisconnect')
def gdisconnect():
  # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        #del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('loadMain'))
    else:
        flash("You were not logged in")
        return redirect(url_for('loadMain'))


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v3.2/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v3.2/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h5>Welcome, '
    output += login_session['username']

    output += '!</h5>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


def createUser(login_session):
  newUser = User(name = login_session['username'],email = login_session['email'], picture = login_session['picture'])
  session.add(newUser)
  session.commit()
  user = session.query(User).filter_by(email=login_session['email']).one()
  return user.id

def getUserInfo(user_id):
  user = session.query(User).filter_by(id = user_id).one()
  return user

def getUserID(email):
  try:
    user = session.query(User).filter_by(email =email).one()
    return user.id
  except:
    return None


def getCategoryID(categoryName):
	category = session.query(Category).filter(func.lower(Category.name) == func.lower(categoryName)).one()
	return category.id


def getCategoryName(categoryID):
	category = session.query(Category).filter_by(id=categoryID).one()
	return category.name


def newItem():
    if request.form['categorySelect']!="Add new category":
        categoryname = request.form['categorySelect'].strip()
    else:
        categoryname = request.form['categoryName'].strip()
    try:
        category_id = getCategoryID(categoryname)
    except:
        newCategory = Category(name = categoryname, user_id = login_session['user_id'])
        session.add(newCategory)
        session.commit()
        category_id = getCategoryID(newCategory.name)
    newItem = catalogItem(title = request.form['title'], description = request.form['description'], category_id = category_id, user_id = login_session['user_id'])
    session.add(newItem)
    session.commit()
    flash('New catalog %s Item Successfully Created' % (newItem.title))
    return None


def editItem(item):
    if request.form['categorySelect']!="Add new category":
        categoryname = request.form['categorySelect'].strip()
    else:
        categoryname = request.form['categoryName'].strip()
    try:
        category_id = getCategoryID(categoryname)
    except:
        newCategory = Category(name = categoryname, user_id = login_session['user_id'])
        session.add(newCategory)
        session.commit()
        category_id = getCategoryID(newCategory.name)
    item.title = request.form['title']
    item.description = request.form['description']
    category_id_old = item.category_id 
    item.category_id = category_id
    session.add(item)
    session.commit()
    deleteCategoryIfneeded(category_id_old)
    flash('Item %s Successfully Edited' % (item.title))
    return None


def deleteItem(item):
    category_id = item.category_id
    session.delete(item)
    session.commit()
    deleteCategoryIfneeded(category_id)
    flash('Item Successfully Deleted')
    return None


def deleteCategoryIfneeded(category_id): # delete empty categories
    if session.query(catalogItem).filter_by(category_id=category_id).count() == 0 :
    	category = session.query(Category).filter_by(id=category_id).one()
    	session.delete(category)
    	session.commit()
        return None
    else:
        return None	

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000, threaded=False)
