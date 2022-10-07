from datetime import datetime, timedelta
from operator import itemgetter
from statistics import mean
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import urllib.parse
import numpy as np
from flask import Flask, jsonify, redirect, url_for, session, request
from flask_dance.consumer import OAuth2ConsumerBlueprint, oauth_authorized
from functools import wraps
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from werkzeug.middleware.proxy_fix import ProxyFix
import os 
from dotenv import load_dotenv
from pathlib import Path
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


# DATABASE INFO
dotenv_path = Path("envFiles/databaseInfo.env")
load_dotenv(dotenv_path=dotenv_path)
hostname = os.getenv('hostname')
database = os.getenv('databaseName')
username = os.getenv('username')
pwd = os.getenv('password')
port_id = os.getenv('portID')

# CREAREA APLICATIEI FLASK SI SETUPul DBului
app = Flask(__name__, template_folder='../FrontEnd/templates',static_folder='../static')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{pwd}@{hostname}:{port_id}/{database}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
asset = db.Table('assets_info', db.metadata, autoload=True, autoload_with=db.engine)
data = db.Table('datapoints_info', db.metadata, autoload=True, autoload_with=db.engine)


# KEYCLOAK
dotenv_path = Path("envFiles/keycloak.env")
load_dotenv(dotenv_path=dotenv_path)
client_id = os.getenv('client_id')
client_secret= os.getenv('client_secret')
base_url=os.getenv('base_url')
token_url=os.getenv('token_url')
authorization_url= os.getenv('authorization_url')
secret = os.getenv('secret_key')

example_blueprint = OAuth2ConsumerBlueprint(
    "oauth-example", __name__,
    client_id=client_id,
    client_secret=client_secret,
    base_url=base_url,
    token_url=token_url,
    authorization_url=authorization_url,
)

app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = secret
app.register_blueprint(example_blueprint, url_prefix="/login")

def auth_required(func):
    @wraps(func)
    def check_authorization(*args, **kwargs):
## Check if authorized or token expired and authenticate if necessary"""        
        token = example_blueprint.session.token        
        if not example_blueprint.session.authorized or token["expires_in"] < 0:
## Store current route before redirecting so we can return after successful auth            
            session["next_url"] = request.full_path            
            return redirect(url_for("oauth-example.login"))
        return func(*args, **kwargs)
    return check_authorization

@app.route('/session', methods=['GET'])
def get_session():
    token = example_blueprint.session.token        
    if not example_blueprint.session.authorized or token["expires_in"] < 0:
        return '', 511
    return '', 200

@oauth_authorized.connect
def redirect_to_next_url(blueprint, token):
## Allows the callback url to be dynamic without having to register each protected endpoint as a redirect with OAuth2ConsumerBlueprint. 
    blueprint.token = token    
    next_url = session["next_url"]
    return redirect("http://localhost:9090/frontend/assets.html")

@app.errorhandler(TokenExpiredError)
def token_expired(_):
## Retrigger the OAuth flow to get a new token."    
    del app.blueprints["oauth-example"].token
    redirect(url_for('oauth-example.login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(f"http://keycloak:8080/realms/Cognite/protocol/openid-connect/logout?post_logout_redirect_uri=http://localhost:9090/frontend/index.html&client_id={client_id}")


#ENDPOINT PENTRU TRANSMITEREA ASSETurilor DIN DB IN FORMAT JSON
@app.route('/assets', methods=['GET'])
@auth_required
def assets():
    results = db.session.query(asset).all()
    output = []
    for asst in results:
        asset_info = {'name': asst.asset_name,'id' : asst.asset_id, 'used': asst.is_used}
        output.append(asset_info)
    return jsonify(output)

#FUNCTIE DE DETECTARE A OUTLIERelor
def getValuesWithOutliers(data):
    data_outliers = data
    values = []
    for list in data:
        values.append(list[1])
    mean = np.mean(values)
    threshold = 1
    standard_deviation =np.std(values)
    i=0
    for value in values:
        z_score= (value - mean)/standard_deviation 
        if np.abs(z_score) > threshold:
            data_outliers[i].append(1)
        else:
            data_outliers[i].append(0)
        i+=1
    return data_outliers

#FUNCTIE DE INTERPOLARE A DATELOR LA O ANUMITA RATA SPECIFICATA
def interpolation(data,rate,outlier_detection):
    values_with_time = []
    interpolation_rate = len(data)/rate
    if interpolation_rate < 1:
        interpolation_rate = 1
    values_for_interpolation = []
    i = 0
    for value in data:
        i +=1            
        if i > interpolation_rate:
                values_with_time.append([value[1],mean(values_for_interpolation)])
                i = 0
                values_for_interpolation = []
        else:
                values_for_interpolation.append(value[0])
    if outlier_detection == 'NO':
        return sorted(values_with_time,key=itemgetter(0))
    else: 
        if outlier_detection == 'YES':
            return getValuesWithOutliers(sorted(values_with_time,key=itemgetter(0)))

#FUNCTIE DE EXTRAGERE A DATELOR CALENDARISTICE DIN PARAMETRUL PRIMIT DE ENDPOINT
def date_separator(date_range):
    list  = date_range.split()
    start_date = datetime.strptime(list[0], '%m/%d/%Y')
    end_date = datetime.strptime(list[2], '%m/%d/%Y')
    return start_date,end_date

#FUNCTIE CARE RETURNEAZA DATAPOINTurile SAU MEDIA/MAXIMUL/MINIMUL UNUI ASSET IN FUNCTIE DE ID PE O ANUMITA PERIOADA SELECTATA
def getValues(asset_id,choice,start,end,interpolation_rate,outlier_detection):
    results = db.session.query(data).filter_by(asset_id=asset_id).all()
    values = []
    values_with_time = []
    try:
        if not isinstance(start,datetime) and not isinstance(end,datetime):
            raise ValueError("Not datetime")
    except(ValueError,IndexError):
        return {"value":ValueError}
    if choice in ['average','maximum','minimum','all']:
        for value in results:
            if datetime.strptime(str(value.timestamp), '%Y-%m-%d %H:%M:%S') > start and datetime.strptime(str(value.timestamp), '%Y-%m-%d %H:%M:%S') < end:
                values.append(value.value)
                values_with_time.append([value.value,value.timestamp.date()])
        if values:
            match choice:
                case "average":
                    return mean(values)
                case "maximum":
                    return max(values)
                case "minimum":
                    return min(values)
                case "all":
                    return interpolation(values_with_time,interpolation_rate,outlier_detection)

        else:
            return f"NoData"
    else:
        return "wrong choice"

#ENDPOINT PENTRU DATAPOINTuri sau OPERATII PE DATAPOINTurile UNUI ASSET
@app.route('/datapoints', methods=['GET'])
def datapoints():
    asset_id = request.args.get('id')
    choice = request.args.get('choice')
    interpolation_rate = int(request.args.get('int_rate'))
    date_range = urllib.parse.unquote(request.args.get('range'))
    outlier_detection = request.args.get('outliers')
    date_list = date_separator(date_range)
    values = getValues(asset_id,choice,date_list[0],date_list[1],interpolation_rate,outlier_detection)
    return {"value":values}
    

if __name__ == '__main__':
    CORS(app)
    app.run(host = "0.0.0.0", debug=True)