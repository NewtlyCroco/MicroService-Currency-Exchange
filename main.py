from flask import Flask, render_template, request, jsonify
import requests

DEVELOPMENT_ENV = True

API_KEY = "b998728b742b15e92c1a06a6"
#BTW if for some reason you get there, this API key only has 1500 requests, though I doubt that you will need that many!


app = Flask(__name__)

app_data = {
    "name": "Will Mitchell's Currency Exchange MicroService!",
    "description": "A basic currency exchange microservice with caching support for fast and more optimised requests",
    "author": "Will Mitchell",
    "html_title": "Willy's Currency Exchange Hub",
    "project_name": "Willy's Currency Exchange Hub",
    "keywords": "flask, webapp, exchange, currency, microservice",
}


@app.route("/")
def index():
    return render_template("index.html", app_data=app_data)


@app.route("/process_currency", methods=["POST"])
def process_currency():
    data = request.get_json()  # Get the JSON data sent from the frontend
    selected_currency = data.get("currency")  # Get the selected currency
    print("Selected currency:", selected_currency)  # Print to console (or save to a variable)

    # Return a JSON response to the frontend
    return jsonify({"message": f"Received: {selected_currency}"})


@app.route("/about")
def about():
    return render_template("about.html", app_data=app_data)


@app.route("/service")
def service():
    return render_template("service.html", app_data=app_data)


@app.route("/contact")
def contact():
    return render_template("contact.html", app_data=app_data)


if __name__ == "__main__":
    app.run(debug=DEVELOPMENT_ENV)