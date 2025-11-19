import dash
from dash import html, dcc, Output, Input, Dash, State, dash_table
import dash_bootstrap_components as dbc
# from base_car import DataLogger
from datalogger import DataLogger
import plotly.express as px
from sonic_car import*
import threading
import os
import pandas as pd
import cv2, base64

# class SensorDashboard(DataLogger):
class SensorDashboard():
    def __init__(self,car):
        # super().__init__()
        self.cap = cv2.VideoCapture(0)
        self.car = car
        self.log = log
        logs_path = "logs"
        self.available_logs = [f for f in os.listdir(logs_path) if f.endswith(".log")]
        # self.is_driving = False  # Fahrstatus
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self._setup_layout()
        self._setup_callbacks()
        # self.dist = 5
        self.speed_mean = 0
        self.speed_min = 0
        self.speed_max = 0
        self.drive_time = 0
        self.ultrasonic_distance = 0
        self._thread = None
        self.drive_distance = 0


    def get_log(self):
        # base_log = super().get_log()
        base_log = log.get_log()
        dist = self.car.get_safe_distance()
        base_log["ultrasonic_distance"] = dist
        return base_log

    def get_frame(self):
        ret, frame = self.cap.read()
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        _, buffer = cv2.imencode('.jpg', frame)
        
        return base64.b64encode(buffer).decode()


    def _setup_layout(self):
        self.app.layout = dbc.Container([
            html.H2("PiCar Dashboard", className="text-center my-4"),

            dbc.Tabs([
#################
# Tab 1: Fahren
#################
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
                                    marks={45: "45°",70: "70°", 90: "90°",110: "110°", 135: "135°"}
                                )
                            ])
                        ], color="info", inverse=True), width=6),
                    ]),
                    dbc.Row([
                        html.Div(style={"height": "30px"}),
                        dbc.Col(dbc.Button("Fahrmodus_1", id="btn-driveMode1", color="success", className="title"), width=2),
                        dbc.Col(dbc.Button("Fahrmodus_2", id="btn-driveMode2", color="success", className="title"), width=2),
                        dbc.Col(dbc.Button("Fahrmodus_3", id="btn-driveMode3", color="success", className="title"), width=2),
                ]),

                    dbc.Row([
                        html.Div(style={"height": "30px"}),
                        dbc.Col(dbc.Button("Fahrmodus_4", id="btn-driveMode4", color="success", className="title"), width=2),
                        dbc.Col(dbc.Button("Fahrmodus_5", id="btn-driveMode5", color="success", className="title"), width=2),
                        dbc.Col(dbc.Button("Fahrmodus_6", id="btn-driveMode6", color="success", className="title"), width=2),
                        dbc.Col(dbc.Button("Fahrmodus_7", id="btn-driveMode7", color="success", className="title"), width=2),
                ]),

                html.Div(style={"height":"30px"}),
                    dbc.Row([
                        dbc.Col(
                            dbc.Card([
                                dbc.CardHeader("Fahrzeugstatus"),
                                dbc.CardBody([
                                html.H4(id="Messwert3", className="title")
                                ])
                            ], color="success", inverse=True, outline=False), width=6),
                        dbc.Col(
                            dbc.Card([
                                dbc.CardHeader("Cam"),
                                dbc.CardBody([
                                    html.Img(id="live-image"),
                                    dcc.Interval(id="cam-interval", interval=200, n_intervals=0)
                                ])
                            ], color="success", inverse=True, outline=False), width=6),
                    ])
            ]),

#########################
# Tab 2: Messwerte
#########################

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
                    dbc.Row([
                        dbc.Col(
                            dcc.Graph(id="logging"),
                            width=12
                        ),
                        dbc.Col(
                            html.Div(
                                dcc.Checklist(
                                    id="value_checklist",
                                    options=[
                                        {"label": "Geschwindigkeit", "value": "speed"},
                                        {"label": "Richtung", "value": "direction"},
                                        {"label": "Lenkwinkel", "value": "steering_angle"},
                                        {"label": "Distanz", "value": "ultrasonic_distance"}
                                    ],
                                    value=["speed","steering_angle"],   # initial ausgewählt
                                    inline=True,
                                    inputStyle={"marginRight":"5px"},
                                    labelStyle={"marginRight":"20px"}
                                ),
                                style={"textAlign":"center"}
                        ),
                            width=12
                        )                        
                    ]),
                    dbc.Row([
                        html.Div(style={"height": "30px"}),
                        dbc.Col(dbc.Button("save log", id="btn-saveLog", color="success", className="title"), width=2),
                ]),
                    dcc.Interval(id="interval-graph",interval=1000,n_intervals=0)
                ]),

