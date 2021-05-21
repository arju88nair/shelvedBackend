from flask import Response, request
from database.model import Category, User
from flask_restful import Resource
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError
from resources.errors import SchemaValidationError, UpdatingItemError, ItemAlreadyExistsError, InternalServerError, \
    DeletingItemError, ItemNotExistsError
from newspaper import Article
import json
from flask_jwt_extended import jwt_required, get_jwt_identity


class CategoriesApi(Resource):
    """[Batch Category actions]
    """

    @jwt_required
    def get(self):
        """[Retrieves all Categories]
        
        Raises:
            InternalServerError: [If Eror in retrieval]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            posts = Category.objects().to_json()
            data = {'data': json.loads(posts), 'message': "Successfully retrieved", "count": len(json.loads(posts))}
            data = json.dumps(data)
            response = Response(data, mimetype="application/json", status=200)
            return response
        except Exception as e:
            raise InternalServerError

    @jwt_required
    def post(self):
        """[Batch Category API]
        
        Raises:
            SchemaValidationError: [If there are validation error in the category data]
            ItemAlreadyExistsError: [If the category already exist]
            InternalServerError: [Error in insertion]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        body = request.get_json()

        # validations
        if 'title' not in body:
            raise SchemaValidationError

        try:
            user_id = get_jwt_identity()
            user = User.objects.get(id=user_id)
            category = Category(**body, added_by=user)
            category.save()
            id = category.id
            data = json.dumps({'id': str(id), 'message': "Successfully inserted", 'category': json.loads(category.to_json())})
            return Response(data, mimetype="application/json", status=200)
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationError
        except NotUniqueError:
            raise ItemAlreadyExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


class CategoryApi(Resource):
    """[Individual Category actions]
    """

    @jwt_required
    def put(self, id):
        """[Updating single]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            SchemaValidationError: [If there are validation error in the category data]
            UpdatingItemError: [Error in update]
            InternalServerError: [Error in insertion]
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            category = Category.objects.get(id=id, added_by=user_id)
            body = request.get_json()
            Category.objects.get(id=id).update(**body)
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
        """[Deleting single category]
        
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
            category = Category.objects.get(id=id, added_by=user_id)
            category.delete()
            data = json.dumps({'message': "Successfully deleted"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise DeletingItemError
        except Exception as e:
            print(e)
            raise InternalServerError

    @jwt_required
    def get(self, id):
        """[Get single category item]
        
        Arguments:
            id {[Object ID]} -- [Mongo Object ID]
        
        Raises:
            ItemNotExistsError: [Can't find the post item]
            InternalServerError: [Error in insertion]    
        
        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            posts = Category.objects.get(id=id).to_json()
            data = json.dumps(
                {'data': json.loads(posts), 'message': "Successfully retrieved", "count": len(json.loads(posts))})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ItemNotExistsError
        except Exception:
            raise InternalServerError
