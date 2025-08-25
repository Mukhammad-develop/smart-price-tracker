import dash
from dash import dcc, html, Input, Output, State, dash_table, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.tracker import PriceTracker
from src.utils.config import Config
from src.utils.profit_calculator import ProfitCalculator

# Initialize components
config = Config()
tracker = PriceTracker(config)
profit_calc = ProfitCalculator()

# Initialize Dash app
app = dash.Dash(__name__, title="Smart Price Tracker Dashboard")
app.config.suppress_callback_exceptions = True

# Custom CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                background-color: #f8f9fa;
            }
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .card {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 20px;
                padding: 20px;
            }
            .metric-card {
                text-align: center;
                padding: 15px;
                margin: 10px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
            }
            .metric-label {
                color: #6c757d;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

def get_dashboard_data():
    """Get data for dashboard"""
    try:
        products = tracker.get_tracked_products()
        analytics = tracker.get_analytics(days=30)
        notification_status = tracker.get_notification_status()
        export_status = tracker.get_export_status()
        
        return {
            'products': products,
            'analytics': analytics,
            'notification_status': notification_status,
            'export_status': export_status
        }
    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        return {
            'products': [],
            'analytics': {},
            'notification_status': {},
            'export_status': {}
        }

def create_price_history_chart(product_id: int):
    """Create price history chart for a product"""
    try:
        history_data = tracker.get_product_history(product_id, days=30)
        
        if 'error' in history_data:
            return go.Figure().add_annotation(text="No price history available", showarrow=False)
        
        price_history = history_data.get('price_history', [])
        if not price_history:
            return go.Figure().add_annotation(text="No price history available", showarrow=False)
        
        df = pd.DataFrame(price_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig = go.Figure()
        
        # Price line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines+markers',
            name='Price',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6)
        ))
        
        # Target price line (if available)
        target_price = history_data.get('target_price')
        if target_price:
            fig.add_hline(
                y=target_price,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Target: ${target_price:.2f}"
            )
        
        fig.update_layout(
            title=f"Price History - {history_data.get('product_title', 'Unknown')[:50]}...",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating price chart: {e}")
        return go.Figure().add_annotation(text="Error loading price history", showarrow=False)

def create_analytics_charts(analytics_data: Dict[str, Any]):
    """Create analytics charts"""
    
    # Platform breakdown pie chart
    platforms = analytics_data.get('platform_breakdown', {})
    if platforms:
        platform_fig = px.pie(
            values=list(platforms.values()),
            names=list(platforms.keys()),
            title="Products by Platform"
        )
        platform_fig.update_traces(textposition='inside', textinfo='percent+label')
    else:
        platform_fig = go.Figure().add_annotation(text="No platform data available", showarrow=False)
    
    # Price trends bar chart
    price_trends = analytics_data.get('price_trends', [])[:10]  # Top 10
    if price_trends:
        trends_df = pd.DataFrame(price_trends)
        trends_fig = px.bar(
            trends_df,
            x='product_title',
            y='change_percent',
            title="Top Price Changes (Last 30 Days)",
            color='change_percent',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        trends_fig.update_xaxes(tickangle=45)
        trends_fig.update_layout(xaxis_title="Product", yaxis_title="Price Change (%)")
    else:
        trends_fig = go.Figure().add_annotation(text="No price trend data available", showarrow=False)
    
    return platform_fig, trends_fig

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🛍️ Smart Price Tracker Dashboard", style={'margin': '0'}),
        html.P("Monitor prices, analyze trends, and maximize profits", style={'margin': '10px 0 0 0'})
    ], className="main-header"),
    
    # Refresh button
    html.Div([
        html.Button("🔄 Refresh Data", id="refresh-btn", n_clicks=0, 
                   style={'margin': '20px', 'padding': '10px 20px', 'background': '#667eea', 
                          'color': 'white', 'border': 'none', 'border-radius': '5px', 'cursor': 'pointer'})
    ]),
    
    # Metrics cards
    html.Div(id="metrics-row"),
    
    # Charts section
    html.Div([
        html.Div([
            dcc.Graph(id="platform-chart")
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id="trends-chart")
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ], className="card"),
    
    # Products table
    html.Div([
        html.H3("📦 Tracked Products"),
        html.Div(id="products-table")
    ], className="card"),
    
    # Product details section
    html.Div([
        html.H3("📈 Product Price History"),
        dcc.Dropdown(
            id="product-dropdown",
            placeholder="Select a product to view price history",
            style={'margin': '10px 0'}
        ),
        dcc.Graph(id="price-history-chart")
    ], className="card"),
    
    # Profit calculator section
    html.Div([
        html.H3("💰 Profit Calculator"),
        html.Div([
            html.Div([
                html.Label("Cost Price ($):"),
                dcc.Input(id="cost-price-input", type="number", value=10, style={'width': '100%', 'margin': '5px 0'})
            ], style={'width': '23%', 'display': 'inline-block', 'margin': '1%'}),
            
            html.Div([
                html.Label("Selling Price ($):"),
                dcc.Input(id="selling-price-input", type="number", value=25, style={'width': '100%', 'margin': '5px 0'})
            ], style={'width': '23%', 'display': 'inline-block', 'margin': '1%'}),
            
            html.Div([
                html.Label("Platform:"),
                dcc.Dropdown(
                    id="platform-dropdown",
                    options=[
                        {'label': 'Amazon', 'value': 'amazon'},
                        {'label': 'eBay', 'value': 'ebay'},
                        {'label': 'Walmart', 'value': 'walmart'},
                    ],
                    value='amazon',
                    style={'margin': '5px 0'}
                )
            ], style={'width': '23%', 'display': 'inline-block', 'margin': '1%'}),
            
            html.Div([
                html.Button("Calculate Profit", id="calc-profit-btn", n_clicks=0,
                           style={'padding': '10px 20px', 'background': '#28a745', 'color': 'white', 
                                  'border': 'none', 'border-radius': '5px', 'cursor': 'pointer', 'margin-top': '25px'})
            ], style={'width': '23%', 'display': 'inline-block', 'margin': '1%'})
        ]),
        
        html.Div(id="profit-results", style={'margin-top': '20px'})
    ], className="card"),
    
    # Status section
    html.Div([
        html.H3("🔧 System Status"),
        html.Div(id="status-info")
    ], className="card"),
    
    # Hidden div for storing data
    html.Div(id="dashboard-data", style={'display': 'none'}),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=300*1000,  # Update every 5 minutes
        n_intervals=0
    )
])

