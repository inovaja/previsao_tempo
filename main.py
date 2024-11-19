import logging
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


API_KEY = "8e20087c6d1fa3d1ffa71e3592d93e54"
GEOCODE_URL = "http://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logger.info("Página inicial acessada")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/weather", response_class=HTMLResponse)
async def get_weather(request: Request, city: str = Form(...)):
    logger.info(f"Solicitação de previsão do tempo para a cidade: {city}")
    try:
        # Passo 1: Obter latitude e longitude da cidade
        geocode_params = {
            "q": city,
            "appid": API_KEY,
            "limit": 1
        }
        geocode_response = requests.get(GEOCODE_URL, params=geocode_params)
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()

        if not geocode_data:
            logger.warning(f"Cidade '{city}' não encontrada.")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error_message": f"Cidade '{city}' não encontrada. Verifique o nome e tente novamente."}
            )

        lat = geocode_data[0]["lat"]
        lon = geocode_data[0]["lon"]
        logger.info(f"Coordenadas obtidas para {city}: Latitude {lat}, Longitude {lon}")

        # Passo 2: Obter dados do tempo usando latitude e longitude
        weather_params = {
            "lat": lat,
            "lon": lon,
            "units": "metric",
            "lang": "pt_br",
            "appid": API_KEY
        }
        weather_response = requests.get(WEATHER_URL, params=weather_params)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        logger.info(f"Dados climáticos obtidos com sucesso para {city}")

        # Extração de dados relevantes para exibição
        weather = {
            "temp": weather_data["main"]["temp"],
            "description": weather_data["weather"][0]["description"],
            "humidity": weather_data["main"]["humidity"],
            "wind_speedy": f"{weather_data['wind']['speed']} m/s"
        }

        # Passar dados relevantes para o template
        return templates.TemplateResponse(
            "weather.html",
            {"request": request, "city_name": city, "weather": weather}
        )

    except requests.RequestException as e:
        logger.error(f"Erro ao fazer requisição às APIs: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error_message": "Erro ao obter dados do tempo. Por favor, tente novamente."}
        )

    except KeyError as e:
        logger.error(f"Erro ao processar dados das APIs: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error_message": "Erro ao processar dados do tempo. Por favor, tente novamente."}
        )

    except Exception as e:
        logger.exception(f"Erro inesperado: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error_message": "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde."}
        )