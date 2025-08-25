import dash
from dash import dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
import sys
import os
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.tracker import PriceTracker
from src.utils.config import Config

# Initialize components
config = Config()
tracker = PriceTracker(config)

# Initialize Dash app
app = dash.Dash(__name__, title="URL Manager - Smart Price Tracker")

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🔗 URL Manager", style={'color': 'white', 'margin': '0'}),
        html.P("Add and manage product URLs for price tracking", style={'color': 'white', 'margin': '10px 0 0 0'})
    ], style={
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'padding': '20px',
        'text-align': 'center'
    }),
    
    # Add Product Section
    html.Div([
        html.H3("➕ Add New Product"),
        
        html.Div([
            html.Label("Product URL:", style={'font-weight': 'bold'}),
            dcc.Input(
                id="product-url-input",
                type="text",
                placeholder="Enter Amazon, eBay, Walmart, or AliExpress URL...",
                style={'width': '100%', 'padding': '10px', 'margin': '10px 0', 'border': '1px solid #ccc', 'border-radius': '5px'}
            )
        ]),
        
        html.Div([
            html.Div([
                html.Label("Target Price ($):", style={'font-weight': 'bold'}),
                dcc.Input(
                    id="target-price-input",
                    type="number",
                    placeholder="Optional target price",
                    style={'width': '100%', 'padding': '10px', 'margin': '10px 0', 'border': '1px solid #ccc', 'border-radius': '5px'}
                )
            ], style={'width': '48%', 'display': 'inline-block', 'margin-right': '2%'}),
            
            html.Div([
                html.Label("Cost Price ($):", style={'font-weight': 'bold'}),
                dcc.Input(
                    id="cost-price-input",
                    type="number",
                    placeholder="Optional cost price for profit calculation",
                    style={'width': '100%', 'padding': '10px', 'margin': '10px 0', 'border': '1px solid #ccc', 'border-radius': '5px'}
                )
            ], style={'width': '48%', 'display': 'inline-block', 'margin-left': '2%'})
        ]),
        
        html.Button(
            "🔍 Add Product",
            id="add-product-btn",
            n_clicks=0,
            style={
                'background': '#28a745',
                'color': 'white',
                'border': 'none',
                'padding': '12px 24px',
                'border-radius': '5px',
                'cursor': 'pointer',
                'font-size': '16px',
                'margin': '10px 0'
            }
        ),
        
        html.Div(id="add-product-result", style={'margin': '10px 0'})
        
    ], style={
        'background': 'white',
        'padding': '20px',
        'margin': '20px',
        'border-radius': '8px',
        'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),
    
    # URL Validation Section
    html.Div([
        html.H3("✅ URL Validation"),
        html.P("Test if a URL is supported and can be scraped:"),
        
        dcc.Input(
            id="validate-url-input",
            type="text",
            placeholder="Enter URL to validate...",
            style={'width': '70%', 'padding': '10px', 'margin': '10px 0', 'border': '1px solid #ccc', 'border-radius': '5px'}
        ),
        
        html.Button(
            "🔍 Validate URL",
            id="validate-url-btn",
            n_clicks=0,
            style={
                'background': '#007bff',
                'color': 'white',
                'border': 'none',
                'padding': '10px 20px',
                'border-radius': '5px',
                'cursor': 'pointer',
                'margin-left': '10px'
            }
        ),
        
        html.Div(id="validation-result", style={'margin': '10px 0'})
        
    ], style={
        'background': 'white',
        'padding': '20px',
        'margin': '20px',
        'border-radius': '8px',
        'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),
    
    # Current Products Section
    html.Div([
        html.H3("📦 Current Tracked Products"),
        html.Button(
            "🔄 Refresh List",
            id="refresh-products-btn",
            n_clicks=0,
            style={
                'background': '#6c757d',
                'color': 'white',
                'border': 'none',
                'padding': '8px 16px',
                'border-radius': '5px',
                'cursor': 'pointer',
                'margin': '10px 0'
            }
        ),
        html.Div(id="products-list")
        
    ], style={
        'background': 'white',
        'padding': '20px',
        'margin': '20px',
        'border-radius': '8px',
        'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),
    
    # Actions Section
    html.Div([
        html.H3("⚡ Quick Actions"),
        
        html.Div([
            html.Button(
                "🧪 Test Notifications",
                id="test-notifications-btn",
                n_clicks=0,
                style={
                    'background': '#fd7e14',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'border-radius': '5px',
                    'cursor': 'pointer',
                    'margin': '5px'
                }
            ),
            
            html.Button(
                "📊 Export to Excel",
                id="export-excel-btn",
                n_clicks=0,
                style={
                    'background': '#17a2b8',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'border-radius': '5px',
                    'cursor': 'pointer',
                    'margin': '5px'
                }
            ),
            
            html.Button(
                "🔄 Run Tracking Update",
                id="run-tracking-btn",
                n_clicks=0,
                style={
                    'background': '#dc3545',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'border-radius': '5px',
                    'cursor': 'pointer',
                    'margin': '5px'
                }
            )
        ]),
        
        html.Div(id="actions-result", style={'margin': '10px 0'})
        
    ], style={
        'background': 'white',
        'padding': '20px',
        'margin': '20px',
        'border-radius': '8px',
        'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),
    
    # Footer
    html.Div([
        html.P([
            "🚀 ",
            html.A("Open Main Dashboard", href="/", target="_blank", style={'color': '#667eea'}),
            " | Smart Price Tracker"
        ], style={'text-align': 'center', 'color': '#6c757d'})
    ], style={'margin': '40px 0 20px 0'})
])

# Callbacks
@app.callback(
    Output('add-product-result', 'children'),
    [Input('add-product-btn', 'n_clicks')],
    [State('product-url-input', 'value'),
     State('target-price-input', 'value'),
     State('cost-price-input', 'value')]
)
def add_product(n_clicks, url, target_price, cost_price):
    """Add a new product for tracking"""
    if n_clicks == 0:
        raise PreventUpdate
    
    if not url:
        return html.Div("❌ Please enter a product URL", style={'color': 'red'})
    
    try:
        # Add product to tracker
        product_id = tracker.add_product(
            url=url.strip(),
            target_price=target_price if target_price else None,
            user_cost_price=cost_price if cost_price else None
        )
        
        if product_id:
            return html.Div([
                html.P("✅ Product added successfully!", style={'color': 'green', 'font-weight': 'bold'}),
                html.P(f"Product ID: {product_id}"),
                html.P("The product will be tracked and you'll receive notifications when prices change.")
            ])
        else:
            return html.Div("❌ Failed to add product. Check if the URL is valid and supported.", style={'color': 'red'})
            
    except Exception as e:
        return html.Div(f"❌ Error adding product: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('validation-result', 'children'),
    [Input('validate-url-btn', 'n_clicks')],
    [State('validate-url-input', 'value')]
)
def validate_url(n_clicks, url):
    """Validate if a URL is supported"""
    if n_clicks == 0:
        raise PreventUpdate
    
    if not url:
        return html.Div("❌ Please enter a URL to validate", style={'color': 'red'})
    
    try:
        platform = tracker.detect_platform(url.strip())
        
        if platform:
            # Test if we can scrape basic info
            scraper = tracker.scrapers.get(platform)
            if scraper and scraper.is_valid_url(url.strip()):
                return html.Div([
                    html.P(f"✅ URL is valid and supported!", style={'color': 'green', 'font-weight': 'bold'}),
                    html.P(f"Platform: {platform.title()}"),
                    html.P("This URL can be added for price tracking.")
                ])
            else:
                return html.Div([
                    html.P(f"⚠️ Platform detected: {platform.title()}", style={'color': 'orange'}),
                    html.P("But the URL format may not be supported. Try adding it to see if it works.")
                ])
        else:
            return html.Div([
                html.P("❌ Unsupported platform", style={'color': 'red'}),
                html.P("Currently supported: Amazon, eBay, Walmart, AliExpress")
            ])
            
    except Exception as e:
        return html.Div(f"❌ Error validating URL: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('products-list', 'children'),
    [Input('refresh-products-btn', 'n_clicks'),
     Input('add-product-btn', 'n_clicks')]
)
def update_products_list(refresh_clicks, add_clicks):
    """Update the list of tracked products"""
    try:
        products = tracker.get_tracked_products()
        
        if not products:
            return html.P("No products tracked yet. Add some products above to get started!")
        
        # Create a table of products
        table_data = []
        for product in products[:20]:  # Show first 20 products
            table_data.append({
                'ID': product.get('id'),
                'Title': product.get('title', 'Unknown')[:60] + ('...' if len(product.get('title', '')) > 60 else ''),
                'Platform': product.get('platform', '').title(),
                'Current Price': f"${product.get('current_price', 0):.2f}" if product.get('current_price') else 'N/A',
                'Target Price': f"${product.get('target_price', 0):.2f}" if product.get('target_price') else 'N/A',
                'Status': '✅ Available' if product.get('availability') else '❌ Out of Stock',
                'Last Checked': product.get('last_checked', 'Never')[:19] if product.get('last_checked') else 'Never'
            })
        
        return dash_table.DataTable(
            data=table_data,
            columns=[
                {'name': 'ID', 'id': 'ID', 'type': 'numeric'},
                {'name': 'Product Title', 'id': 'Title'},
                {'name': 'Platform', 'id': 'Platform'},
                {'name': 'Current Price', 'id': 'Current Price'},
                {'name': 'Target Price', 'id': 'Target Price'},
                {'name': 'Status', 'id': 'Status'},
                {'name': 'Last Checked', 'id': 'Last Checked'}
            ],
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial'
            },
            style_header={
                'backgroundColor': '#667eea',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            page_size=10,
            sort_action="native",
            filter_action="native"
        )
        
    except Exception as e:
        return html.P(f"Error loading products: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('actions-result', 'children'),
    [Input('test-notifications-btn', 'n_clicks'),
     Input('export-excel-btn', 'n_clicks'),
     Input('run-tracking-btn', 'n_clicks')]
)
def handle_actions(test_clicks, export_clicks, tracking_clicks):
    """Handle quick action button clicks"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == 'test-notifications-btn' and test_clicks > 0:
            results = tracker.test_notifications()
            
            if any(results.values()):
                successful = [service for service, success in results.items() if success]
                failed = [service for service, success in results.items() if not success]
                
                return html.Div([
                    html.P("📬 Notification Test Results:", style={'font-weight': 'bold'}),
                    html.P(f"✅ Successful: {', '.join(successful)}" if successful else ""),
                    html.P(f"❌ Failed: {', '.join(failed)}" if failed else ""),
                    html.P("Check your email, Telegram, or Slack for test messages.")
                ])
            else:
                return html.P("❌ No notification services are configured.", style={'color': 'red'})
        
        elif button_id == 'export-excel-btn' and export_clicks > 0:
            result = tracker.export_data("excel", export_type="comprehensive")
            
            if result['success']:
                return html.Div([
                    html.P("📊 Excel Export Successful!", style={'color': 'green', 'font-weight': 'bold'}),
                    html.P(f"File saved: {result['filepath']}")
                ])
            else:
                return html.P(f"❌ Export failed: {result['message']}", style={'color': 'red'})
        
        elif button_id == 'run-tracking-btn' and tracking_clicks > 0:
            result = tracker.run_tracking()
            
            return html.Div([
                html.P("🔄 Tracking Update Complete!", style={'color': 'green', 'font-weight': 'bold'}),
                html.P(f"Updated: {result['updated']} products"),
                html.P(f"Failed: {result['failed']} products"),
                html.P(f"Total: {result['total']} products")
            ])
            
    except Exception as e:
        return html.P(f"❌ Action failed: {str(e)}", style={'color': 'red'})
    
    raise PreventUpdate

if __name__ == '__main__':
    print("🔗 Starting URL Manager...")
    print("📋 URL Manager will be available at: http://127.0.0.1:8051")
    app.run_server(debug=True, host='127.0.0.1', port=8051) 