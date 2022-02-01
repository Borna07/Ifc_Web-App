import os

from celery import shared_task
import ifcopenshell as ifc
import pandas as pd
from ifcopenshell.util.element import get_psets 
import pandas as pd

@shared_task(bind=True)
def project_information_task(contents, last_model):
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


    return last_model  
