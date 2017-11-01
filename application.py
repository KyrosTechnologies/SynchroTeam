#!flask/bin/python
import sys
sys.path.insert(0, "/sites/flaskfirst")
from random import randint
import jwt 
from flask_security import auth_token_required,Security
from flask import Flask, session, jsonify, abort, request, make_response, url_for
# from flask_httpauth import HTTPBasicAuth
from database import DatabaseHelper
import datetime 
from flask_mongoengine import MongoEngine, MongoEngineSessionInterface
from bson import json_util, ObjectId
import json
from functools import wraps
from flask_mail import Mail,Message
import random
import string
from flask_cors import CORS

# app = Eve(settings='settings.py')
# Flask
flask = Flask(__name__)
application= api = Flask(__name__, static_url_path="")
application.config['WTF_CSRF_ENABLED'] = False
application.config['SECRET_KEY'] = 'super-secret'
application.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = 'mrjsiva25@gmail.com',
    MAIL_PASSWORD = 'l0rdmurug@gmail'
)
if "application.py" == sys.argv[0]:
    db = DatabaseHelper()
else:
    db = DatabaseHelper()  # if running unit tests

security=Security(application,db)
mail = Mail(application)
CORS(application)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        

        token = request.headers['Authorization'].encode('ascii','ignore')   

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 403

        try: 
            data = jwt.decode(token,'super-secret',algorithm='HS256')
        except:
            return jsonify({'message' : 'Token is invalid!'}), 403

        return f(*args, **kwargs)

    return decorated


@application.route('/domain/register', methods=['POST'])
def register_domain():
    firstname = request.json["firstName"]
    lastname = request.json["lastName"]
    companyname = request.json["companyName"]
    email = request.json["email"]
    telephoneNumber = request.json["phone"]
    domainName = request.json["domain"]
    created_at=datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    username=email.split('@')[0]
    password=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    siteAddress="https://"+domainName+".synchroteam.com"
    user_info={"firstName":firstname,"lastName":lastname,"email":email,"profile":"admin","isVerified":False,"phone":telephoneNumber,"username":username,"password":password}
    company_info={"company":companyname,"domain":domainName,"site":siteAddress}
    domain=db.retrieve_domain_by_domainname(domainName)
    if (domain is None) or (len(domain) == 0):
        result=db.insert_domain_to_db(user_info,company_info,username,password,created_at)
    else:
        return jsonify('domain already exist')
    # bi =  BinData(3,str(result));  
    if result == "User Already exists":
        return jsonify({'user':result })
    else:
        try:
            mail_status=send_mail(email,username,password) 
        except: 
            mail_status='mail is not valid'
        # domain=db.retrieve_domain_by_domain_id(bi)
        return jsonify({'user':mail_status })

@application.route('/domain/getById/<user_id>',methods=['GET'])
def get_domain(user_id):
    user = db.retrieve_domain_by_domain_id(user_id)
    if (user is None) or (len(user) == 0):
        abort(404)
    return jsonify({'user': json.loads(json_util.dumps(user))})


def send_mail(email,username,password):
    msg = mail.send_message(
        'Welcome to Synchroteam',
        sender='mrjsiva25@gmail.com',
        recipients=[email],
        body="Congratulations you've succeeded with registeration! \n here is ur password and user name \n"+username+"\n"+password
    )
    return 'Mail sent'

def make_public_task(task):
    new_task = {}
    for field in task:
        if field == '_id':
            # new_task['uri'] = url_for('get_task', user_id=task['_id'],_external=True)
            m_id=task['_id']
            new_task['id']=m_id['$oid']
        else:
            new_task[field] = task[field]
    return new_task


#1
""" METHODS FOR USERS COLLECTIONS  """


@application.route('/users/add', methods=['POST'])
@token_required
def register_user():
    profile = request.json["profile"]
    username = request.json["username"]
    password = request.json["password"]
    created_at=datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    user=db.retrieve_user_by_username(username)
    if(profile is None) :
         return jsonify('profile field is required')
    else:
        if (user is None) or (len(user) == 0):
            db.create_non_existing_user_to_database(username,password,created_at,request.json)
        else:
            return jsonify('User already exist')

    user=db.retrieve_user_by_username(username)
    return jsonify('user',json.loads(json_util.dumps(user)))

@application.route('/users/getById/<user_id>',methods=['GET'])
@token_required
def get_user(user_id):
    user = db.retrieve_user_by_user_id(user_id)
    if (user is None) or (len(user) == 0):
        abort(404)
    # return jsonify({'user': json.loads(json_util.dumps(user))})
    return jsonify([make_public_task(json.loads(json_util.dumps(user)))])


@application.route('/users/login',methods=['POST'])
def login():
    username = request.json["username"]
    password = request.json["password"]
    result=db.check_password_hash_for_user(username,password)
    user=db.retrieve_user_by_username(username)
    if result == False or (user is None) or (len(user) == 0):
        return jsonify({'result':result,'userDetails':'User or password doesnot match'})
    token = jwt.encode({'user' :username},'super-secret',algorithm='HS256')
    token_JSON={'token':token.decode('UTF-8')}

    user.update(token_JSON)
    return jsonify({'result':result,'userDetails':make_public_task(json.loads(json_util.dumps(user)))})

@application.route('/users/logout')
def logout():
	session['logged_in']=False
	return jsonify('You were logged out')

@application.route('/users/getAll',methods=['GET'])
@token_required
def getall():
	users=[]
	for user in  db.retrieve_users():
		users.append(make_public_task(json.loads(json_util.dumps(user))))
	return jsonify(users)
    # return jsonify([make_public_task(users)])

