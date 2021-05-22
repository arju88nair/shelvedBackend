from bson import ObjectId
from bson.json_util import dumps
from flask import Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mongoengine.errors import DoesNotExist

from database.model import Post
from resources.errors import InternalServerError, ItemNotExistsError


class ByBoardApi(Resource):
    """[Batch Comment actions]
    """

    @jwt_required
    def get(self, id):
        """[Retrieves all Posts under a board]
        
        Raises:
            InternalServerError: [If Eror in retrieval]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            posts = Post.objects.aggregate(
                {"$lookup": {
                    "from": "board",
                    "foreignField": "_id",
                    "localField": "board",
                    "as": "board",
                }},
                {"$unwind": "$Board"},
                {"$match": {"board._id": ObjectId(id)}},
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
