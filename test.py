@app.get("/")
def home():
    return {"message": "Adhyan backend is running"}