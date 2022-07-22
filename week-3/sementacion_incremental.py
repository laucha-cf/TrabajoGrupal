import pandas as pd
import numpy as np
import requests
import json
import boto3
from io import StringIO

# -- Cargamos los datos de las zonas dentro de Nueva York --#
df_all_zones = pd.read_csv('../data/taxi+_zone_lookup.csv')
# -- Cargamos los datos de los viajes en taxi. Datos previamente procesados, así como los outliers --#
df_all = pd.read_csv('../processed_data/data_taxis_nyc_2018.csv', parse_dates=['tpep_pickup_datetime'])
df_outliers = pd.read_csv('../processed_data/outliers.csv')
# -- Creamos una copia del DataFrame para no afectar el original --#
df = df_all.copy()

# -- Cargamos los datos del clima para cada Borough --#
df_weather = pd.read_csv('../data/NY_Boroughs_Weathers_01-2018.csv', parse_dates=['Datetime'])

# -- Agregamos info del clima al DataFrame de viajes --#
bors = df_all_zones.Borough.unique()
df_bors = pd.DataFrame(enumerate(bors), columns=['IdBorough', 'Borough'])
df_weather = df_weather.merge(right=df_bors, how='inner', on='Borough')
df_weather['Key_1'] = df_weather.Datetime.dt.strftime('%Y%m%d%H')
df_weather.IdBorough = [*map(str, df_weather.IdBorough)]
df_weather['Key_final'] = df_weather.IdBorough + df_weather.Key_1


df = df.merge(right=df_all_zones, how='left', left_on='PULocationID', right_on='LocationID')
df = df.merge(right=df_bors, how='inner', on='Borough')
df['Key_1'] = df['tpep_pickup_datetime'].dt.strftime('%Y%m%d%H')
df.IdBorough = [*map(str, df.IdBorough)]
df['Key_final'] = df.IdBorough + df.Key_1
df = df.merge(right=df_weather, how='left', on='Key_final')
columns = list(df_all) + ['Temperature', 'Precip_Type']
df = df[columns]

# -- Calendar --#
df['tpep_pickup_datetime'] = [*map(str, df['tpep_pickup_datetime'])]
only_dates = df['tpep_pickup_datetime'].str.split()

for i, elem in enumerate(only_dates):
    only_dates[i] = elem[0]
    
unique_dates = list(only_dates.unique())

df_calendar = pd.DataFrame({
    'Date': unique_dates
})
df_calendar['Date'] = pd.to_datetime(df_calendar['Date'])
df_calendar.insert(loc=0, column='DateID', value=df_calendar.Date.dt.strftime('%Y%m%d'))

df_calendar['Year'] = df_calendar['Date'].dt.year
df_calendar['Month'] = df_calendar['Date'].dt.month
df_calendar['Day'] = df_calendar['Date'].dt.day
df_calendar['Week'] = df_calendar['Date'].dt.isocalendar().week
df_calendar['Day_of_Week'] = df_calendar['Date'].dt.day_name

# -- Trip --#
datetime = df['tpep_pickup_datetime'].str.split()
dates = []
times = []
for date, time in datetime:
    dates.append(date)
    times.append(time)

df_trip = pd.DataFrame({
    'VendorID': df['VendorID'],
    'Date': dates,
    'PU_Time': times,
    'Duration': df['Travel_time'],
    'Passenger_count': df['passenger_count'],
    'Distance': df['trip_distance'],
    'PU_IdZone': df['PULocationID'],
    'DO_IdZone': df['DOLocationID'], 
    'Temperature': df['Temperature'],
    'Precip_Type': df['Precip_Type']
})

df_trip.Date = pd.to_datetime(df_trip.Date)
df_trip.Date = df_trip.Date.dt.strftime('%Y%m%d')
df_trip.Duration = df_trip.Duration.round()
df_trip.Precip_Type = df_trip.Precip_Type.round()
df_trip.insert(loc=0, column='IdTrip', value=np.arange(len(df_trip)))

# -- Payment --#
df_payment = df[['RatecodeID', 'payment_type', 'fare_amount', 'extra', 'mta_tax',
                 'improvement_surcharge', 'tolls_amount', 'total_amount']]

df_payment.insert(loc=0, column='IdTrip', value=df_trip['IdTrip'])
df_payment.insert(loc=0, column='IdPayment', value=np.arange(len(df_payment)))

# -- Outlier -- #
df_outliers = df_outliers[['Unnamed: 0']]

# -- Renombrar Columnas - Normalizar --#
df_calendar.columns = ['iddate', 'date', 'year', 'month', 'day', 'week', 'day_of_week']

df_trip.columns = ['idtrip', 'idvendor', 'iddate', 'pu_time', 'duration', 'passenger_count',
                    'distance', 'pu_idzone', 'do_idzone', 'temperature', 'idprecip_type']

df_payment.columns = ['idpayment', 'idtrip', 'idrate_code', 'idpayment_type', 'fare_amount',
                    'extra', 'mta_tax', 'improvement_surcharge', 'tolls_amount', 'total_amount']

df_outliers.columns = ['idrecord']

# -- Exportar a archivos CSV --#

df_calendar.to_csv('../tables/calendar_i.csv', index=False)
df_trip.to_csv('../tables/trip_i.csv', index=False)
df_payment.to_csv('../tables/payment_i.csv', index=False)
df_outliers.to_csv('../tables/outlier_i.csv', index=False)
