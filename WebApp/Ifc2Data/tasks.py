import os

from celery import shared_task
import ifcopenshell as ifc
import pandas as pd
from ifcopenshell.util.element import get_psets 
import pandas as pd
from Ifc2Data.models import Document
from pathlib import Path
from WebApp.settings import MEDIA_ROOT
from celery_progress.backend import ProgressRecorder


DOCU_DIR = Path(MEDIA_ROOT) / 'documents'






@shared_task(bind=True)
def project_information_task(self,file_name, selected_project_id):

    contents = Path(MEDIA_ROOT) / file_name
    last_model = Document.objects.get(id = selected_project_id)

    ifc_file = ifc.open(contents)
    project = ifc_file.by_type("IfcProject")[0]
    application = ifc_file.by_type("IfcApplication")[0][2]
    info = project.get_info()
    project_info = {}
    infos = ["Name", "Description"]
    
    for inf in infos:
        project_info[inf] = info[inf]
    wrapper = ifc_file.wrapped_data.header


    #TODO if no infromation then write "No Info"
    last_model.organization = wrapper.file_name.organization[0]
    last_model.author =  wrapper.file_name.author[0]
    last_model.project_name = wrapper.file_name.name
    last_model.given_name = info["Name"]
    last_model.description = info["Description"]
    last_model.time_stamp = wrapper.file_name.time_stamp
    last_model.schema_identifiers = wrapper.file_schema.schema_identifiers[0]
    last_model.software = application


    last_model.save()


   # Collect all building elements
    building_elements = ifc_file.by_type("IfcBuildingElement")
    # Collect all spaces
    spaces = ifc_file.by_type("IfcSpace")
    # Collect project name
    project = ifc_file.by_type("IfcProject")[0].Name

    #celery_recorder
    progress_recorder = ProgressRecorder(self)

    #celery_task length
    task_length = len(building_elements) + len(spaces)


    #List of all elements data dictionarys
    all_elements_data = []

    for i,element in enumerate(building_elements):
        #Create an empty dictionary for all the element data
        element_data = {}
        #Get element name
        element_data.update({"Name": element.Name})
        #Get element IfcType
        element_data.update({"IfcType": element.is_a()})

        #Get relating element type if there is one
        for x in element.IsDefinedBy:
            if x.is_a("IfcRelDefinesByType") == True:
                element_data.update({"Type_Name": x.get_info()["RelatingType"].Name})
            else:
                element_data.update({"Type_Name": "No RelatingType"})

        #Get all the psets key:value pairs, ignore pset group
        try:
            psets = get_psets(element)
            for key in psets.keys():
                element_data.update(psets[key])
        except:
            pass    
        #Add project name to element info
        element_data.update({"Project": project})

        #Get element storey
        try:
            structure = ifc_file[element.id()].ContainedInStructure
            storey = structure[0].RelatingStructure.Name
            element_data.update({"Storey": storey})
        except: 
            element_data.update({"Storey": "No BuildingStorey found"})
        
        progress_recorder.set_progress(i + 1, task_length, description="Downloading")

        all_elements_data.append(element_data)

    for space in spaces:
        #Create an empty dictionary for all the space data
        space_data = {}
        #Get element name
        space_data.update({"Name": space.Name})
        #Get element IfcType
        space_data.update({"IfcType": space.is_a()})

        #Get all the psets key:value pairs, ignore pset group
        try:
            psets = get_psets(space)
            for key in psets.keys():
                space_data.update(psets[key])
        except:
            pass

        #Add project name to element info
        space_data.update({"Project": project})

        #Get element storey
        storey = space.Decomposes[0].RelatingObject.Name
        space_data.update({"Storey": storey})
        space_data.update({"LongName": space.get_info()["LongName"]})
        
        
        all_elements_data.append(space_data)

    # df1 = pd.DataFrame(all_elements_data)

    return all_elements_data




# @shared_task(bind=True)
# def project_information_task(self,file_name, selected_project_id):

#     contents = Path(MEDIA_ROOT) / file_name
#     last_model = Document.objects.get(id = selected_project_id)

#     ifc_file = ifc.open(contents)
#     project = ifc_file.by_type("IfcProject")[0]
#     application = ifc_file.by_type("IfcApplication")[0][2]
#     info = project.get_info()
#     project_info = {}
#     infos = ["Name", "Description"]
    
#     for inf in infos:
#         project_info[inf] = info[inf]
#     wrapper = ifc_file.wrapped_data.header


#     #TODO if no infromation then write "No Info"
#     last_model.organization = wrapper.file_name.organization[0]
#     last_model.author =  wrapper.file_name.author[0]
#     last_model.project_name = wrapper.file_name.name
#     last_model.given_name = info["Name"]
#     last_model.description = info["Description"]
#     last_model.time_stamp = wrapper.file_name.time_stamp
#     last_model.schema_identifiers = wrapper.file_schema.schema_identifiers[0]
#     last_model.software = application


#     last_model.save()


    # return selected_project_id  
