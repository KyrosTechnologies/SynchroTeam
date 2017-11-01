import bcrypt
import sys
from flask.json import jsonify
from pymongo import MongoClient
from pymongo import errors
from bson import ObjectId
import json
from bson import json_util, ObjectId
import datetime 


MONGO_HOST = "192.168.1.19"
MONGO_PORT = 27017
MONGO_DB = "testdb1"
MONGO_USER = "sampleuser"
MONGO_PASS = "password"



if "application.py" == sys.argv[0]:
    ENCRYPTION_ROUNDS = 12
else:
    ENCRYPTION_ROUNDS = 12  # if running unit tests


class DatabaseHelper(object):
    def __init__(self):
        try:
            URI = 'mongodb://KyrosAdmin:fw4Pzn3MN1RXGQ1J@pipedrivecluster-shard-00-00-idbj4.mongodb.net:27017,pipedrivecluster-shard-00-01-idbj4.mongodb.net:27017,pipedrivecluster-shard-00-02-idbj4.mongodb.net:27017/sample_db?ssl=true&replicaSet=PipeDriveCluster-shard-0&authSource=admin'
            
            # self.client = MongoClient(MONGO_HOST, MONGO_PORT)
            self.client = MongoClient(URI) 
            self.db=self.client.sample_db
            # self.db = self.client[MONGO_DB]
            # self.db.authenticate(MONGO_USER,MONGO_PASS)
            #list of collections
            self.domain=self.db.domain
            
            self.users = self.db.users #1
            self.customers=self.db.customers #2
            self.teams=self.db.teams #3
            self.ActivityType=self.db.ActivityType #4
            self.StockParts=self.db.StockParts #5
            self.Jobs=self.db.Jobs #6
            self.Activities=self.db.Activities #7
            self.RegionalSettings=self.db.RegionalSettings #8
            self.Taxes=self.db.Taxes #9
            self.ToolsAndResources=self.db.ToolsAndResources #10
            self.JobTypes=self.db.JobTypes #11
            self.CustomFieldsValues=self.db.CustomFieldsValues #12
            self.Equipments=self.db.Equipments #13
            self.Tags=self.db.Tags #14
            self.ProjectTypes=self.db.ProjectTypes #15
            self.Attachments=self.db.Attachments #16
            self.Sites=self.db.Sites #17
            self.Projects=self.db.Projects #18
            self.UserJobs=self.db.UserJobs #19 collection to save schedulled jobs
            self.Roles=self.db.Roles #20
            self.Resources=self.db.Resources #20
            self.Messages=self.db.Messages #21
            self.Quotations=self.db.Quotations #22
            self.Invoices=self.db.Invoices #23
            self.BusinessHours=self.db.BusinessHours #24
            
        except errors.ServerSelectionTimeoutError as err:
            print(err)

    def create_hash(self,password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(ENCRYPTION_ROUNDS))

    def insert_domain_to_db(self, user_info,domain_info,username,password,created_at):
        result=self.create_non_existing_user_to_database(username,password,created_at,user_info)
        if result == "User Already exists":
            return "User Already exists"
        else:
            info_to_insert={'idUser':str(result),'userinfo':json.loads(json_util.dumps(self.retrieve_user_by_user_id_without_id(str(result))))}
            info_to_insert.update(domain_info)
            self.domain.insert(info_to_insert)
            for domain in  self.retrieve_domains():
                return domain

    def retrieve_domains(self):
        return self.domain.find({})

    def retrieve_domain_by_domain_id(self,domain_id):
        return self.domain.find_one({'_id':ObjectId(domain_id)})


    def retrieve_domain_by_domainname(self, domain_name):
        return self.domain.find_one({'domain': domain_name})


