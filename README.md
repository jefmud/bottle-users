# bottle_users
A simplified user module for web frameworks like Bottle, Flask, etc.

A very simple user database with encryption/authentication.  The only thing required for defining a user is the
username and the password (which is stored encrypted and hashed).  But one can easily add extra keyword/value pairs to user records
if you require more.  There is no "opinionated" part except for username/password and that we use SHA256/3000 rounds.  This
provides decent encryption.

You have to do the rest!

dependencies:

passlib - from their website "Passlib is a password hashing library for Python 2 & 3, which provides cross-platform implementations"

https://passlib.readthedocs.io/en/stable/

TinyMongo and TinyDB - from the website "A simple wrapper to make a drop in replacement for mongodb out of tinydb."

The TinyMongo client provides simple JSON storage of a user database.

https://github.com/schapman1974/tinymongo


PIP installation (use at your own risk!).  Note, you must also "pip install" the dependencies.

```
$ pip install https://github.com/jefmud/bottle_users
$ pip install tinymongo
$ pip install passlib
```

Simple Usage:
```
import bottle_users

bottle_users.initialize()

# simple create users
user1 = bottle_users.create_user('myusername','mypassword')

# create a user with many keyword/value pairs,
# whatever you want that makes sense with JSON would work.
user2 = bottle_users.create_user(
    username='user1',
    password='somesecret',
    lastname='Smith',
    firstname='John',
    roles=['author','editor']
)


# get all users
users = bottle_users.get_users()

# authenticate a user with plain-text password
if bottle_users.authenticate(username, password):
    print("You passed authentication")
else:
    print("You failed authentication")
```

## Using Usermanager object

A more advanced use case would involve instantiating the class UserManager.  This encapsulates
the functions of a UserManager.  I am also using with a Session object in the package.  This allows
the programmer to access the decorator @login_required for a function, which works in concert with the
session object.

```
from bottle_users.session import Session
from bottle_users.users import UserManager, login_required

from bottle import Bottle, request, redirect
import json

app = Bottle()
SECRET = 'IamASecretSecret'
session = Session(SECRET)
usermanager = UserManager(SECRET)

@app.route('/', name="index")
def index():
    return "Index Route"

@app.route('/login', method=('GET', 'POST'), name='login')
def login():
    form = usermanager.login_page
    if request.method == 'POST':
        username = request.forms.get('username')
        password = request.forms.get('password')
        if usermanager.authenticate(username, password):
            usermanager.login_user(username)
            return redirect(app.get_url('users'))
    return form

@app.route('/logout')
def logout():
    usermanager.logout_user()
    return "you are now logged out"

@app.route('/users', name='users')
def users_view():
    return json.dumps(usermanager.get_users())

@app.route('/user')
@app.route('/user/<username>')
@login_required
def user_view(username=None):
    if username:
        return json.dumps(usermanager.get_user(username))
    return json.dumps(usermanager.get_user())

@app.route('/sessions')
def sessions_view():
    return json.dumps(usermanager.sessions)

if __name__ == '__main__':
    usermanager.create_user('admin','admin')
    usermanager.create_user('user1', 'user1me')
    app.run(port=5000, server='paste')
```


