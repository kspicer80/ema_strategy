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

    # Debugging information
    print(f'Data for {ticker}:')
    print(data)

    # Check for missing values
    print(f'Missing values in data: {data.isnull().sum()}')

    # Handle missing values by dropping them
    data = data.dropna()

    # Calculate EMAs
    data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
    data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
    data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()

    # Debugging information for EMAs
    print(f'EMA_5: {data["EMA_5"].tail()}')
    print(f'EMA_13: {data["EMA_13"].tail()}')
    print(f'EMA_8: {data["EMA_8"].tail()}')

    # Generate buy/sell signals
    buy_signals = []
    sell_signals = []

    for i in range(1, len(data)):
        if data['EMA_5'].iloc[i] > data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] <= data['EMA_13'].iloc[i-1]:
            buy_signals.append((data.index[i], data['Close'].iloc[i]))
        elif data['EMA_5'].iloc[i] < data['EMA_13'].iloc[i] and data['EMA_5'].iloc[i-1] >= data['EMA_13'].iloc[i-1]:
            sell_signals.append((data.index[i], data['Close'].iloc[i]))

    # Debugging information for buy/sell signals
    print(f'Buy signals: {buy_signals}')
    print(f'Sell signals: {sell_signals}')

    # Create the figure
    fig = go.Figure()

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

    # Update the layout
    fig.update_layout(
        title=f'{ticker} Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals',
        xaxis_title='Date',
        yaxis_title='Price'
    )

    # Get the current price (last value in the 'Close' column)
    current_price = data['Close'].iloc[-1]

    # Debugging information
    print(f'current_price type: {type(current_price)}')
    print(f'current_price value: {current_price}')

    # Ensure current_price is a single float value
    if isinstance(current_price, pd.Series):
        current_price = current_price.iloc[-1]

    return fig, f'Current Price: {current_price:.2f}'

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)
