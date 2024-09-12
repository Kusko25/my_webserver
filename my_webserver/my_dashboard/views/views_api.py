from typing import Any
from pathlib import Path
from logging import getLogger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from django.utils import timezone

from ..models import AppSettings
from ..logic import parse_tv_feed
from .utils import monitor_toggle, get_headset_data

from PyP100 import PyP110

logger = getLogger(__name__)

class BaseJSONView(APIView):
        
    def validate_missing_parameters(self, body, required_parameters):
        missing = [par for par in required_parameters if par not in body]
        response = Response({
            'message': 'Missing parameters',
            'missing_parameters': missing,
        }, status=400)
        return response if missing else None

class ControlMonitorView(BaseJSONView):
    @property
    def allowed_methods(self):
        return ['GET']
    def get(self,request):
        monitor = request.GET.get('monitor',2)
        try:
            monitor_toggle(monitor)
            return Response(
                {'message':'success'},
                status=200
            )
        except Exception as e:
            logger.error("Execution of monitor_toggle failed with monitor " + str(monitor))
            logger.error(str(e))
            return Response(
                {'message':'execution failed'},
                status=500
            )

class RefreshFeedsView(BaseJSONView):
    @property
    def allowed_methods(self):
        return ['GET']
    def get(self,request):
        try:
            result, exception = parse_tv_feed(request=request)
            # result, exception = True, None
            if result:
                return Response(
                    {'message':'success'},
                    status=200
                )
            else:
                if isinstance(exception, InterruptedError):
                    return Response(
                        {'message':'Refresh interval not met'},
                        status=200
                    )
                else:
                    return Response(
                        {'message':'execution failed'},
                        status=500
                    )
        except Exception as e:
            logger.error("Execution of parse_tv_feed failed")
            logger.error(str(e))
            return Response(
                {'message':'execution failed with exception'},
                status=500
            )

class RefreshGadgetView(BaseJSONView):
    @property
    def allowed_methods(self):
        return ['GET']
    def get(self,request):
        switch = request.GET.get('gadget')
        if switch is None:
            return Response(
                {'message':'missing parameter'},
                status=400
            )
        try:
            if switch == 'headset':
                data = get_headset_data()
                if not data:
                    return Response(
                        {'message':'execution failed'},
                        status=500
                    )
                return Response(
                    data,
                    status=200
                )
            else:
                return Response(
                    {'message':'invalid parameter'},
                    status=400
                )
        except Exception as e:
            logger.error("Execution of get_headset_data failed")
            logger.error(str(e))
            return Response(
                {'message':'execution failed with exception'},
                status=500
            )

class ErrorView_404(BaseJSONView):
    @property
    def allowed_methods(self):
        return ['GET']
    def get(self, request, *args, **kwargs):
        data = {
            'message': 'Resource not found',
        }
        return Response(data, status=404)

class ControllerView_DailyTemp(BaseJSONView):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.path_skip = Path(r"I:\temp\Daily_temp\skip.txt")
        self.path_no_skip = Path(r"I:\temp\Daily_temp\no_skip.txt")
        
        self.file_content = """
        Rename this File to control deletion. 
        1. skip.txt means deletion will be skipped on next launch 
        2. Anything else. Deletion proceeds as planned. 
        """
    
    def _allowed_methods(self):
        return ['GET', 'POST']
    
    def get(self, request, *args, **kwargs):
        data = {
            "skip_status": self.path_skip.exists(),
        }
        return Response(data)
    
    def post(self, request, *args, **kwargs):
        body = JSONParser().parse(request)
        if response := self.validate_missing_parameters(body, ['set_deletion']):
            return response
        
        try:
            if body['set_deletion']: # Deletion will happen
                if self.path_skip.exists():
                    self.path_skip.unlink()
                if not self.path_no_skip.exists():
                    self.path_no_skip.write_text(self.file_content)
            else: # Deletion will be skipped
                if self.path_no_skip.exists():
                    self.path_no_skip.unlink()
                if not self.path_skip.exists():
                    self.path_skip.write_text(self.file_content)
            return Response({'message': 'Success'})
        except Exception as e:
            logger.exception(e)
            return Response({'message': 'Failed'}, status=500)

class PowerReadingView(BaseJSONView):
    def get(self, request, *args, **kwargs):
        p110 = PyP110.P110(
            address=AppSettings.get_key('p110_address'),
            email=AppSettings.get_key('p110_email'),
            password=AppSettings.get_key('p110_password')
        )
        energy_data = p110.getEnergyUsage()
        data = {
            "timestamp": timezone.now().isoformat(),
            "power": 0.0
        }
        if 'current_power' in energy_data:
            data['power'] = energy_data['current_power']
        return Response(data)