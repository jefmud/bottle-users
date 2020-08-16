# A one module Session manager class for the Bottle microframework
# This is still experimental, so caveat emptor
# written by Jeff
# Heavy debt to the fine work of the Python Project, TinyMongo, TinyDB, and
# Marcel Hellkamp's Bottle microframework.
#
import time
import tinymongo as tm
import tinydb
from bottle import request, response, abort

# a required stub for the new Tiny Mongo to use JSON local storage
# you could easily modify this to use a Mongo server, if you know what I am
# talking about, I expect you would understand what needs to be changed to support pymongo
class TinyMongoClient(tm.TinyMongoClient):
    @property
    def _storage(self):
        return tinydb.storages.JSONStorage

class Session:
    """
    Session class manages cookie based sessions
    __init__(self, secret, data_dir='./data', cookie_name='session', max_age=86400)
    : parameter secret : a secret key (string) which is used for encryption
    : parameter data_dir : the directory where the session JSON is stored default = './data'
    : parameter cookie_name : the cookie key stored.  Some people like to modify this to obfuscate its function
    : parameter max_age : the expiration time in seconds from now.  default=86400 (24 hours)
    
    NOTE: this Session Object is very simple and does not support caching.  It is not a huge problem.
    But introduces a quirk (derived from the Bottle microframework) in that when a cookie is set,
    it is not available to be read until the request/response cycle is completed.
    Once the initial session cookie has been set with the session
    database id, then multiple writes in any controller function are supported.
    
    Thus, when a user "arrives" on the site you should limit yourself to one "set", "set_dict"
    or "set_kwargs" transaction in the first request/response cycle.
    
    If you don't then the cookie is reset each time you try to put in
    more data!  In essence, you will have zombie session records, which are eventually cleaned up when
    these expire.
    
    workaround: one can use the app add_hook to hook a "before_request" similar to flask decorator
    method.  The session cookie can be checked and established and the user's request.remote_address
    could be put into the session.  This can be used to help prevent cookie poaching. 
    
    example
     > # instantiate a session with a secret key -- a secret key is required to encrypt the session
     > session = Session('secretKey!')
     > # put some data in the session
     > # during a request/response cycle
     > session.set_kwargs(username="jim2112", is_authenticated=True, roles=['editor','author'])
     > # you can also set data with a dictionary
     > session.set_dict({'username':'delta52','is_authenticated=True', roles=['subscriber'])
     > # you can get data from the session in 2 ways
     > username = session.get('username')
     > # or you can get the entire session data record (returned as a dictionary)
     > data = session.data
     
    """
    def __init__(self, secret, data_dir='./data', cookie_name='session', max_age=86400):
        """
        __init__(self, secret, data_dir='./data', cookie_name='session', max_age=86400) -
        see docstring for the Session class for details on parameters.
        """
        self.secret = secret
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.data_dir = data_dir
        
        self.db = TinyMongoClient(data_dir).sessions
        
    def set(self, key, value):
        """
        set(self, key, value) - set a key/value pair in the session.
        """
        self.set_dict({key:value})
        
    def set_dict(self, data):
        """
        set_dict(self, data) - adds a dictionary to the session
        : parameter data : data is a dictionary of key/value pairs
        
        example
         > session.set_dict({'first_name':'Ricky', 'last_name':'LeFleur'})
        """
        self.set_kwargs(**data)
        
    def set_kwargs(self, **kwargs):
        """set(self, **kwargs)
        set session values as keyword args.
        Because of the way Bottle handles cookies-- you should NOT set session values multiple times
        as it could have unexpected results.
        
        example
          > session.set_kwargs(first_name='Ricky', last_name='LeFleur')
        """
        # first, check if session cookie exists
        sid = request.get_cookie(self.cookie_name, default=None, secret=self.secret)
        if sid:
            sess_key = {'_id':sid}
            data = self.db.sessions.find_one(sess_key)
            if data:
                # existing session record, convert to dictionary
                data = dict(data)
            else:
                # could not find session record, change the sid to None
                # (this should not happen in normal circustances, but need to anticipate)
                # at this point it looks like a fresh new session
                sid = None

        if sid is None:
            # prepare a new record with a timestamp
            data = {'_timestamp_':int(time.time())}
            
        for key, value in kwargs.items():
            # add the kwargs to the data, note-- we will allow
            # programmer to possibly affect important values without raising an error
            # which is a programmer choice ;-)
            data[key] = value
            
        # write the data
        if sid:
            # update existing record in the database
            self.db.sessions.update_one(sess_key, {'$set': data})
        else:
            # this is a new record, so need to set the cookie
            sid = self.db.sessions.insert_one(data).inserted_id
            response.set_cookie(name=self.cookie_name, value=sid,
                                secret=self.secret,
                                path='/',
                                max_age=self.max_age)
        self.clean_up_expired()
                
    def get(self, key, default_value=None, strict=False):
        """
        get(self, key, default_value=None)
        returns a key value from the session data
        : param key : the key to get
        : param default_value : the default value if no key exists
        : param strict : if True, raise an error if no session cookie exists
        """
        # read the session from the cookie
        sid = request.get_cookie(self.cookie_name, default=None, secret=self.secret)
        if strict and not sid:
            raise ValueError("Session cookie does not exist")
        data = self.db.sessions.find_one({'_id':sid})
        if data is None:
            # trap non-existent record
            if strict:
                raise ValueError("Session was not found sid={}".format(sid))
            return default_value
        
        return data.get(key, default_value)
        
    def clear(self, strict=False):
        """
        clear(self) - clears a session
        """
        sid = request.get_cookie(self.cookie_name, default=None, secret=self.secret)
        sess_key = {'_id':sid}
        if strict and not sid:
            # cookie was not found, so we can give an 400 (Bad Request)
            abort(400)
        data = self.db.sessions.find_one(sess_key)
        if data is None and strict:
            # no matching session data record found (Bad Request)
            abort(400)
        if data:
            self.db.sessions.remove(data)
            response.delete_cookie(key=self.cookie_name, secret=self.secret)
            return True
        return False
        
    @property
    def data(self):
        """
        data is a property that returns the session dictionary.  This should be used carefully
        since there might be secret data in the session.
        """
        sid = request.get_cookie(self.cookie_name, default=None, secret=self.secret)
        if sid:
            sess_key = {'_id':sid}
            sess_data = self.db.sessions.find_one(sess_key)
            if sess_data:
                return dict(sess_data)
        return {}
        
    def clean_up_expired(self):
        """
        clean_up_expired() ==> cleans up expired sessions in the database
        :return: None
        
        Note: this is automatically called anytime a new session begins
        """
        sessions = self.db.sessions.find()
        for session in sessions:
            start_time = session.get('_timestamp_', 0)
            current_time = int(time.time())
            if current_time - start_time > self.max_age:
                self.db.sessions.remove(session)
        return None
    
    @property
    def sessions(self):
        """
        sessions(self) - :returns: LIST of session database records
        Note: this would not normally be used, but it is here for testing convenience
        """
        return list(self.db.sessions.find())

    def session_purge_id(self, sid):
        """
        session_purge_id(self, id) ==> allows a programmer to purge a particular sid
        : return : the deleted session record or None (if not present)
        I would not expect this to be needed in normal operations, but it could be used
        for testing scenarios where the session database records might have been deleted.
        """
        session_key = {'_id', sid}
        session = self.db.sessions.find_one(session_key)
        if session:
            self.db.sessions.remove(session)
        return session
    
    def age(self):
        """
        age() ==> return the age in seconds of the session
        """
        return int(time.time()) - self.get('_timestamp_', 0)
    
    def expired(self):
        """
        expired() ==> return a boolean True if expired session, else False
        """
        return self.age() > self.max_age    