# 1) **********************    USERS OPERATIONS     **********************


    def validateUserDocument():
        self.db.runCommand({'collMod': 'users', 'validator': { '$or': [ { 'phone': { '$exists': true } }, { 'email': { '$exists': true } } ] },'validationLevel': "moderate"} )

    def insert_user_to_db(self, user_info):
        result=self.users.insert(user_info)
        for user in  self.retrieve_users():
            return result

    def retrieve_users(self):
        return self.users.find({})

    def retrieve_user_by_username(self, username):
        return self.users.find_one({'username': username})

    def retrieve_user_by_email(self, email):
        return self.users.find_one({'email': email})

    def retrieve_user_by_user_id(self, user_id):
        try:
            return self.users.find_one({'_id':  ObjectId(user_id)})
        except:
            return ""

    def retrieve_user_by_domain_id(self,domain_id):
        try:
            return self.users.find_one({'_id':  ObjectId(domain_id)})
        except:
            return ""

    def changepassword(self,user_id,password):
        hash_ = self.create_hash(password)
        jsontosend={"password":password,"hash":hash_}
        self.users.update({'_id':ObjectId(user_id)}, { '$set' :jsontosend})

    def retrieve_user_by_user_id_without_id(self, user_id):
        return self.users.find_one({'_id':ObjectId(user_id)},{"_id":0})

    def create_non_existing_user_to_database(self, username, password,created_at,user_info_passed):
        hash_ = self.create_hash(password)
        user_info = {'username': username, 'hash': hash_,'created_at':created_at}
        user_info.update(user_info_passed)
        user = self.retrieve_user_by_username(username)
        if not user:
            result=self.insert_user_to_db(user_info)
        else:
            result="User Already exists"
        return result

    def check_email(email):
        return self.users.find_one({'email':  ObjectId(domain_id)})

    def check_password_hash_for_user(self, username, password):
        try:
            user = next(user for user in self.users.find({}) if user['username'] == username)
            return bcrypt.hashpw(password.encode('utf-8'), user['hash'].encode('utf-8'))== user['hash'].encode('utf-8')
        except StopIteration:
            return False

    def find_and_update_user(self, user_id,user_info):
        try:
            self._update_user(user_id,user_info)
        except:
            raise ValueError("userprofile was not found")

    def _update_user(self, user_id, user_info):
        self.users.update({'_id':ObjectId(user_id)}, { '$set' :user_info})
        return True
        
    def get_technicians(self):
        return self.users.find({'profile': 'technician'})

    def get_managers(self):
        return self.users.find({'profile': 'manager'})




# 2) **********************     CUSTOMERS OPERATIONS     **********************RATIONS



    def insert_customer_to_db(self, customer_info):
        self.customers.insert_one(customer_info)
        for customer in  self.retrieve_customers():
            # user_g = self.retrieve_user_by_username(user['username'])
            # self.users.update({{'_id': user_g.get('_id')}},{ '$set': {"m_id": user_g.get('_id')}}, False, True)
            return customer

    def retrieve_customers(self):
        return self.customers.find({})

    def retrieve_customer_by_customername(self, customer_name):
        return self.customers.find_one({'name': customer_name})

    def retrieve_customers_by_info(self,info):
        return self.customers.find(info)

    def retrieve_customer_by_customer_id(self, user_id):
        return self.customers.find_one({'_id':  ObjectId(user_id)})

    def retrieve_customer_by_domain_id(self, domain_id):
        return self.customers.find({'idDomain':  domain_id})

    def remove_customer_by_id(self,customer_id):
        self.customers.remove({'_id': ObjectId(customer_id)})

    def find_and_update_customer(self, customer_id,customer_info):
        try:
            self._update_customer(customer_id,customer_info)
        except:
            raise ValueError("customer was not found")

    def _update_customer(self, customer_id, customer_info):
        self.customers.update({'_id':ObjectId(customer_id)}, { '$set' :customer_info})
        return True




# 3) **********************     ACTIVITY TYPE OPERATIONS     **********************



    def insert_activity_type_to_db(self, activity_type_info):
        self.ActivityType.insert_one(activity_type_info)
        for activity_type in  self.retrieve_activity_types():
            return activity_type

    def retrieve_activity_types(self):
        return self.ActivityType.find({})

    def retrieve_activity_type_by_activity_typename(self, activity_typename):
        return self.ActivityType.find_one({'name': activity_typename},{'_id': 0})

    def retrieve_activity_types_by_info(self,info):
        return self.ActivityType.find(info)

    def retrieve_activity_type_by_activity_type_id(self, activity_type_id):
        return self.ActivityType.find_one({'_id':  ObjectId(activity_type_id)})

    def retrieve_activity_type_by_domain_id(self, domain_id):
        return self.ActivityType.find({'idDomain': domain_id})

    def remove_activity_type_by_id(self,activity_type_id):
        self.ActivityType.remove({'_id': ObjectId(activity_type_id)})

    def find_and_update_activity_type(self, activity_type_id,activity_type_info):
        try:
            self._update_activity_type(activity_type_id,activity_type_info)
        except:
            raise ValueError("activity type was not found")

    def _update_activity_type(self, activity_type_id,activity_type_info):
        self.ActivityType.update({'_id': ObjectId(activity_type_id)}, { '$set' :activity_type_info})
        return True


