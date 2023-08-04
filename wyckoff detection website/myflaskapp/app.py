from flask import Flask, request, render_template
import requests
import time
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from tensorflow.keras.models import load_model

# load the previously trained model
model = load_model('C:/Users/Admin/Downloads/model.h5')  # replace with the path to your model file

def detect_wyckoff_patterns(pair, timeframe):
    api_key = 'BAynQVkSHDMtIdqWdllA'
    scaler = MinMaxScaler()
    start_time = pd.Timestamp.now()
    detected_patterns = []

    while True:
        # wait for the next hour
        while pd.Timestamp.now() < start_time + pd.DateOffset(hours=1):
            time.sleep(1)

        start_time += pd.DateOffset(hours=1)

        # Get the data for the past 38 hours
        end_time = start_time - pd.DateOffset(hours=1)
        start_time_req = (end_time - pd.DateOffset(hours=38)).strftime('%Y-%m-%d-%H:%M')
        end_time_req = end_time.strftime('%Y-%m-%d-%H:%M')

        data_url = f'https://marketdata.tradermade.com/api/v1/historical?api_key={api_key}&date_from={start_time_req}&date_to={end_time_req}&interval={timeframe}&format=records&currency={pair}'
        response = requests.get(data_url)
        data = response.json()['quotes']

        # Convert data to DataFrame and drop unnecessary columns
        df = pd.DataFrame(data)
        df.drop(['symbol', 'timestamp'], axis=1, inplace=True)

        # Normalize the datacd
        normalized_data = scaler.fit_transform(df)

        # Reshape the data to match the input shape of the model
        normalized_data = normalized_data.reshape(1, 37, 5)

        # Use the model to predict whether the current window represents a Wyckoff pattern
        prediction = model.predict(normalized_data)

        # If the model predicts a Wyckoff pattern, add the start and end date/time to the detected_patterns list
        if prediction > 0.5:
            detected_patterns.append((start_time_req, end_time_req))

    return detected_patterns

app = Flask(__name__)

@app.route('/', methods=['GET'])
def form():
    return render_template('form.html')

@app.route('/detect', methods=['POST'])
def detect():
    pair = request.form['pair']
    timeframe = request.form['timeframe']

    # Call the detect_wyckoff_patterns() function and get the detected patterns
    detected_patterns = detect_wyckoff_patterns(pair, timeframe)

    # Return the detected patterns as a response
    return str(detected_patterns)

if __name__ == '__main__':
    app.run(debug=True)
