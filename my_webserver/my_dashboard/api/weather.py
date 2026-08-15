from datetime import datetime, timedelta
from typing import ClassVar

import requests
from django.utils.timezone import get_default_timezone
from rest_framework.response import Response
from rest_framework.views import APIView

tz = get_default_timezone()

class WeatherInfo:
    weather_data:ClassVar[list[tuple[datetime,int]]] = []
    last_refresh:ClassVar[datetime | None] = None
    refresh_interval:ClassVar[timedelta] = timedelta(hours=1)
    
    @classmethod
    def getData(cls):
        if cls.last_refresh and cls.last_refresh < datetime.now(tz=tz) + cls.refresh_interval and cls.weather_data:
            return cls.weather_data
        
        response = requests.get('https://app-prod-ws.warnwetter.de/v30/stationOverviewExtended?stationIds=10505')
        response.raise_for_status()
        weather_data = []
        for station in response.json().values():
            for key in station:
                if not (isinstance(key,str) and key.startswith('forecast') and isinstance(station[key],dict)):
                    continue
                forecast = station[key]
                start = forecast['start']
                step = forecast['timeStep']
                temperatures = forecast['temperature']
                for i in range(len(temperatures)):
                    weather_data.append(
                        (
                            datetime.fromtimestamp(
                                float(start + (i*step))/1000,
                                tz=tz
                            ),
                            temperatures[i]
                        )
                    )
        cls.weather_data = sorted(weather_data)
        cls.last_refresh = datetime.now(tz=tz)
        return cls.weather_data

class WeatherInfoView(APIView):
    def get(self,request):
        response_data = []
        for time,temperature in WeatherInfo.getData():
            if time < datetime.now(tz=tz) - timedelta(hours=4):
                continue
            if time > datetime.now(tz=tz) + timedelta(hours=4):
                break
            temperature_str = str(temperature)
            temperature_str = f"{temperature_str[:-1]}.{temperature_str[-1]}°C"
            response_data.append({
                "id": len(response_data),
                "temperature": temperature_str,
                "hour": time.strftime('%H:%M'),
                "sun": "tbd"
            })
        return Response(response_data)