# 4) **********************     STOCK PARTS OPERATIONS     **********************

    



    def insert_stock_part_to_db(self, stock_part_info):
        self.StockParts.insert_one(stock_part_info)
        for stock_part in  self.retrieve_stock_parts():
            return stock_part

    def retrieve_stock_parts(self):
        return self.StockParts.find({})

    def retrieve_stock_part_by_stock_partname(self, stock_partname):
        return self.StockParts.find_one({'name': stock_partname})

    def retrieve_stock_part_by_domain_id(self, domain_id):
        return self.StockParts.find({'idDomain': domain_id})

    def retrieve_stock_part_by_stock_part_id(self, stock_id):
        return self.StockParts.find_one({'_id':ObjectId(stock_id)})

    def retrieve_stock_parts_by_info(self,info):
        return self.StockParts.find(info)

    def remove_stock_part_by_id(self,stock_part_id):
        self.StockParts.remove({'_id': ObjectId(stock_part_id)})

    def find_and_update_stock_part(self, stock_part_id,stock_part_info):
        try:
            self._update_stock_part(stock_part_id,stock_part_info)
        except:
            raise ValueError("stock_part was not found")

    def _update_stock_part(self, stock_part_id,stock_part_info):
        self.StockParts.update({'_id':ObjectId(stock_part_id)}, { '$set' :stock_part_info})
        return True



# 5) **********************     TEAMS OPERATIONS     **********************



    def insert_team_to_db(self, team_info):
        self.teams.insert_one(team_info)
        for team in  self.retrieve_teams():
            return team

    def retrieve_teams(self):
        return self.teams.find({})

    def retrieve_team_by_teamname(self, team_name):
        return self.teams.find_one({'name': team_name})

    def retrieve_team_by_domain_id(self, domain_id):
        return self.teams.find({'idDomain': domain_id})

    def retrieve_team_by_team_id(self, team_id):
        return self.teams.find_one({'_id': ObjectId(team_id)})


    def remove_team_by_id(self,team_id):
        self.teams.remove({'_id': ObjectId(team_id)})


    def _update_team(self, team_id, team):
        try:
            self.teams.update({'_id': ObjectId(team_id)}, {'$set': team})
        except:
            return jsonify({'result':'team not available'})





# 6) **********************     ACTIVITIES OPERATIONS     **********************



    def insert_activities_to_db(self, activity_info):
        self.Activities.insert_one(activity_info)
        for activity in  self.retrieve_activities():
            return activity

    def retrieve_activities(self):
        return self.Activities.find({})

    def retrieve_activity_by_activityname(self, activity_name):
        return self.Activities.find_one({'nmActivity': activity_name})


    def retrieve_activity_by_activity_id(self, activity_id):
        return self.Activities.find_one({'_id': ObjectId(activity_id)})

    def retrieve_activity_by_user_id(self, user_id):
        return self.Activities.find({'idUser': user_id})

    def remove_activity_by_id(self,activity_id):
        self.Activities.remove({'_id': ObjectId(activity_id)})

    def _update_activity(self, activity_id, activity):
        try:
            self.Activities.update({'_id': ObjectId(activity_id)}, {'$set': activity})
        except:
            return jsonify({'result':'activity not available'})




