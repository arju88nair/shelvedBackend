from flask import Flask
from database.db import initialize_db
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api
from resources.errors import errors
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from util.routes import initialize_routes
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app)

# app.config.from_envvar('ENV_FILE_LOCATION')
# app.config['JWT_SECRET_KEY'] = environ.get('JWT_SECRET_KEY')
# app.config['MONGODB_SETTINGS'] = environ.get('MONGODB_SETTINGS')

api = Api(app, errors=errors)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
app.config.from_pyfile('env.py')
# @jwt.token_in_blacklist_loader
# def check_if_token_in_blacklist(decrypted_token):
#     jti = decrypted_token['jti']
#     return RevokedTokenModel.is_jti_blacklisted(jti)


app.config['JWT_SECRET_KEY'] = app.config.get("JWT_SECRET_KEY")
app.config['MONGODB_SETTINGS'] = app.config.get("MONGODB_SETTINGS")
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['MONGODB_SETTINGS'] = {
    'host': 'mongodb://localhost/til'
}
app.config['CORS_HEADERS'] = 'Content-Type'

initialize_db(app)
initialize_routes(api)
if __name__ == "__main__":
    app.run(debug=True)
    app.run(host='0.0.0.0')
    app.run(port=5000)
