from flask import Response, request
from database.model import Post, User
from flask_restful import Resource
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError
from resources.errors import SchemaValidationError, InternalServerError, DeletingItemError, ItemNotExistsError, \
    ItemAlreadyExistsError, UpdatingItemError
from newspaper import Article
from util.helpers import validateURL
import json
from util.slugGenerator import generateSlug
from flask_jwt_extended import jwt_required, get_jwt_identity
from util.summariser import summarize, get_keywords
from bson.json_util import dumps
from bson import ObjectId


class PostsApi(Resource):
    """[Batch Post actions]
    """

    @jwt_required
    def get(self):
        """[Retrieves all Posts]
        
        Raises:
            InternalServerError: [If Eror in retrieval]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            posts = Post.objects().to_json()
            print(type(posts))
            data = {'data': json.loads(posts), 'message': "Successfully retrieved", "count": len(json.loads(posts))}
            data = json.dumps(data)
            response = Response(data, mimetype="application/json", status=200)
            return response
        except Exception as e:
            raise InternalServerError

    @jwt_required
    def post(self):
        """[Batch Post API]
        
        Raises:
            SchemaValidationError: [If there are validation error in the post data]
            ItemAlreadyExistsError: [If the post already exist]
            InternalServerError: [Error in insertion]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        body = request.get_json()

        # source validations
        if 'source' not in body or 'source_url' not in body or 'board' not in body:
            raise SchemaValidationError

        source = body['source']
        source_url = body['source_url']
        board = body['board']

        if source is None or source == '':
            raise SchemaValidationError

        if source_url is None or source_url == '':
            raise SchemaValidationError

        if board is None or board == '':
            raise SchemaValidationError

        if validateURL(source_url) is False and source is not None:
            summary = summarize(body['source'], 3)
            body['summary'] = summary
            body['text'] = body['source']
            body['type'] = "Text"
            body['keywords'] = get_keywords(body['source'])
            body['tags'] = get_keywords(summary)
        else:
            if validateURL(source_url) is False:
                raise SchemaValidationError
            article = Article(source_url)
            article.download()
            article.parse()
            article.nlp()

            body['summary'] = article.summary
            body['text'] = article.text
            body['keywords'] = article.keywords
            body['tags'] = article.keywords
            body['type'] = "URL"

        body['source'] = source
        body['source_url'] = source_url
        body['slug'] = generateSlug()
        data = json.dumps(body)
        try:
            user_id = get_jwt_identity()
            user = User.objects.get(id=user_id)
            post = Post(**body, added_by=user)
            post.save()
            postId = post.id
            data = json.dumps({'id': str(postId), 'message': "Successfully inserted"})
            return Response(data, mimetype="application/json", status=200)
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationError
        except NotUniqueError:
            raise ItemAlreadyExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


class PostApi(Resource):
    """[Individual Post actions]
    """

    @jwt_required
    def put(self, id):
        """[Updating single]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            SchemaValidationError: [If there are validation error in the post data]
            UpdatingItemError: [Error in update]
            InternalServerError: [Error in insertion]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        body = request.get_json()

        # source validations
        if 'source' not in body or 'source_url' not in body or 'board' not in body:
            raise SchemaValidationError

        source = body['source']
        source_url = body['source_url']
        board = body['board']

        if source is None or source == '':
            raise SchemaValidationError

        if source_url is None or source_url == '':
            raise SchemaValidationError

        if board is None or board == '':
            raise SchemaValidationError

        try:
            user_id = get_jwt_identity()
            body = request.get_json()
            Post.objects.get(id=id, added_by=user_id).update(**body)
            data = json.dumps({'message': "Successfully updated"})
            return Response(data, mimetype="application/json", status=200)
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingItemError
        except Exception:
            raise InternalServerError

    @jwt_required
    def delete(self, id):
        """[Deleting single post]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            DeletingItemError: [Error in deletion]
            InternalServerError: [Error in insertion]    
                
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            post = Post.objects.get(id=id, added_by=user_id)
            post.delete()
            data = json.dumps({'message': "Successfully deleted"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise DeletingItemError
        except Exception:
            raise InternalServerError

    @jwt_required
    def get(self, id):
        """[Get single post item]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            ItemNotExistsError: [Can't find the post item]
            InternalServerError: [Error in insertion]    
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            posts = Post.objects.aggregate(
                {"$match": {"_id": ObjectId(id)}},
                {"$lookup": {
                    "from": "board",
                    "foreignField": "_id",
                    "localField": "board",
                    "as": "board",
                }},
                {"$unwind": "$board"},
                {
                    "$addFields": {
                        "liked": {
                            "$in": [user_id, "$liked_by"]
                        }
                    }
                })
            post = list(posts)
            data = dumps({'data': post[0], 'message': "Successfully retrieved"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ItemNotExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


