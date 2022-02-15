from django.shortcuts import render, redirect
from pathlib import Path
import pandas as pd

# Create your views here.
from django.http import HttpResponse

from Ifc2Data.forms import DownloadForm, DocumentForm
from django.http import FileResponse
from Ifc2Data.models import Document
from WebApp.settings import MEDIA_ROOT
from celery.result import AsyncResult
from WebApp.Functions import all_divide, parser_api, unique, unique_csv, unique_divide, project_information

from .tasks import project_information_task

DOCU_DIR = Path(MEDIA_ROOT) / 'documents'


def index(request):
    return render(request, 'Ifc2Data/index.html')


def model_upload(request):
    if request.method == 'POST':
        myfile = request.FILES['document']     
        #check if ifc file                 
        if myfile.name.endswith('.Ifc'.lower()):                
            form = DocumentForm(request.POST, request.FILES)    
            if form.is_valid():
                #save the model in the database
                form.save(commit=True)

                #get the session id
                selected_project_id = Document.objects.latest("uploaded_at").id    
                
                #WO CELERY
                # file_name = myfile.name  

                # contents = Path(MEDIA_ROOT) / file_name
                # last_model = Document.objects.get(id = selected_project_id)


                # project_information(contents, last_model)

                #CELERY IMPLEMENTATION
                #insted get the file name

                file_name = myfile.name  


                task = project_information_task.delay(file_name, selected_project_id)

                #save the object id in the session
                request.session['selected_project_id'] = selected_project_id
                request.session['task_id'] = task.task_id
                #request.session['task_id'] = task.id

                print(task.task_id)
                # return redirect('model_download')
                return render(request, 'Ifc2Data/upload.html', {'task_id' : task.task_id})

    else:
        form = DocumentForm()
    return render(request, 'Ifc2Data/upload.html', {
        'form': form, 
    })




def model_download(request):
    form = DownloadForm(request.POST or None, initial={"file_download": "all","file_format": "xlsx"})
    
    #get the defined session id and the object
    selected_project_id = request.session.get('selected_project_id')
    last_model = Document.objects.get(id = selected_project_id)

    #Retrive celery task result
    task_id = request.session.get('task_id')

    result = AsyncResult(id=task_id)
    all_elements_data = result.get() # 4
    model = pd.DataFrame(all_elements_data)

    if form.is_valid():
        #get the radio button values
        selected = form.cleaned_data.get("file_download")     
        file_format = form.cleaned_data.get("file_format")
        

        last_model_name = last_model.document.name


        # path to last uploaded document
        # MODEL_DIR = Path(MEDIA_ROOT) / last_model_name              
        # parsing the ifc file and converting to dataframe

        #model = parser_api(MODEL_DIR)     
        #  
        # get the name of last uploaded document without the suffix                           

        xlsx_name = Path(last_model_name).stem                                  

        if selected == "all":
            if file_format == "xlsx":
                XLS_DIR = Path(DOCU_DIR) / (xlsx_name + '_ALL.xlsx')  
                # saving the converted ifc file to documents
                model.to_excel(XLS_DIR)                                
                response = FileResponse(open(XLS_DIR, 'rb'))
            if file_format == "csv":
                CSV_DIR = Path(DOCU_DIR) / (xlsx_name + '_ALL.csv')  
                model.to_csv(CSV_DIR, encoding = 'utf-8')
                # saving the converted ifc file to documents                                
                response = FileResponse(open(CSV_DIR, 'rb'))
            return response



        if selected == "all_divide":
            XLS_DIR = Path(DOCU_DIR) / (xlsx_name + '_ALL_per_Type.xlsx')  
            all_divide(model, XLS_DIR)
            response = FileResponse(open(XLS_DIR, 'rb'))
            return response

        if selected == "unique":
            if file_format == "xlsx":
                XLS_DIR = Path(DOCU_DIR) / (xlsx_name + '_UNIQUE.xlsx') 
                unique(model, XLS_DIR)
                response = FileResponse(open(XLS_DIR, 'rb'))
            if file_format == "csv":
                CSV_DIR = Path(DOCU_DIR) / (xlsx_name + '_ALL.csv')  
                unique_csv(model, CSV_DIR)
                response = FileResponse(open(CSV_DIR, 'rb'))
            return response

        if selected == "unique_divide":
            XLS_DIR = Path(DOCU_DIR) / (xlsx_name + '_UNIQUE_per_Type.xlsx') 
            unique_divide(model, XLS_DIR)
            response = FileResponse(open(XLS_DIR, 'rb'))
            return response
    
    return render(request, 'Ifc2Data/download.html', {'form':form, 'ifc':last_model })