from datetime import datetime, timedelta
from cognite.client import CogniteClient, ClientConfig, global_config
from cognite.client.credentials import APIKey
import time
import psycopg2
import schedule
import json
from dotenv import load_dotenv
from pathlib import Path
import os


# VARIABILA DE TIMP PENTRU REFRESHul DB
refresh_time = 8 # days

# DATABASE INFO
dotenv_path = Path("envFiles/databaseInfo.env")
load_dotenv(dotenv_path=dotenv_path)
hostname = os.getenv('hostname')
database = os.getenv('databaseName')
username = os.getenv('username')
pwd = os.getenv('password')
port_id = os.getenv('portID')

# AUTENTIFICARE COGNITE
dotenv_path = Path("envFiles/cogniteClientInfo.env")
load_dotenv(dotenv_path=dotenv_path)
api_key = os.getenv('APIKey')
client_name = os.getenv('clientName')
project_name = os.getenv('projectName')
config = ClientConfig(client_name = client_name, project = project_name, credentials = APIKey(api_key))
c = CogniteClient(config)

# FUNCTIE DE ADAUGAT ASSET-urile in DB(NUMELE ASSET-ului, ASSET ID-ul SI STAREA DE UTILIZARE)
def add_asset_to_db(asset):
    cursor, connection = None, None
    try:
        connection = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cursor = connection.cursor()
        insert_script = 'INSERT INTO assets_info (asset_id,asset_name,is_used) VALUES (%s,%s,%s)'
        insert_data = (asset[0], asset[1], asset[2])
        cursor.execute(insert_script, insert_data)
        connection.commit()
    except Exception as error:
        print(error)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

#FUNCTIE DE UPDATE AL INFORMATILOR DESPRE UN ASSET IN FUNCTIE DE ID
def update_asset_info(asset_in_json):
    cursor, connection = None, None
    update_script = f'''UPDATE assets_info SET asset_name='{asset_in_json.get('assetName')}', is_used='{asset_in_json.get('isUsed')}' WHERE asset_id = {asset_in_json.get('assetID')}'''
    try:
        connection = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cursor = connection.cursor()
        cursor.execute(update_script)
        connection.commit()
    except Exception as error:
        print(error)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


#FUNCTIE CARE VERIFICA DACA UN ASSET CARE ESTE IN DB ESTE PREZENT SI IN JSON
def check_for_deletion(json_assets):
    json_ids = []
    for asset in json_assets:
        json_ids.append(int(json_assets[f'{asset}'].get('assetID')))
    for id in get_assets_id_in_db(all):
        if id not in json_ids:
            cursor, connection = None, None
            try:
                connection = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
                cursor = connection.cursor()
                update_script = f'''UPDATE assets_info SET is_used='false' WHERE asset_id = {id}'''
                cursor.execute(update_script)
                connection.commit()
            except Exception as error:
                print(error)
            finally:
                if cursor is not None:
                    cursor.close()
                if connection is not None:
                    connection.close()

# FUNCTIE DE UPDATE al ASSET-urilor in DB (ADAUGARE/MODIFICARE)
def refresh_assets_info(assets_list):
    cursor, connection = None, None
    try:
        connection = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cursor = connection.cursor()
        assets_id_in_db =  get_assets_id_in_db("all")
        for asset in assets_list:
            if int(assets_list[f'{asset}'].get('assetID')) not in assets_id_in_db:
                add_asset_to_db([assets_list[f'{asset}'].get('assetID'), assets_list[f'{asset}'].get('assetName'), 
                assets_list[f'{asset}'].get('isUsed')])
            else:
                update_asset_info(assets_list[f'{asset}'])
        check_for_deletion(assets_list)
    except Exception as error:
        print(error)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
        print("UPDATED ASSETS INFO")

# FUNCTIE CARE RETURNEAZA O LISTA CU TOATE ID-urile ASSET-urilor DIN TABELA assets_info
def get_assets_id_in_db(type):
    if type == "only_used_assets":
        script = 'SELECT asset_id FROM assets_info WHERE is_used=true'
    else:
        script = 'SELECT asset_id FROM assets_info'
    cursor, connection = None, None
    try:
        connection = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cursor = connection.cursor()
        cursor.execute(script)
        assets_in_db = [int(id[0]) for id in cursor.fetchall()]
    except Exception as error:
        print(error)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
        return assets_in_db

