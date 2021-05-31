import urllib.parse as urlparse
from database.model import RevokedTokenModel
from flask_jwt_extended import decode_token
from datetime import datetime
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, ValidationError
from resources.errors import (SchemaValidationError, EmailAlreadyExistsError, UnauthorizedError,
                              InternalServerError, BadTokenError, TokenNotFound)
import random


def validateURL(url):
    """[Checking if string is ur]
    
    Arguments:
        url {[string]} -- [URL]
    
    Returns:
        [Boolean]
    """
    return urlparse.urlparse(url).scheme != ""


def _epoch_utc_to_datetime(epoch_utc):
    """
    Helper function for converting epoch timestamps (as stored in JWTs) into
    python datetime objects (which are easier to use with sqlalchemy).
    """
    return datetime.fromtimestamp(epoch_utc)


def add_token_to_database(encoded_token, identity_claim):
    """[    Adds a new token to the database. It is not revoked when it is added.
        :param encoded_token:
        :param identity_claim:]

    Arguments:
        encoded_token {[Token]} 
        identity_claim {[Tag]}

    Raises:
        SchemaValidationError
        PostAlreadyExistsError
        InternalServerErroridentity_claimidentity_claim
        TokenNotFoundidentity_claim
        InternalServerError
    """

    try:
        body = {}
        decoded_token = decode_token(encoded_token)
        body["jti"] = decoded_token['jti']
        body["token_type"] = decoded_token['type']
        body["user_identity"] = decoded_token[identity_claim]
        body["expires"] = _epoch_utc_to_datetime(decoded_token['exp'])
        body["revoked"] = False
        db_token = RevokedTokenModel(**body)
        db_token.save()

    except (FieldDoesNotExist, ValidationError):
        raise SchemaValidationError
    except NotUniqueError:
        raise PostAlreadyExistsError
    except Exception as e:
        raise InternalServerError


def revoke_token(token_id, user):
    """[    Revokes the given token. Raises a TokenNotFound error if the token does
    not exist in the database]
    
    Arguments:
        token_id {[JTI]} -- [Token]
        user {[Current user]} -- [User]
    
    Raises:
        TokenNotFound: [If Token is unavailable]
    """
    try:
        token = RevokedTokenModel.objects(user_identity=user, jti=token_id).update(revoked=True)
    except FieldDoesNotExist:
        raise TokenNotFound
    except Exception as e:
        raise InternalServerError


def generateName():
    secure_random = random.SystemRandom()
    name = secure_random.choice(slugGenWords) + '_' + secure_random.choice(right)
    return name