# 7) **********************     JOBS OPERATIONS     **********************


    def insert_jobs_to_db(self,job_info):
        self.Jobs.insert_one(job_info)
        for job in self.retrieve_jobs():
            return job

    def retrieve_jobs(self):
        return self.Jobs.find({})

    def retrieve_job_by_job_myId(self, job_myId):
        return self.Jobs.find_one({'myId': job_myId})


    def retrieve_job_by_job_id(self, job_id):
        return self.Jobs.find_one({'_id':ObjectId(job_id)})

    def retrieve_job_by_domain_id(self, domain_id):
        return self.Jobs.find({'idDomain':domain_id})


    def remove_job_by_id(self,job_id):
        self.Jobs.remove({'_id': ObjectId(job_id)})

    def _update_job(self, job_id, job):
        try:
            self.Jobs.update({'_id': ObjectId(job_id)}, {'$set': job})
        except:
            return jsonify({'result':'job not available'})




# 8) **********************     REGIONAL SETTINGS OPERATIONS     **********************



    def insert_regional_settings_to_db(self,settings_info):
        self.RegionalSettings.insert_one(settings_info)
        for setting in self.retrieve_settings():
            return setting

    def retrieve_settings(self):
        return self.RegionalSettings.find({},{'_id':0})

    def retrieve_settings_by_domain_id(self,domain_id):
        return self.RegionalSettings.find({'idDomain':domain_id})






# 9) **********************     TAXES OPERATIONS     **********************



    def insert_taxes_to_db(self,tax_info):
        self.Taxes.insert_one(tax_info)
        for tax in self.retrieve_taxes():
            return tax

    def retrieve_taxes(self):
        return self.Taxes.find({})

    def retrieve_tax_by_tax_name(self, tax_name):
        return self.Taxes.find_one({'name': tax_name})

    def retrieve_tax_by_domain_id(self, domain_id):
        return self.Taxes.find({'idDomain': domain_id})

    def retrieve_tax_by_tax_id(self, tax_id):
        return self.Taxes.find_one({'_id': ObjectId(tax_id)})

    def remove_tax_by_id(self,tax_id):
        self.Taxes.remove({'_id': ObjectId(tax_id)})

    def _update_tax(self, tax_id, tax_info):
        try:
            self.Taxes.update({'_id': ObjectId(tax_id)}, {'$set': tax_info})
        except:
            return jsonify({'result':'tax not available'})


# Needed
# 10) **********************     TOOLS AND RESOURCES OPERATIONS     **********************



    def insert_toolsresources_to_db(self,resource_info):
        self.ToolsAndResources.insert_one(resource_info)
        for resource in self.retrieve_resources():
            return resource

    def retrieve_toolsresources(self):
        return self.ToolsAndResources.find({})

    def retrieve_toolsresource_by_resource_name(self, resource_name):
        return self.ToolsAndResources.find_one({'resource_name': resource_name})

    def retrieve_toolsresource_by_resource_id(self, resource_id):
        return self.ToolsAndResources.find_one({'_id': ObjectId(resource_id)})

    def retrieve_toolsresource_by_domain_id(self, domain_id):
        return self.ToolsAndResources.find({'idDomain':domain_id})

    def remove_toolsresource_by_id(self,resource_id):
        self.ToolsAndResources.remove({'_id': ObjectId(resource_id)})

    def _update_toolsresource(self, resource_id, resource_info):
        self.ToolsAndResources.update({'_id': ObjectId(resource_id)}, {'$set': resource_info})



# 11) **********************    JOB TYPES OPERATIONS     **********************



    def insert_job_types_to_db(self,job_type_info):
        self.JobTypes.insert_one(job_type_info)
        for job_type in self.retrieve_job_types():
            return job_type

    def retrieve_job_types(self):
        return self.JobTypes.find({})

    def retrieve_jobtype_by_jobtype_name(self, job_type_name):
        return self.JobTypes.find_one({'job_type_name': job_type_name})

    def retrieve_jobtype_by_domain_id(self, domain_id):
        return self.JobTypes.find({'idDomain': domain_id})

    def retrieve_jobtype_by_jobtype_id(self, job_type_id):
        return self.JobTypes.find_one({'_id': ObjectId(job_type_id)})

    def remove_job_type_by_id(self,job_type_id):
        self.JobTypes.remove({'_id': ObjectId(job_type_id)})

    def _update_job_type(self, job_type_id, job_type_info):
        self.JobTypes.update({'_id': ObjectId(job_type_id)}, {'$set': job_type_info})



