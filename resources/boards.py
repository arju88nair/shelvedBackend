import json

from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError

from database.model import Board, User
from resources.errors import SchemaValidationError, UpdatingItemError, ItemAlreadyExistsError, InternalServerError, \
    DeletingItemError, ItemNotExistsError
import timeago, datetime


class BoardsApi(Resource):
    """[Batch Board actions]
    """

    @jwt_required()
    def get(self):
        """[Retrieves all Boards]
        
        Raises:
            InternalServerError: [If Eror in retrieval]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:

            pipeline = [
                {"$sort": {"name": -1}},
            ]
            boards = Board.objects().aggregate(pipeline)
            print(len(boards))
            data = {'data': json.loads(boards), 'message': "Successfully retrieved", "count": len(json.loads(boards))}
            data = json.dumps(data)
            response = Response(data, mimetype="application/json", status=200)
            return response
        except Exception as e:
            print(e)
            raise InternalServerError

    @jwt_required()
    def post(self):
        """[Batch Board API]
        
        Raises:
            SchemaValidationError: [If there are validation error in the board data]
            ItemAlreadyExistsError: [If the board already exist]
            InternalServerError: [Error in insertion]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        now = datetime.datetime.now() + datetime.timedelta(seconds=60 * 3.4)
        print(now)
        date = datetime.datetime.now()
        print(date)
        data = timeago.format(date, now)
        return Response(data, mimetype="application/json", status=200)

        body = request.get_json()

        # validations
        if 'title' not in body:
            raise SchemaValidationError

        try:
            user_id = get_jwt_identity()
            user = User.objects.get(id=user_id)
            board = Board(**body, added_by=user)
            board.save()
            board_id = board.id
            data = json.dumps({'id': str(id), 'message': "Successfully inserted", 'board': json.loads(board.to_json())})
            return Response(data, mimetype="application/json", status=200)
        except (FieldDoesNotExist, ValidationError) as e:
            print(e)
            raise SchemaValidationError
        except NotUniqueError as e:
            print(e)
            raise ItemAlreadyExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


class BoardApi(Resource):
    """[Individual Board actions]
    """

    @jwt_required()
    def put(self, id):
        """[Updating single]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            SchemaValidationError: [If there are validation error in the board data]
            UpdatingItemError: [Error in update]
            InternalServerError: [Error in insertion]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            board = Board.objects.get(id=id, added_by=user_id)
            body = request.get_json()
            Board.objects.get(id=id).update(**body)
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
        """[Deleting single board]
        
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
            board = Board.objects.get(id=id, added_by=user_id)
            board.delete()
            data = json.dumps({'message': "Successfully deleted"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise DeletingItemError
        except Exception as e:
            print(e)
            raise InternalServerError

    @jwt_required()
    def get(self, id):
        """[Get single board item]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            ItemNotExistsError: [Can't find the post item]
            InternalServerError: [Error in insertion]    
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            boards = Board.objects.get(id=id).to_json()
            data = json.dumps(
                {'data': json.loads(boards), 'message': "Successfully retrieved", "count": len(json.loads(boards))})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ItemNotExistsError
        except Exception:
            raise InternalServerError
