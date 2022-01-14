from django.shortcuts import render, redirect
from pathlib import Path

# Create your views here.
from django.http import HttpResponse

from Ifc2Data.forms import DownloadForm, DocumentForm
from django.http import FileResponse
from Ifc2Data.models import Document
from WebApp.settings import MEDIA_ROOT

from WebApp.Functions import all_divide, parser_api, unique, unique_csv, unique_divide, project_information

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

                #get the session uploaded model
                last_model = Document.objects.get(id = selected_project_id)

                #get the path to saved model
                MODEL_DIR = Path(MEDIA_ROOT) / myfile.name        
                
                #retrive project information from the model and save them to the object
                info = project_information(MODEL_DIR)
                last_model.organization = info["organization"]
                last_model.author = info["author"]
                last_model.project_name = info["project_name"]
                last_model.given_name = info["Name"]
                last_model.description = info["Description"]
                last_model.time_stamp = info["time_stamp"]
                last_model.schema_identifiers = info["schema_identifiers"]
                last_model.software = info["software"]
                last_model.save()

                #save the object id in the session
                request.session['selected_project_id'] = selected_project_id
                print(selected_project_id)


                return redirect('model_download')
    else:
        form = DocumentForm()
    return render(request, 'Ifc2Data/upload.html', {
        'form': form
    })




def model_download(request):
    form = DownloadForm(request.POST or None, initial={"file_download": "all","file_format": "xlsx"})
    
    #get the defined session id and the object
    selected_project_id = request.session.get('selected_project_id')
    last_model = Document.objects.get(id = selected_project_id)

    if form.is_valid():
        #get the radio button values
        selected = form.cleaned_data.get("file_download")     
        file_format = form.cleaned_data.get("file_format")
        

        last_model_name = last_model.document.name
        # path to last uploaded document
        MODEL_DIR = Path(MEDIA_ROOT) / last_model_name              
        # parsing the ifc file and converting to dataframe
        model = parser_api(MODEL_DIR)      
        # get the name of last uploaded document without the suffix                           
        xlsx_name = Path(last_model_name).stem                                  

        if selected == "all":
            if file_format == "xlsx":
                XLS_DIR = Path(DOCU_DIR) / (xlsx_name + '_ALL.xlsx')  
                print(XLS_DIR)
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