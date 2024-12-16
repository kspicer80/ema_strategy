import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dash import Dash, html, dcc, Input, Output
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
    [Output('stock-graph', 'figure'),
     Output('current-price', 'children')],
    [Input('ticker-dropdown', 'value'),
     Input('submit-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')]  # Triggered on Interval
)

def update_graph(n_clicks, ticker):
    try:
        # Debugging: Log the ticker input
        print(f"Fetching data for ticker: {ticker}")

        # Validate ticker input
        if not ticker:
            raise ValueError("No ticker symbol provided.")

        # Calculate the date range for the last 60 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=60)

        # Download the data from Yahoo Finance
        data = yf.download(ticker, start=start_date, end=end_date, interval='1d')

        # Debugging: Check if data was fetched
        if data.empty:
            raise ValueError(f"No data found for ticker: {ticker}. Check the ticker symbol.")

        print("Fetched data:")
        print(data.tail())

        # Calculate EMAs
        data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
        data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
        data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()

        # Debugging: Confirm EMAs were calculated
        print("Calculated EMAs:")
        print(data[['Close', 'EMA_5', 'EMA_13', 'EMA_8']].tail())

        # Generate buy/sell signals
        buy_signals = []
        sell_signals = []

        for i in range(1, len(data)):
            if data['EMA_5'].iloc[i] > data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] <= data['EMA_13'].iloc[i-1]:
                buy_signals.append((data.index[i], data['Close'].iloc[i]))
            elif data['EMA_5'].iloc[i] < data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] >= data['EMA_13'].iloc[i-1]:
                sell_signals.append((data.index[i], data['Close'].iloc[i]))

        print("Buy Signals:", buy_signals)
        print("Sell Signals:", sell_signals)

        # Create the figure
        fig = go.Figure()

        # Plot Close prices and EMAs
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='EMA 5'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='EMA 13'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='EMA 8'))

        # Add Buy Signals
        for signal in buy_signals:
            fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers', name='Buy Signal',
                                     marker=dict(symbol='triangle-up', size=10, color='green')))

        # Add Sell Signals
        for signal in sell_signals:
            fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers', name='Sell Signal',
                                     marker=dict(symbol='triangle-down', size=10, color='red')))

        # Update layout
        fig.update_layout(
            title=f"{ticker} Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals",
            xaxis_title='Date',
            yaxis_title='Price'
        )

        # Get the latest price
        current_price = data['Close'].iloc[-1]

        return fig, f"Current Price: {current_price:.2f}"

    except Exception as e:
        # Log the error for debugging
        print(f"Error: {e}")

        # Return an empty figure and an error message
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error occurred while processing data")
        return empty_fig, f"Error: {str(e)}"


# Run the app
if __name__ == '__main__':
    print("Starting Dash app...")
    port = int(os.environ.get("PORT", 8080))
    app.run_server(debug=False, host='0.0.0.0', port=port)

