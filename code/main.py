import pandas as pd
import numpy as np
import itertools
import warnings
import os

from utils import *

warnings.filterwarnings("ignore")
BASE_DIR = os.path.normpath(os.getcwd() + os.sep + os.pardir)

#clean preview executions
clean_folder(os.path.join(BASE_DIR, 'logs'))
clean_folder(os.path.join(BASE_DIR, 'output'))

def upload_files():
    INPUT_DIR = os.path.join(BASE_DIR, 'input')
    df_children = pd.read_excel(os.path.join(BASE_DIR, 'input','Hijos.xlsx'), header=0)
    df_parents = pd.read_excel(os.path.join(BASE_DIR, 'input','Padres.xlsx'), header=0)
    df_schools = pd.read_excel(os.path.join(BASE_DIR, 'input','Colegios.xlsx'), header=0)

    dist_actual_col = []
    for index, row in df_children.iterrows():
        colegio = row['Cod_dane']
        lat_hijo = row['Latitud_hijo']
        lon_hijo = row['Longitud_hijo']
        if not(np.isnan(colegio) or np.isnan(lat_hijo) or np.isnan(lon_hijo)):
            lat_col = df_schools.loc[df_schools['Cod_dane'] == colegio, 'Latitud_colegio'].iloc[0]
            lon_col = df_schools.loc[df_schools['Cod_dane'] == colegio, 'Longitud_colegio'].iloc[0]
            source_cord = (lat_hijo, lon_hijo)
            target_cord = (lat_col, lon_col)
            d = vincenty_distance(source_cord, target_cord)
            dist_actual_col.append(d)
        else:
            dist_actual_col.append(np.nan)
    df_children["distancia_colegio_actual"] = dist_actual_col
    return df_children, df_parents, df_schools

def validations(df_children, df_parents, df_schools):
    """children validations"""
    #validacion numero de columnas
    num_column_validation(len(df_children.columns), 13, 'Hijos', BASE_DIR)
    #validacion nombre columnas
    col_accepteds = ['Tipo_ID','Id_hijo','Id_padre','Cod_dane','Cod_q7_institucion','Edad_hijo',
                    'Periodos_aprobados','Municipio_residencia_hijo','Departamento_residencia_hijo',
                    'Pais_residencia_hijo','Direccion_residencia_hijo','Latitud_hijo','Longitud_hijo']
    column_names_validation(list(df_children.columns), col_accepteds, 'Hijos', BASE_DIR)
    #validacion llaves primarias
    count_pk_validation('Id_hijo', df_children, 'Hijos', BASE_DIR)

    """parents validations"""
    #validacion numero de columnas
    num_column_validation(len(df_parents.columns), 9, 'Padres', BASE_DIR)
    #validacion nombre columnas
    col_accepteds = ['Id_padre','Nombre_padre','Rango_salarial','Municipio_residencia_padre',
                    'Departamento_residencia_padre','Pais_residencia_padre','Direccion_residencia_padre',
                    'Latitud_padre','Longitud_padre']
    column_names_validation(list(df_parents.columns), col_accepteds, 'Padres', BASE_DIR)
    #validacion llaves primarias
    count_pk_validation('Id_padre', df_parents, 'Padres', BASE_DIR)

    """schools validations"""
    #validacion numero de columnas
    num_column_validation(len(df_schools.columns), 10, 'Colegios', BASE_DIR)
    #validacion nombre columnas
    col_accepteds = ['Cod_dane','Nombre_institucion','Municipio_institucion','Departamento_institucion','Sector',
                    'Pais_instutucion','Direccion_institucion','Calidad','Latitud_colegio','Longitud_colegio']
    column_names_validation(list(df_schools.columns), col_accepteds, 'Colegios', BASE_DIR)
    #validacion llaves primarias
    count_pk_validation('Cod_dane', df_schools, 'Colegios', BASE_DIR)

    """extra validations"""
    #validacion colegios hijos en base colegios
    schools_not_found = []
    children_schools = set(df_children['Cod_dane'].dropna().astype(int).tolist())
    schools = df_schools['Cod_dane'].dropna().astype(int).tolist()
    for s in children_schools:
        if s not in schools:
            schools_not_found.append(s)
    if len(schools_not_found) > 0:
        df = pd.DataFrame(schools_not_found, columns =['Cod_dane'])
        file_name = os.path.join(BASE_DIR, 'output', 'colegios_faltantes.xlsx')
        df.to_excel(file_name, index=False, sheet_name='colegios_faltantes')
        log_info = f'Hay colegios en Hijos.xlsx que no se encuentran en Colegios.xlsx, porfavor revise la carpeta output'
        log_type = 'VALIDATION ERROR'
        write_log(log_type, log_info, BASE_DIR)
    else:
        log_info = f'Todos los colegios de Hijos.xlsx se encuentran en la en Colegios.xlsx'
        log_type = 'VALIDATION OK'
        write_log(log_type, log_info, BASE_DIR)
    #validacion id_padre en base hijos
    childrens = []
    parents = df_parents['Id_padre'].dropna().astype(int).tolist()
    for index, row in df_children.iterrows():
        x = row['Id_padre']
        if np.isnan(x) or (x not in parents):
            if row['Id_hijo'] not in childrens:
                childrens.append(row['Id_hijo'])
    if len(childrens) > 0:
        df = pd.DataFrame(childrens, columns =['Id_hijo'])
        file_name = os.path.join(BASE_DIR, 'output', 'hijos_Id_padre_incorrecto.xlsx')
        df.to_excel(file_name, index=False, sheet_name='hijos_Id_padre_incorrecto')
        log_info = f'Hay ninos en Hijos.xlsx que tienen un Id_padre incorrecto, porfavor revise la carpeta output'
        log_type = 'VALIDATION ERROR'
        write_log(log_type, log_info, BASE_DIR)
    else:
        log_info = f'Todos los ninos de Hijos.xlsx tienen un Id_padre correcto'
        log_type = 'VALIDATION OK'
        write_log(log_type, log_info, BASE_DIR)
    #validacion Periodos_aprobados hijos
    pa = {'Id_hijo': [], 'Periodos_aprobados':[]}
    for index, row in df_children.iterrows():
        x = row['Periodos_aprobados']
        if np.isnan(x) or (x > 12) or (x < 0):
            pa['Id_hijo'].append(row['Id_hijo'])
            pa['Periodos_aprobados'].append(row['Periodos_aprobados'])
    if len(pa['Id_hijo']) > 0:
        df = pd.DataFrame(pa)
        file_name = os.path.join(BASE_DIR, 'output', 'hijos_Per_aprob_incorrecto.xlsx')
        df.to_excel(file_name, index=False, sheet_name='hijos_Per_aprob_incorrecto')
        log_info = f'Hay ninos en Hijos.xlsx que tienen Periodos_aprobados incorrectos, porfavor revise la carpeta output'
        log_type = 'VALIDATION ERROR'
        write_log(log_type, log_info, BASE_DIR)
    else:
        log_info = f'Todos los ninos de Hijos.xlsx tienen Periodos_aprobados correcto'
        log_type = 'VALIDATION OK'
        write_log(log_type, log_info, BASE_DIR)
    #validacion informacion que pueda ser georeferenciable
    non_georeferenced_info(df_children, 'Hijos', BASE_DIR)
    non_georeferenced_info(df_schools, 'Colegios', BASE_DIR)
    return

