import json
from datetime import datetime

from bson import ObjectId
from bson.json_util import dumps
from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError

from database.model import Comment, User
from resources.errors import SchemaValidationError, InternalServerError, DeletingItemError, \
    ItemNotExistsError, ItemAlreadyExistsError, UpdatingItemError
from util.slugGenerator import generateSlug


class CommentsApi(Resource):
    """[Batch Comment actions]
    """

    @jwt_required
    def get(self):
        """[Retrieves all Comments]
        
        Raises:
            InternalServerError: [If Eror in retrieval]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            comments = Comment.objects().to_json()
            data = {'data': json.loads(comments), 'message': "Successfully retrieved",
                    "count": len(json.loads(comments))}
            data = json.dumps(data)
            response = Response(data, mimetype="application/json", status=200)
            return response
        except Exception:
            raise InternalServerError

    @jwt_required
    def post(self):
        """[Batch Comment API]
        
        Raises:
            SchemaValidationError: [If there are validation error in the post data]
            ItemAlreadyExistsError: [If the comment already exist]
            InternalServerError: [Error in insertion]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        payload = request.get_json()

        # source validations
        if 'comment' not in payload and 'post_id' not in payload:
            raise SchemaValidationError

        body = {}
        posted = datetime.utcnow()
        post_id = payload['post_id']
        parent_slug = ""
        if 'slug_id' in payload:
            slug_id = payload['slug_id']
            parent = Comment.objects.get(slug=slug_id, post_id=post_id)
            # parent['full_slug']
            parent_slug = parent['slug']

        # generate the unique portions of the slug and full_slug
        slug_part = generateSlug()
        full_slug_part = posted.strftime('%Y.%m.%d.%H.%M.%S') + ':' + slug_part
        # load the parent comment (if any)
        if parent_slug:
            slug = parent['slug'] + '/' + slug_part
            full_slug = parent['full_slug'] + '/' + full_slug_part
        else:
            slug = slug_part
            full_slug = full_slug_part
        user_id = get_jwt_identity()
        user = User.objects.get(id=user_id)
        body["added_by"] = user
        body["post_id"] = payload['post_id']
        body["slug"] = slug
        body["full_slug"] = full_slug
        body["comment"] = payload['comment']

        try:
            comment = Comment(**body)
            comment.save()
            id = comment.id
            data = json.dumps({'id': str(id), 'message': "Successfully inserted"})
            return Response(data, mimetype="application/json", status=200)
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationError
        except NotUniqueError:
            raise ItemAlreadyExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


class CommentApi(Resource):
    """[Individual Comment actions]
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
        try:
            get_jwt_identity()
            body = request.get_json()
            Comment.objects.get(id=id).update(**body)
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
        """[Deleting single comment]
        
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
            comment = Comment.objects.get(id=id, added_by=user_id)
            comment.delete()
            data = json.dumps({'message': "Successfully deleted"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise DeletingItemError
        except Exception as e:
            print(e)
            raise InternalServerError

    @jwt_required
    def get(self, id):
        """[Get single comment item]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            ItemNotExistsError: [Can't find the item]
            InternalServerError: [Error in insertion]    
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            comments = Comment.objects.aggregate(
                {"$match": {"post_id": ObjectId(id)}},
                {
                    "$addFields": {
                        "liked": {
                            "$in": [user_id, "$liked_by"]
                        }
                    }
                }, {"$sort": {"full_slug": 1}})
            converted = []
            for item in list(comments):
                converted.append(item)
            data = dumps({'data': list(converted), 'message': "Successfully retrieved"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ItemNotExistsError
        except Exception as e:
            print(e)
            raise InternalServerError
