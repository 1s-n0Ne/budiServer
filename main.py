from fastapi import FastAPI
import random
import pandas as pd
from datetime import datetime, timedelta
import googlemaps
import google.generativeai as genai


# Generate random dates within the current year
def generate_random_date():
    start_date = datetime(datetime.now().year, 1, 1)
    end_date = datetime(datetime.now().year, 12, 31)
    time_between_dates = end_date - start_date
    random_number_of_days = random.randrange(time_between_dates.days)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date.date()


app = FastAPI()


@app.get('/getMissions')
def mission_fetcher():
    genai.configure(api_key='AIzaSyDCFQNyB_Jof3_h-Cq6pzukKc72LZjP75A')
    model = genai.GenerativeModel('models/gemini-pro')
    prompt = '''
    "Budi" es una util aplicación para que las personas puedan monitorear y  reducir su huella de carbono asociada a sus transportes. La aplicación genera rutas candidatas para que los usuarios puedan ir a los lugares a los que siempre van usando metodos de transporte alternativos que tengan un menor impacto de emisiones de carbono. Los medios de transporte validos para la aplicación son "caminar", "automovil", "autobus" y "bicicleta".
Para mantener a las personas enganchadas en la aplicación, también se dan misiones semanales que sean sencillas y convenientes de realizar para los usuarios y que no afecten de manera negativa las rutinas de las personas.
Ejemplos de estas misiones pueden ser:
* "Realiza un viaje a pie"
* "Camina 500 metros"
* "Realiza un viaje en autobus"
* "No relizes un viaje en coche"
Crea una nueva mision semanal para la aplicación "Budi". No debe ser de más de una enunciado de longitud.
    '''
    result = model.generate_content(prompt)
    return result.text


@app.get('/getUserData/{user_id}')
def user_getter(user_id: int):
    num_rows = random.randint(100, 150)
    vehicles = ["car", "bus", "bicycle", "walking"]

    # Create the dataframe
    df = pd.DataFrame({
        'Date': [generate_random_date() for _ in range(num_rows)],
        'Vehicle': [random.choice(vehicles) for _ in range(num_rows)],
        'Distance': [random.uniform(0, 30) for _ in range(num_rows)]
    })

    response = {'day': {}, 'week': {}, 'month': {}, 'year': {}}

    latest = df['Date'].sort_values(ascending=False).to_numpy()[0]
    for v in vehicles:
        response['day'][v] = df[(df['Date'] == latest) & (df['Vehicle'] == v)].shape[0]

    latest_year, latest_week, _ = latest.isocalendar()
    df['Year'], df['Week'], _ = zip(*df['Date'].apply(lambda x: x.isocalendar()))
    same_week_as_latest = df[(df['Year'] == latest_year) & (df['Week'] == latest_week)]
    df['Date'] = pd.to_datetime(df['Date'])
    same_month_as_latest = df[df['Date'].dt.month == latest.month]

    for v in vehicles:
        response['week'][v] = same_week_as_latest[same_week_as_latest['Vehicle'] == v].shape[0]

    for v in vehicles:
        response['month'][v] = same_month_as_latest[same_month_as_latest['Vehicle'] == v].shape[0]

    for v in vehicles:
        response['year'][v] = df[df['Vehicle'] == v].shape[0]

    return response


@app.get('/alternateRouter')
def router():
    now = datetime.now()
    gmaps = googlemaps.Client(key='AIzaSyB3ZqvkjbbkHnmDEMqdVTHvEszp2gxuulg')

    transport_modes = ['driving', 'walking', 'transit', 'bicycling']
    factors = {'driving': 0.188, 'walking': 0, 'transit': 0.01576, 'bicycling': 0}

    response = {}

    for mode in transport_modes:
        directions_result = gmaps.directions("Expo Guadalajara, Guadalajara",
                                             "Central de Autobuses Nueva, Guadalajara",
                                             mode=mode,
                                             # alternatives=True,
                                             departure_time=now)

        distance = sum([leg['distance']['value'] for leg in directions_result[0]['legs']])

        distance = distance / 1000
        carbon_emitted = distance * factors[mode]
        polyline = directions_result[0]['overview_polyline']['points']

        mode_response = {'distance': distance, 'carbon_emitted': carbon_emitted, 'polyline': polyline}
        response[mode] = mode_response

    return response

