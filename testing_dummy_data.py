from dash import Dash, dcc, html, Input, Output, State
import yfinance as yf
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
from datetime import datetime, timedelta
import os

# Initialize the app
app = Dash(__name__)

# App Layout
app.layout = html.Div([
    html.H1("Stock Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals"),
    
    html.Div([
        dcc.Input(
            id='ticker-input',
            type='text',
            value='SOL-USD',  # Default 
            placeholder="Enter a ticker symbol",
            style={'width': '200px'}
        ),
        html.Button("Submit", id='submit-button', n_clicks=0, style={'marginLeft': '10px'}),
    ], style={'marginBottom': '20px'}),
    
    dcc.Graph(id='graph'),
    html.Div(id='current-price', style={'marginTop': '20px', 'fontWeight': 'bold'})
])

# Callback for graph and price updates
@app.callback(
    [Output('graph', 'figure'), Output('current-price', 'children')],
    Input('submit-button', 'n_clicks'),
    State('ticker-input', 'value')
)
def update_graph(n_clicks, ticker):
    if n_clicks == 0:
        raise PreventUpdate  # Avoid triggering on app startup

    try:
        print(f"Button clicked {n_clicks} times. Fetching data for {ticker}...")

        # Validate user input
        if not ticker:
            return go.Figure(), "Error: Please enter a valid ticker symbol."

        # Fetch stock data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=60)
        data = yf.download(ticker, start=start_date, end=end_date, interval='1d')

        if data.empty:
            return go.Figure(), f"Error: No data found for {ticker}. Please check the symbol."

        # Calculate EMAs
        data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
        data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()
        data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()

        # Generate Buy/Sell Signals
        buy_signals = []
        sell_signals = []

        for i in range(1, len(data)):
            if (
                data['EMA_5'].iloc[i] > data['EMA_13'].iloc[i] and
                data['EMA_5'].iloc[i - 1] <= data['EMA_13'].iloc[i - 1]
            ):
                buy_signals.append((data.index[i], data['Close'].iloc[i]))
            elif (
                data['EMA_5'].iloc[i] < data['EMA_13'].iloc[i] and
                data['EMA_5'].iloc[i - 1] >= data['EMA_13'].iloc[i - 1]
            ):
                sell_signals.append((data.index[i], data['Close'].iloc[i]))

        print("Buy Signals:", buy_signals)
        print("Sell Signals:", sell_signals)

        # Create the graph
        fig = go.Figure()

        # Add Close Prices and EMAs
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='EMA 5'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='EMA 13'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='EMA 8'))

        # Add Buy Signals
        for signal in buy_signals:
            fig.add_trace(go.Scatter(
                x=[signal[0]], y=[signal[1]],
                mode='markers+text', name='Buy Signal',
                marker=dict(symbol='triangle-up', size=10, color='green'),
                text=["Buy"], textposition='top center'
            ))

        # Add Sell Signals
        for signal in sell_signals:
            fig.add_trace(go.Scatter(
                x=[signal[0]], y=[signal[1]],
                mode='markers+text', name='Sell Signal',
                marker=dict(symbol='triangle-down', size=10, color='red'),
                text=["Sell"], textposition='bottom center'
            ))

        # Update layout
        fig.update_layout(
            title=f"{ticker.upper()} Prices with 5, 13, and 8-day EMAs and Buy/Sell Signals",
            xaxis_title='Date',
            yaxis_title='Price',
            template="plotly_white"
        )

        # Display the current price
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

