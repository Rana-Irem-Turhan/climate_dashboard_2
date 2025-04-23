import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Load and clean dataset
df = pd.read_csv("combined_climate_data_normalized.csv")
df = df.drop(columns=['Unnamed: 0'])  # Drop auto-index column if present

df.columns = df.columns.str.strip().str.replace(" ", "_").str.replace("(", "").str.replace(")", "")

# Print for debug
print("COLUMNS:", df.columns.tolist())

variables = ['CO2', 'Sea_Level', 'Global_Temp_Anomaly', 'NH_Temp_Anomaly', 'SH_Temp_Anomaly']

# App initialization
app = Dash(__name__)
app.title = "Correlation & Insight Explorer"

# Layout
app.layout = html.Div([
    html.H2("Correlation & Insight Explorer", style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            html.Label("X-axis Variable"),
            dcc.Dropdown(
                id='x-axis-dropdown',
                options=[{'label': var.replace("_", " "), 'value': var} for var in variables],
                value='CO2'
            )
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Y-axis Variable"),
            dcc.Dropdown(
                id='y-axis-dropdown',
                options=[{'label': var.replace("_", " "), 'value': var} for var in variables],
                value='Global_Temp_Anomaly'
            )
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '10px'})
    ]),

    html.Div([
        html.Label("Select Year Range"),
        dcc.RangeSlider(
            id='year-slider',
            min=df['Year'].min(),
            max=df['Year'].max(),
            value=[df['Year'].min(), df['Year'].max()],
            marks={str(year): str(year) for year in range(df['Year'].min(), df['Year'].max()+1, 5)},
            step=1
        )
    ], style={'padding': '20px'}),

    dcc.Graph(id='scatter-plot'),

    html.H4("Correlation Matrix (All Variables)", style={'textAlign': 'center', 'marginTop': '30px'}),
    dcc.Graph(id='correlation-heatmap')
])


# Callback for updates
@app.callback(
    Output('scatter-plot', 'figure'),
    Output('correlation-heatmap', 'figure'),
    Input('x-axis-dropdown', 'value'),
    Input('y-axis-dropdown', 'value'),
    Input('year-slider', 'value')
)
def update_figures(x_var, y_var, year_range):
    filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

    # Scatter Plot with Regression
    scatter = px.scatter(
        filtered,
        x=x_var,
        y=y_var,
        trendline="ols",
        labels={x_var: x_var.replace("_", " "), y_var: y_var.replace("_", " ")},
        title=f"{x_var.replace('_', ' ')} vs {y_var.replace('_', ' ')}"
    )
    scatter.update_layout(template='plotly_white')
    print("FILTERED COLUMNS:", filtered.columns.tolist())
    # Correlation Heatmap
    corr = filtered[variables].select_dtypes(include='number').corr().round(2)
    heatmap = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        colorscale='RdBu',
        zmin=-1, zmax=1,
        colorbar=dict(title="Pearson r")
    ))
    heatmap.update_layout(
        template="plotly_white",
        title="Correlation Matrix (Pearson Correlation)"
    )

    return scatter, heatmap


# Run app
if __name__ == '__main__':
    app.run(debug=True)