# FUNCTIE DE EXTRAGERE IN FORMAT DE LISTA A VALORILOR DIN COGNITEDB IMPREUNA CU ORA, DATA SI ASSET ID-ul
def get_datapoints_list_format(datapoints_id, asset_id):
    datapoints = c.datapoints.retrieve(id=datapoints_id, start=datetime.now(
    )-timedelta(days=refresh_time), end=datetime.now())
    data_list = []
    #i = 0
    for data in datapoints:
        #i += 1
        data_to_dump = []
        data_to_dump.append(time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(data.timestamp/1000)))
        data_to_dump.append(data.value)
        data_to_dump.append(asset_id)
        data_list.append(data_to_dump)
        #if i == 5:
            #break
    print("GOT NEW DATA LIST")
    return data_list


# FUNCTIE DE ADAUGARE A DATELOR IN DB
def transfer_datapoints_to_db(assets_data):
    cursor, connection = None, None
    counter = 0
    try:
        connection = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cursor = connection.cursor()
        insert_script = 'INSERT INTO datapoints_info (timestamp,value,asset_id) VALUES (%s,%s,%s)'
        for data in assets_data:
            for individual_data in data:
                insert_data = (
                    individual_data[0], individual_data[1], individual_data[2])
                counter += 1
                cursor.execute(insert_script, insert_data)
        connection.commit()
    except Exception as error:
        print(error)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
        print(f"ADDED NEW DATA TO DB\nNumber of entries: {counter}")

# FUNCTIE PRINCIPALA - APELEAZA FUNCTIILE NECESARE PENTRU UPDATE-ul DB-ului
def add_new_datapoints_to_db():
    print("\nStarted script")
    astInf = open('jsonFiles/assets.json')
    assets_list = json.load(astInf)
    refresh_assets_info(assets_list)
    active_assets_id = get_assets_id_in_db("only_used_assets")
    assets_data = []
    for asset in assets_list:
        if int(assets_list[f'{asset}'].get('assetID')) in active_assets_id:
            assets_data.append(get_datapoints_list_format(int(assets_list[f'{asset}'].get('datapointsID')), 
            int(assets_list[f'{asset}'].get('assetID'))))
    transfer_datapoints_to_db(assets_data)
    print("FINISHED SCRIPT")

#FUNCTIE CARE VERIFICA DACA EXISTA TABELELE NECESARE IN DB, IAR IN CAZUL IN CARE ACESTEA NU EXISTA, SUNT CREATE
def create_tables():
    cursor, connection = None, None
    try:
        connection = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cursor = connection.cursor()
        script = ("""CREATE TABLE IF NOT EXISTS public.assets_info
                                    (
                    id integer NOT NULL GENERATED BY DEFAULT AS IDENTITY ( CYCLE INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
                    asset_id bigint NOT NULL,
                    asset_name character varying(256) COLLATE pg_catalog."default" NOT NULL,
                    is_used boolean NOT NULL,
                    CONSTRAINT assets_info_pkey PRIMARY KEY (id),
                    CONSTRAINT assets_info_asset_id_key UNIQUE (asset_id)
                )""","""CREATE TABLE IF NOT EXISTS public.datapoints_info
                (
                    id integer NOT NULL GENERATED BY DEFAULT AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
                    "timestamp" timestamp without time zone NOT NULL,
                    value double precision NOT NULL,
                    asset_id bigint NOT NULL,
                    CONSTRAINT datapoints_info_pkey PRIMARY KEY (id),
                    CONSTRAINT datapoints_info_id_asset_fkey FOREIGN KEY (asset_id)
                        REFERENCES public.assets_info (asset_id) MATCH SIMPLE
                        ON UPDATE NO ACTION
                        ON DELETE NO ACTION
                )""")
        for command in script:
            cursor.execute(command)
            connection.commit()
    except Exception as error:
        print(error)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

# APELARI INITIALE
create_tables()
add_new_datapoints_to_db()

# SCHEDULER CARE APELEAZA FUNCTIA PRINCIPALA LA UN TIMP DICTAT DE VARIABILA REFRESH TIME
schedule.every(refresh_time).days.do(add_new_datapoints_to_db)
while True:
    schedule.run_pending()
    time.sleep(1)