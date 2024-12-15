import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State

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
    # Calculate the date range for the last 60 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=60)

    # Download the data for the last 60 days (daily intervals)
    data = yf.download(ticker, start=start_date, end=end_date, interval='1d')

    # Calculate the EMAs
    data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
    data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
    data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()

    # Identify buy and sell signals with a confirmation period
    buy_signals = []
    sell_signals = []
    confirmation_period = 3  # Number of days to confirm the signal

    for i in range(confirmation_period, len(data)):
        # Buy signal: 5-day EMA crosses above 13-day EMA and stays above for the confirmation period
        if all(data['EMA_5'].iloc[i-j] > data['EMA_13'].iloc[i-j] for j in range(confirmation_period)) and \
           data['EMA_5'].iloc[i-confirmation_period] <= data['EMA_13'].iloc[i-confirmation_period]:
            buy_signals.append((data.index[i], data['Close'].iloc[i]))
        # Sell signal: 5-day EMA crosses below 13-day EMA and stays below for the confirmation period
        elif all(data['EMA_5'].iloc[i-j] < data['EMA_13'].iloc[i-j] for j in range(confirmation_period)) and \
             data['EMA_5'].iloc[i-confirmation_period] >= data['EMA_13'].iloc[i-confirmation_period]:
            sell_signals.append((data.index[i], data['Close'].iloc[i]))

    # Get the current price
    current_price = data['Close'].iloc[-1]

    # Create the Plotly figure
    fig = go.Figure()

    # Add the actual prices
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Actual Price', line=dict(color='red')))

    # Add the 5-day EMA
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='5-day EMA', line=dict(color='blue')))

    # Add the 13-day EMA
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='13-day EMA', line=dict(color='orange')))

    # Add the 8-day EMA
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='8-day EMA', line=dict(color='green')))

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

    # Update the layout
    fig.update_layout(title=f'{ticker} Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals',
                      xaxis_title='Date',
                      yaxis_title='Price')

    return fig, f'Current Price: {current_price:.2f}'

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)