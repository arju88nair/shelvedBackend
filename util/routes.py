from resources.post import PostsApi, PostApi
from resources.comments import CommentsApi, CommentApi
from resources.like import LikeApi, UnLikeApi
from resources.boards import BoardsApi, BoardApi
from resources.user import SignupApi, LoginApi, TokenApi, LogoutApi, LogoutRefreshAPI
from resources.main import ByBoardApi


def initialize_routes(api):
    api.add_resource(SignupApi, '/api/auth/signup')
    api.add_resource(LoginApi, '/api/auth/login')
    api.add_resource(TokenApi, '/api/auth/refresh')
    api.add_resource(LogoutApi, '/api/auth/logout')
    api.add_resource(LogoutRefreshAPI, '/api/auth/revoke')

    api.add_resource(PostsApi, '/api/posts')
    api.add_resource(PostApi, '/api/post/<id>')

    api.add_resource(BoardsApi, '/api/boards')
    api.add_resource(BoardApi, '/api/board/<id>')

    api.add_resource(CommentsApi, '/api/comments')
    api.add_resource(CommentApi, '/api/comment/<id>')

    api.add_resource(LikeApi, '/api/like')
    api.add_resource(UnLikeApi, '/api/unlike')

    api.add_resource(ByBoardApi, '/api/by-board/<id>')
