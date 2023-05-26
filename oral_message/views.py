from django.shortcuts import render
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import json

from .oral_message import serialized_om

def index(request):
    return render(request, 'oral_message/index.html')

@csrf_exempt
def om_api(request):
    request_dict = json.loads(request.body)
    
    traitor_statuses = request_dict['statuses']
    initial_order = request_dict['order']
    json_result = serialized_om(traitor_statuses, initial_order)
    return HttpResponse(json_result, content_type="application/json")