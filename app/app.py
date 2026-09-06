from fastapi import FastAPI, HTTPException
from app.schemas import ApiResponse, PostCreate, PostResponse



app = FastAPI()

text_posts = {
    1: {
        "title": "Getting Started with FastAPI",
        "content": "FastAPI makes it easy to build modern Python APIs with automatic documentation.",
    },
    2: {
        "title": "Why Type Hints Matter",
        "content": "Type hints make Python code easier to understand, validate, and maintain.",
    },
    3: {
        "title": "Learning by Building",
        "content": "Small projects are a practical way to turn programming concepts into useful skills.",
    },
    4: {
        "title": "Clean Code, Clear Ideas",
        "content": "Readable names and focused functions help teams understand code quickly.",
    },
    5: {
        "title": "The Value of Documentation",
        "content": "Good documentation helps users discover what an API can do and how to use it.",
    },
    6: {
        "title": "Debugging with Patience",
        "content": "A clear error message and a small reproducible example can make debugging much easier.",
    },
    7: {
        "title": "Version Control Basics",
        "content": "Git helps developers track changes, experiment safely, and collaborate on projects.",
    },
    8: {
        "title": "Testing Small Pieces",
        "content": "Testing individual behaviors gives you confidence before combining larger features.",
    },
    9: {
        "title": "Building Consistent APIs",
        "content": "Consistent routes and response formats make APIs more predictable for clients.",
    },
    10: {
        "title": "Keep Improving",
        "content": "Regular practice and small improvements are the foundation of lasting progress.",
    },
}

@app.get("/posts", response_model=ApiResponse, status_code=200)
def get_all_posts(limit: int = None):
    if limit:
        posts = list(text_posts.values())[:limit]
    else:
        posts = text_posts

    return {
        "status_code": 200,
        "message": "Posts retrieved successfully",
        "data": posts,
    }

@app.get("/posts/{post_id}", response_model=ApiResponse, status_code=200)
def get_post_by_id(post_id: int):
    if post_id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "status_code": 200,
        "message": "Post retrieved successfully",
        "data": text_posts[post_id],
    }


@app.post("/posts", response_model=ApiResponse, status_code=201)
def create_post(post: PostCreate):
    new_post = {"title": post.title, "content": post.content}
    text_posts[max(text_posts.keys()) + 1] = new_post

    return {
        "status_code": 201,
        "message": "Post created successfully",
        "data": new_post,
    }

@app.delete("/posts/{post_id}", response_model=ApiResponse, status_code=200)
def delete_post(post_id: int):
    if post_id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")

    del text_posts[post_id]
    return {
        "status_code": 200,
        "message": "Post deleted successfully",
        "data": None,
    }


@app.put("/posts/{post_id}", response_model=ApiResponse, status_code=200)
def update_post(post_id: int, post: PostCreate):
    if post_id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")

    updated_post = {"title": post.title, "content": post.content}
    text_posts[post_id] = updated_post
    return {
        "status_code": 200,
        "message": "Post updated successfully",
        "data": updated_post,
    }

@app.patch("/posts/{post_id}", response_model=ApiResponse, status_code=200)
def partial_update_post(post_id: int, post: PostCreate):
    if post_id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_post = text_posts[post_id]
    updated_post = {
        "title": post.title if post.title else existing_post["title"],
        "content": post.content if post.content else existing_post["content"]
    }
    text_posts[post_id] = updated_post
    return {
        "status_code": 200,
        "message": "Post partially updated successfully",
        "data": updated_post,
    }
