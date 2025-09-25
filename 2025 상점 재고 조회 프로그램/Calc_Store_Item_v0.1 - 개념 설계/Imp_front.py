from flask import render_template
def register_routes_front(app):
    @app.get("/")
    def index():
        return render_template("index.html")
