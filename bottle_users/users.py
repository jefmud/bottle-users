############## Simple user model for applications
# uses SHA256 which is generally robust for producing encrypted/hashed passwords
#
# The only requirements for the user model are a username and a password
#
# exposes:
#
# function { authenticate(username, password) } - looks for an existing username
#          and checks if the password matches the hashed version in the database
#          if it does, it returns True, not, it returns False
# function {initialize(datadir)} - initializes the JSON database in a directory
# function {get_user(username, uid)} - returns a user record from a username
#  or id.  On failure returns None
# function {get_users()} - returns a list of all users
# function {delete_user(username, uid)} - returns a user if it deleted a user
#     identified by username or uid
# function {create_user(username, password, **kwargs)} - creates a user record
#      username, password required -- the only validation is that username does not
#      currently exist.  **kwargs are optional keyword arguments to include in the
#      user record... for example is_active=True, display_name=John Doe
# function { update_user(username, **kwargs) } - add additional keyword arguments
#       to an existing record.  If a keyword argument value is EXPLICITLY set to None
#       the existing key/value will be removed.
#
# The programmer can easily extend this with an update_user
# EXAMPLE of Usage
#  -- see example.py

######## ENCRYPTION SECTION ###############
# establish a simple user model and authentication handling
# encryption inspired by Jose Salvatierra's excellent blog on encrypting password
# https://blog.tecladocode.com/learn-python-encrypting-passwords-python-flask-and-passlib/
#
# should provide a relatively independent user model stored in a JSON file
#
import functools
from passlib.context import CryptContext
from session import Session

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)

def encrypt_password(password):
    return pwd_context.encrypt(password)

def check_encrypted_password(password, hashed):
    return pwd_context.verify(password, hashed)

import os

# importing TinyMongo support
import tinymongo as tm
import tinydb

# a required stub for the new Tiny Mongo to use JSON local storage
# you could easily modify this to use a Mongo server, if you know what I am
# talking about, I expect you would understand what needs to be changed to support pymongo
class TinyMongoClient(tm.TinyMongoClient):
    @property
    def _storage(self):
        return tinydb.storages.JSONStorage

############ USER MODEL and OPERATIONS ##############
#
# we can fix this later, for now, put userdata JSON in local data dir

# internal database and session
_db = None
_session = None

def initialize(data_dir=None):
    """initialize(datadir=None) ==> initializes the database
    : param {data_dir} : (optional) the directory where the JSON will be stored.

    Note: by default, it is stored in the app level data folder.
    Your project may want to explicitly specify something that fits
    with your project's data specifications.
    """
    global _db
    if data_dir is None:
        # use module level data directory
        # moduledir = os.path.dirname(__file__)
        # datadir = os.path.join(moduledir, 'data')
        # CHANGED - use project relative data dir
        data_dir = './data'
    _db = TinyMongoClient(data_dir).userdata


def get_users():
    """get_users() - return a list of all users JSON records"""
    if _db is None:
        raise ValueError("Database not initialized!")
    return list(_db.users.find())

def get_user(username=None, uid=None):
    """get_user(username, uid) ==> find a user record by uid or username
    : param {username} : - a specific username (string)
    : param {uid} : - a specific user id (string) - note, this is actual '_id' in databse
    : return : a user record or None if not found
    """
    if _db is None:
        raise ValueError("Database not initialized!")
    # first try the username--
    user = None
    if username:
        user = _db.users.find_one({'username': username})
    if uid:
        user = _db.users.find_one({'_id':uid})
    return user

def create_user(username, password, **kwargs):
    """
    create_user(username, password, **kwargs) ==> create a user --
    : param {username} and param {password} : REQUIRED
    : param **kwargs : python style (keyword arguments, optional)
    : return : Boolean True if user successfully created, False if exisiting username
    example
    create_user('joe','secret',display_name='Joe Smith',is_editor=True)
    """
    user = get_user(username=username)
    if user:
        # user exists, return failure
        return False
    # build a user record from scratch
    user = {'username':username, 'password': encrypt_password(password)}
    for key, value in kwargs.items():
        user[key] = value

    _db.users.insert_one(user)
    return True

def update_user(username, **kwargs):
    """
    update_user(username, **kwargs) - update a user record with keyword arguments
    : param {username} : an existing username in the database
    : param **kwargs : Python style keyword arguments.
    : return : True if existing username modified, False if no username exists.
    update a user with keyword arguments
    return True for success, False if fails
    if a keyword argument is EXPLICITLY set to None,
    the argument will be deleted from the record.
    NOTE THAT TinyMongo doesn't implement $unset
    """
    user = get_user(username)
    if user:
        idx = {'_id': user['_id']}
        for key, value in kwargs.items():
            if value is None and key in user:
                # delete the key
                _db.users.update_one(idx, {'$unset': {key:""}} )
            else:
               # user[key] = value
               _db.users.update_one(idx, {'$set': {key:value}} )
        #_db.users.update_one(idx, user)
        return True
    return False