#########################
# Tab 3: Logs
#########################

                dbc.Tab(label="Logs", tab_id="tab-logs", children=[
                    html.Div(style={"height": "30px"}),

                    dbc.Row([
                        dbc.Col(dbc.Card([
                            dbc.CardHeader("Log-Auswahl"),
                            dbc.CardBody([
                                dcc.Dropdown(
                                    id="log-dropdown",
                                    options=[
                                        {"label": fname, "value": fname}
                                        for fname in self.available_logs  # Liste der CSV-Dateien im logs-Verzeichnis
                                    ],
                                    placeholder="Bitte Log-Datei auswählen",
                                    value=None,
                                    clearable=False
                                )
                            ])
                        ], color="info", outline=True), width=6),
                    ]),

                    html.Div(style={"height": "30px"}),

                    dbc.Row([
                        dbc.Col(dbc.Card([
                            dbc.CardHeader("Log-Daten"),
                            dbc.CardBody([
                                # Tabelle zur Anzeige der CSV-Inhalte
                                dash_table.DataTable(
                                    id="log-table",
                                    columns=[],
                                    data=[],
                                    page_size=10,
                                    style_table={"overflowX": "auto"},
                                    style_cell={"textAlign": "left"}
                                )
                            ])
                        ], color="secondary", outline=True), width=12),
                    ]),
                    dbc.Row([
                        dbc.Col(
                            dcc.Graph(id="logging_logs"),
                            width=12
                        ),                      
                    ]),
                ])


            ], id="tabs", active_tab="tab-steuerung"),

            html.Div(id="action-output", className="mt-3 text-center"),

            # Intervall zur Synchronisierung der Slider mit car-Werten
            dcc.Interval(id="interval-sync", interval=1000, n_intervals=0)
        ], fluid=True)
        

