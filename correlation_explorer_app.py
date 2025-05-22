import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, ctx
import dash_daq as daq
import numpy as np

# 1. Data Loading & Preprocessing

df_global = pd.read_csv("merged_global.csv")
df_hemi = pd.read_csv("hemispheric_merged.csv")
# Merge by Year and Month 
df = pd.merge(df_global, df_hemi, on=["year", "month"], suffixes=("", "_hemi"))
# Add Season column
def get_season(month):
    return {
        12: "DJF", 1: "DJF", 2: "DJF",
        3: "MAM", 4: "MAM", 5: "MAM",
        6: "JJA", 7: "JJA", 8: "JJA",
        9: "SON", 10: "SON", 11: "SON"
    }[month]
df["Season"] = df["month"].apply(get_season)

# 2. App Initialization
app = Dash(__name__)
app.title = "Correlation & Insight Explorer"

# Define the variables for the dropdowns
def get_variables(scope):
    if scope == "global":
        return {
            "norm_co2": "CO₂ Anomaly",
            "norm_land_ocean_temp": "Global Land+Ocean Temp Anomaly",
            "norm_land_temp": "Global Land Temp Anomaly",
            "norm_sea_level": "Sea Level Change"
        }
    elif scope == "nh":
        return {
            "norm_north_co2": "NH CO₂ Anomaly",
            "norm_north_land_ocean": "NH Land+Ocean Temp Anomaly",
            "norm_north_land": "NH Land Temp Anomaly",
            "norm_msl_north": "NH Sea Level Change"

        }
    elif scope == "sh":
        return {
            "norm_south_co2": "SH CO₂ Anomaly",
            "norm_south_land_ocean": "SH Land+Ocean Temp Anomaly",
            "norm_south_land": "SH Land Temp Anomaly",
            "norm_msl_south": "SH Sea Level Change"
        }