# Callbacks
@app.callback(
    Output('dashboard-data', 'children'),
    [Input('refresh-btn', 'n_clicks'),
     Input('interval-component', 'n_intervals')]
)
def update_dashboard_data(refresh_clicks, intervals):
    """Update dashboard data"""
    data = get_dashboard_data()
    return dash.utils.PlotlyJSONEncoder().encode(data)

@app.callback(
    [Output('metrics-row', 'children'),
     Output('platform-chart', 'figure'),
     Output('trends-chart', 'figure'),
     Output('products-table', 'children'),
     Output('product-dropdown', 'options'),
     Output('status-info', 'children')],
    [Input('dashboard-data', 'children')]
)
def update_dashboard_components(data_json):
    """Update all dashboard components"""
    
    if not data_json:
        empty_fig = go.Figure().add_annotation(text="No data available", showarrow=False)
        return [], empty_fig, empty_fig, "No data", [], "No status"
    
    data = dash.utils.PlotlyJSONEncoder().decode(data_json)
    
    # Metrics cards
    analytics = data.get('analytics', {})
    products = data.get('products', [])
    
    metrics = html.Div([
        html.Div([
            html.Div(str(len(products)), className="metric-value"),
            html.Div("Tracked Products", className="metric-label")
        ], className="metric-card", style={'width': '18%', 'display': 'inline-block'}),
        
        html.Div([
            html.Div(str(analytics.get('total_price_checks', 0)), className="metric-value"),
            html.Div("Price Checks", className="metric-label")
        ], className="metric-card", style={'width': '18%', 'display': 'inline-block'}),
        
        html.Div([
            html.Div(f"${analytics.get('average_price', 0):.2f}", className="metric-value"),
            html.Div("Avg Price", className="metric-label")
        ], className="metric-card", style={'width': '18%', 'display': 'inline-block'}),
        
        html.Div([
            html.Div(str(analytics.get('products_with_changes', 0)), className="metric-value"),
            html.Div("Price Changes", className="metric-label")
        ], className="metric-card", style={'width': '18%', 'display': 'inline-block'}),
        
        html.Div([
            html.Div(str(len(data.get('notification_status', {}).get('configured_services', []))), className="metric-value"),
            html.Div("Notifications", className="metric-label")
        ], className="metric-card", style={'width': '18%', 'display': 'inline-block'})
    ])
    
    # Charts
    platform_fig, trends_fig = create_analytics_charts(analytics)
    
    # Products table
    if products:
        products_df = pd.DataFrame(products)
        products_table = dash_table.DataTable(
            data=products_df[['title', 'platform', 'current_price', 'target_price', 'availability']].to_dict('records'),
            columns=[
                {'name': 'Product', 'id': 'title'},
                {'name': 'Platform', 'id': 'platform'},
                {'name': 'Current Price', 'id': 'current_price', 'type': 'numeric', 'format': {'specifier': '$.2f'}},
                {'name': 'Target Price', 'id': 'target_price', 'type': 'numeric', 'format': {'specifier': '$.2f'}},
                {'name': 'Available', 'id': 'availability'}
            ],
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': '#667eea', 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            page_size=10
        )
    else:
        products_table = html.P("No products tracked yet. Add some products to get started!")
    
    # Product dropdown options
    dropdown_options = [
        {'label': f"{p.get('title', 'Unknown')[:50]}... - ${p.get('current_price', 0):.2f}", 'value': p.get('id')}
        for p in products if p.get('id')
    ]
    
    # Status info
    notification_status = data.get('notification_status', {})
    export_status = data.get('export_status', {})
    
    status_info = html.Div([
        html.H4("📬 Notifications"),
        html.P(f"Configured services: {', '.join(notification_status.get('configured_services', []))}"),
        
        html.H4("📊 Export"),
        html.P(f"Google Sheets: {'✅' if export_status.get('google_sheets_available') else '❌'}"),
        html.P(f"Excel: {'✅' if export_status.get('excel_available') else '❌'}"),
        html.P(f"Recent exports: {len(export_status.get('recent_exports', []))}")
    ])
    
    return metrics, platform_fig, trends_fig, products_table, dropdown_options, status_info

