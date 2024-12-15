import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dash import Dash, html, dcc, Input, Output
import time

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

    # Interval Component: Updates every 2 minutes (120,000 milliseconds)
    dcc.Interval(
        id='interval-component',
        interval=2*60*1000,  # 2 minutes in milliseconds
        n_intervals=0  # Starts from 0
    )
])

@app.callback(
    [Output('stock-graph', 'figure'),
     Output('current-price', 'children')],
    [Input('ticker-dropdown', 'value'),
     Input('submit-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')]  # Triggered on Interval
)
def update_graph(ticker, n_clicks, n_intervals):
    # Fetch current date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=60)

    try:
        print(f"Fetching data for {ticker}...")

        # Fetch data from Yahoo Finance
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            return go.Figure(), "Error: No data available"

        # Calculate EMAs
        data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
        data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
        data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()

        # Drop missing values
        data = data.dropna()

        # Create figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='EMA 5', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='EMA 13', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='EMA 8', line=dict(color='purple')))

        # Update layout
        fig.update_layout(
            title=f"{ticker} Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals",
            xaxis_title="Date",
            yaxis_title="Price",
            plot_bgcolor="rgba(240,240,240,0.95)",
            paper_bgcolor="white",
        )

        # Get latest price
        current_price = float(data['Close'].iloc[-1])
        return fig, f"Current Price: {current_price:.2f}"

    except Exception as e:
        print(f"Error occurred: {e}")
        return go.Figure(), "Error occurred while fetching data."

if __name__ == '__main__':
    app.run_server(debug=True)
