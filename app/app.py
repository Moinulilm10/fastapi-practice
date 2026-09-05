from fastapi import FastAPI, HTTPException



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

@app.get("/posts")
def get_all_posts(limit: int):
    if limit:
        return list(text_posts.values())[:limit]

    return text_posts

@app.get("/posts/{post_id}")
def get_post_by_id(id: int):
    if id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")

    return text_posts.get(id)