@app.callback(
    Output('price-history-chart', 'figure'),
    [Input('product-dropdown', 'value')]
)
def update_price_history_chart(selected_product_id):
    """Update price history chart based on selected product"""
    if not selected_product_id:
        return go.Figure().add_annotation(text="Select a product to view price history", showarrow=False)
    
    return create_price_history_chart(selected_product_id)

@app.callback(
    Output('profit-results', 'children'),
    [Input('calc-profit-btn', 'n_clicks')],
    [State('cost-price-input', 'value'),
     State('selling-price-input', 'value'),
     State('platform-dropdown', 'value')]
)
def calculate_profit(n_clicks, cost_price, selling_price, platform):
    """Calculate and display profit analysis"""
    if n_clicks == 0 or not cost_price or not selling_price:
        return html.P("Enter cost and selling prices, then click Calculate Profit")
    
    try:
        profit_data = profit_calc.calculate_profit_for_platform(platform, selling_price, cost_price)
        
        return html.Div([
            html.H4(f"Profit Analysis - {platform.title()}"),
            
            html.Div([
                html.Div([
                    html.Strong("Gross Profit: "),
                    f"${profit_data['gross_profit']:.2f}"
                ], style={'margin': '5px 0'}),
                
                html.Div([
                    html.Strong("Total Fees: "),
                    f"${profit_data['total_fees']:.2f}"
                ], style={'margin': '5px 0'}),
                
                html.Div([
                    html.Strong("Net Profit: "),
                    f"${profit_data['net_profit']:.2f}"
                ], style={'margin': '5px 0', 'color': 'green' if profit_data['is_profitable'] else 'red'}),
                
                html.Div([
                    html.Strong("Profit Margin: "),
                    f"{profit_data['profit_margin_percent']:.1f}%"
                ], style={'margin': '5px 0'}),
                
                html.Div([
                    html.Strong("ROI: "),
                    f"{profit_data['roi_percent']:.1f}%"
                ], style={'margin': '5px 0'}),
                
                html.Div([
                    html.Strong("Break-even Price: "),
                    f"${profit_data['break_even_price']:.2f}"
                ], style={'margin': '5px 0'}),
            ]),
            
            html.H5("Fee Breakdown:"),
            html.Ul([
                html.Li(f"{fee_name.replace('_', ' ').title()}: ${fee_value:.2f}")
                for fee_name, fee_value in profit_data['fee_breakdown'].items()
            ])
        ])
        
    except Exception as e:
        return html.Div([
            html.P(f"Error calculating profit: {str(e)}", style={'color': 'red'})
        ])

if __name__ == '__main__':
    print("🚀 Starting Smart Price Tracker Dashboard...")
    print("📊 Dashboard will be available at: http://127.0.0.1:8050")
    print("🔄 Dashboard auto-refreshes every 5 minutes")
    app.run_server(debug=True, host='127.0.0.1', port=8050) 