############################################################
# Callbacks
############################################################

    def _setup_callbacks(self):
        @self.app.callback([
                Output("Messwert","children"),
                Output("Messwert2","children"),
                Output("Messwert3","children"),
        ],
                [Input("interval-sync","n_intervals")],
                [State("interval-sync","interval")]
        )
        def update_values(n_intervals,interval_ms):
            speed = self.car.speed
            # if self.car.state == 'drive' and not self.car.logs.empty:
            if not self.car.logs.empty:
                if self.car.state == 'drive':
                    log.write_log()
                    self.drive_time = self.drive_time + interval_ms / 1000
                    self.drive_distance = self.drive_distance + abs(self.car.speed) * 1/3.6
                self.speed_mean = abs(self.car.logs["speed"]).mean()
                self.speed_min = self.car.logs["speed"].min()
                self.speed_max = self.car.logs["speed"].max()
                speed=self.car.speed
                

            self.state = self.car.state
            self.ultrasonic_distance=self.car.get_safe_distance()
            return(
                html.Div(
                    f"IST:\t\t{speed:.0f} km/h\n\n"
                    f"min:\t\t{self.speed_min:.0f} km/h\n"
                    f"max:\t{self.speed_max:.0f} km/h\n"
                    f"mean:\t{self.speed_mean:.0f} km/h",
                    style={"whiteSpace": "pre"}  # fpr Tabs (\t) und Zeilenumbrüche (\n)
                ),
                html.Div(
                f"IST:\t\t{self.car.steering_angle}°",
                style={"whiteSpace": "pre"}
                ),
                html.Div(
                    f"state = {self.state}\n"
                    f"ultrasonic distance = {self.ultrasonic_distance} cm\n"
                    f"drive time =  {self.drive_time:.0f} s\n"
                    f"drive distance = {self.drive_distance:.1f} m",
                    style={"whiteSpace": "pre"}
                )
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
            if car.state in ['ready','drive']:
                self.car.drive()
                pass
            if self.car.state == 'drive':
                # self.log.write_log()
                pass
            return f"{self.car.speed} km/h", f"{self.car.steering_angle} °"

        @self.app.callback(
            Output("action-output", "children"),
            Input("btn-drive", "n_clicks"),
            Input("btn-stop", "n_clicks"),
            Input("btn-driveMode1","n_clicks"),
            Input("btn-driveMode2","n_clicks"),
            Input("btn-driveMode3","n_clicks"),
            Input("btn-driveMode4","n_clicks"),
            Input("btn-driveMode5","n_clicks"),
            Input("btn-driveMode6","n_clicks"),
            Input("btn-driveMode7","n_clicks"),
            Input("btn-saveLog","n_clicks"),
            prevent_initial_call=True
        )
        def handle_buttons(drive_clicks,
                           stop_clicks,
                           driveMode1_clicks,
                           driveMode2_clicks,
                           driveMode3_clicks,
                           driveMode4_clicks,
                           driveMode5_clicks,
                           driveMode6_clicks,
                           driveMode7_clicks,
                           saveLog_clicks
                           ):
            ctx = dash.callback_context
            if not ctx.triggered:
                return ""
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id in ["btn-driveMode1",
                             "btn-driveMode2",
                             "btn-driveMode3",
                             "btn-driveMode4",
                             "btn-driveMode5",
                             "btn-driveMode6",
                             "btn-driveMode7",] and self.car.state != 'drive':
                return "Fahrbereitschaft über Fahren herstellen"
            elif button_id == "btn-drive":
                self.car.state = 'ready'
                self.car.drive()
                self.log.write_log()
                return "Fahrbereitschaft hergestellt."
            elif button_id == "btn-stop":
                car.state = 'stop'
                self.car.speed = 0
                self.car.steering_angle = 90
                self.car.stop()
                self.log.write_log()
                return "Fahrzeug gestoppt."
            elif button_id == "btn-driveMode1":
                self.car.fahrmodus_1()
                return "Fahrmodus_1 gestartet"
                # self._thread = threading.Thread(target=self.car.fahrmodus_1)
                # self._thread.start()
            elif button_id == "btn-driveMode2":
                self.car.fahrmodus_2()
                return "Fahrmodus_2 gestartet"
            elif button_id == "btn-driveMode3":
                self.car.fahrmodus_3()
                return 'Fahrmodus_3 gestartet'
            elif button_id == "btn-driveMode4":
                self.car.fahrmodus_4()
            elif button_id == "btn-driveMode5":
                # self.car.fahrmodus_5()
                return 'under construction'
            elif button_id == "btn-driveMode6":
                # self.car.fahrmodus_6()
                return 'under construction'
            elif button_id == "btn-driveMode7":
                # self.car.fahrmodus_7()
                return 'under construction'
            elif button_id == "btn-saveLog":
                self.car.save_logs()
            

        # Intervall → Slider synchronisieren mit car-Werten
        @self.app.callback(
            Output("speed-slider", "value"),
            Output("angle-slider", "value"),
            Input("interval-sync", "n_intervals")
        )
        def sync_sliders(n):
            return self.car.speed, self.car.steering_angle

        @self.app.callback(
            Output("logging", "figure"),
            Input("value_checklist", "value"),
            Input("interval-sync","n_intervals")
        )
        def update_graph(selected_metrics, n_intervals):
            if self.car.logs.empty:
                # Leere Grafik zurückgeben
                fig = px.scatter(title="Noch keine Logs vorhanden")
            else:
                df = self.car.logs.copy()
                fig = px.line(df, x="time", y=selected_metrics, title="title",line_shape="hv")
                fig.update_traces(mode='markers+lines')
                fig.update_layout(xaxis_title="Zeit", yaxis_title="Wert")
            return fig
        
        @self.app.callback(
            Output("log-table", "columns"),
            Output("log-table", "data"),
            Output("logging_logs","figure"),
            Input("log-dropdown", "value"),
            # Input("value_checklist", "value")
        )
        def update_log_table(selected_file):
            if selected_file is None:
                return [], [], {}

            df = pd.read_csv(f"logs/{selected_file}")

            columns = [{"name": c, "id": c} for c in df.columns]
            data = df.to_dict("records")
            fig = px.line(df, x=df.index, y=df.columns, title=f'Log:{selected_file}', line_shape="hv")
            return columns, data, fig

        @self.app.callback(dash.Output("live-image", "src"), dash.Input("cam-interval", "n_intervals"))
        def update_image(n):
            return "data:image/jpeg;base64," + self.get_frame()

    def run(self):
        self.app.run_server(host="0.0.0.0",  port=8050 ,debug=True, use_reloader=False) #lokale IP Adresse
        


if __name__ == "__main__":
    car = SonicCar()
    log = DataLogger(car)
    dashboard = SensorDashboard(car)
    
    try:
        dashboard.run()
    except KeyboardInterrupt:
        print("Interrupt by user")
    finally:
        car.save_logs() #speichert die logs


#  app = dash.Dash(__name__)
#  cap = cv2.VideoCapture(0)



#  app.layout = html.Div([
#      html.H1("Live Kamera"),
#      html.Img(id="live-image"),
#      dcc.Interval(id="interval", interval=500, n_intervals=0)
#  ])

#  @app.callback(dash.Output("live-image", "src"), dash.Input("interval", "n_intervals"))
#  def update_image(n):
#      return "data:image/jpeg;base64," + get_frame()