# 12) **********************     CUSTOM FIELDS OPERATIONS     **********************



    def insert_customFields_to_db(self,custom_field_info):
        self.CustomFieldsValues.insert_one(custom_field_info)
        for custom_field in self.retrieve_custom_fields():
            return custom_field

    def retrieve_custom_fields(self):
        return self.CustomFieldsValues.find({})

    def retrieve_custom_field_by_custom_field_name(self, custom_field_name):
        return self.CustomFieldsValues.find_one({'name': custom_field_name})

    def retrieve_custom_field_by_custom_field_id(self, custom_field_id):
        return self.CustomFieldsValues.find_one({'_id': ObjectId(custom_field_id)})

    def remove_custom_field_by_id(self,custom_field_id):
        self.CustomFieldsValues.remove({'_id': ObjectId(custom_field_id)})

    def _update_custom_field(self, custom_field_id, custom_field_info):
        try:
            self.CustomFieldsValues.update({'_id': ObjectId(custom_field_id)}, {'$set': custom_field_info})
        except:
            return jsonify({'result':'custom field was not updated'})






# 13) **********************     EQUIPMENTS OPERATIONS     **********************



    def insert_equipments_to_db(self,equipment_info):
        self.Equipments.insert(equipment_info)
        for equipment in self.retrieve_equipments():
            return equipment

    def retrieve_equipments(self):
        return self.Equipments.find({})

    def retrieve_equipment_by_equipment_name(self, equipment_name):
        return self.Equipments.find_one({'name': equipment_name})

    def retrieve_equipment_by_equipment_myId(self, equipment_myId):
        return self.Equipments.find_one({'myId': equipment_myId})

    def retrieve_equipment_by_domain_id(self, domain_id):
        return self.Equipments.find({'idDomain': domain_id})

    def retrieve_equipment_by_equipment_id(self, equipment_id):
        return self.Equipments.find({'_id': ObjectId(equipment_id)})

    def remove_equipment_by_id(self,equipment_id):
        self.Equipments.remove({'_id': ObjectId(equipment_id)})

    def _update_equipment(self, equipment_id, equipment_info):
        try:
            self.Equipments.update({'_id': ObjectId(equipment_id)}, {'$set': equipment_info})
        except:
            return jsonify({'result':'equipemt was not updated'})




# 14) **********************     TAGS OPERATIONS     **********************



    def insert_tags_to_db(self,tag_info):
        self.Tags.insert_one(tag_info)
        for tag in self.retrieve_tags():
            return tag

    def retrieve_tags(self):
        return self.Tags.find({})

    def retrieve_tag_by_tag_name(self, tag_name):
        return self.Tags.find_one({'name': tag_name})

    def retrieve_tag_by_domain_id(self, domain_id):
        return self.Tags.find({'idDomain': domain_id})

    def retrieve_tag_by_tag_id(self, tag_id):
        return self.Tags.find_one({'_id': ObjectId(tag_id)})

    def remove_tag_by_id(self,tag_id):
        self.Tags.remove({'_id': ObjectId(tag_id)})

    def _update_tag(self, tag_id, tag_info):
        try:
            self.Tags.update({'_id':ObjectId(tag_id)}, {'$set': tag_info})
        except:
            return jsonify({'result':'tag was not updated'})





# 15) **********************     PROJECT TYPES OPERATIONS     **********************



    def insert_project_types_to_db(self,project_type_info):
        self.ProjectTypes.insert_one(project_type_info)
        for project_type in self.retrieve_project_types():
            return project_type

    def retrieve_project_types(self):
        return self.ProjectTypes.find({})

    def retrieve_project_type_by_project_typename(self, project_typename):
        return self.ProjectTypes.find_one({'type_name': project_typename})

    def retrieve_project_type_by_domain_id(self, domain_id):
        return self.ProjectTypes.find({'idDomain': domain_id})

    def retrieve_project_type_by_project_type_id(self, project_type_id):
        return self.ProjectTypes.find_one({'_id': ObjectId(project_type_id)})

    def remove_project_type_by_id(self,project_type_id):
        self.ProjectTypes.remove({'_id': ObjectId(project_type_id)})

    def _update_project_type(self, project_type_id, project_type_info):
        try:
            self.ProjectTypes.update({'_id':ObjectId(project_type_id)}, {'$set': project_type_info})
        except:
            return jsonify({'result':'project type was not updated'})