@application.route('/users/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def getall_by_domain_id(domain_id):
    users=[]
    for user in  db.retrieve_user_by_domain_id(domain_id):
        users.append(json.loads(json_util.dumps(user)))
    return jsonify({'users':users})

@application.route('/users/getTechnicians',methods=['GET'])
@token_required
def getTechnicians():
    users=[]
    for user in  db.get_technicians():
        users.append(json.loads(json_util.dumps(user)))
    return jsonify({'technicians':users})

@application.route('/users/getManagers',methods=['GET'])
@token_required
def getManagers():
    users=[]
    for user in  db.get_managers():
        users.append(json.loads(json_util.dumps(user)))
    return jsonify({'managers':users})

@application.route('/users/update/<user_id>',methods=['PUT'])
@token_required
def update_user(user_id):
    user = db.retrieve_user_by_user_id(user_id)
    if (user is None) or (len(user) == 0):
        abort(404)
    user_info=request.json
    result=db.find_and_update_user(user_id,user_info)
    return jsonify({'result': result})	


@application.route('/users/changePassword/<user_id>',methods=['PUT'])
@token_required
def changePassword(user_id):
    password=request.json["password"]
    db.changepassword(user_id,password)
    user = db.retrieve_user_by_user_id(user_id)
    if (user is None) or (len(user) == 0):
        abort(404)
    return jsonify( json.loads(json_util.dumps(user)))

@application.route('/users/forgetPassword',methods=['PUT'])
@token_required
def forgetPassword():
    email=db.retrieve_user_by_email(request.json["email"])
    if (email is None) or (len(email) == 0):
        abort(404)  
    password=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    db.changepassword(str(email["_id"]),password)
    try:
        mail_status=send_mail(email,username,password) 
    except: 
        mail_status='mail is not valid'
    return jsonify({'user':mail_status })    

#2
"""   METHODS FOR CUSTOMERS COLLECTION  """



@application.route('/customers/send', methods=['POST'])
@token_required
def send_customer():
    name = request.json["name"]
    customer=db.retrieve_customer_by_customername(name)
    if (customer is None) or (len(customer) == 0):
        db.insert_customer_to_db(request.json)
    else:
        return jsonify('Customer already exist')
    customer=db.retrieve_customer_by_customername(name)
    return jsonify({'customer':json.loads(json_util.dumps(customer))})

@application.route('/customers/list',methods=['GET'])
@token_required
def list_customers():
    customers=[]
    for customer in db.retrieve_customers():
        customers.append(json.loads(json_util.dumps(customer)))
    return jsonify({'customers':customers})

@application.route('/customers/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def list_customers_by_domain_id(domain_id):
    customers=[]
    for customer in db.retrieve_customer_by_domain_id(domain_id):
        customers.append(json.loads(json_util.dumps(customer)))
    return jsonify({'customers':customers})

@application.route('/customers/delete/<cust_id>',methods=['DELETE'])
@token_required
def delete_customer(cust_id):
    db.remove_customer_by_id(cust_id)
    return jsonify({'result':True})

@application.route('/customers/getByInfo',methods=['POST'])
@token_required
def get_customers_deatils():
    info={}
    for key,value in request.json.items():
        info[key]=value
    customers=[]
    for customer in {"result":"No Result Found"} if (db.retrieve_customers_by_info(info) is None)  else db.retrieve_customers_by_info(info):
        customers.append(json.loads(json_util.dumps(customer)))
    return jsonify({'customers':customers})

@application.route('/customers/update/<customer_id>',methods=['PUT'])
@token_required
def update_customer(customer_id):
    customer = db.retrieve_customer_by_customer_id(customer_id)
    if (customer is None) or (len(customer) == 0):
        abort(404)
    customer_info=request.json
    result=db.find_and_update_customer(customer_id,customer_info)
    return jsonify({'result': result})  

#3
""" METHODS FOR ACTIVITY_TYPES COLLECTION """


@application.route('/activity_types/send',methods=['POST'])
@token_required
def send_activity_types():
    activity_name=request.json["name"]
    activity_type=db.retrieve_activity_type_by_activity_typename(activity_name)
    if (activity_type is None) or (len(activity_type) == 0):
        db.insert_activity_type_to_db(request.json)
    else:
        return jsonify('activity type already exist')
    activity_type=db.retrieve_activity_type_by_activity_typename(activity_name)
    # db.ActivityType.update({'_id': activity_type.get('_id')},{'$set':{"m_id":activity_type.get('_id')}},False,True)
    return jsonify({'activity_type':activity_type})

@application.route('/activity_types/delete/<act_id>',methods=['DELETE'])
@token_required
def delete_activity_type(act_id):
    db.remove_activity_type_by_id(act_id)
    return jsonify({'result':True})

@application.route('/activity_types/getAll',methods=['GET'])
@token_required
def get_all_activity_type():
    act_types=[]
    for act_type in  db.retrieve_activity_types():
        act_types.append(json.loads(json_util.dumps(act_type)))
    return jsonify({'activity_types':act_types})
    
@application.route('/activity_types/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_activity_type(domain_id):
    act_types=[]
    for act_type in  db.retrieve_activity_type_by_domain_id(domain_id):
        act_types.append(json.loads(json_util.dumps(act_type)))
    return jsonify({'activity_types':act_types})

@application.route('/activity_types/update/<act_id>',methods=['PUT'])
@token_required
def update_activity_type(act_id):
    act_type = db.retrieve_activity_type_by_activity_type_id(act_id)
    if (act_type is None) or (len(act_type) == 0):
        abort(404)
    activity_type_info=request.json
    result=db.find_and_update_activity_type(act_id,activity_type_info)
    return jsonify({'result': result})


#4
""" METHODS FOR STOCK PARTS """



@application.route('/stock_parts/send',methods=['POST'])
@token_required
def send_stock_parts():
    name = request.json["name"]
    tax_id=request.json['taxId']
    stock_part=db.retrieve_stock_part_by_stock_partname(name)
    if (stock_part is None) or (len(stock_part) == 0):
        tax=db.retrieve_tax_by_tax_id(tax_id)
        if (tax is None) or (len(tax) == 0):
            return jsonify({'result':'tax you have mentioned is not available'})
        else:
            db.insert_stock_part_to_db(request.json)
    else:
        return jsonify('stock part already exist')
    stock_part=db.retrieve_customer_by_customername(name)
    # db.StockParts.update({'_id': stock_part.get('_id')},{'$set':{"m_id":stock_part.get('_id')}},False,True)
    return jsonify({'stock_part':json.loads(json_util.dumps(stock_part))})

@application.route('/stock_parts/getAll',methods=['GET'])
@token_required
def get_all_stock_parts():
    stock_parts=[]
    for stock_part in  db.retrieve_stock_parts():
        stock_parts.append(json.loads(json_util.dumps(stock_part)))
    return jsonify({'stock_parts':stock_parts})

@application.route('/stock_parts/getByInfo',methods=['POST'])
@token_required
def get_stock_part_deatils():
    # result=db.retrieve_customers_by_info(info)
    info={}
    for key,value in request.json.items():
        info[key]=value
    stock_parts=[]
    for stock_part in {"result":"No Result Found"} if (db.retrieve_stock_parts_by_info(info) is None)  else db.retrieve_stock_parts_by_info(info):
        stock_parts.append(json.loads(json_util.dumps(stock_part)))
    return jsonify({'stock_parts':stock_parts})


@application.route('/stock_parts/delete/<stock_part_id>',methods=['DELETE'])
@token_required
def delete_stock_part(stock_part_id):
    db.remove_stock_part_by_id(stock_part_id)
    return jsonify({'result':True})

@application.route('/stock_parts/list',methods=['GET'])
@token_required
def listStockParts():
    stock_parts=[]
    for stock_part in db.retrieve_stock_parts():
        stock_parts.append(json.loads(json_util.dumps(stock_part)))
    return jsonify({'stock_parts':stock_parts})

@application.route('/stock_parts/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def listStockParts_by_domqin_id(domain_id):
    stock_parts=[]
    for stock_part in db.retrieve_stock_part_by_domain_id(domain_id):
        stock_parts.append(json.loads(json_util.dumps(stock_part)))
    return jsonify({'stock_parts':stock_parts})

@application.route('/stock_parts/update/<stock_part_id>',methods=['PUT'])
@token_required
def update_stock_part(stock_part_id):
    stock_part = db.retrieve_stock_part_by_stock_part_id(stock_part_id)
    if (stock_part is None) or (len(stock_part) == 0):
        abort(404)
    stock_part_info=request.json
    result=db._update_stock_part(stock_part_id,stock_part_info)
    return jsonify({'result': result})



#5
""" METHODS FOR TEAMS """



@application.route('/teams/add',methods=['POST'])
@token_required
def add_team():
    name = request.json["name"]
    team=db.retrieve_team_by_teamname(name)
    if (team is None) or (len(team) == 0):
        db.insert_team_to_db(request.json)
    else:
        return jsonify('team already exist')
    team=db.retrieve_team_by_teamname(name)
    return jsonify({'team':json.loads(json_util.dumps(team))})

@application.route('/teams/getAll',methods=['GET'])
@token_required
def getall_teams():
    teams=[]
    for team in  db.retrieve_teams():
        teams.append(json.loads(json_util.dumps(team)))
    return jsonify({'teams' :teams})

@application.route('/teams/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_teams(domain_id):
    teams=[]
    for team in  db.retrieve_team_by_domain_id(domain_id):
        teams.append(json.loads(json_util.dumps(team)))
    return jsonify({'teams' :teams})

@application.route('/teams/getById/<team_id>',methods=['GET'])
@token_required
def get_team(team_id):
    team = db.retrieve_team_by_team_id(team_id)
    if len(team) == 0:
        abort(404)
    return jsonify({'team':json.loads(json_util.dumps( team))})

@application.route('/teams/update/<team_id>',methods=['PUT'])
@token_required
def update_team(team_id):
    team = db.retrieve_team_by_team_id(team_id)
    if (team is None) or (len(team) == 0):
        abort(404)
    result =db._update_team(team_id,request.json)
    return jsonify({'result':result}) 

@application.route('/teams/delete/<team_id>',methods=['DELETE'])
@token_required
def delete_team(team_id):
    db.remove_team_by_id(team_id)
    return jsonify({'result':True})



#6
"""  METHODS OF ACTIVITIES """


@application.route('/activities/add',methods=['POST'])
@token_required
def add_activity():
    name = request.json["nmActivity"]
    dtstart=datetime.datetime.strptime(request.json['dtStart'], '%Y-%m-%d %I:%M %p')
    dtend=datetime.datetime.strptime(request.json['dtEnd'], '%Y-%m-%d %I:%M %p')
    request.json.update({'dateStart':dtstart,'dateEnd':dtend})
    activity=db.retrieve_activity_by_activityname(name)
    if (activity is None) or (len(activity) == 0):
        db.insert_activities_to_db(request.json)
    else:
        return jsonify({'result':'activity already exist'})
    activity=db.retrieve_activity_by_activityname(name)
    return jsonify({'activity':json.loads(json_util.dumps(activity))})

@application.route('/activities/getAll',methods=['GET'])
@token_required
def getall_activities():
    activities=[]
    for activity in  db.retrieve_activities():
        activities.append(json.loads(json_util.dumps(activity)))
    return jsonify({'activities': activities})

@application.route('/activities/getById/<activity_id>',methods=['GET'])
@token_required
def get_activity(activity_id):
    activity = db.retrieve_activity_by_activity_id(activity_id)
    if len(activity) == 0:
        abort(404)
    return jsonify({'activity':json.loads(json_util.dumps(activity))})

@application.route('/activities/getByUserId/<user_id>',methods=['GET'])
@token_required
def get_activity_user_id(user_id):
    activity = db.retrieve_activity_by_user_id(user_id)
    if (len is None):
        abort(404)
    return jsonify({'activity':json.loads(json_util.dumps(activity))})

@application.route('/activities/update/<activity_id>',methods=['PUT'])
@token_required
def update_activity(activity_id):
    activity = db.retrieve_activity_by_activity_id(activity_id)
    if (activity is None) or (len(activity) == 0):
        abort(404)
    result=db._update_activity(activity_id,request.json)
    activity_rslt = db.retrieve_activity_by_activity_id(activity_id)
    return jsonify({'result':json.loads(json_util.dumps(activity_rslt))}) 
 
@application.route('/activities/delete/<activity_id>',methods=['DELETE'])
@token_required
def delete_activity(activity_id):
    db.remove_activity_by_id(activity_id)
    return jsonify({'result':True})


#7
"""  METHODS OF JOBS """


@application.route('/jobs/add',methods=['POST'])
@token_required
def add_jobs():
    myId = request.json["myId"]
    job=db.retrieve_job_by_job_myId(myId)
    if (job is None) or (len(job) == 0):
        db.insert_jobs_to_db(request.json)
    else:
        return jsonify('job already exist')
    job=db.retrieve_job_by_job_myId(myId)
    return jsonify({'job':json.loads(json_util.dumps(job))})

@application.route('/jobs/getAll',methods=['GET'])
@token_required
def getall_jobs():
    jobs=[]
    for job in  db.retrieve_jobs():
        jobs.append(json.loads(json_util.dumps(job)))
    return jsonify({'jobs' : jobs})

@application.route('/jobs/getbyDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_jobs(domain_id):
    jobs=[]
    for job in  db.retrieve_job_by_domain_id(domain_id):
        jobs.append(json.loads(json_util.dumps(job)))
    return jsonify({'jobs' : jobs})

@application.route('/jobs/getById/<job_id>',methods=['GET'])
@token_required
def get_job(job_id):
    job = db.retrieve_job_by_job_id(job_id)
    if len(job) == 0:
        abort(404)
    return jsonify({'job':json.loads(json_util.dumps(job))})

@application.route('/jobs/update/<job_id>',methods=['PUT'])
@token_required
def update_job(job_id):
    job = db.retrieve_job_by_job_id(job_id)
    if (job is None) or (len(job) == 0):
        abort(404)
    db._update_job(job_id,request.json)
    result=db.retrieve_job_by_job_id(job_id)
    return jsonify({'jobs':json.loads(json_util.dumps(result))})

@application.route('/jobs/delete/<job_id>',methods=['DELETE'])
@token_required
def delete_job(job_id):
    db.remove_job_by_id(job_id)
    return jsonify({'result':True})



#8
"""  METHODS OF REGIONAL SETTINGS """

@application.route('/regional_settings/add',methods=['POST'])
@token_required
def add_setting():
    db.insert_regional_settings_to_db(request.json)
    setting=db.retrieve_settings()
    return jsonify({'regional_settings':json.loads(json_util.dumps(setting))})

@application.route('/regional_settings/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_all_settings(domain_id):
    settings=db.retrieve_settings_by_domain_id(domain_id)
    return jsonify({'regional_settings' :json.loads(json_util.dumps(settings))})

#9
"""  METHODS OF TAXES """



@application.route('/taxes/add',methods=['POST'])
@token_required
def add_taxes():
    name = request.json["name"]
    tax=db.retrieve_tax_by_tax_name(name)
    if (tax is None) or (len(tax) == 0):
        db.insert_taxes_to_db(request.json)
    else:
        return jsonify('tax already exist')
    tax=db.retrieve_tax_by_tax_name(name)
    return jsonify({'tax':json.loads(json_util.dumps(tax))})

@application.route('/taxes/getAll',methods=['GET'])
@token_required
def getall_taxes():
    taxes=[]
    for tax in  db.retrieve_taxes():
        taxes.append(json.loads(json_util.dumps(tax)))
    return jsonify({'taxes' :taxes})

@application.route('/taxes/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_taxes(domain_id):
    taxes=[]
    for tax in  db.retrieve_tax_by_domain_id(domain_id):
        taxes.append(json.loads(json_util.dumps(tax)))
    return jsonify({'taxes' :taxes})

@application.route('/taxes/getById/<tax_id>',methods=['GET'])
@token_required
def get_tax(tax_id):
    taxes = db.retrieve_tax_by_tax_id(tag_id)
    if len(tax) == 0:
        abort(404)
    return jsonify({'tax':json.loads(json_util.dumps(tax))})

@application.route('/taxes/update/<tax_id>',methods=['PUT'])
@token_required
def update_tax(tax_id):
    tax = db.retrieve_tax_by_tax_id(tax_id)
    if (tax is None) or (len(tax) == 0):
        abort(404)
    db._update_tax(tax_id,request.json)
    result=db.retrieve_tax_by_tax_id(tax_id)
    return jsonify({'tax':json.loads(json_util.dumps(result))})

@application.route('/taxes/delete/<tax_id>',methods=['DELETE'])
@token_required
def delete_tax(tax_id):
    db.remove_tax_by_id(tax_id)
    return jsonify('result',True)



#10
"""  METHODS OF TOOLS AND RESOURCES """



@application.route('/tools_and_resources/add',methods=['POST'])
@token_required
def add_toolsAndResources():
    name = request.json["resource_name"]
    resource=db.retrieve_toolsresource_by_resource_name(name)
    if (resource is None) or (len(resource) == 0):
        db.insert_toolsresources_to_db(request.json)
    else:
        return jsonify('resource already exist')
    resource=db.retrieve_toolsresource_by_resource_name(name)
    return jsonify({'resource':json.loads(json_util.dumps(resource))})

@application.route('/tools_and_resources/getAll',methods=['GET'])
@token_required
def getall_toolsAndResources():
    resources=[]
    for resource in  db.retrieve_toolsresources():
        resources.append(json.loads(json_util.dumps(resource)))
    return jsonify({'resources' :resources})

@application.route('/tools_and_resources/getById/<resource_id>',methods=['GET'])
@token_required
def get_toolsAndResource(resource_id):
    resource = db.retrieve_toolsresource_by_resource_id(resource_id)
    if len(resource) == 0:
        abort(404)
    return jsonify({'resource': json.loads(json_util.dumps(resource))})

@application.route('/tools_and_resources/update/<resource_id>',methods=['PUT'])
@token_required
def update_toolsAndResource(resource_id):
    resource = db.retrieve_toolsresource_by_resource_id(resource_id)
    if (resource is None) or (len(resource) == 0):
        abort(404)
    db._update_toolsresource(resource_id,request.json)
    result=db.retrieve_toolsresource_by_resource_id(resource_id)
    return jsonify({'resource': json.loads(json_util.dumps(result))})

@application.route('/tools_and_resources/delete/<resource_id>',methods=['DELETE'])
@token_required
def delete_toolsAndResource(resource_id):
    db.remove_toolsresource_by_id(resource_id)
    return jsonify('result',True)

@application.route('/tools_and_resources/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def getByDomainId_toolsAndResources(domain_id):
    resources=[]
    for resource in  db.retrieve_toolsresource_by_domain_id(domain_id):
        resources.append(json.loads(json_util.dumps(resource)))
    return jsonify({'resources' :resources})


#11
"""  METHODS OF JOB TYPES """



@application.route('/job_types/add',methods=['POST'])
@token_required
def add_job_types():
    name = request.json["job_type_name"]
    job_type=db.retrieve_jobtype_by_jobtype_name(name)
    if (job_type is None) or (len(job_type) == 0):
        db.insert_job_types_to_db(request.json)
    else:
        return jsonify('job_type already exist')
    job_type=db.retrieve_jobtype_by_jobtype_name(name)
    return jsonify({'job_type':json.loads(json_util.dumps(job_type))})

@application.route('/job_types/getAll',methods=['GET'])
@token_required
def getall_job_type():
    job_types=[]
    for job_type in  db.retrieve_job_types():
        job_types.append(json.loads(json_util.dumps(job_type)))
    return jsonify({'job_types' :job_types})

@application.route('/job_types/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_job_type(domain_id):
    job_types=[]
    for job_type in  db.retrieve_jobtype_by_domain_id(domain_id):
        job_types.append(json.loads(json_util.dumps(job_type)))
    return jsonify({'job_types' :job_types})

@application.route('/job_types/getById/<job_type_id>',methods=['GET'])
@token_required
def get_job_type(job_type_id):
    job_type = db.retrieve_jobtype_by_jobtype_id()
    if len(job_type) == 0:
        abort(404)
    return jsonify({'job_type':job_type})

@application.route('/job_types/update/<job_type_id>',methods=['PUT'])
@token_required
def update_job_type(job_type_id):
    job_type = db.retrieve_jobtype_by_jobtype_id(job_type_id)
    if (job_type is None) or (len(job_type) == 0):
        abort(404)
    db._update_job_type(job_type_id,request.json)
    result=db.retrieve_jobtype_by_jobtype_id(job_type_id)
    return jsonify({'job_types':json.loads(json_util.dumps(result))})

@application.route('/job_types/delete/<job_type_id>',methods=['DELETE'])
@token_required
def delete_job_type(job_type_id):
    db.remove_job_type_by_id(job_type_id)
    return jsonify({'result':True})



#12
"""  METHODS OF CUSTOM FIELDS """


@application.route('/custom_fields/add',methods=['POST'])
@token_required
def add_custom_fieldS():
    name = request.json["name"]
    custom_field=db.retrieve_custom_field_by_custom_field_name(name)
    if (custom_field is None) or (len(custom_field) == 0):
        db.insert_customFields_to_db(request.json)
    else:
        return jsonify('custom_field already exist')
    custom_field=db.retrieve_custom_field_by_custom_field_name(name)
    return jsonify({'custom_field':json.loads(json_util.dumps(custom_field))})

@application.route('/custom_fields/getAll',methods=['GET'])
@token_required
def getall_custom_fields():
    custom_fields=[]
    for custom_field in  db.retrieve_custom_fields():
        custom_fields.append(json.loads(json_util.dumps(custom_field)))
    return jsonify({'custom_fields' :custom_fields})

@application.route('/custom_fields/getById/<custom_field_id>',methods=['GET'])
@token_required
def get_custom_field(custom_field_id):
    custom_field = db.retrieve_custom_field_by_custom_field_id(custom_field_id)
    if len(custom_field) == 0:
        abort(404)
    return jsonify({'custom_field': json.loads(json_util.dumps(custom_field))})

@application.route('/custom_fields/update/<custom_field_id>',methods=['PUT'])
@token_required
def update_custom_field(custom_field_id):
    custom_field = db.retrieve_custom_field_by_custom_field_id(custom_field_id)
    if (custom_field is None) or (len(custom_field) == 0):
        abort(404)
    db._update_custom_field(custom_field_id,request.json)
    result=db.retrieve_custom_field_by_custom_field_id(custom_field_id)
    return jsonify({'custom_field':json.loads(json_util.dumps(result))})

@application.route('/custom_fields/delete/<custom_field_id>',methods=['DELETE'])
@token_required
def delete_custom_field(custom_field_id):
    db.remove_custom_field_by_id(custom_field_id)
    return jsonify({'result':True})




#13
"""  METHODS OF EQUIPMENTS """



@application.route('/equipments/add',methods=['POST'])
@token_required
def add_equipemnts():
    name = request.json["myId"]
    equipment=db.retrieve_equipment_by_equipment_name(name)
    if (equipment is None) or (len(equipment) == 0):
        db.insert_equipments_to_db(request.json)
    else:
        return jsonify('equipment already exist')
    equipment=db.retrieve_equipment_by_equipment_myId(name)
    return jsonify({'equipment':json.loads(json_util.dumps(equipment))})

@application.route('/equipments/getAll',methods=['GET'])
@token_required
def getall_equipments():
    equipments=[]
    for equipment in  db.retrieve_equipments():
        equipments.append(json.loads(json_util.dumps(equipment)))
    return jsonify({'equipments' : equipments})

@application.route('/equipments/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def getby_domain_id_equipments(domain_id):
    equipments=[]
    for equipment in  db.retrieve_equipment_by_domain_id(domain_id):
        equipments.append(json.loads(json_util.dumps(equipment)))
    return jsonify({'equipments' : equipments})


@application.route('/equipments/getById/<equipment_id>',methods=['GET'])
@token_required
def get_equipment(equipment_id):
    equipment = db.retrieve_equipment_by_equipment_id(equipment_id)
    if len(equipment) == 0:
        abort(404)
    return jsonify({'equipment':json.loads(json_util.dumps(equipment))})

@application.route('/equipments/update/<equipment_id>',methods=['PUT'])
@token_required
def update_equipment(equipment_id):
    equipment = db.retrieve_equipment_by_equipment_id(equipment_id)
    if (equipment is None) or (len(equipment) == 0):
        abort(404)
    db._update_equipment(equipment_id,request.json)
    result=db.retrieve_equipment_by_equipment_id(equipment_id)
    return jsonify({'equipment':json.loads(json_util.dumps(equipment))})

@application.route('/equipments/delete/<equipment_id>',methods=['DELETE'])
@token_required
def delete_equipment(equipment_id):
    db.remove_equipment_by_id(equipment_id)
    return jsonify({'result':True})





#14
"""  METHODS OF TAGS """



@application.route('/tags/add',methods=['POST'])
@token_required
def add_tags():
    name = request.json["name"]
    tag=db.retrieve_tag_by_tag_name(name)
    if (tag is None) or (len(tag) == 0):
        db.insert_tags_to_db(request.json)
    else:
        return jsonify('tag already exist')
    tag=db.retrieve_tag_by_tag_name(name)
    return jsonify({'tag':json.loads(json_util.dumps(tag))})

@application.route('/tags/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_tags(domain_id):
    tags=[]
    for tag in  db.retrieve_tag_by_domain_id(domain_id):
        tags.append(json.loads(json_util.dumps(tag)))
    return jsonify({'tags' : tags})

@application.route('/tags/getAll',methods=['GET'])
@token_required
def getall_tags():
    tags=[]
    for tag in  db.retrieve_tags():
        tags.append(json.loads(json_util.dumps(tag)))
    return jsonify({'tags' : tags})

@application.route('/tags/getById/<tag_id>',methods=['GET'])
@token_required
def get_tag(tag_id):
    tag = db.retrieve_tag_by_tag_id(tag_id)
    if len(tag) == 0:
        abort(404)
    return jsonify({'tag':json.loads(json_util.dumps(result))})

@application.route('/tags/update/<tag_id>',methods=['PUT'])
@token_required
def update_tag(tag_id):
    tag = db.retrieve_tag_by_tag_id(tag_id)
    if (tag is None) or (len(tag) == 0):
        abort(404)
    db._update_tag(tag_id,request.json)
    result=db.retrieve_tag_by_tag_id(tag_id)   
    return jsonify({'tag':json.loads(json_util.dumps(result))})

@application.route('/tags/delete/<tag_id>',methods=['DELETE'])
@token_required
def delete_tag(tag_id):
    db.remove_tag_by_id(tag_id)
    return jsonify({'result':True})


#15
"""  METHODS OF PROJECT TYPES """



@application.route('/project_types/add',methods=['POST'])
@token_required
def add_project_types():
    name = request.json["type_name"]
    project_type=db.retrieve_project_type_by_project_typename(name)
    if (project_type is None) or (len(project_type) == 0):
        db.insert_project_types_to_db(request.json)
    else:
        return jsonify('project_type already exist')
    project_type=db.retrieve_project_type_by_project_typename(name)
    return jsonify({'project_type':json.loads(json_util.dumps(project_type))})

@application.route('/project_types/getAll',methods=['GET'])
@token_required
def getall_project_types():
    project_types=[]
    for project_type in  db.retrieve_project_types():
        project_types.append(json.loads(json_util.dumps(project_type)))
    return jsonify({'project_types' : project_types})

@application.route('/project_types/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_project_types(domain_id):
    project_types=[]
    for project_type in  db.retrieve_project_type_by_domain_id(domain_id):
        project_types.append(json.loads(json_util.dumps(project_type)))
    return jsonify({'project_types' : project_types})

@application.route('/project_types/getById/<project_type_id>',methods=['GET'])
@token_required
def get_project_type(project_type_id):
    project_type = db.retrieve_project_type_by_project_type_id(project_type_id)
    if len(project_type) == 0:
        abort(404)
    return jsonify({'project_type':json.loads(json_util.dumps(project_type))})

@application.route('/project_types/update/<project_type_id>',methods=['PUT'])
@token_required
def update_project_type(project_type_id):
    project_type = db.retrieve_project_type_by_project_type_id(project_type_id)
    if (project_type is None) or (len(project_type) == 0):
        abort(404)
    db._update_project_type(project_type_id,request.json)
    result=db.retrieve_project_type_by_project_type_id(project_type_id)       
    return jsonify({'project_type':json.loads(json_util.dumps(result))})

@application.route('/project_types/delete/<project_type_id>',methods=['DELETE'])
@token_required
def delete_project_type(project_type_id):
    db.remove_project_type_by_id(project_type_id)
    return jsonify({'result':True})



#16
"""  METHODS OF ATTACHMENTS """



@application.route('/attachments/add',methods=['POST'])
@token_required
def add_attachments():
    name = request.json["fileName"]
    attachment=db.retrieve_attachment_by_attachment_name(name)
    if (attachment is None) or (len(attachment) == 0):
        db.insert_attachments_to_db(request.json)
    else:
        return jsonify('attachment already exist')
    attachment=db.retrieve_attachment_by_attachment_name(name)
    return jsonify({'attachment':json.loads(json_util.dumps(attachment))})

@application.route('/attachments/getAll',methods=['GET'])
@token_required
def getall_attachments():
    attachments=[]
    for attachment in  db.retrieve_attachments():
        attachments.append(json.loads(json_util.dumps(attachment)))
    return jsonify({'attachments':attachments})

@application.route('/attachments/getById/<attachment_id>',methods=['GET'])
@token_required
def get_attachment(attachment_id):
    attachment = db.retrieve_attachment_by_attachment_id(attachment_id)
    if len(attachment) == 0:
        abort(404)
    return jsonify({'attachment':json.loads(json_util.dumps(attachment))})

@application.route('/attachments/update/<attachment_id>',methods=['PUT'])
@token_required
def update_attachment(attachment_id):
    attachment = db.retrieve_attachment_by_attachment_id(attachment_id)
    if (attachment is None) or (len(attachment) == 0):
        abort(404)
    db._update_attachment(attachment_id,request.json)
    result=db.retrieve_attachment_by_attachment_id(attachment_id)          
    return jsonify({'attachment':json.loads(json_util.dumps(result))})

@application.route('/attachments/delete/<attachment_id>',methods=['DELETE'])
@token_required
def delete_attachment(attachment_id):
    db.remove_attachment_by_id(attachment_id)
    return jsonify({'result':True})


#17
"""  METHODS OF SITES """



@application.route('/sites/add',methods=['POST'])
@token_required
def add_sites():
    name = request.json["name"]
    site=db.retrieve_site_by_site_name(name)
    if (site is None) or (len(site) == 0):
        db.insert_sites_to_db(request.json)
    else:
        return jsonify('site already exist')
    site=db.retrieve_site_by_site_name(name)
    return jsonify({'site':json.loads(json_util.dumps(site))})

@application.route('/sites/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def getby_domain_id_sites(domain_id):
    sites=[]
    for site in  db.retrieve_site_by_domain_id(domain_id):
        sites.append(json.loads(json_util.dumps(site)))
    return jsonify({'sites' : sites})

@application.route('/sites/getAll',methods=['GET'])
@token_required
def getall_sites():
    sites=[]
    for site in  db.retrieve_sites():
        sites.append(json.loads(json_util.dumps(site)))
    return jsonify({'sites' : sites})

@application.route('/sites/getById/<site_id>',methods=['GET'])
@token_required
def get_site(site_id):
    site = db.retrieve_site_by_site_id(site_id)
    if len(site) == 0:
        abort(404)
    return jsonify({'site':json.loads(json_util.dumps(site))})

@application.route('/sites/update/<site_id>',methods=['PUT'])
@token_required
def update_site(site_id):
    site = db.retrieve_site_by_site_id(site_id)
    if (site is None) or (len(site) == 0):
        abort(404)
    db._update_site(site_id,request.json)
    result=db.retrieve_site_by_site_id(site_id)      
    return jsonify({'site':json.loads(json_util.dumps(site))})

@application.route('/sites/delete/<site_id>',methods=['DELETE'])
@token_required
def delete_site(site_id):
    db.remove_site_by_id(site_id)
    return jsonify({'result':True})



#18
"""  METHODS OF PROJECTS """



@application.route('/projects/add',methods=['POST'])
@token_required
def add_projects():
    name = request.json["custom_project_no"]
    project=db.retrieve_project_by_project_name(name)
    if (project is None) or (len(project) == 0):
        db.insert_projects_to_db(request.json)
    else:
        return jsonify('project already exist')
    project=db.retrieve_project_by_project_name(name)
    return jsonify({'project':json.loads(json_util.dumps(project))})

@application.route('/projects/getAll',methods=['GET'])
@token_required
def getall_projects():
    projects=[]
    for project in  db.retrieve_projects():
        projects.append(json.loads(json_util.dumps(project)))
    return jsonify({'projects' : projects})

@application.route('/projects/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_projects(domain_id):
    projects=[]
    for project in  db.retrieve_project_by_domain_id(domain_id):
        projects.append(json.loads(json_util.dumps(project)))
    return jsonify({'projects' : projects})

@application.route('/projects/getById/<project_id>',methods=['GET'])
@token required
def get_project(project_id):
    project = db.retrieve_project_by_project_id(project_id)
    if len(project) == 0:
        abort(404)
    return jsonify({'project':json.loads(json_util.dumps(project))})

@application.route('/projects/update/<project_id>',methods=['PUT'])
@token_required
def update_project(project_id):
    project = db.retrieve_project_by_project_id(project_id)
    if (project is None) or (len(project) == 0):
        abort(404)
    db._update_project(project_id,request.json)
    result=db.retrieve_project_by_project_id(project_id)      
    return jsonify({'project':json.loads(json_util.dumps(result))})

@application.route('/projects/delete/<project_id>',methods=['DELETE'])
@token_required
def delete_project(project_id):
    db.remove_project_by_id(project_id)
    return jsonify({'result':True})



#19
"""  METHODS OF USERJOBS """



@application.route('/userjobs/schedule',methods=['POST'])
@token_required
def add_userjobs():
    user_id= request.json["idUser"]
    job_id=request.json["idJob"]
    scheduledBeginDate=datetime.datetime.strptime(request.json["scheduledBeginDateString"], "%Y-%m-%d %I:%M %p")
    scheduledEndDate=datetime.datetime.strptime(request.json["scheduledEndDateString"], "%Y-%m-%d %I:%M %p")
    dateJson={"scheduledBeginDate":scheduledBeginDate,"scheduledEndDate":scheduledEndDate}
    if scheduledBeginDate > datetime.datetime.now() and scheduledBeginDate <scheduledEndDate :
        user = db.retrieve_user_by_user_id(user_id)
        job=db.retrieve_job_by_job_id(job_id)
        if (user is None) or (len(user) == 0): # whether user exists in Users
            return jsonify({'result':'user does not exist'})
        else:
            if (job is None) or (len(job) == 0): # whether job exists in JObs
                return jsonify({'result':'job does not exist'})
            else:
                userjobs=[]
                for userjob in  db.retrieve_jobs_by_user_id(user_id):
                    userjobs.append(json.loads(json_util.dumps(userjob)))
                if (userjobs is None) or (len(userjobs) == 0):
                    result=db.insert_userjobs_to_db(request.json,user_id,job_id)
                else:
                    for userjob in  db.retrieve_jobs_by_user_id(user_id):
                        # check status of userjob
                        if userjob["status"] == "completed" or userjob["status"] == "validated" or userjob["status"] == "cancelled":
                            pass
                        else:
                            # if user assigned with job check duration 
                            if userjob["scheduledBeginDate"] > scheduledBeginDate and userjob["scheduledEndDate"] > scheduledBeginDate :
                                pass
                                # if userjob["scheduledBeginDate"] < scheduledBeginDate and userjob["scheduledEndDate"] < scheduledBeginDate :
                                #     pass
                                # else:
                                #     return jsonify({'result':'User already Engaged with job'})
                            else:
                                return jsonify({'result':'User already Engaged with job'})
                            
                    # insert if duration is ellapsed or status is completed/validated/cancelled
                    request.json.update(dateJson)
                    result=db.insert_userjobs_to_db(request.json,user_id,job_id)
                    
        return jsonify({'result':json.loads(json_util.dumps(result))})
    else:
        return jsonify({'result':'scheduledEndDate is lesser than scheduledBeginDate '})

@application.route('/userjobs/getAll',methods=['GET'])
@token_required
def getall_userjobs():
    userjobs=[]
    for userjob in  db.retrieve_user_jobs():
        userjobs.append(json.loads(json_util.dumps(userjob)))
    return jsonify({'userjobs' : userjobs})

@application.route('/userjobs/getJobs/<user_id>',methods=['GET'])
@token_required
def getJobs_by_user_id(user_id):
    userjobs=[]
    for userjob in  db.retrieve_jobs_by_user_id(user_id):
        # user_info=db.retrieve_user_by_user_id(userjob['idUser'])
        job_info=db.retrieve_job_by_job_id(userjob['idJob'])
        jsonnew={"jobInfo":job_info}
        userjob.update(jsonnew)
        userjobs.append(json.loads(json_util.dumps(userjob)))
    return jsonify({'userjobs' : userjobs})

@application.route('/userjobs/getByInfo',methods=['POST'])
@token_required
def getJobs_by_info():
    info={}
    for key,value in request.json.items():
        info[key]=value
    userjobs=[]
    for userjob in {"result":"No Result Found"} if (db.retrieve_jobs_by_info(info) is None)  else db.retrieve_jobs_by_info(info):
        userjobs.append(json.loads(json_util.dumps(userjob)))
    return jsonify({'userjobs':userjobs})

@application.route('/userjobs/updateStatus/<userjob_id>',methods=['PUT'])
@token_required
def updateStaus(userjob_id):
    userjob = db.retrieve_userjob_by_userjob_id(userjob_id)
    if (userjob is None) or (len(userjob) == 0):
        abort(404)
    db.update_status(userjob_id,request.json)
    result=db.retrieve_userjob_by_userjob_id(userjob_id)      
    return jsonify({'userjob':json.loads(json_util.dumps(result))})

@application.route('/userjobs/updateStarted/<userjob_id>',methods=['PUT'])
@token_required
def updateStarted(userjob_id):
    userjob = db.retrieve_userjob_by_userjob_id(userjob_id)
    if (userjob is None) or (len(userjob) == 0):
        abort(404)
    db.update_started(userjob_id)
    result=db.retrieve_userjob_by_userjob_id(userjob_id)      
    return jsonify({'userjob':json.loads(json_util.dumps(result))})


@application.route('/userjobs/updatePaused/<userjob_id>',methods=['PUT'])
@token_required
def updatePaused(userjob_id):
    userjob = db.retrieve_userjob_by_userjob_id(userjob_id)
    if (userjob is None) or (len(userjob) == 0):
        abort(404)
    db.update_paused(userjob_id)
    result=db.retrieve_userjob_by_userjob_id(userjob_id)      
    return jsonify({'userjob':json.loads(json_util.dumps(result))})

@application.route('/userjobs/updateCompleted/<userjob_id>',methods=['PUT'])
@token_required
def updateCompleted(userjob_id):
    userjob = db.retrieve_userjob_by_userjob_id(userjob_id)
    if (userjob is None) or (len(userjob) == 0):
        abort(404)
    db.update_completed(userjob_id)
    result=db.retrieve_userjob_by_userjob_id(userjob_id)      
    return jsonify({'userjob':json.loads(json_util.dumps(result))})

@application.route('/userjobs/updateValidated/<current_user_id>/<userjob_id>',methods=['PUT'])
@token_required
def updateValidated(current_user_id,userjob_id):
    userjob = db.retrieve_userjob_by_userjob_id(userjob_id)
    if (userjob is None) or (len(userjob) == 0):
        abort(404)
    db.update_validated(current_user_id,userjob_id)
    result=db.retrieve_userjob_by_userjob_id(userjob_id)      
    return jsonify({'userjob':json.loads(json_util.dumps(result))})

@application.route('/userjobs/updateCancelled/<userjob_id>',methods=['PUT'])
@token_required
def updateCancelled(userjob_id):
    userjob = db.retrieve_userjob_by_userjob_id(userjob_id)
    if (userjob is None) or (len(userjob) == 0):
        abort(404)
    db.update_cancelled(userjob_id)
    result=db.retrieve_userjob_by_userjob_id(userjob_id)      
    return jsonify({'userjob':json.loads(json_util.dumps(result))})

@application.route('/userjobs/getCurrentJobs/<user_id>',methods=['GET'])
@token_required
def get_current_jobs(user_id):
    userjobs=[]
    for userjob in  db.retrieve_jobs_by_user_id(user_id):
        mydatetime=datetime.datetime.strptime(userjob["scheduledBeginDateString"], "%Y-%m-%d %I:%M %p")
        if(mydatetime.date()==datetime.datetime.today().date()):
            # user_info=db.retrieve_user_by_user_id(userjob['idUser'])
            job_info=db.retrieve_job_by_job_id(userjob['idJob'])
            jsonnew={"jobInfo":job_info}
            userjob.update(jsonnew)
            userjobs.append(json.loads(json_util.dumps(userjob)))        
    return jsonify({'userjobs' : userjobs})

@application.route('/userjobs/getLateJobs/<user_id>',methods=['GET'])
@token_required
def get_late_jobs(user_id):
    userjobs=[]
    for userjob in  db.retrieve_jobs_by_user_id(user_id):
        mydatetime=datetime.datetime.strptime(userjob["scheduledBeginDateString"], "%Y-%m-%d %I:%M %p")
        if(mydatetime.date()<datetime.datetime.today().date()):
            # user_info=db.retrieve_user_by_user_id(userjob['idUser'])
            job_info=db.retrieve_job_by_job_id(userjob['idJob'])
            jsonnew={"jobInfo":job_info}
            userjob.update(jsonnew)
            userjobs.append(json.loads(json_util.dumps(userjob)))    
    return jsonify({'userjobs' : userjobs})

@application.route('/userjobs/getUpcomingJobs/<user_id>',methods=['GET'])
@token_required
def get_upcoming_jobs(user_id):
    userjobs=[]
    for userjob in  db.retrieve_jobs_by_user_id(user_id):
        mydatetime=datetime.datetime.strptime(userjob["scheduledBeginDateString"], "%Y-%m-%d %I:%M %p")
        if(mydatetime.date()>datetime.datetime.today().date()):
            # user_info=db.retrieve_user_by_user_id(userjob['idUser'])
            job_info=db.retrieve_job_by_job_id(userjob['idJob'])
            jsonnew={"jobInfo":job_info}
            userjob.update(jsonnew)
            userjobs.append(json.loads(json_util.dumps(userjob)))
    return jsonify({'userjobs' : userjobs})

@application.route('/userjobs/getJobsByDate/<user_id>',methods=['PUT'])
@token_required
def get_jobs_by_date(user_id):
    dateGiven=datetime.datetime.strptime(request.json["date"], "%Y-%m-%d")
    userjobs=[]
    for userjob in db.retrieve_jobs_by_user_id(user_id):
        mydatetime=datetime.datetime.strptime(userjob["scheduledBeginDateString"], "%Y-%m-%d %I:%M %p")
        if(mydatetime.date()==dateGiven.date()):
            # user_info=db.retrieve_user_by_user_id(userjob['idUser'])
            job_info=db.retrieve_job_by_job_id(userjob['idJob'])
            jsonnew={"jobInfo":job_info}
            userjob.update(jsonnew)
            userjobs.append(json.loads(json_util.dumps(userjob)))
    return jsonify({'userjobs' : userjobs})
    



#20
"""  METHODS OF RESOURCES """



@application.route('/resources/add',methods=['POST'])
@token_required
def add_resources():
    dtstart=datetime.datetime.strptime(request.json['dtStart'], '%Y-%m-%d %I:%M %p')
    dtend=datetime.datetime.strptime(request.json['dtEnd'], '%Y-%m-%d %I:%M %p')
    request.json.update({'dateStart':dtstart,'dateEnd':dtend,"isReturned":False})
    db.insert_resources_to_db(request.json)
    resources=[]
    for resource in  db.retrieve_resources():
        resources.append(json.loads(json_util.dumps(resource)))
    return jsonify({'resources' :resources})

@application.route('/resources/getAll',methods=['GET'])
@token_required
def getall_resources():
    resources=[]
    for resource in  db.retrieve_resources():
        resources.append(json.loads(json_util.dumps(resource)))
    return jsonify({'resources' :resources})

@application.route('/resources/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_resources(domain_id):
    resources=[]
    for resource in  db.retrieve_resource_by_domain_id(domain_id):
        resources.append(json.loads(json_util.dumps(resource)))
    return jsonify({'resources' :resources})

@application.route('/resources/getById/<resource_id>',methods=['GET'])
@token_required
def get_resource(resource_id):
    resources = db.retrieve_resource_by_resource_id(resource_id)
    if len(resource) == 0:
        abort(404)
    return jsonify({'resource':json.loads(json_util.dumps(resource))})

@application.route('/resources/update/<resource_id>',methods=['PUT'])
@token_required
def update_resource(resource_id):
    resource = db.retrieve_resource_by_resource_id(resource_id)
    if (resource is None) or (len(resource) == 0):
        abort(404)
    db._update_resource(resource_id,request.json)
    result=db.retrieve_resource_by_resource_id(resource_id)
    return jsonify({'resource':json.loads(json_util.dumps(result))})

@application.route('/resources/delete/<resource_id>',methods=['DELETE'])
@token_required
def delete_resource(resource_id):
    db.remove_resource_by_id(resource_id)
    return jsonify('result',True)

@application.route('/resources/returned/<resource_id>',methods=['PUT'])
@token_required
def return_resource(resource_id):
    resource = db.retrieve_resource_by_resource_id(resource_id)
    if (resource is None) or (len(resource) == 0):
        abort(404)
    return_date=request.json['dtReturned']
    db.return_by_id(resource_id,return_date)
    result=db.retrieve_resource_by_resource_id(resource_id)
    return jsonify({'resource':json.loads(json_util.dumps(result))})



#21
"""  METHODS OF MESSAGES """



@application.route('/messages/add',methods=['POST'])
@token_required
def add_messages():
    user=db.retrieve_user_by_user_id(request.json['idUser'])
    if (user is None) or (len(user) == 0):
        return jsonify({'result' :"User doesnot exist"})
    info={"isSent":0,'isRead':0,"isDeleted":0}
    info.update(request.json)
    result=db.insert_messages_to_db(info)
    message=db.retrieve_message_by_message_id(json.loads(json_util.dumps(result))['$oid']) 
    return jsonify({'message' :json.loads(json_util.dumps(message))})

@application.route('/messages/getAll',methods=['GET'])
@token_required
def getall_messages():
    messages=[]
    for message in  db.retrieve_messages():
        messages.append(json.loads(json_util.dumps(message)))
    return jsonify({'messages' :messages})

@application.route('/messages/getById/<message_id>',methods=['GET'])
@token_required
def get_message(message_id):
    messages = db.retrieve_message_by_message_id(message_id)
    if len(messages) == 0:
        abort(404)
    return jsonify({'message':json.loads(json_util.dumps(message))})

@application.route('/messages/sent/<message_id>',methods=['PUT'])
@token_required
def sent_msg(message_id):
    message = db.retrieve_message_by_message_id(message_id)
    if (message is None) or (len(message) == 0):
        abort(404)
    db.update_sent_msg_by_id(message_id)
    result=db.retrieve_message_by_message_id(message_id)
    return jsonify({'message':json.loads(json_util.dumps(result))})

@application.route('/messages/read/<message_id>',methods=['PUT'])
@token_required
def read_msg(message_id):
    message = db.retrieve_message_by_message_id(message_id)
    if (message is None) or (len(message) == 0):
        abort(404)
    db.update_read_by_id(message_id)
    result=db.retrieve_message_by_message_id(message_id)
    return jsonify({'message':json.loads(json_util.dumps(result))})

@application.route('/messages/deleted/<message_id>',methods=['PUT'])
@token_required
def delete_msg(message_id):
    message = db.retrieve_message_by_message_id(message_id)
    if (message is None) or (len(message) == 0):
        abort(404)
    result1=db.update_deleted_msg_by_id(message_id)
    result=db.retrieve_message_by_message_id(message_id)
    return jsonify({'message':json.loads(json_util.dumps(result))})

@application.route('/messages/getByUserId/<user_id>',methods=['GET'])
@token_required
def getall_messages_by_user_id(user_id):
    messages=[]
    for message in  db.get_messages_by_user_id(user_id):
        if (message['isDeleted']==0):
            messages.append(json.loads(json_util.dumps(message)))
    return jsonify({'messages' :messages})


#22
"""  METHODS OF QUOTATIONS """



@application.route('/quotations/add',methods=['POST'])
@token_required
def add_quotations():
    amt=request.json['amount']
    tax_rate=request.json['tax']
    discount_rate=request.json['discount']
    date=datetime.datetime.strptime(request.json['dateString'], '%Y-%m-%d %I:%M %p')
    tax=amt* tax_rate/100
    total=amt+tax
    discount=total*discount_rate/100
    total=total-discount
    jsonToSend={"total":total,'tax_c':tax,'discount_c':discount,"date":date}
    jsonToSend.update(request.json)
    db.insert_quotations_to_db(jsonToSend)
    quotations=[]
    for quotation in  db.retrieve_quotations():
        quotations.append(json.loads(json_util.dumps(quotation)))
    return jsonify({'quotations' :quotations})

@application.route('/quotations/getAll',methods=['GET'])
@token_required
def getall_quotations():
    quotations=[]
    for quotation in  db.retrieve_quotations():
        quotations.append(json.loads(json_util.dumps(quotation)))
    return jsonify({'quotations' :quotations})

@application.route('/quotations/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_quotations(domain_id):
    quotations=[]
    for quotation in  db.retrieve_quotation_by_domain_id(domain_id):
        quotations.append(json.loads(json_util.dumps(quotation)))
    return jsonify({'quotations' :quotations})

@application.route('/quotations/getById/<quotation_id>',methods=['GET'])
@token_required
def get_quotation(quotation_id):
    quotation = db.retrieve_quotation_by_quotation_id(quotation_id)
    if len(quotation) == 0:
        abort(404)
    return jsonify({'quotation':json.loads(json_util.dumps(quotation))})

@application.route('/quotations/sent/<quotation_id>',methods=['PUT'])
@token_required
def sent_quotation(quotation_id):
    quotation = db.retrieve_quotation_by_quotation_id(quotation_id)
    if (quotation is None) or (len(quotation) == 0):
        abort(404)
    db.update_sent_by_id(quotation_id)
    result=db.retrieve_quotation_by_quotation_id(quotation_id)
    return jsonify({'quotation':json.loads(json_util.dumps(result))})

@application.route('/quotations/accepted/<quotation_id>',methods=['PUT'])
@token_required
def accepted_quotation(quotation_id):
    quotation = db.retrieve_quotation_by_quotation_id(quotation_id)
    if (quotation is None) or (len(quotation) == 0):
        abort(404)
    db.update_accepted_by_id(quotation_id)
    result=db.retrieve_quotation_by_quotation_id(quotation_id)
    return jsonify({'quotation':json.loads(json_util.dumps(result))})

@application.route('/quotations/deleted/<quotation_id>',methods=['PUT'])
@token_required
def deleted_quotation(quotation_id):
    quotation = db.retrieve_quotation_by_quotation_id(quotation_id)
    if (quotation is None) or (len(quotation) == 0):
        abort(404)
    db.update_deleted_by_id(quotation_id)
    result=db.retrieve_quotation_by_quotation_id(quotation_id)
    return jsonify({'quotation':json.loads(json_util.dumps(result))})

@application.route('/quotations/getByUserId/<user_id>',methods=['GET'])
@token_required
def getall_quotations_by_user_id(user_id):
    quotations=[]
    for quotation in  db.get_quotations_by_user_id(user_id):
        quotations.append(json.loads(json_util.dumps(quotation)))
    return jsonify({'quotations' :quotations})

@application.route('/quotations/update/<quotation_id>',methods=['PUT'])
@token_required
def update_quotation(quotation_id):
    quotation = db.retrieve_quotation_by_quotation_id(quotation_id)
    if (quotation is None) or (len(quotation) == 0):
        abort(404)
    db._update_quotation(quotation_id,request.json)
    result=db.retrieve_quotation_by_quotation_id(quotation_id)
    return jsonify({'quotation':json.loads(json_util.dumps(result))})

@application.route('/quotations/delete/<quotation_id>',methods=['DELETE'])
@token_required
def delete_quotation(quotation_id):
    db.remove_quotation_by_id(quotation_id)
    return jsonify('result',True)


#23
"""  METHODS OF INVOICES """



@application.route('/invoices/add',methods=['POST'])
@token_required
def add_invoices():
    amt=request.json['amount']
    tax_rate=request.json['tax']
    discount_rate=request.json['discount']
    date=datetime.datetime.strptime(request.json['dateString'], '%Y-%m-%d %I:%M %p')
    tax=amt* tax_rate/100
    total=amt+tax
    discount=total*discount_rate/100
    total=total-discount
    jsonToSend={"total":total,'tax_c':tax,'discount_c':discount,"date":date}
    jsonToSend.update(request.json)
    db.insert_invoices_to_db(jsonToSend)
    invoices=[]
    for invoice in  db.retrieve_invoices():
        invoices.append(json.loads(json_util.dumps(invoice)))
    return jsonify({'invoices' :invoices})

@application.route('/invoices/getAll',methods=['GET'])
@token_required
def getall_invoices():
    invoices=[]
    for invoice in  db.retrieve_invoices():
        invoices.append(json.loads(json_util.dumps(invoice)))
    return jsonify({'invoices' :invoices})

@application.route('/invoices/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def get_by_domain_id_invoices(domain_id):
    invoices=[]
    for invoice in  db.retrieve_invoice_by_domain_id(domain_id):
        invoices.append(json.loads(json_util.dumps(invoice)))
    return jsonify({'invoices' :invoices})

@application.route('/invoices/getById/<invoice_id>',methods=['GET'])
@token_required
def get_invoice(invoice_id):
    invoice = db.retrieve_invoice_by_invoice_id(invoice_id)
    if len(invoice) == 0:
        abort(404)
    return jsonify({'invoice':json.loads(json_util.dumps(invoice))})

@application.route('/invoices/sent/<invoice_id>',methods=['PUT'])
@token_required
def sent_invoice(invoice_id):
    invoice = db.retrieve_invoice_by_invoice_id(invoice_id)
    if (invoice is None) or (len(invoice) == 0):
        abort(404)
    db.update_sent_by_id(invoice_id)
    result=db.retrieve_invoice_by_invoice_id(invoice_id)
    return jsonify({'invoice':json.loads(json_util.dumps(result))})

@application.route('/invoices/draft/<invoice_id>',methods=['PUT'])
@token_required
def accepted_invoice(invoice_id):
    invoice = db.retrieve_invoice_by_invoice_id(invoice_id)
    if (invoice is None) or (len(invoice) == 0):
        abort(404)
    db.update_draft_by_id(invoice_id)
    result=db.retrieve_invoice_by_invoice_id(invoice_id)
    return jsonify({'invoice':json.loads(json_util.dumps(result))})

@application.route('/invoices/paid/<invoice_id>',methods=['PUT'])
@token_required
def paid_invoice(invoice_id):
    invoice = db.retrieve_invoice_by_invoice_id(invoice_id)
    if (invoice is None) or (len(invoice) == 0):
        abort(404)
    db.update_paid_by_id(invoice_id)
    result=db.retrieve_invoice_by_invoice_id(invoice_id)
    return jsonify({'invoice':json.loads(json_util.dumps(result))})

@application.route('/invoices/late/<invoice_id>',methods=['PUT'])
@token_required
def late_invoice(invoice_id):
    invoice = db.retrieve_invoice_by_invoice_id(invoice_id)
    if (invoice is None) or (len(invoice) == 0):
        abort(404)
    db.update_late_by_id(invoice_id)
    result=db.retrieve_invoice_by_invoice_id(invoice_id)
    return jsonify({'invoice':json.loads(json_util.dumps(result))})

@application.route('/invoices/cancelled/<invoice_id>',methods=['PUT'])
@token_required
def cancel_invoice(invoice_id):
    invoice = db.retrieve_invoice_by_invoice_id(invoice_id)
    if (invoice is None) or (len(invoice) == 0):
        abort(404)
    db.update_cancelled_by_id(invoice_id)
    result=db.retrieve_invoice_by_invoice_id(invoice_id)
    return jsonify({'invoice':json.loads(json_util.dumps(result))})


@application.route('/invoices/getByUserId/<user_id>',methods=['GET'])
@token_required
def getall_invoices_by_user_id(user_id):
    invoices=[]
    for invoice in  db.get_invoices_by_user_id(user_id):
        invoices.append(json.loads(json_util.dumps(invoice)))
    return jsonify({'invoices' :invoices})

@application.route('/invoices/update/<invoice_id>',methods=['PUT'])
@token_required
def update_invoice(invoice_id):
    invoice = db.retrieve_invoice_by_invoice_id(invoice_id)
    if (invoice is None) or (len(invoice) == 0):
        abort(404)
    db._update_invoice(invoice_id,request.json)
    result=db.retrieve_invoice_by_invoice_id(invoice_id)
    return jsonify({'invoice':json.loads(json_util.dumps(result))})

@application.route('/invoices/delete/<invoice_id>',methods=['DELETE'])
@token_required
def delete_invoice(invoice_id):
    db.remove_invoice_by_id(invoice_id)
    return jsonify('result',True)

#23
"""  METHODS OF BUSINESS HOURS """

@application.route('/business_hours/save',methods=['POST'])
@token_required
def save_business_hours(domain_id):
    jsonToSend={"idDOmain":domain_id}
    jsonToSend.update(request.json)
    bh=db.retrieve_business_hour_by_domain_id(domain_id)
    if(dh is None) or (len(bh)==0):
        db.insert_business_hours_to_db(jsonToSend)
    else:
        db._update_business_hour(domain_id,request.json)
    result=db.retrieve_business_hour_by_domain_id(domain_id)
    return jsonify({"business_hour":json.loads(json_util.dumps(result))})

@application.route('/business_hours/update/<bh_id>',methods=['PUT'])
@token_required
def update_business_hours(bh_id):
    bh = db.retrieve_business_hour_by_bh_id(bh_id)
    if (bh is None) or (len(bh) == 0):
        abort(404)
    db._update_business_hour(bh_id,request.json)
    result=db.retrieve_business_hour_by_bh_id(bh_id)
    return jsonify({'business_hour':json.loads(json_util.dumps(result))})

@application.route('/business_hours/getByDomainId/<domain_id>',methods=['GET'])
@token_required
def getall_business_hours_by_domain_id(domain_id):
    result=db.retrieve_business_hour_by_bh_id(bh_id)
    return jsonify({'business_hour':json.loads(json_util.dumps(result))})


if __name__ == '__main__':
    application.run(host='0.0.0.0',debug=True)