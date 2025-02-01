from flask import Flask, render_template, request, jsonify, session
from flask_session import Session 
import redis
import requests
from datetime import datetime, timedelta
DEVELOPMENT_ENV = True


app = Flask(__name__)
app.secret_key = "asdfnoiwabnefoinbzciovnbzdsfg"


app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_REDIS"] = redis.Redis(host='localhost', port=6379, db=0)


Session(app)


class CurrencyValidator:
    def __init__(self, first, second, third):
        self.translatorC = first
        self.finalC = second
        self.amount = third
        self.api_key = "b998728b742b15e92c1a06a6"
        # BTW if for some reason you get there, this API key only has 1500 requests, though I doubt that you will need that many!
        self.currency_dict = {
            "US dollar (USD)": "USD",
            "Euro (EUR)": "EUR",
            "Japanese yen (JPY)": "JPY",
            "Pound sterling (GBP)": "GBP",
            "Australian dollar (AUD)": "AUD",
            "Canadian dollar (CAD)": "CAD",
            "Swiss franc (CHF)": "CHF"
        }

    def validate(self):
        return (self.translatorC and self.finalC and self.amount) is not None


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
    session["user_choices"] = {"translatorC": None, "finalC": None, "amount": None}  
    return render_template("index.html", app_data=app_data)


@app.route("/process_currency", methods=["POST"])
def process_currency():
    if "user_choices" in session:
        session["user_choices"]["translatorC"] = request.form.get("currency")  
        print("Selected currency:", session["user_choices"])
    return "No user choices found in session."


@app.route("/process_post_currency", methods=["POST"])
def process_post_currency():
    if "user_choices" in session:
        session["user_choices"]["finalC"] = request.form.get("currency2")  
        print("Selected currency:", session["user_choices"])
    return "No user choices found in session."


@app.route("/process_amount", methods=["POST"])
def process_amount():
    if "user_choices" in session:
        session["user_choices"]["amount"] = request.form.get("amount") 
        print("Selected currency:", session["user_choices"])
    return "No user choices found in session."



@app.route("/convert_currency", methods=["POST"])
def convert_currency():
    if "user_choices" in session:
        sessiontemp = session["user_choices"]
        calculatedValue = CurrencyValidator(sessiontemp["translatorC"], sessiontemp["finalC"], sessiontemp["amount"])

        if calculatedValue.validate():
            
            base_value = calculatedValue.currency_dict.get(calculatedValue.translatorC)
            final_value = calculatedValue.currency_dict.get(calculatedValue.finalC)

            if not base_value or not final_value:
                return "<p class='text-danger'>Invalid currency selection.</p>"

            # Create a unique key for the currency pair
            redis_key = f"{base_value}_{final_value}"

            # Check if the conversion rate is already cached in the session
            if redis_key in session:
                cached_data = session[redis_key]
                cache_time = datetime.fromisoformat(cached_data["cache_time"])

                # Check if the cache is still valid (within 5 minutes)
                if datetime.now() - cache_time < timedelta(minutes=5):
                    # Use the cached data
                    conversion_rate = cached_data["conversion_rate"]
                    last_update = cached_data["last_update"]

                    # Calculate the conversion result
                    conversion_result = float(conversion_rate) * float(calculatedValue.amount)

                    # Build the result HTML
                    result_html = f"""
                        <p>Conversion Result (Cached):</p>
                        <ul class="list-group">
                            <li class="list-group-item"><strong>From:</strong> {calculatedValue.amount} {base_value}</li>
                            <li class="list-group-item"><strong>To:</strong> {conversion_result} {final_value}</li>
                            <li class="list-group-item"><strong>Conversion Rate:</strong> 1 {base_value} = {conversion_rate} {final_value}</li>
                            <li class="list-group-item"><strong>Last Updated:</strong> {last_update}</li>
                            <li class="list-group-item"><strong>Cache Time:</strong> {cache_time}</li>
                        </ul>
                    """
                    return result_html
                else:
                    # Cache expired, delete it and make a new API request
                    del session[redis_key]

            # If not cached or cache expired, make the API request
            try:
                response = requests.get(
                    "https://v6.exchangerate-api.com/v6/{API}/pair/{FROM}/{TO}".format(
                        API=calculatedValue.api_key,
                        FROM=base_value,
                        TO=final_value,
                    )
                )
                response.raise_for_status()  
                data = response.json()

                if data.get("result") == "success":
                    conversion_rate = data.get("conversion_rate")
                    last_update = data.get("time_last_update_utc")

                    conversion_result = float(conversion_rate) * float(calculatedValue.amount)

                    session[redis_key] = {
                        "conversion_rate": conversion_rate,
                        "last_update": last_update,
                        "cache_time": datetime.now().isoformat()  # Store the current timestamp
                    }

                   
                    result_html = f"""
                        <p>Conversion Result:</p>
                        <ul class="list-group">
                            <li class="list-group-item"><strong>From:</strong> {calculatedValue.amount} {base_value}</li>
                            <li class="list-group-item"><strong>To:</strong> {conversion_result} {final_value}</li>
                            <li class="list-group-item"><strong>Conversion Rate:</strong> 1 {base_value} = {conversion_rate} {final_value}</li>
                            <li class="list-group-item"><strong>Last Updated:</strong> {last_update}</li>
                            <li class="list-group-item"><strong>Cache Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        </ul>
                    """
                    return result_html
                else:
                    return f"<p class='text-danger'>Error: {data.get('error-type')}</p>"
            except requests.exceptions.RequestException as e:
                return f"<p class='text-danger'>API request failed: {e}</p>"
        else:
            return "<p class='text-danger'>Invalid input. Please fill out all fields.</p>"
    return "<p class='text-danger'>No user choices found in session.</p>"


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