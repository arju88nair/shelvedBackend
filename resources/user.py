from flask import Response, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    jwt_required, get_jwt, unset_jwt_cookies
from database.model import User, RevokedTokenModel, Category
from flask_restful import Resource
import datetime
import json
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist
from resources.errors import (SchemaValidationError, EmailAlreadyExistsError, UnauthorizedError,
                              InternalServerError, BadTokenError, UserDoesnotExistError, UserNameDoesnotExistsError)
from util.helpers import add_token_to_database, revoke_token
from flask import current_app as app


class SignupApi(Resource):
    @staticmethod
    def post():
        """[Signup]
        
        Raises:
            SchemaValidationError: [Error in data]
            EmailAlreadyExistsError: [Email exists]
            InternalServerError: [Query error]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            body = request.get_json()
            user = User(**body)
            user.hash_password()
            user.save()
            userId = user.id
            return tokenCreation(user, body, "Successfully Signed Up", userId)
        except FieldDoesNotExist as e:
            print(e)
            raise SchemaValidationError
        except NotUniqueError as e:
            print(e)
            for field in User._fields:  # You could also loop in User._fields to make something generic
                if field in str(e):
                    if field == 'username':
                        raise UserNameDoesnotExistsError
                    if field == 'email':
                        raise EmailAlreadyExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


class LoginApi(Resource):

    @staticmethod
    def post():
        """[Login API]

        Raises:
            UnauthorizedError: [Without the token]
            InternalServerError: [Query error]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            body = request.get_json()
            user = User.objects.get(email=body.get('email'))
            return tokenCreation(user, body, "Successfully Logged In", user.id)
        except UnauthorizedError:
            raise UnauthorizedError
        except  DoesNotExist:
            raise UserDoesnotExistError
        except Exception as e:
            print(e)
            raise InternalServerError


class TokenApi(Resource):

    @jwt_required(refresh=True)
    def post(self):
        """[Token Refresh API]
        
        Raises:
            BadTokenError: [Something went wrong with the identity for token generation]
        Returns:
            [json] -- Json with updated tokens.
        """
        try:
            currentUserID = get_jwt_identity()
            if not currentUserID:
                raise BadTokenError
            else:
                access_token = create_access_token(identity=str(currentUserID))
                add_token_to_database(access_token, app.config['JWT_IDENTITY_CLAIM'])
                data = json.dumps({'access_token': access_token, 'message': "Token refreshed."})
                return Response(data, mimetype="application/json", status=200)

        except BadTokenError:
            raise BadTokenError


class LogoutApi(Resource):
    @jwt_required
    def delete(self):
        """[Logout and access token revoke]
        
        Arguments:
            Resource {Self}
        
        Returns:
            [json] -- Json with message.
        """
        jti = get_jwt()['jti']
        try:
            user_identity = get_jwt_identity()
            revoke_token(jti, user_identity)
            payload = json.dumps({'message': 'Access token has been revoked'})
            return Response(payload, mimetype="application/json", status=200)
        except:
            return InternalServerError


class LogoutRefreshAPI(Resource):
    @jwt_required(refresh=True)
    def delete(self):
        """[Revoke Refresh tokens]
        
        Arguments:
            Resource {[self]} -- 
        
        Returns:
            [json] -- Json with message.
        """
        jti = get_jwt()['jti']
        try:
            user_identity = get_jwt_identity()
            revoke_token(jti, user_identity)
            payload = json.dumps({'message': 'Refresh token has been revoked'})
            return Response(payload, mimetype="application/json", status=200)
        except:
            return InternalServerError


def  tokenCreation(user, body, message, userId):
    authorized = user.check_password(body.get('password'))
    if not authorized:
        raise UnauthorizedError
    accessTokenExpiry = datetime.timedelta(days=7)
    refreshTokenExpiry = datetime.timedelta(days=60)
    access_token = create_access_token(identity=str(user.id), expires_delta=accessTokenExpiry)
    refresh_token = create_refresh_token(identity=str(user.id), expires_delta=refreshTokenExpiry)

    # Store the tokens in our store with a status of not currently revoked.
    add_token_to_database(access_token, app.config['JWT_IDENTITY_CLAIM'])
    add_token_to_database(refresh_token, app.config['JWT_IDENTITY_CLAIM'])
    data = json.dumps(
        {'id': str(userId), 'access_token': access_token, "refresh_token": refresh_token,
         'message': message, 'username': user.username, 'email': user.email})
    return Response(data, mimetype="application/json", status=200)
