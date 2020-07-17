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


PIP installation (use at your own risk!)
```
$ pip install https://github.com/jefmud/bottle_users
```

Usage:
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



