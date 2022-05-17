import pandas as pd
import numpy as np
import os
from geopy.distance import distance
from math import sin, cos, sqrt, atan2, radians

def clean_folder(PATH):
    for f in os.listdir(PATH):
        os.remove(os.path.join(PATH, f))
    return

def write_log(log_type, log_info, PATH):
    error_file = os.path.join(PATH, 'logs', 'eds_geo.log')
    with open(error_file, 'a') as f:
        f.write(f'[{log_type}]. Info: {log_info}.\n')
    return

############### validation functions ##################

def num_column_validation(num_col, num_col_accepted, file, PATH):
    log_info, log_type = None, None
    if num_col < num_col_accepted:
        log_info = f'Faltan columnas en el archivo {file}.xlsx'
        log_type = 'VALIDATION ERROR'
    else:
        log_info = f'Numero de columnas correcto en el archivo {file}.xlsx'
        log_type = 'VALIDATION OK'
    write_log(log_type, log_info, PATH)
    return

def column_names_validation(columns, col_accepteds, file, PATH):
    ans = True
    for c in columns:
        if c not in col_accepteds:
            ans = False
            log_info = f'La columna {c} en el archivo {file}.xlsx no tiene el nombre estipulado'
            write_log('VALIDATION ERROR', log_info, PATH)
    if ans:
        log_info = f'Nombre columnas correcto en el archivo {file}.xlsx'
        write_log('VALIDATION OK', log_info, PATH)
    return

def count_pk_validation(pk, df, file, PATH):
    pk_val = df[pk].isnull().sum()
    if pk_val > 0:
        log_info = f'Faltan datos en la columna {pk} en el archivo {file}.xlsx'
        log_type = 'VALIDATION ERROR'
    else:
        log_info = f'Llaves primarias completas en el archivo {file}.xlsx'
        log_type = 'VALIDATION OK'
    write_log(log_type, log_info, PATH)
    return

def non_georeferenced_info(df, file, PATH):
    identifier, lat, lon = None, None, None
    if file == 'Hijos':
        identifier = 'Id_hijo'
        lat, lon = 'Latitud_hijo', 'Longitud_hijo'
    else:
        identifier = 'Cod_dane'
        lat, lon = 'Latitud_colegio', 'Longitud_colegio'
    d = {identifier: [], lat : [], lon : []}
    for index, row in df.iterrows():
        if np.isnan(row[lat]) or np.isnan(row[lon]):
            d[identifier].append(row[identifier])
            d[lat].append(row[lat])
            d[lon].append(row[lon])
    if len(d[identifier]) > 0:
        df = pd.DataFrame(d)
        file_name = os.path.join(PATH, 'output', '{0}_no_georeferen.xlsx'.format(file))
        df.to_excel(file_name, index=False, sheet_name='{0}_no_georeferen'.format(file))
        log_info = f'Hay elementos en {file}.xlsx que no pueden ser georeferenciados, porfavor revise la carpeta output'
        log_type = 'VALIDATION ERROR'
        write_log(log_type, log_info, PATH)
    else:
        log_info = f'Todos los elementos en {file}.xlsx pueden ser georeferenciados'
        log_type = 'VALIDATION OK'
        write_log(log_type, log_info, PATH)
    return

##################### distance functions ######################
def haversine_distance(source_cord, target_cord):
    """
    utiliza ley de los semiversenos de la trignometria esferica para calcular la distancia.
    menos costoso computacionalmente (formula) pero menos preciso
    accuracy de 5m
    """
    R = 6373 #approximate average radius of earth in km
    lat1 = radians(source_cord[0])
    lon1 = radians(source_cord[1])
    lat2 = radians(target_cord[0])
    lon2 = radians(target_cord[1])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    ans = R * c
    return ans

def vincenty_distance(source_cord, target_cord):
    """
    calcula la distancia utlizando geodesicas en un esferoide (elipsoide de revolucion)
    mas costoso computacionalmente (algoritmo iterativo) pero mas preciso
    accuracy de 0.5mm
    """
    ans = distance(source_cord, target_cord).km
    return ans

def calculate_distance(source_cord, target_cord, dist_method):
    """dist_method: 0 for haversine_distance, 1 for vincenty_distance"""
    ans = None
    if dist_method == 0: ans = haversine_distance(source_cord, target_cord)
    elif dist_method == 1: ans = vincenty_distance(source_cord, target_cord)
    else: print("El metodo ingresado no es valido. Escoger 0 para usar haversine_distance() y 1 para usar vincenty_distance()")
    return ans

def calculate_nearby_schools(df, child, dist_method, cant, clasif):
    #calculo de distancias a todos los colegios
    df['distancia'] = df.apply(lambda x: calculate_distance(child, (x.Latitud_colegio, x.Longitud_colegio), dist_method), axis=1)
    #filtrado por calidad de colegio y cercania
    df = df[df["Calidad"].isin(clasif)]
    df = df.sort_values('distancia', ascending=True)
    nearby_schools = df.head(cant)
    return nearby_schools
