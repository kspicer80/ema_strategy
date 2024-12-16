import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dash import Dash, html, dcc, Input, Output, State, PreventUpdate
import time
import os

# Create a Dash app
app = Dash(__name__)

# Layout with Interval Component for periodic updates
app.layout = html.Div([
    html.H1("Stock Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals", style={'font-weight': 'bold'}),

    html.Div([
        dcc.Dropdown(
            id='ticker-dropdown',
            options=[{'label': 'SOL-USD', 'value': 'SOL-USD'},
                     {'label': 'BTC-USD', 'value': 'BTC-USD'}],
            value='SOL-USD',
            style={'width': '200px', 'display': 'inline-block'}
        ),
        html.Button("Submit", id="submit-button", n_clicks=0, style={'margin-left': '10px'}),
    ], style={'margin-bottom': '20px'}),

    dcc.Loading(
        id="loading-graph",
        type="circle",
        children=[dcc.Graph(id='stock-graph')]
    ),
    
    html.Div(id='current-price', style={'margin-top': '20px', 'font-weight': 'bold'}),

    # Interval Component: Updates every hour
    #dcc.Interval(
        #id='interval-component',
        #interval=60*60*1000,  # 60 minutes in milliseconds
        #3n_intervals=0  # Starts from 0
    #)
])

@app.callback(
    [Output('graph', 'figure'), Output('current-price', 'children')],
    Input('submit-button', 'n_clicks'),  # Input
    State('ticker-dropdown', 'value')    # State
)

def update_graph(n_clicks, ticker):
    if n_clicks is None:  # Prevent triggering when the page initially loads
        raise PreventUpdate

    try:
        print(f"Button clicked {n_clicks} times. Fetching data for {ticker}...")

        # Ensure ticker is valid
        if not ticker:
            return go.Figure(), "Error: Please select a ticker."

        # Fetch data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=60)
        data = yf.download(ticker, start=start_date, end=end_date, interval='1d')

        if data.empty:
            return go.Figure(), f"Error: No data found for {ticker}."

        # Calculate EMAs
        data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
        data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
        data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()

        # Create figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='EMA 5'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='EMA 13'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='EMA 8'))

        fig.update_layout(
            title=f"{ticker} Prices with 5, 13, and 8-day EMAs",
            xaxis_title='Date',
            yaxis_title='Price'
        )

        current_price = data['Close'].iloc[-1]
        return fig, f"Current Price: {current_price:.2f}"

    except Exception as e:
        print(f"Error occurred: {e}")
        return go.Figure(), f"Error: {str(e)}"

# Run the app
if __name__ == '__main__':
    print("Starting Dash app...")
    port = int(os.environ.get("PORT", 8080))
    app.run_server(debug=False, host='0.0.0.0', port=port)