#  3. App Layout
app.layout = html.Div([
    html.H2("Correlation & Insight Explorer", style={'textAlign': 'center'}),

    html.Div([
        html.Label("Scope"),
        dcc.RadioItems(id="scope-selector", options=[
            {"label": "🌍 Global", "value": "global"},
            {"label": "🌎 Northern Hemisphere", "value": "nh"},
            {"label": "🌏 Southern Hemisphere", "value": "sh"}
        ],
        value="global",
        labelStyle={"display": "inline-block", "margin-right": "15px"}),
    
        html.Label("Theme", style={'marginTop': '10px'}),
        daq.ToggleSwitch(
            id='theme-toggle',
            label=['Light', 'Dark'],
            value=False,
            style={'marginTop': '5px'}
        )
    ], style={
        'width': '100%',
        'maxWidth': '1200px',
        'margin': '0 auto',
        'fontSize': '16px'
    }),
    
    
    html.Div([
        html.Div([
            html.Label("X-axis Variable"),
            dcc.Dropdown(id='x-axis-dropdown'),
            html.Label("Y-axis Variable", style={'marginTop': '10px'}),
            dcc.Dropdown(id='y-axis-dropdown')],
        style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            html.Label("Year Range"),
            dcc.RangeSlider(
                id='year-slider',
                min=df['year'].min(), max=df['year'].max(),
                value=[df['year'].min(), df['year'].max()],
                marks={str(year): str(year) for year in range(df['year'].min(), df['year'].max()+1, 5)},
                step=1       
            ),
            html.Label("View Mode", style={'marginTop': '10px'}),
            dcc.RadioItems(
                id='view-mode',
                options=[{"label": "Monthly", "value": "Monthly"}, {"label": "Seasonal", "value": "Seasonal"}],
                value="Monthly",
                labelStyle={"display": "inline-block", "margin-right": "10px"}
            )
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'})
    ], style={
        'width': '100%',
        'maxWidth': '1200px',
        'margin': '0 auto',
        'fontSize': '16px'
    }),

    html.Div([
        html.H4("What You're Seeing", style={"marginTop": "20px"}),
        html.P("This tool allows you to explore statistical relationships between CO₂ emissions, sea level rise, and temperature anomalies."),
        html.P("You can switch between Global, Northern, or Southern Hemisphere views and compare how these factors correlate over time."),
        html.P("Use the sliders and dropdowns to control the timeframe and variable axes. The scatter plot shows how two selected variables move together over time, while the heatmap shows all pairwise correlations.")
    ], style={
        "backgroundColor": "#f5f5f5",
        "padding": "15px",
        "border": "1px solid #ccc",
        "borderRadius": "6px",
        "marginTop": "20px",
        "maxWidth": "900px",
        "fontSize": "16px"
    }),

    html.Div(id='correlation-note', style={'padding': '10px', 'fontSize': '16px'}),

    dcc.Graph(id='scatter-plot'),
    html.H4("Correlation Matrix (Pearson)", style={'textAlign': 'center', 'marginTop': '30px'}),
    dcc.Graph(id='correlation-heatmap')
])
# 4. Callbacks
@app.callback(
    Output('x-axis-dropdown', 'options'),
    Output('y-axis-dropdown', 'options'),
    Output('x-axis-dropdown', 'value'),
    Output('y-axis-dropdown', 'value'),
    Input('scope-selector', 'value')  ) 

def update_variable_options(scope):
    vars = get_variables(scope)
    options = [{'label': v, 'value': k} for k, v in vars.items()]
    return options, options, list(vars.keys())[0], list(vars.keys())[1]
@app.callback(
    Output('scatter-plot', 'figure'),
    Output('correlation-heatmap', 'figure'),
    Output('correlation-note', 'children'),
    Input('x-axis-dropdown', 'value'),
    Input('y-axis-dropdown', 'value'),
    Input('year-slider', 'value'),
    Input('view-mode', 'value'),
    Input('scope-selector', 'value'),
    Input('theme-toggle', 'value')
)
def update_visuals(x_var, y_var, year_range, mode, scope, dark_mode):
    vars_dict = get_variables(scope)
    dff = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    if mode == "Seasonal":
        dff = dff.groupby(['year', 'Season']).mean(numeric_only=True).reset_index()
    else:
        dff = dff.copy()
    r = dff[[x_var, y_var]].corr().iloc[0, 1]
    strength = "No correlation"
    if abs(r) > 0.8:
        strength = "🔍 Very strong correlation"
    elif abs(r) > 0.6:
        strength = "🔍 Strong correlation"
    elif abs(r) > 0.4:
        strength = "🔍 Moderate correlation"
    elif abs(r) > 0.2:
        strength = "🔍 Weak correlation"
    elif abs(r) > 0:
        strength = "🔍 Very weak correlation"

    corr_sentence = f"{strength} detected (r = {r:.2f})"
    # Scatter Plot with Regression
    fig = px.scatter(
        dff, x=x_var, y=y_var, trendline="ols",
        title=f"{vars_dict[x_var]} vs {vars_dict[y_var]}",
        labels={x_var: vars_dict[x_var], y_var: vars_dict[y_var]},
        template="plotly_dark" if dark_mode else "plotly_white"
    )
    fig.update_traces(
        hovertemplate=f"<b>Year</b>: %{{customdata[0]}}<br><b>Month/Season</b>: %{{customdata[1]}}<br><b>{vars_dict[x_var]}</b>: %{{x:.3f}}<br><b>{vars_dict[y_var]}</b>: %{{y:.3f}}",
        customdata=dff[["year", "Season"]] if mode == "Seasonal" else dff[["year", "month"]]
    )
# Add R² if OLS exists
    try:
        results = px.get_trendline_results(fig)
        r_squared = results.iloc[0]["px_fit_results"].rsquared
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.95, y=0.05,
            text=f"R² = {r_squared:.2f}",
            showarrow=False,
            font=dict(size=14, color="white" if dark_mode else "black")
        )
    except:
        pass

    corr = dff[list(vars_dict.keys())].corr().round(2)
    heatmap = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=list(vars_dict.values()),
        y=list(vars_dict.values()),
        colorscale='Cividis',
        zmin=-1, zmax=1,
        colorbar=dict(title="Pearson r")
    ))
    heatmap.update_layout(template="plotly_dark" if dark_mode else "plotly_white")

    return fig, heatmap, corr_sentence

# 5. Run app
if __name__ == '__main__':
    app.run(debug=True)