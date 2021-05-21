from flask import Response, request
from database.model import Comment, User, Post
from flask_restful import Resource
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError
from resources.errors import SchemaValidationError, InternalServerError, UpdatingItemError, DeletingItemError, \
    ItemNotExistsError, ItemAlreadyExistsError, UpdatingItemError
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from bson import ObjectId
from bson.json_util import dumps


class ByCategoryApi(Resource):
    """[Batch Comment actions]
    """

    @jwt_required
    def get(self, id):
        """[Retrieves all Posts under a category]
        
        Raises:
            InternalServerError: [If Eror in retrieval]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            posts = Post.objects.aggregate(
                {"$lookup": {
                    "from": "category",
                    "foreignField": "_id",
                    "localField": "category",
                    "as": "category",
                }},
                {"$unwind": "$category"},
                {"$match": {"category._id": ObjectId(id)}},
                {
                    "$addFields": {
                        "liked": {
                            "$in": [user_id, "$liked_by"]
                        }
                    }
                }, {"$sort": {"created_date": 1}})
            converted = []
            for item in list(posts):
                converted.append(item)
            print(converted)
            data = dumps({'data': list(converted), 'message': "Successfully retrieved"})
            return Response(data, mimetype="application/json", status=200)
        except  DoesNotExist:
            raise ItemNotExistsError
        except Exception as e:
            print(e)
            raise InternalServerError