# 16) **********************     ATTACHMENTS OPERATIONS     **********************



    def insert_attachments_to_db(self,attachment_info):
        self.Attachments.insert_one(attachment_info)
        for attachment in self.retrieve_attachments():
            return attachment

    def retrieve_attachments(self):
        return self.Attachments.find({})

    def retrieve_attachment_by_attachment_name(self, attachment_name):
        return self.Attachments.find_one({'name': attachment_name})

    def retrieve_attachment_by_attachment_id(self, attachment_id):
        return self.Attachments.find_one({'_id': ObjectId(attachment_id)})

    def remove_attachment_by_id(self,attachment_id):
        self.Attachments.remove({'_id': ObjectId(attachment_id)})

    def _update_attachment(self, attachment_id, attachment_info):
        try:
            self.Attachments.update({'_id': ObjectId(attachment_id)}, {'$set': attachment_info})
        except:
            return jsonify({'result':'attachment was not updated'})




# 17) **********************     SITES OPERATIONS     **********************



    def insert_sites_to_db(self,site_info):
        self.Sites.insert_one(site_info)
        for site in self.retrieve_sites():
            return site

    def retrieve_sites(self):
        return self.Sites.find({})

    def retrieve_site_by_site_name(self, site_name):
        return self.Sites.find_one({'name': site_name})

    def retrieve_site_by_domain_id(self, domain_id):
        return self.Sites.find({'idDomain': domain_id})

    def retrieve_site_by_site_id(self, site_id):
        return self.Sites.find_one({'_id': ObjectId(site_id)})

    def remove_site_by_id(self,site_id):
        self.Sites.remove({'_id': ObjectId(site_id)})

    def _update_site(self, site_id, site_info):
        try:
            self.Sites.update({'_id': ObjectId(site_id)}, {'$set': site_info})
        except:
            return jsonify({'result':'site was not updated'})





# 18) **********************     PROJECTS OPERATIONS     **********************



    def insert_projects_to_db(self,project_info):
        self.Projects.insert_one(project_info)
        for project in self.retrieve_projects():
            return project

    def retrieve_projects(self):
        return self.Projects.find({})

    def retrieve_project_by_project_name(self, project_name):
        return self.Projects.find_one({'custom_project_no': project_name})

    def retrieve_project_by_domain_id(self, domain_id):
        return self.Projects.find({'idDomain': domain_id})

    def retrieve_project_by_project_id(self, project_id):
        return self.Projects.find_one({'_id': ObjectId(project_id)})

    def remove_project_by_id(self,project_id):
        self.Projects.remove({'_id': ObjectId(project_id)})

    def _update_project(self, project_id, project_info):
        try:
            self.Projects.update({'_id': ObjectId(project_id)}, {'$set': project_info})
        except:
            return jsonify({'result':'project was not updated'})




