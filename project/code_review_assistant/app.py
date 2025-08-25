from fastapi import FastAPI

# TODO: Create a FastAPI application with title "Code Review Assistant" and version "1.0.0"
app = FastAPI(title="Code Review Assistant", version="1.0.0")
# TODO: Define a GET endpoint for the root path ("/") that returns a dictionary
# with a welcome message


@app.get("/")
def read_root():
    return {"message": "Welcome to the Code Review Assistant!"}
