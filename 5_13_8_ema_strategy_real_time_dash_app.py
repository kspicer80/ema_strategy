import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import os
import plotly.io as pio

# Set default renderer (force rendering for debugging)
pio.renderers.default = 'json'

# Initialize the Dash app
app = Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1("Stock Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals"),
    dcc.Input(id='ticker-input', type='text', value='SOL-USD', style={'marginRight': '10px'}),
    html.Button(id='submit-button', n_clicks=0, children='Submit'),
    dcc.Graph(id='price-graph'),
    html.Div(id='current-price', style={'marginTop': '20px'}),
    dcc.Interval(
        id='interval-component',
        interval=30000,  # Update every thirty seconds
        n_intervals=0
    )
])

# Callback to update the graph and current price
@app.callback(
    [Output('price-graph', 'figure'),
     Output('current-price', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('submit-button', 'n_clicks')],
    [State('ticker-input', 'value')]
)
def update_graph(n, n_clicks, ticker):
    # Debugging: Print ticker and server environment
    print(f"Ticker received: {ticker}")
    print(f"Server Time (UTC): {datetime.utcnow()}")
    print(f"Local Time: {datetime.now()}")
    print(f"Working Directory: {os.getcwd()}")

    # Calculate the date range for the last 60 days
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=60)
        print(f"Start Date: {start_date}, End Date: {end_date}")
    except Exception as e:
        print(f"Error calculating date range: {e}")
        return go.Figure(), "Error in date range calculation"

    # Download data
    try:
        print("Fetching data...")
        data = yf.download(ticker, start=start_date, end=end_date, interval='1d')
        print("Data fetched successfully.")
        print(data.tail())
    except Exception as e:
        print(f"Error fetching data: {e}")
        return go.Figure(), "Error fetching data"

    # Check if data is empty
    if data.empty:
        print("No data returned. Check the ticker or date range.")
        return go.Figure(), "No data available"

    # Check for null values
    print("Checking for missing values...")
    print(data.isnull().sum())
    if data['Close'].isnull().any():
        print("Null values detected in 'Close' column.")
        return go.Figure(), "Missing values in data."

    # Calculate EMAs
    try:
        data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
        data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
        data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()
        print("EMAs calculated successfully.")
    except Exception as e:
        print(f"Error calculating EMAs: {e}")
        return go.Figure(), "Error calculating EMAs"

    # Generate buy/sell signals
    buy_signals = []
    sell_signals = []

    try:
        for i in range(1, len(data)):
            if data['EMA_5'].iloc[i] > data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] <= data['EMA_13'].iloc[i-1]:
                buy_signals.append((data.index[i], data['Close'].iloc[i]))
            elif data['EMA_5'].iloc[i] < data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] >= data['EMA_13'].iloc[i-1]:
                sell_signals.append((data.index[i], data['Close'].iloc[i]))
        print(f"Buy signals: {buy_signals}")
        print(f"Sell signals: {sell_signals}")
    except Exception as e:
        print(f"Error generating buy/sell signals: {e}")
        return go.Figure(), "Error generating signals"

    # Create the figure
    fig = go.Figure()

    try:
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='EMA 5'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='EMA 13'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='EMA 8'))

        # Add buy signals
        for signal in buy_signals:
            fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers+text', name='Buy Signal',
                                     marker=dict(symbol='triangle-up', size=10, color='green'),
                                     text=['Buy'], textposition='top center'))

        # Add sell signals
        for signal in sell_signals:
            fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers+text', name='Sell Signal',
                                     marker=dict(symbol='triangle-down', size=10, color='red'),
                                     text=['Sell'], textposition='bottom center'))

        fig.update_layout(
            title=f'{ticker} Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals',
            xaxis_title='Date',
            yaxis_title='Price'
        )
        print("Figure created successfully.")
    except Exception as e:
        print(f"Error creating figure: {e}")
        return go.Figure(), "Error creating graph"

    # Get the current price
    try:
        current_price = data['Close'].iloc[-1]
        if pd.isnull(current_price):
            print("Current price is null.")
            current_price = "N/A"
        print(f"Current Price: {current_price}")
    except Exception as e:
        print(f"Error fetching current price: {e}")
        current_price = "Error fetching price"

    return fig, f'Current Price: {current_price:.2f}' if isinstance(current_price, (float, int)) else current_price

# Run the app
if __name__ == '__main__':
    print("Starting Dash App...")
    app.run_server(debug=True, host='0.0.0.0', port=8080)
