from flask import Flask, request, abort
from flask_restful import Api, Resource, reqparse, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

class VideoModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # String(100) is the max length of the string
    views = db.Column(db.Integer, nullable= False)
    likes = db.Column(db.Integer, nullable=False) 

    def __repr__(self):
        return f"Video(name = {name}, views = {views}, likes = {likes})"


video_put_args = reqparse.RequestParser()
video_put_args.add_argument("name", type=str, help="Name of the video")
video_put_args.add_argument("views", type=int, help="Views of the video")
video_put_args.add_argument("likes", type=int, help="Likes of the video")

# implement the marsehal function thing
resource_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "views": fields.Integer,
    "likes": fields.Integer
}

class Video(Resource):
    # result is initially returned as an SQLalchemy instance, define the information of the fields in the instance, and the marshal_with serializes (converts) it into json format
    # Put it above any method that you want to have the return serialized
    @marshal_with(resource_fields)
    def get(self, video_id):
        result = VideoModel.query.filter_by(id=video_id).first()
        if not result:
            abort(404, description="Could not find video with that id")
        return result
    
    @marshal_with(resource_fields)
    def put(self, video_id):
        args = video_put_args.parse_args()
        result = VideoModel.query.filter_by(id=video_id).first()
        if result:
            abort(409, description="Video id taken...")
        
        if not args["name"] or not args["views"] or not args["likes"]:
            abort(400, description="Missing arguments")
        
        # Creates a new video model like creating a new class
        video = VideoModel(id=video_id, name=args["name"], views=args["views"], likes=args["likes"])
        db.session.add(video)
        db.session.commit()
        # Add is temp add, commit is permanently add into the db
        
        result = VideoModel.query.filter_by(id=video_id).first()
        return result, 201
    
    # There should be more args passed into this one
    @marshal_with(resource_fields)
    def patch(self, video_id):
        args = video_put_args.parse_args()
        result = VideoModel.query.filter_by(id=video_id).first()

        # make sure it exists
        if not result:
            abort(404, description="Video doesn't exist, cannot update")
        
        # user can update only the fields they want to update
        # the args object might have fields that have None values, so need to check if they are none or not

        if args["name"]:
            result.name = args["name"]
        if args["views"]:
            result.views = args["views"]
        if args["likes"]:
            result.likes = args["likes"]
        
        db.session.commit()

        return result, 200
    
    def delete(self, video_id):
        result = VideoModel.query.filter_by(id=video_id).first()
        if not result:
            abort(404, description="Video doesn't exist, cannot delete")
        db.session.delete(result)
        db.session.commit()

        return "", 204


api.add_resource(Video, "/video/<int:video_id>")

if __name__ == "__main__":
    app.run()