from typing import Any
from pathlib import Path
from logging import getLogger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

logger = getLogger(__name__)

class BaseJSONView(APIView):
        
    def validate_missing_parameters(self, body, required_parameters):
        missing = [par for par in required_parameters if par not in body]
        response = Response({
            'message': 'Missing parameters',
            'missing_parameters': missing,
        }, status=400)
        return response if missing else None

class ErrorView_404(BaseJSONView):
    def dispatch(self, request, *args, **kwargs):
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