# 19) **********************     USERJOBS OPERATIONS     **********************



    def insert_userjobs_to_db(self,scheduling_info,user_id,job_id):
        # userinfo=json.loads(json_util.dumps(self.users.find_one({'_id': ObjectId(user_id)},{"_id":0})))
        # jobinfo=json.loads(json_util.dumps(self.Jobs.find_one({'_id': ObjectId(job_id)},{"_id":0})))
        data={'status':'scheduled'}
        # data={'user_id':user_id,'job_id':job_id}
        scheduling_info.update(json.loads(json_util.dumps(data)))
        self.UserJobs.insert_one(scheduling_info)
        for userjob in self.retrieve_user_jobs():
            return userjob

    def retrieve_user_jobs(self):
        return self.UserJobs.find({})

    def retrieve_userjob_by_userjob_id(self, userjob_id):
        return self.UserJobs.find_one({'_id': ObjectId(userjob_id)})

    def retrieve_jobs_by_user_id(self,user_id):
        return self.UserJobs.find({"idUser":user_id})

    def retrieve_jobs_by_info(self,info):
        return self.UserJobs.find(info)

    def update_status(self,userjobs_id,status_val):
        self.UserJobs.update({'_id': ObjectId(userjob_id)}, {'$set': status_val})

    def update_started(self,userjobs_id):
        self.UserJobs.update({'_id':ObjectId(userjobs_id)},{'$set':{'status':'started','realBeginDateString':datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),'realBeginDate':datetime.datetime.now()}})

    def update_paused(self,userjobs_id):
        self.UserJobs.update({'_id':ObjectId(userjobs_id)},{'$set':{'status':'paused'}})

    def update_completed(self,userjobs_id):
        userjob=self.retrieve_userjob_by_userjob_id(userjobs_id)
        userjob_r=json.loads(json_util.dumps(userjob))
        duration=self.getDuration(datetime.datetime.now(),userjob_r["realBeginDate"])
        self.UserJobs.update({'_id':ObjectId(userjobs_id)},{'$set':{'status':'completed','realEndDateString':datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),'duration':duration,"realEndDate":datetime.datetime.now()}})

    def update_validated(self,user_id,userjobs_id):
        self.UserJobs.update({'_id':ObjectId(userjobs_id)},{'$set':{'status':'validated','validationDateString':datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),'validationDate':datetime.datetime.now(),'validationUser':user_id}})

    def update_cancelled(self,userjobs_id):
        self.UserJobs.update({'_id':ObjectId(userjobs_id)},{'$set':{'status':'cancelled'}})

    def getDuration(self,end_date,begin_date):
        return (end_date-begin_date).total_seconds()


# 20) **********************     RESOURCES OPERATIONS     **********************



    def insert_resources_to_db(self,resource_info):
        self.Resources.insert_one(resource_info)
        for resource in self.retrieve_resources():
            return resource

    def retrieve_resources(self):
        return self.Resources.find({})

    def retrieve_resource_by_resource_id(self, resource_id):
        return self.Resources.find_one({'_id': ObjectId(resource_id)})

    def retrieve_resource_by_domain_id(self, domain_id):
        return self.Resources.find({'idDomain': domain_id})

    def remove_resource_by_id(self,resource_id):
        self.Resources.remove({'_id': ObjectId(resource_id)})

    def return_by_id(self,resource_id,return_date):
        self.Resources.update({'_id':ObjectId(resource_id)},{'$set':{'dtReturned':return_date}})

    def _update_resource(self, resource_id, resource_info):
        try:
            self.Resources.update({'_id': ObjectId(resource_id)}, {'$set': resource_info})
        except:
            return jsonify({'result':'resource not available'})


# 21) **********************     MESSAGES OPERATIONS     **********************



    def insert_messages_to_db(self,message_info):
        return self.Messages.insert(message_info)

    def retrieve_messages(self):
        return self.Messages.find({})

    def retrieve_message_by_message_id(self, message_id):
        try:
            return self.Messages.find_one({'_id': ObjectId(message_id)})
        except:
            return jsonify({'result':'objectID not available'})

    def remove_message_by_id(self,message_id):
        self.Messages.remove({'_id': ObjectId(message_id)})

    def update_sent_msg_by_id(self,message_id):
        self.Messages.update({'_id':ObjectId(message_id)},{'$set':{'isSent':1}})

    def update_read_by_id(self,message_id):
        self.Messages.update({'_id':ObjectId(message_id)},{'$set':{'isRead':1}})

    def update_deleted_msg_by_id(self,message_id):
        return self.Messages.update({'_id':ObjectId(message_id)},{'$set':{'isDeleted':1}})

    def get_messages_by_user_id(self,user_id):
        return self.Messages.find({'idUser': user_id})


