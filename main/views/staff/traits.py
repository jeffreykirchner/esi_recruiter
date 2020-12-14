from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging

@login_required
@user_is_staff
def traitsView(request):
    logger = logging.getLogger(__name__) 
    
    # logger.info("some info")

    if request.method == 'POST':       

        f = request.FILES['file']

        logger.info(f"File to be uploaded {f}")

        v=""

        for chunk in f.chunks():
            v+=str(chunk.decode("utf-8"))
        
        logger.info(v)
        logger.info(v.splitlines())


        data = json.loads(request.body.decode('utf-8'))
        u = request.user

        if data["action"] == "uploadCSV":
            return takeCSVUpload(data,u)
        elif data["action"] == "action2":
            pass
           
        return JsonResponse({"response" :  "fail"},safe=False)     

    else:      
        return render(request,'staff/traits.html',{"u":None ,"id":None}) 

def takeCSVUpload(data,u):
    logger = logging.getLogger(__name__) 
    logger.info("Take trait CSV upload")
    logger.info(data)

    status = "success"
   

    return JsonResponse({"status" :  status,
                                },safe=False)