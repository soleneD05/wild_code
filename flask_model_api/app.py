import json
import joblib
import numpy as np
from flask import Flask, jsonify, request

app = Flask(__name__)
model = joblib.load('model.pkl')


@app.route('/')
def home():
    return "welcome"


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)

    try:
        # Extract features from each item in the list
        feature_list = [item["features"] for item in data]

        # Predict for all
        predictions = model.predict(feature_list)

        # Return the prediction for each item
        response = [
            {"input": item["features"], "prediction": pred}
            for item, pred in zip(data, predictions)
        ]
        
        return jsonify({"prediction": float(np.expm1(predictions[0]))})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)