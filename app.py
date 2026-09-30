"""Simple CMS: a small server-rendered blog backed by MongoDB."""

import os
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "simple-cms-dev-key")

mongo_client = MongoClient(
    os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017"),
    serverSelectionTimeoutMS=3000,
)
posts_collection = mongo_client[os.environ.get("MONGODB_DATABASE", "cms_lab")]["posts"]


@app.errorhandler(ServerSelectionTimeoutError)
def mongo_unavailable(_error):
    return render_template("mongo-unavailable.html"), 503


@app.get("/")
@app.get("/posts")
def list_posts():
    posts = list(
        posts_collection.find(
            {}, {"title": 1, "author": 1, "createdAt": 1}
        ).sort("createdAt", -1)
    )
    return render_template("posts.html", posts=posts)


@app.get("/posts/new")
def new_post():
    return render_template("new-post.html")


@app.post("/posts")
def create_post():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    author = request.form.get("author", "").strip()
    if not title or not content or not author:
        flash("Please fill in the title, content, and author.", "error")
        return render_template(
            "new-post.html", values={"title": title, "content": content, "author": author}
        ), 400

    posts_collection.insert_one(
        {"title": title, "content": content, "author": author, "createdAt": datetime.now()}
    )
    flash("Your post has been published.", "success")
    return redirect(url_for("list_posts"))


@app.get("/posts/<post_id>")
def show_post(post_id):
    try:
        object_id = ObjectId(post_id)
    except (InvalidId, TypeError):
        abort(404)
    post = posts_collection.find_one({"_id": object_id})
    if post is None:
        abort(404)
    return render_template("post.html", post=post)


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
