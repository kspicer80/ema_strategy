import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import socket
import os

# Initialize the Dash app
app = Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1("Stock Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals"),
    dcc.Input(id='ticker-input', type='text', value='SOL-USD', style={'marginRight': '10px'}),
    html.Button(id='submit-button', n_clicks=0, children='Submit'),
    dcc.Graph(id='price-graph'),
    html.Div(id='current-price', style={'marginTop': '20px'}),
])

# Test internet connection
def test_internet():
    try:
        socket.create_connection(("www.google.com", 80), timeout=5)
        print("Internet connection: OK")
        return True
    except OSError:
        print("Internet connection: FAILED")
        return False

# Callback to update the graph
@app.callback(
    [Output('price-graph', 'figure'),
     Output('current-price', 'children')],
    [Input('submit-button', 'n_clicks')],
    [State('ticker-input', 'value')]
)
def update_graph(n_clicks, ticker):
    print(f"Ticker: {ticker}")
    
    if not test_internet():
        return go.Figure(), "No internet connection. Cannot fetch data."
    
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=60)
        print(f"Fetching data for {ticker} from {start_date} to {end_date}")

        # Use timeout to prevent hanging
        data = yf.download(ticker, start=start_date, end=end_date, interval='1d', timeout=10)

        if data.empty:
            print("No data returned for the ticker.")
            return go.Figure(), "No data available for the given ticker."

        # Calculate EMAs
        data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
        data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
        data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()

        # Generate buy/sell signals
        buy_signals = []
        sell_signals = []

        for i in range(1, len(data)):
            if data['EMA_5'].iloc[i] > data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] <= data['EMA_13'].iloc[i-1]:
                buy_signals.append((data.index[i], data['Close'].iloc[i]))
            elif data['EMA_5'].iloc[i] < data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] >= data['EMA_13'].iloc[i-1]:
                sell_signals.append((data.index[i], data['Close'].iloc[i]))

        # Plot the graph
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='EMA 5'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='EMA 13'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='EMA 8'))

        for signal in buy_signals:
            fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers', name='Buy Signal',
                                     marker=dict(symbol='triangle-up', size=10, color='green')))

        for signal in sell_signals:
            fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers', name='Sell Signal',
                                     marker=dict(symbol='triangle-down', size=10, color='red')))

        fig.update_layout(
            title=f"{ticker} Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals",
            xaxis_title="Date",
            yaxis_title="Price",
        )

        current_price = data['Close'].iloc[-1]
        return fig, f"Current Price: {current_price:.2f}"

    except Exception as e:
        print(f"Error: {e}")
        return go.Figure(), "Error occurred while processing data."

# Run the app
if __name__ == '__main__':
    print("Starting Dash app...")
    port = int(os.environ.get("PORT", 8080))  # Dynamic port for Render
    app.run_server(debug=False, host='0.0.0.0', port=port)