def school_suggestions(df_children, df_schools, cant, clasif, dist_method):
    """
    Input: df_children -> dataframe de hijos, df_schools -> dataframe de colegios,
    cant -> cantidad de colegios a sugerir por cada sector (publico o privado),
    clasif -> Calidad de los colegios requerida.
    Output: colegios_sugeridos_todos -> archivo excel con las sugerencias de colegios para cada nino
    """
    #crear archivo de salida
    cols = list(df_schools.columns)
    cols.insert(0, 'Id_hijo')
    cols.insert(2, 'distancia')
    colegios_sugeridos_todos = pd.DataFrame(columns=cols)
    #separacion de colegios por sector
    colegios_publicos = df_schools[df_schools["Sector"] == "OFICIAL"]
    colegios_privados = df_schools[df_schools["Sector"] == "NO OFICIAL"]
    #usar los hijos que tengan georeferenciacion posible
    df_children = df_children.dropna(how='any', subset=['Latitud_hijo', 'Longitud_hijo'])
    for index1, row1 in df_children.iterrows():
        child = (row1['Latitud_hijo'], row1['Longitud_hijo'])
        #calculo distancias colegios privados
        colegio_privados_cercanos = calculate_nearby_schools(colegios_privados, child, dist_method, cant, clasif)
        colegio_publicos_cercanos = calculate_nearby_schools(colegios_publicos, child, dist_method, cant, clasif)
        #crear dataframe de colegios sugeridos para el nino_i
        sugerencia_colegios_nino_i = pd.concat([colegio_privados_cercanos, colegio_publicos_cercanos], ignore_index=True)
        #agregar las sugerencias al archivo de salida
        for index2, row2 in sugerencia_colegios_nino_i.iterrows():
            new_items = {'Id_hijo': row1['Id_hijo']}
            s = pd.Series(new_items)
            row2 = row2.append(s)
            colegios_sugeridos_todos = colegios_sugeridos_todos.append(row2, ignore_index=True)
    file_name = os.path.join(BASE_DIR, 'output', 'sugerencia_colegios.xlsx')
    colegios_sugeridos_todos.to_excel(file_name, index=False, sheet_name='sugerencia_colegios')
    log_info = 'Se han sugerido colegios para los ninos que podian ser georeferenciados'
    log_type = 'EXECUTION OK'
    write_log(log_type, log_info, BASE_DIR)
    return

def work_flow():
    #Cargue de archivos
    df_children, df_parents, df_schools = upload_files()
    #Alistamiento (validaciones)
    validations(df_children, df_parents, df_schools)
    cant_col_sugeridos = 1
    clasificacion_requerida = ["A+", "A"]
    #sugerencia de colegios
    school_suggestions(df_children, df_schools, cant_col_sugeridos, clasificacion_requerida, dist_method=1)
work_flow()
