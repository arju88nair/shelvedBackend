from bson import ObjectId
from bson.json_util import dumps
from flask import Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mongoengine.errors import DoesNotExist

from database.model import Item
from resources.errors import InternalServerError, ItemNotExistsError


class BoardItems(Resource):
    """[Batch Comment actions]
    """

    @jwt_required()
    def get(self, id):
        """[Retrieves all Items under a board]

        Raises:
            InternalServerError: [If Error in retrieval]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:

            user_id = get_jwt_identity()
            items = Item.objects.aggregate(
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
                }, {"$sort": {"created_at": 1}})
            converted = []
            for item in list(items):
                converted.append(item)
            print(converted)
            data = dumps({'data': list(converted), 'message': "Successfully retrieved"})
            return Response(data, mimetype="application/json", status=200)
        except  DoesNotExist:
            raise ItemNotExistsError
        except Exception as e:
            print(e)
            raise InternalServerError