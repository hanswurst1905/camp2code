import dash
from dash import html, dcc, Output, Input, Dash
import dash_bootstrap_components as dbc
from base_car import BaseCar  # deine Car-Klasse mit speed & steering_angle

class SensorDashboard:
    def __init__(self, car):
        self.car = car
        self.is_driving = False  # Fahrstatus
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self._setup_layout()
        self._setup_callbacks()

    def _setup_layout(self):
        self.app.layout = dbc.Container([
            html.H2("PiCar Dashboard", className="text-center my-4"),

            dbc.Tabs([
                # Tab 1: Fahren
                dbc.Tab(label="Fahren", tab_id="tab-steuerung", children=[
                    dbc.Row([
                        html.Div(style={"height": "30px"}),
                        dbc.Col(dbc.Button("Fahren", id="btn-drive", color="success", className="title"), width=6),
                        dbc.Col(dbc.Button("Stop", id="btn-stop", color="danger", className="title"), width=6),
                    ]),

                html.Div(style={"height":"30px"}),                    

                    dbc.Row([
                        dbc.Col(dbc.Card([
                            dbc.CardHeader("Speed"),
                            dbc.CardBody([
                                html.H4(id="speed-display", className="card-title"),
                                dcc.Slider(
                                    id="speed-slider", min=-100, max=100, step=1, value=self.car.speed,
                                    marks={-100: "-100", -30: "-30", 0: "0", 30: "30", 100: "100"}
                                )
                            ])
                        ], color="primary", inverse=True), width=6),

                        dbc.Col(dbc.Card([
                            dbc.CardHeader("Steering Angle"),
                            dbc.CardBody([
                                html.H4(id="angle-display", className="card-title"),
                                dcc.Slider(
                                    id="angle-slider", min=45, max=135, step=1, value=self.car.steering_angle,
                                    marks={45: "45°", 90: "90°", 135: "135°"}
                                )
                            ])
                        ], color="info", inverse=True), width=6),
                    ]),
                    dbc.Row([
                        html.Div(style={"height": "30px"}),
                        dbc.Col(dbc.Button("Fahrmodus_1", id="btn-driveMode1", color="success", className="title"), width=3),
                        dbc.Col(dbc.Button("Fahrmodus_2", id="btn-driveMode2", color="success", className="title"), width=3),
                        dbc.Col(dbc.Button("Fahrmodus_3", id="btn-driveMode3", color="success", className="title"), width=3),
                        dbc.Col(dbc.Button("Fahrmodus_4", id="btn-driveMode4", color="success", className="title"), width=3),
                ]),
            ]),

                # Tab 2: Messwerte
                dbc.Tab(label="Messwerte", tab_id="tab-messwerte", children=[
                    html.Div(style={"height": "30px"}),
                    dbc.Row([
                        dbc.Col(dbc.Card([
                            dbc.CardHeader("Geschwindigkeit"),
                            dbc.CardBody([
                                html.H4(id="Messwert", className="title")
                            ])
                        ], color="warning", inverse=True), width=6),

                        dbc.Col(dbc.Card([
                            dbc.CardHeader("Lenkwinkel"),
                            dbc.CardBody([
                                html.H4(id="Messwert2", className="title")
                            ])
                        ], color="success", inverse=True), width=6),
                    ]),
                ]),
            ], id="tabs", active_tab="tab-steuerung"),

            html.Div(id="action-output", className="mt-3 text-center"),

            # Intervall zur Synchronisierung der Slider mit car-Werten
            dcc.Interval(id="interval-sync", interval=1000, n_intervals=0)
        ], fluid=True)


    def _setup_callbacks(self):
        @self.app.callback(
                Output("Messwert","children"),
                Output("Messwert2","children"),
                Input("interval-sync","n_intervals")
                
        )
        def update_values(n_intervals):
            return(
                html.Div(
                f"IST:\t\t{self.car.speed} km/h\n\nmin:\t\t{self.car.direction} km/h\nmax:\t{self.car.speed} km/h\nmean:\t{self.car.speed} km/h",
                style={"whiteSpace": "pre"}  # behält Tabs (\t) und Zeilenumbrüche (\n)
                ),

                f"{self.car.steering_angle}°"
            ) 
        # Sliderbewegung → Werte setzen + ggf. fahren
        @self.app.callback(
            Output("speed-display", "children"),
            Output("angle-display", "children"),
            Input("speed-slider", "value"),
            Input("angle-slider", "value")
        )
        def update_values(speed, angle):
            self.car.speed = speed
            self.car.steering_angle = angle
            if self.is_driving:
                self.car.drive()
            return f"{self.car.speed} km/h", f"{self.car.steering_angle} °"

        # Buttons → Fahrstatus setzen + Werte ggf. zurücksetzen
        @self.app.callback(
            Output("action-output", "children"),
            Input("btn-drive", "n_clicks"),
            Input("btn-stop", "n_clicks"),
            Input("btn-driveMode1","n_clicks"),
            Input("btn-driveMode2","n_clicks"),
            Input("btn-driveMode3","n_clicks"),
            Input("btn-driveMode4","n_clicks"),
            prevent_initial_call=True
        )
        def handle_buttons(drive_clicks, stop_clicks, driveMode1_clicks, driveMode2_clicks,driveMode3_clicks,driveMode4_clicks):
            ctx = dash.callback_context
            if not ctx.triggered:
                return ""
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "btn-drive":
                self.is_driving = True
                self.car.drive()
                return "Fahren gestartet."
            elif button_id == "btn-stop":
                self.is_driving = False
                self.car.speed = 0
                self.car.steering_angle = 90
                self.car.stop()
                return "Fahrzeug gestoppt."
            elif button_id == "btn-driveMode1":
                self.car.fahrmodus_1()
                return "Fahrmodus_1 gestartet"
            elif button_id == "btn-driveMode2":
                self.car.fahrmodus_2()
                return "Fahrmodus_2 gestartet"
            elif button_id == "btn-driveMode3":
                return "under construction"
            elif button_id == "btn-driveMode4":
                return "under construction"

        # Intervall → Slider synchronisieren mit car-Werten
        @self.app.callback(
            Output("speed-slider", "value"),
            Output("angle-slider", "value"),
            Input("interval-sync", "n_intervals")
        )
        def sync_sliders(n):
            return self.car.speed, self.car.steering_angle

    def run(self):
        self.app.run_server(host="0.0.0.0",  port=8050 ,debug=True) #lokale IP Adresse
        


if __name__ == "__main__":
    car = BaseCar()
    dashboard = SensorDashboard(car)
    dashboard.run()
