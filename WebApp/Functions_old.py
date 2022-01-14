import ifcopenshell as ifc
# import plotly.express as px
import pandas as pd
from ifcopenshell.util.element import get_psets 
import pandas as pd
import ifcopenshell as ifc


def get_attr_of_pset(_id, ifc_file):
    """ Get all attributes of an instance by given Id
        param _id: id of instance
        return: dict of dicts of attributes
    """
    dict_psets = {}

    try:
        defined_by_type = [x.RelatingType for x in ifc_file[_id].IsDefinedBy if x.is_a("IfcRelDefinesByType")]
        defined_by_properties = [x.RelatingPropertyDefinition for x in ifc_file[_id].IsDefinedBy if
                                 x.is_a("IfcRelDefinesByProperties")]
    except:
        dict_psets.update({ifc_file[_id].GlobalId: "No Attributes found"})
    else:
        for x in defined_by_type:
            if x.HasPropertySets:
                for y in x.HasPropertySets:
                    for z in y.HasProperties:
                        dict_psets.update({z.Name: z.NominalValue.wrappedValue})

        for x in defined_by_properties:
            if x.is_a("IfcPropertySet"):
                for y in x.HasProperties:
                    if y.is_a("IfcPropertySingleValue"):
                        dict_psets.update({y.Name: y.NominalValue.wrappedValue})
                    # this could be usefull for multilayered walls in Allplan
                    if y.is_a("IfcComplexProperty"):
                        for z in y.HasProperties:
                            dict_psets.update({z.Name: z.NominalValue.wrappedValue})
            if x.is_a("IfcElementQuantity"):
                for y in x.Quantities:
                    dict_psets.update({y[0]: y[3]})

    finally:
        dict_psets.update({"IfcGlobalId": ifc_file[_id].GlobalId})

        return dict_psets


def get_structural_storey(_id, ifc_file):
    """ Get structural (IfcBuilgingStorey) information of an instance by given Id
        param _id: id of instance
        return: dict of attributes
    """
    dict_structural = {}
    instance = ifc_file[_id]
    try:
        structure = instance.ContainedInStructure
        storey = structure[0].RelatingStructure.Name

    except:
        dict_structural.update({"Storey": "No Information found"})

    else:
        dict_structural.update({"Storey": storey})
    finally:
        return dict_structural

def movecol(df, cols_to_move=[], ref_col='', place='After'):
    cols = df.columns.tolist()
    if place == 'After':
        seg1 = cols[:list(cols).index(ref_col) + 1]
        seg2 = cols_to_move
    if place == 'Before':
        seg1 = cols[:list(cols).index(ref_col)]
        seg2 = cols_to_move + [ref_col]

    seg1 = [i for i in seg1 if i not in seg2]
    seg3 = [i for i in cols if i not in seg1 + seg2]

    return (df[seg1 + seg2 + seg3])


def parser(contents):
    ifc_file = ifc.open(contents)
    rooms = ifc_file.by_type("IfcSpace")
    instances = ifc_file.by_type("IfcBuildingElement")
    project = ifc_file.by_type("IfcProject")[0].Name
    for room in rooms:
            instances.append(room)
    excel_list = []

    for inst in instances:
        info_pset = get_attr_of_pset(inst.id(), ifc_file=ifc_file)
        info = inst.get_info()
        for x in inst.IsDefinedBy:
            if x.is_a("IfcRelDefinesByType") == True:
                info_pset.update({"Type_Name": x.get_info()["RelatingType"].Name})
            else:
                pass
        info_pset.update({"Name": inst.Name})
        info_pset.update({"IfcType": info["type"]})
        info_pset.update({"Project": project})

        if inst.is_a("IfcSpace") == True:
            info_structural = inst.Decomposes[0].RelatingObject.Name
            info_pset.update({"Storey": info_structural})
        else:
            info_structural = get_structural_storey(inst.id(), ifc_file=ifc_file)
            info_pset.update(info_structural)


        excel_list.append(info_pset)

    df1 = pd.DataFrame(excel_list)

    df2 = movecol(df1,
                    cols_to_move=['IfcType', 'Storey'],
                    ref_col=df1.columns[0],
                    place='Before')
    
    return df2

