import pandas as pd
from prophet import Prophet
import logging
import os
import plotly.graph_objects as go
import yfinance as yf
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta

# Initialize the Dash app
app = Dash(__name__)

# Layout of the app
app.layout = html.Div([
    dcc.Input(id='ticker-input', type='text', value='AAPL'),
    html.Button(id='submit-button', n_clicks=0, children='Submit'),
    dcc.Graph(id='price-graph'),
    html.Div(id='current-price'),
    html.Div(id='suggested-prices')
])

def check_internet_connection():
    try:
        # Check internet connection
        return True
    except OSError:
        logging.info("Internet connection: FAILED")
        return False

# Callback to update the graph
@app.callback(
    [Output('price-graph', 'figure'),
     Output('current-price', 'children'),
     Output('suggested-prices', 'children')],
    [Input('submit-button', 'n_clicks')],
    [State('ticker-input', 'value')]
)
def update_graph(n_clicks, ticker):
    try:
        # Calculate the date range for the last 60 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=60)

        # Download the data for the last 60 days (daily intervals)
        logging.info(f"Fetching data for {ticker}...")
        data = yf.download(ticker, start=start_date, end=end_date, interval='1d')

        # Debugging information
        logging.info(f"Data columns for {ticker}: {data.columns}")
        logging.info(f"First few rows of data for {ticker}:")
        logging.info(data.head())
        logging.info(f"Full data for {ticker}:")
        logging.info(data)

        if data.empty:
            logging.info("No data retrieved.")
            return go.Figure(), "No valid data available for the selected ticker.", ""

        # Reset index and rename columns to ensure single-level index
        data = data.reset_index()
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]

        if 'Close' not in data.columns:
            return go.Figure(), "No valid data available for the selected ticker.", ""

        # Calculate EMAs
        data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
        data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
        data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()

        # Identify buy/sell signals
        buy_signals = []
        sell_signals = []
        for i in range(1, len(data)):
            if data['EMA_5'].iloc[i] > data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] <= data['EMA_13'].iloc[i-1]:
                buy_signals.append((data['Date'].iloc[i], data['Close'].iloc[i]))
            elif data['EMA_5'].iloc[i] < data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] >= data['EMA_13'].iloc[i-1]:
                sell_signals.append((data['Date'].iloc[i], data['Close'].iloc[i]))

        # Create the figure
        fig = go.Figure()

        # Add price line
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], mode='lines', name='Close'))

        # Add EMAs
        fig.add_trace(go.Scatter(x=data['Date'], y=data['EMA_5'], mode='lines', name='EMA 5'))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['EMA_13'], mode='lines', name='EMA 13'))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['EMA_8'], mode='lines', name='EMA 8'))

        # Add buy signals
        for signal in buy_signals:
            fig.add_trace(go.Scatter(
                x=[signal[0]], y=[signal[1]], mode='markers+text', name='Buy Signal',
                marker=dict(symbol='triangle-up', size=15, color='green'),
                text=[f'Buy: {signal[1]:.2f}'], textposition='top center'
            ))

        # Add sell signals
        for signal in sell_signals:
            fig.add_trace(go.Scatter(
                x=[signal[0]], y=[signal[1]], mode='markers+text', name='Sell Signal',
                marker=dict(symbol='triangle-down', size=15, color='red'),
                text=[f'Sell: {signal[1]:.2f}'], textposition='bottom center'
            ))

        # Update layout
        fig.update_layout(
            title=f"{ticker.upper()} Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white"
        )

        # Current price
        current_price = data['Close'].iloc[-1]

        # Ensure current_price is a single float value
        if isinstance(current_price, pd.Series):
            current_price = current_price.iloc[-1]

        # Predict future prices
        forecast = predict_future_prices(data)

        # Get suggested buy/sell prices
        suggested_buy_price, suggested_sell_price = get_suggested_prices(forecast)

        # Suggested prices message
        suggested_prices_message = (
            f"If price hits {suggested_buy_price:.2f}, you might want to consider buying. "
            f"If price hits {suggested_sell_price:.2f}, you might want to consider selling."
        )

        return fig, f"Current Price: {current_price:.2f}", suggested_prices_message

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return go.Figure(), f"Error: {str(e)}", ""

def predict_future_prices(data, periods=30):
    # Prepare data for Prophet
    df = data[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
    
    # Initialize and fit the model
    model = Prophet()
    model.fit(df)
    
    # Make future predictions
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

def get_suggested_prices(forecast):
    # Get the last predicted price
    last_prediction = forecast.iloc[-1]
    suggested_buy_price = last_prediction['yhat_lower']
    suggested_sell_price = last_prediction['yhat_upper']
    
    return suggested_buy_price, suggested_sell_price

# Run the app
if __name__ == '__main__':
    logging.info("Starting Dash app...")
    port = int(os.environ.get("PORT", 8080))
    app.run_server(debug=False, host='0.0.0.0', port=port)