import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dash import Dash, html, dcc, Input, Output

# Create a dummy Dash app for testing
app = Dash(__name__)

# Layout of the app
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
    
    dcc.Graph(id='stock-graph'),
    html.Div(id='current-price', style={'margin-top': '20px', 'font-weight': 'bold'})
])

# Updated function with dummy data for testing
@app.callback(
    [Output('stock-graph', 'figure'),
     Output('current-price', 'children')],
    [Input('ticker-dropdown', 'value'),
     Input('submit-button', 'n_clicks')]
)
def update_graph(ticker, n_clicks):
    # Test start and end dates
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=60)
    
    # Create dummy data
    print("Using dummy data for testing...")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dummy_close = np.linspace(100, 200, len(dates)) + np.random.randn(len(dates)) * 5
    data = pd.DataFrame({'Close': dummy_close}, index=dates)
    data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
    data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
    data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()
    
    # Debugging prints
    print("Close prices:")
    print(data['Close'].tail())
    print("EMA_5:")
    print(data['EMA_5'].tail())
    
    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='EMA 5', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='EMA 13', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='EMA 8', line=dict(color='purple')))
    
    # Add dummy buy/sell signals
    buy_signals = [(data.index[-20], data['Close'].iloc[-20])]
    sell_signals = [(data.index[-10], data['Close'].iloc[-10])]
    
    for signal in buy_signals:
        fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers', name='Buy Signal',
                                 marker=dict(symbol='triangle-up', size=10, color='green')))
    for signal in sell_signals:
        fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers', name='Sell Signal',
                                 marker=dict(symbol='triangle-down', size=10, color='red')))
    
    # Update layout
    fig.update_layout(
        title=f"{ticker} Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals",
        xaxis_title="Date",
        yaxis_title="Price",
        plot_bgcolor="rgba(240,240,240,0.95)",
        paper_bgcolor="white",
        legend=dict(x=0, y=1)
    )
    
    # Current price
    current_price = float(data['Close'].iloc[-1])
    return fig, f"Current Price: {current_price:.2f}"

# Run the app
if __name__ == '__main__':
    print("Starting Dash app...")
    port = int(os.environ.get("PORT", 8080))
    app.run_server(debug=False, host='0.0.0.0', port=port)