def Parser_api_V2(path):

    ifc_file = ifc.open(path)

    # Collect all building elements
    building_elements = ifc_file.by_type("IfcBuildingElement")
    # Collect all spaces
    spaces = ifc_file.by_type("IfcSpace")
    # Collect project name
    project = ifc_file.by_type("IfcProject")[0].Name


    #List of all elements data dictionarys
    all_elements_data = []

    for element in building_elements:
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
        psets = get_psets(element)
        for key in psets.keys():
            element_data.update(psets[key])
        
        #Add project name to element info
        element_data.update({"Project": project})

        #Get element storey
        try:
            structure = ifc_file[element.id].ContainedInStructure
            storey = structure[0].RelatingStructure.Name
            element_data.update({"Storey": storey})
        except: 
            element_data.update({"Storey": "No BuildingStorey found"})
        
        
        all_elements_data.append(element_data)

    for space in spaces:
        #Create an empty dictionary for all the space data
        space_data = {}
        #Get element name
        space_data.update({"Name": space.Name})
        #Get element IfcType
        space_data.update({"IfcType": space.is_a()})

        #Get all the psets key:value pairs, ignore pset group
        psets = get_psets(space)
        for key in psets.keys():
            space_data.update(psets[key])
        
        #Add project name to element info
        space_data.update({"Project": project})

        #Get element storey
        storey = space.Decomposes[0].RelatingObject.Name
        space_data.update({"Storey": storey})
        space_data.update({"LongName": space.get_info()["LongName"]})
        
        
        all_elements_data.append(space_data)

    df1 = pd.DataFrame(all_elements_data)

    return df1

def all_divide(df2, path):
    worterbuch = {}
    for item in df2.IfcType.unique():
        DF = df2[df2['IfcType'].str.contains(item, na=False)]
        DF = DF.dropna(axis='columns', how='all')
        worterbuch[item] = DF

    with pd.ExcelWriter(path) as writer:
        for i in worterbuch.keys():
            worterbuch[i].to_excel(writer, sheet_name=i)

def unique(df, path):
    names = []
    data = []
    for column in df.columns:
        name = column
        value = list(df[name].unique())
        names.append(name)
        data.append(value)

    df2 = pd.DataFrame(data, names)
    df2 = df2.transpose()
    df2.to_excel(path)


def unique_csv(df, path):
    names = []
    data = []
    for column in df.columns:
        name = column
        value = list(df[name].unique())
        names.append(name)
        data.append(value)

    df2 = pd.DataFrame(data, names)
    df2 = df2.transpose()
    df2.to_csv(path, encoding='utf-8')


def unique_divide(df, path):
    worterbuch = {}
    dfs = dict(tuple(df.groupby('IfcType')))
    for key in dfs.keys():
        df = dfs[key]
        names = []
        data = []
        for column in df.columns:
            name = column
            value = list(df[name].unique())
            names.append(name)
            data.append(value)

        df2 = pd.DataFrame(data, names)
        worterbuch[key] = df2.transpose()

    with pd.ExcelWriter(path) as writer:
        for i in worterbuch.keys():
            worterbuch[i].to_excel(writer, sheet_name=i)


def project_information(contents):
    ifc_file = ifc.open(contents)
    project = ifc_file.by_type("IfcProject")[0]
    application = ifc_file.by_type("IfcApplication")[0][2]
    info = project.get_info()
    project_info = {}
    #infos = ["Name", "Description","LongName","Phase"]
    infos = ["Name", "Description"]
    
    for inf in infos:
        project_info[inf] = info[inf]
    wrapper = ifc_file.wrapped_data.header
    project_info.update({"organization": wrapper.file_name.organization[0]})
    project_info.update({"author": wrapper.file_name.author[0]})
    project_info.update({"time_stamp": wrapper.file_name.time_stamp})
    project_info.update({"project_name": wrapper.file_name.name})
    project_info.update({"schema_identifiers": wrapper.file_schema.schema_identifiers[0]})
    project_info.update({"software": application})
    return project_info    