def delete_user(username=None, uid=None):
    """delete_user(username, uid) deletes a user record by username or uid
    : param {username} : string username on None
    : param {uid} : string database id or None
    : return : returns user record upon success, None if fails
    """
    user = None
    if username:
        user = get_user(username=username)
    if uid:
        user = get_user(uid=uid)
    if user:
        _db.users.remove(user)
    return user

def authenticate(username, password):
    """
    authenticate(username, password) ==> authenticate username, password against datastore
    : param {username} : string username
    : param {password} : string password in plain-text
    : return : Boolean True if match, False if no match
    """
    user = get_user(username)
    if user:
        if check_encrypted_password(password, user['password']):
            return True
    return False
def login_page(login_filename=None):
    """login_form(login_file=None) returns a login page as a string contained
    login_file if None, then if loads module level file login.html
    : param {login_filename} : string of filename of login page HTML document or None.
    If None, then the package level standard login.html is loaded.
    : return : string HTML of login page
    NOTE: this is an experimental feature
    """
    # use module level 'login.html''
    if login_filename is None:
        moduledir = os.path.dirname(__file__)
        login_filename = os.path.join(moduledir, 'login.html')
    with open(login_filename) as fp:
        data = fp.read()
    return data

def login_required(func):
    """
    login_required() - a decorator function which checks session associated with
    the UserManager class to determine if the user is logged in.

    Note: this only works with an instantiated UserManager class that contains an
    associated session.
    """
    from bottle import redirect, abort
    @functools.wraps(func)
    def wrapper_login_required(*args, **kwargs):
        fail_url = '/login'
        if _session is None:
            msg = 'login_required ONLY works with UserManager class'
            raise ValueError(msg)
        username = _session.get('username')
        if username is None:
            if fail_url == None:
                abort(403)
            return redirect(fail_url)
        return func(*args, **kwargs)
    return wrapper_login_required

class UserManager:
    """
    UserManager(secret, data_dir) -this class simply wraps the exposed user
    functions into an object along with a session object.  A programmer could
    still another Session object if required.
    """
    def __init__(self, secret, data_dir=None, max_age=86400, login_filename=None):
        """
        __init__(self, secret, data_dir=None)
        : param {secret} : secret to encrypt _um cookies
        : param {data_dir} : data directory for user database default='./data'
        " param {max_age} : maximum age in seconds for user sessions, default 24 hours
        : param {login_page} : string path to a login.html template file, if None
        load the standard form login.html from this package.
        """
        global _session, _db
        self.login_page = login_page(login_filename)
        if data_dir is None:
            data_dir = './data'
        self.secret = secret
        self.data_dir = data_dir
        self.max_age = max_age
        # initialize user db if needed
        if _db is None:
            initialize(data_dir=data_dir)
        self.db = _db

        # initialize internal session.
        if _session is None:
            # establish a new session
            _session = Session(self.secret,
                data_dir=data_dir,
                cookie_name="_um",
                max_age=max_age)
        self.session = _session
        
    def create_user(self, username, password, **kwargs):
        return create_user(username, password, **kwargs)

    def authenticate(self, username, password):
        return authenticate(username, password)

    def get_users(self):
        return get_users()

    def get_user(self, username=None, uid=None):
        if username is None and uid is None:
            username = self.current_username
        return get_user(username=username, uid=uid)

    def delete_user(self, username=None, uid=None):
        return delete_user(username=username, uid=uid)

    def update_user(self, username, **kwargs):
        return update_user(username, **kwargs)

    @property
    def current_username(self):
        if self.session:
            return self.session.get('username')
    @property
    def current_uid(self):
        if self.session:
            return self.session.get('_id')

    def login_user(self, username=None, uid=None):
        """
        login_user(username=None, uid=None) - perform session operations for a particular user
        : param {username} : - string with a valid username or None
        : param {uid} : - string with a valid uid or None
        : return : True if user logged in, False if failed
        """
        if username is None and uid is None:
            msg = 'UserManager.login_user() requires either a username or uid'
            raise ValueError(msg)

        user = self.get_user(username)
        if user:
            # remove the password and _id, for security and non-collision
            del user['password']
            del user['_id']
            # push the user record into the session database
            self.session.set_dict(user)
            return True
        return False

    def logout_user(self):
        """
        logout_user() - logout current user
        : return : None
        """
        self.session.clear()

    @property
    def sessions(self):
        return self.session.sessions
        

