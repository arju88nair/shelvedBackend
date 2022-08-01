from flask import Response, request
from database.model import Item, User, Board
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


class ItemsApi(Resource):
    """[Batch Item actions]
    """

    @jwt_required()
    def get(self):
        """[Retrieves all Items]
        
        Raises:
            InternalServerError: [If Error in retrieval]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            items = Item.objects().to_json()
            print(type(items))
            data = {'data': json.loads(items), 'message': "Successfully retrieved", "count": len(json.loads(items))}
            data = json.dumps(data)
            response = Response(data, mimetype="application/json", status=200)
            return response
        except Exception as e:
            raise InternalServerError

    @jwt_required()
    def post(self):
        """[Batch Item API]
        
        Raises:
            SchemaValidationError: [If there are validation error in the item data]
            ItemAlreadyExistsError: [If the item already exist]
            InternalServerError: [Error in insertion]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        body = request.get_json()

        # source validations
        if 'board' not in body:
            raise SchemaValidationError
        # source validations
        if 'item_type' not in body:
            raise SchemaValidationError

        source = body['source']
        source_url = body['source_url']
        board = body['board']
        item_type = body['item_type']

        if source is None or source == '':
            raise SchemaValidationError

        # if source_url is None or source_url == '':
        #     raise SchemaValidationError

        if board is None or board == '':
            raise SchemaValidationError
        if item_type.rstrip() == 'Post':
            summary = summarize(body['source'], 3)
            body['summary'] = body['summary']
            body['content'] = body['summary']
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
            body['content'] = article.text
            body['title'] = article.text
            body['keywords'] = article.keywords
            body['tags'] = article.keywords

        body['source'] = source
        body['source_url'] = source_url
        body['slug'] = generateSlug()
        print(body)
        if 'title' not in body:
            raise SchemaValidationError
        try:
            user_id = get_jwt_identity()
            user = User.objects.get(id=user_id)
            newBoard = Board.objects.get(slug=board)
            body['board'] = newBoard
            item = Item(**body, added_by=user, )
            item.save()
            item_id = item.id
            data = json.dumps({'id': str(item_id), 'message': "Successfully inserted"})
            return Response(data, mimetype="application/json", status=200)
        except (FieldDoesNotExist, ValidationError) as e:
            print(e)
            raise SchemaValidationError
        except NotUniqueError:
            raise ItemAlreadyExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


class ItemApi(Resource):
    """[Individual Item actions]
    """

    @jwt_required()
    def put(self, id):
        """[Updating single]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            SchemaValidationError: [If there are validation error in the item data]
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
            Item.objects.get(id=id, added_by=user_id).update(**body)
            data = json.dumps({'message': "Successfully updated"})
            return Response(data, mimetype="application/json", status=200)
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingItemError
        except Exception:
            raise InternalServerError

    @jwt_required()
    def delete(self, id):
        """[Deleting single item]
        
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
            item = Item.objects.get(id=id, added_by=user_id)
            item.delete()
            data = json.dumps({'message': "Successfully deleted"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise DeletingItemError
        except Exception:
            raise InternalServerError

    @jwt_required()
    def get(self, id):
        """[Get single item item]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            ItemNotExistsError: [Can't find the item item]
            InternalServerError: [Error in insertion]    
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            items = Item.objects.aggregate(
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
            item = list(items)
            data = dumps({'data': item[0], 'message': "Successfully retrieved"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ItemNotExistsError
        except Exception as e:
            print(e)
            raise InternalServerError
