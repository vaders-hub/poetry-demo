import uvicorn

# pre-commit

def start():
    uvicorn.run("src.router:app", host="0.0.0.0", port=8001, reload=True)

if __name__ == "__main__":
    start()