# 22) **********************     QUOTATIONS OPERATIONS     **********************


    def insert_quotations_to_db(self,quotation_info):
        self.Quotations.insert_one(quotation_info)
        for quotation in self.retrieve_quotations():
            return quotation

    def retrieve_quotations(self):
        return self.Quotations.find({})

    def retrieve_quotation_by_quotation_id(self, quotation_id):
        try:
            return self.Quotations.find_one({'_id': ObjectId(quotation_id)})
        except:
            return jsonify({'result':'objectID not available'})

    def retrieve_quotation_by_domain_id(self, domain_id):
        try:
            return self.Quotations.find({'idDomain': domain_id})
        except:
            return jsonify({'result':'objectID not available'})

    def remove_quotation_by_id(self,quotation_id):
        self.Quotations.remove({'_id': ObjectId(quotation_id)})

    def update_sent_by_id(self,quotation_id):
        self.Quotations.update({'_id':ObjectId(quotation_id)},{'$set':{'status':'sent'}})

    def update_accepted_by_id(self,quotation_id):
        self.Quotations.update({'_id':ObjectId(quotation_id)},{'$set':{'status':'accepted'}})

    def update_deleted_by_id(self,quotation_id):
        self.Quotations.update({'_id':ObjectId(quotation_id)},{'$set':{'status':'deleted'}})

    def get_quotation_by_user_id(self,user_id):
        return self.Quotations.find({'idUser': user_id})

    def remove_quotation_by_id(self,quotation_id):
        self.Quotations.remove({'_id': ObjectId(quotation_id)})

    def _update_quotation(self, quotation_id, quotation_info):
        try:
            self.Quotations.update({'_id': ObjectId(quotation_id)}, {'$set': quotation_info})
        except:
            return jsonify({'result':'quotation not available'})


# 23) **********************     INVOICES OPERATIONS     **********************


    def insert_invoices_to_db(self,invoice_info):
        self.Invoices.insert_one(invoice_info)
        for invoice in self.retrieve_invoices():
            return invoice

    def retrieve_invoices(self):
        return self.Invoices.find({})

    def retrieve_invoice_by_invoice_id(self, invoice_id):
        try:
            return self.Invoices.find_one({'_id': ObjectId(invoice_id)})
        except:
            return jsonify({'result':'objectID not available'})

    def retrieve_invoice_by_domain_id(self, domain_id):
        try:
            return self.Invoices.find({'idDomain': domain_id})
        except:
            return jsonify({'result':'objectID not available'})

    def remove_invoice_by_id(self,invoice_id):
        self.Invoices.remove({'_id': ObjectId(invoice_id)})

    def update_sent_by_id(self,invoice_id):
        self.Invoices.update({'_id':ObjectId(invoice_id)},{'$set':{'status':'sent'}})

    def update_draft_by_id(self,invoice_id):
        self.Invoices.update({'_id':ObjectId(invoice_id)},{'$set':{'status':'draft'}})

    def update_paid_by_id(self,invoice_id):
        self.Invoices.update({'_id':ObjectId(invoice_id)},{'$set':{'status':'paid'}})

    def update_late_by_id(self,invoice_id):
        self.Invoices.update({'_id':ObjectId(invoice_id)},{'$set':{'status':'late'}})

    def update_cancelled_by_id(self,invoice_id):
        self.Invoices.update({'_id':ObjectId(invoice_id)},{'$set':{'status':'cancelled'}})

    def get_invoices_by_user_id(self,user_id):
        return self.Invoices.find({'idUser': user_id})

    def remove_invoice_by_id(self,invoice_id):
        self.Invoices.remove({'_id': ObjectId(invoice_id)})

    def _update_invoice(self, invoice_id, invoice_info):
        try:
            self.Invoices.update({'_id': ObjectId(invoice_id)}, {'$set': invoice_info})
        except:
            return jsonify({'result':'invoice not available'})


# 24) **********************     BUSINESS HOURS OPERATIONS     **********************



    def insert_business_hours_to_db(self,bh_info):
        self.BusinessHours.insert(bh_info)
        for bh in self.retrieve_business_hours():
            return bh

    def retrieve_business_hours(self):
        return self.BusinessHours.find({})

    def retrieve_business_hour_by_domain_id(self, domain_id):
        return self.BusinessHours.find({'idDomain': domain_id})

    def retrieve_business_hour_by_bh_id(self, bh_id):
        return self.BusinessHours.find_one({'_id': bh_id})

    def _update_business_hour(self, domain_id, bh_info):
        try:
            self.BusinessHours.update({'idDomain': domain_id}, {'$set': bh_info})
        except:
            return jsonify({'result':'business hour not available'})


    
