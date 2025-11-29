from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="FastAPI Asimov",
    description="This is example 1 from class 3.",
    version="0.1.0",
    contact={
        "name": "Caio",
        "email": "caio.zendron@gmail.com"
    }
)


@app.get("/")
def read_root():
    return {"message": "Hello world!"}

@app.get("/hello/{name}")
def read_hello_name(name: str):
    return {"message": f"Hello {name}!"}

if __name__ == "__main__":
    uvicorn.run("example_1:app", host="0.0.0.0", port=8000, reload=True)

