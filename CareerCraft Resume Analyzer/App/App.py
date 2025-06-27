import streamlit as st # core package used in this project
st.set_page_config(page_title="CareerCraft Resume Analyzer", page_icon='App/Logo/resume.png')
import spacy
import pandas as pd
import base64, random
import time,datetime
# import pymysql
# import mysql.connector
import re
import os
import socket
import platform
import geocoder
import secrets
import io,random
import plotly.express as px # to create visualisations at the admin session
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
# libraries used to parse the pdf files
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
# pre stored data for prediction purposes
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
import nltk
nltk.download('stopwords')
# sql connector
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine("mysql+pymysql://root:Root123$@localhost/cv", poolclass=QueuePool, pool_size=5)
con = engine.raw_connection()  # ✅ FIXED: Use raw_connection()
cursor = con.cursor()



# To load more faster

@st.cache_resource
def load_spacy_model():
    return spacy.load("en_core_web_sm")

nlp = load_spacy_model()

#code for implementing validations for name, email mobile and email
  # Add this if not already imported

def validate_name(name):
    return bool(re.match(r"^[A-Za-z\s]{2,}$", name))

def validate_mobile(mobile):
    return bool(re.match(r"^\d{10}$", mobile))

def validate_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


###### Preprocessing functions ######


# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format 
def get_csv_download_link(df,filename,text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()      
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=False,
                                      check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()

    ## close open handles
    converter.close()
    fake_file_handle.close()
    return text


# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# course recommendations which has data already loaded from Courses.py
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 👨‍🎓**")
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


###### Database Stuffs ######


# sql connector
# con = pymysql.connect(host='localhost',user='root',password='Root123$',db='cv')
# cursor = con.cursor()


# inserting miscellaneous data, fetched results, prediction and recommendation into user_data table
def insert_data(sec_token,ip_add,host_name,dev_user,os_name_ver,latlong,city,state,country,act_name,act_mail,act_mob,name,email,res_score,timestamp,no_of_pages,reco_field,cand_level,skills,recommended_skills,courses,pdf_name):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (str(sec_token),str(ip_add),host_name,dev_user,os_name_ver,str(latlong),city,state,country,act_name,act_mail,act_mob,name,email,str(res_score),timestamp,str(no_of_pages),reco_field,cand_level,skills,recommended_skills,courses,pdf_name)
    cursor.execute(insert_sql, rec_values)
    con.commit()


# inserting feedback data into user_feedback table
def insertf_data(feed_name,feed_email,feed_score,comments,Timestamp):
    DBf_table_name = 'user_feedback'
    insertfeed_sql = "insert into " + DBf_table_name + """
    values (0,%s,%s,%s,%s,%s)"""
    rec_values = (feed_name, feed_email, feed_score, comments, Timestamp)
    cursor.execute(insertfeed_sql, rec_values)
    con.commit()


###### Setting Page Configuration (favicon, Logo, Title) ######


# st.set_page_config(
#    page_title="AI Resume Analyzer",
#    page_icon='./Logo/recommend.png',
# )


###### Main function run() ######


def run():
    
    # (Logo, Heading, Sidebar etc)
    img = Image.open('App/Logo/Careercraft.jpg')
    st.image(img)
    st.sidebar.markdown("<div class='sidebar-container'>", unsafe_allow_html=True)
    st.sidebar.markdown("<p class='sidebar-title'>🔍 Choose an Option</p>", unsafe_allow_html=True)

    activities = ["User", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)

    link = '''
        <b>Built with 🤍 by:</b> <br>
        <a href="https://linkedin.com/in/sahil-binjwe-ab9890320" class='sidebar-link' target="_blank">SAHIL BINJWE</a> <br>
        <a href="https://linkedin.com/in/shravani-suryawanshi-a935b4344" class='sidebar-link' target="_blank">SHRAVANI SURYAWANSHI</a>
    '''
    st.sidebar.markdown(link, unsafe_allow_html=True)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)



    ###### Creating Database and Table ######


    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS CV;"""
    cursor.execute(db_sql)


    # Create table user_data and user_feedback
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                    sec_token varchar(20) NOT NULL,
                    ip_add varchar(50) NULL,
                    host_name varchar(50) NULL,
                    dev_user varchar(50) NULL,
                    os_name_ver varchar(50) NULL,
                    latlong varchar(50) NULL,
                    city varchar(50) NULL,
                    state varchar(50) NULL,
                    country varchar(50) NULL,
                    act_name varchar(50) NOT NULL,
                    act_mail varchar(50) NOT NULL,
                    act_mob varchar(20) NOT NULL,
                    Name varchar(500) NOT NULL,
                    Email_ID VARCHAR(500) NOT NULL,
                    resume_score VARCHAR(8) NOT NULL,
                    Timestamp VARCHAR(50) NOT NULL,
                    Page_no VARCHAR(5) NOT NULL,
                    Predicted_Field BLOB NOT NULL,
                    User_level BLOB NOT NULL,
                    Actual_skills BLOB NOT NULL,
                    Recommended_skills BLOB NOT NULL,
                    Recommended_courses BLOB NOT NULL,
                    pdf_name varchar(50) NOT NULL,
                    PRIMARY KEY (ID)
                    );
                """
    cursor.execute(table_sql)


    DBf_table_name = 'user_feedback'
    tablef_sql = "CREATE TABLE IF NOT EXISTS " + DBf_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                        feed_name varchar(50) NOT NULL,
                        feed_email VARCHAR(50) NOT NULL,
                        feed_score VARCHAR(5) NOT NULL,
                        comments VARCHAR(100) NULL,
                        Timestamp VARCHAR(50) NOT NULL,
                        PRIMARY KEY (ID)
                    );
                """
    cursor.execute(tablef_sql)


    ###### CODE FOR CLIENT SIDE (USER) ######

    if choice == "User":
        st.markdown("""
            <style>
                .main-container {
                    background-color: #ffffff;
                    padding: 25px;
                    border-radius: 15px;
                    box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.15);
                }
                .submit-button {
                    background-color: #007BFF !important;
                    color: white !important;
                    font-weight: bold;
                    border-radius: 8px;
                    padding: 10px;
                    width: 100%;
                }
                .input-field {
                    border: 2px solid #007BFF;
                    border-radius: 8px;
                    padding: 8px;
                    width: 100%;
                }
                .stTextInput > div > div > input {
                    border: 2px solid #007BFF !important;
                    border-radius: 8px !important;
                    padding: 8px !important;
                }
            </style>
        """, unsafe_allow_html=True)

        st.subheader("📂 User Section")
        st.write("Upload your resume and get a detailed analysis.")

        # User Input Fields
        col1, col2 = st.columns(2)
        with col1:
            act_name = st.text_input("👤 Name*", placeholder="Enter your full name")
        with col2:
            act_mob = st.text_input("📞 Mobile Number*", placeholder="Enter your 10-digit mobile number")

        act_mail = st.text_input("📧 Email*", placeholder="Enter your email address")

        # Generating additional system data
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        dev_user = os.getlogin()
        os_name_ver = platform.system() + " " + platform.release()
        g = geocoder.ip('me')
        latlong = g.latlng
        geolocator = Nominatim(user_agent="http")
        location = geolocator.reverse(latlong, language='en')
        address = location.raw['address']
        city = address.get('city', '')
        state = address.get('state', '')
        country = address.get('country', '')

        # Submit Button
        if st.button("🚀 Proceed", key="submit_button", help="Click to proceed"):
            errors = []
            if not validate_name(act_name):
                errors.append("❌ Invalid Name! Only alphabets and spaces are allowed.")
            if not validate_email(act_mail):
                errors.append("❌ Invalid Email! Please enter a valid email address.")
            if not validate_mobile(act_mob):
                errors.append("❌ Invalid Mobile Number! Enter a 10-digit number.")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.success("✅ Details submitted successfully!")

        st.markdown("</div>", unsafe_allow_html=True)

        # Stylish Section Footer
        st.markdown(
            """
            <h5 style='text-align: center; color: #021659;'>
                🌟 Upload Your Resume & Get Smart Recommendations!
            </h5>
            """, unsafe_allow_html=True
        ) 
        ## file upload in pdf format
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)
        
            ### saving the uploaded resume to folder
            save_image_path = 'app/Uploaded_Resumes/'+pdf_file.name
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            ### parsing and extracting whole resume 
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                
                ## Get the whole resume data into resume_text
                resume_text = pdf_reader(save_image_path)

                ## Stylish Header for Resume Analysis
                st.markdown("""
                    <style>
                        .analysis-container {
                            background-color: #ffffff;
                            padding: 25px;
                            border-radius: 15px;
                            box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.15);
                            text-align: center;
                        }
                        .info-box {
                            background-color: #f8f9fa;
                            padding: 12px;
                            border-radius: 8px;
                            margin: 10px 0;
                            box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
                        }
                        .icon {
                            font-size: 18px;
                            color: #007BFF;
                            font-weight: bold;
                        }
                        .highlight {
                            font-weight: bold;
                            color: #021659;
                        }
                    </style>
                """, unsafe_allow_html=True)

                # st.markdown("<div class='analysis-container'>", unsafe_allow_html=True)
                
                st.header("📄 **Resume Analysis 🤘**")
                st.success(f"Hello, {resume_data.get('name', 'User')}! 👋")

                ## Basic Information Section
                st.subheader("💡 **Your Basic Info**")

                try:
                    st.markdown(f"<div class='info-box'><span class='icon'>👤</span> <span class='highlight'>Name:</span> {resume_data.get('name', 'N/A')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='info-box'><span class='icon'>📧</span> <span class='highlight'>Email:</span> {resume_data.get('email', 'N/A')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='info-box'><span class='icon'>📞</span> <span class='highlight'>Contact:</span> {resume_data.get('mobile_number', 'N/A')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='info-box'><span class='icon'>🎓</span> <span class='highlight'>Degree:</span> {str(resume_data.get('degree', 'N/A'))}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='info-box'><span class='icon'>📑</span> <span class='highlight'>Resume Pages:</span> {str(resume_data.get('no_of_pages', 'N/A'))}</div>", unsafe_allow_html=True)

                except:
                    pass

                st.markdown("</div>", unsafe_allow_html=True)
                ## Predicting Candidate Experience Level 
                
                ### Trying with different possibilities
                cand_level = ''
                fresher_msg = "<h4 style='text-align: left; color: #d73b5c; font-weight: bold;'>🚀 You are at Fresher level!</h4>"
                intermediate_msg = "<h4 style='text-align: left; color: #1ed760; font-weight: bold;'>🌟 You are at Intermediate level!</h4>"
                experienced_msg = "<h4 style='text-align: left; color: #fba171; font-weight: bold;'>🔥 You are at Experienced level!</h4>"
                
                if resume_data['no_of_pages'] < 1:                
                    cand_level = "NA"
                    st.markdown(fresher_msg, unsafe_allow_html=True)
                
                #### Checking for Internship keywords
                elif any(keyword in resume_text for keyword in ['INTERNSHIP', 'INTERNSHIPS', 'Internship', 'Internships']):
                    cand_level = "Intermediate"
                    st.markdown(intermediate_msg, unsafe_allow_html=True)
                
                #### Checking for Experience keywords
                elif any(keyword in resume_text for keyword in ['EXPERIENCE', 'WORK EXPERIENCE', 'Experience', 'Work Experience']):
                    cand_level = "Experienced"
                    st.markdown(experienced_msg, unsafe_allow_html=True)
                
                else:
                    cand_level = "Fresher"
                    st.markdown(fresher_msg, unsafe_allow_html=True)


                ## Skills Analyzing and Recommendation
                st.subheader("**Skills Recommendation 💡**")
                
                ### Current Analyzed Skills
                keywords = st_tags(label='### Your Current Skills',
                text='See our skills recommendation below',value=resume_data['skills'],key = '1  ')

                ### Keywords for Recommendations
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress','javascript', 'angular js', 'C#', 'Asp.net', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
                n_any = ['english','communication','writing', 'microsoft office', 'leadership','customer management', 'social media']
                ### Skill Recommendations Starts                
                recommended_skills = []
                reco_field = ''
                rec_course = ''

                ### condition starts to check skills from keywords and predict field
                for i in resume_data['skills']:
                
                    #### Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ds_course)
                        break

                    #### Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(web_course)
                        break

                    #### Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(android_course)
                        break

                    #### IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ios_course)
                        break

                    #### Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(uiux_course)
                        break

                    #### For Not Any Recommendations
                    elif i.lower() in n_any:
                        print(i.lower())
                        reco_field = 'NA'
                        st.warning("** Currently our tool only predicts and recommends for Data Science, Web, Android, IOS and UI/UX Development**")
                        recommended_skills = ['No Recommendations']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Currently No Recommendations',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #092851;'>Maybe Available in Future Updates</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = "Sorry! Not Available for this Field"
                        break


                ## Resume Scorer & Resume Writing Tips
                st.subheader("**Resume Tips & Ideas 🥂**")
                resume_score = 0
                
                ### Predicting Whether these key points are added to the resume
                if 'Objective' or 'Summary' in resume_text:
                    resume_score = resume_score+6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective/Summary</h4>''',unsafe_allow_html=True)                
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)

                if 'Education' or 'School' or 'College'  in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Education Details</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Education. It will give Your Qualification level to the recruiter</h4>''',unsafe_allow_html=True)

                if 'EXPERIENCE' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''',unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Experience. It will help you to stand out from crowd</h4>''',unsafe_allow_html=True)

                if 'INTERNSHIPS'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'INTERNSHIP'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'Internships'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'Internship'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Internships. It will help you to stand out from crowd</h4>''',unsafe_allow_html=True)

                if 'SKILLS'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'SKILL'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'Skills'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'Skill'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Skills. It will help you a lot</h4>''',unsafe_allow_html=True)

                if 'HOBBIES' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                elif 'Hobbies' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Hobbies. It will show your personality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',unsafe_allow_html=True)

                if 'INTERESTS'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''',unsafe_allow_html=True)
                elif 'Interests'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Interest. It will show your interest other that job.</h4>''',unsafe_allow_html=True)

                if 'ACHIEVEMENTS' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                elif 'Achievements' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Achievements. It will show that you are capable for the required position.</h4>''',unsafe_allow_html=True)

                if 'CERTIFICATIONS' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                elif 'Certifications' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                elif 'Certification' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Certifications. It will show that you have done some specialization for the required position.</h4>''',unsafe_allow_html=True)

                if 'PROJECTS' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'PROJECT' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'Projects' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'Project' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Projects. It will show that you have done work related the required position or not.</h4>''',unsafe_allow_html=True)

                st.subheader("**Resume Score 📝**")
                
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )

                ### Score Bar
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score +=1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)

                ### Score
                st.success('** Your Resume Writing Score: ' + str(score)+'**')
                st.warning("** Note: This score is calculated based on the content that you have in your Resume. **")

                # print(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)


                ### Getting Current Date and Time
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)


                ## Calling insert_data to add all the data into user_data                
                insert_data(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)

                ## Recommending Resume Writing Video
                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                ## Recommending Interview Preparation Video
                st.header("**Bonus Video for Interview Tips💡**")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

                ## On Successful Result 
                st.balloons()

            else:
                st.error('Something went wrong..') 

              


    ###### CODE FOR FEEDBACK SIDE ######


    elif choice == 'Feedback':   
        # Timestamp
        ts = time.time()
        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        timestamp = str(cur_date + '_' + cur_time)

        # Title & Description
        st.markdown(
            """
            <style>
                .feedback-container {
                    text-align: center;
                    border: 1px solid #021659;
                    padding: 5px;
                    border-radius: 10px;
                    background-color: #f9f9f9;
                }
                .feedback-title {
                    color: #021659;
                    font-size: 24px;
                    font-weight: bold;
                }
                .feedback-description {
                    font-size: 16px;
                    color: #555;
                }
            </style>
            <div class="feedback-container">
                <h2 class="feedback-title">📝 We Value Your Feedback!</h2>
                <p class="feedback-description">
                    Your feedback helps us improve <b>CareerCraft Resume Analyzer</b>.  
                    Please take a moment to share your thoughts!😊
                </p>
            </div><br>
            """,
            unsafe_allow_html=True
        )

        # Feedback Form with Improved Styling
        with st.form("feedback_form"):
            st.markdown("### ✍️ Tell Us What You Think")

            feed_name = st.text_input('👤 Name*')
            feed_email = st.text_input('📧 Email*')
            feed_score = st.slider('⭐ Rate Us From 1 - 5', 1, 5, step=1)
            comments = st.text_area('💬 Your Comments (Optional)')
            
            submitted = st.form_submit_button("🚀 Submit Feedback")

            if submitted:
                if not feed_name or not feed_email:
                    st.error("⚠️ Name and Email are required fields!")
                else:
                    insertf_data(feed_name, feed_email, feed_score, comments, timestamp)    
                    st.success("🎉 Thank you! Your feedback has been recorded.") 
                    st.balloons()  

        # Fetching Feedback Data
        st.markdown("<br><h2 style='text-align: center; color: #4CAF50; border-bottom: 3px solid #4CAF50; padding-bottom: 5px;'>📊 User Feedback Statistics</h2>", unsafe_allow_html=True)

        query = 'SELECT * FROM user_feedback'
        plotfeed_data = pd.read_sql(query, con=engine)  

        # Pie Chart for Ratings with Dark Borders
        if not plotfeed_data.empty:
            labels = plotfeed_data.feed_score.unique()
            values = plotfeed_data.feed_score.value_counts()

            fig = px.pie(
                values=values, 
                names=labels, 
                title="⭐ User Rating Distribution",
                color_discrete_sequence=px.colors.qualitative.Plotly_r,  # Stronger colors
                hole=0.3,  # Donut effect
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⚠️ No feedback data available yet.")

        # Display User Comments with Darker Borders
        cursor.execute('SELECT feed_name, comments FROM user_feedback')
        plfeed_cmt_data = cursor.fetchall()

        st.markdown("<h3 style='text-align: center; color: #1E88E5; border-bottom: 2px solid #1E88E5; padding-bottom: 5px;'>💬 What Users Are Saying</h3>", unsafe_allow_html=True)

        dff = pd.DataFrame(plfeed_cmt_data, columns=['User', 'Comment'])

        if not dff.empty:
            st.dataframe(dff.style.set_properties(**{'border': '2px solid black'}), width=800, height=300)
        else:
            st.info("💡 No feedback available yet. Be the first to leave a comment!")



    ###### CODE FOR ABOUT PAGE ######
    elif choice == 'About':   
        st.markdown(
            """
            <div style="text-align: center;">
                <h2 style="color: #021659;">🚀 About CareerCraft Resume Analyzer</h2>
            </div>
            
            <p style="text-align: justify; font-size: 16px;">
                CareerCraft Resume Analyzer is an AI-powered tool that analyzes resumes using <b>Natural Language Processing (NLP)</b> 
                and provides valuable insights to improve job application success. 
                It extracts key information, evaluates skills, and offers smart <b>course recommendations</b>.
            </p>

            <h3 style="color: #1ed760;">🔹 Features:</h3>
            <ul style="font-size: 16px;">
                <li>📄 <b>Resume Parsing</b> - Extracts essential details from resumes.</li>
                <li>📊 <b>AI-Powered Skill Analysis</b> - Identifies key strengths.</li>
                <li>🎯 <b>Job Field Prediction</b> - Suggests career paths based on skills.</li>
                <li>📚 <b>Course Recommendations</b> - Recommends relevant learning resources.</li>
                <li>💡 <b>Resume Improvement Tips</b> - Helps in creating a strong resume.</li>
                <li>📉 <b>Resume Score</b> - Provides an AI-generated resume rating.</li>
            </ul>

            <h3 style="color: #fba171;">🛠 How It Works:</h3>
            <ol style="font-size: 16px;">
                <li>📝 Upload your resume (PDF format).</li>
                <li>🔍 Our AI scans & extracts key details.</li>
                <li>📈 Receive a detailed analysis with skill suggestions.</li>
                <li>🎓 Get personalized course recommendations.</li>
                <li>📊 View your resume score & tips to improve it.</li>
            </ol>

            <h3 style="color: #092851;">👨‍💻 Developers:</h3>
            <p>
                Built with ❤️ by  
                <a href="https://linkedin.com/in/sahil-binjwe-ab9890320" style="text-decoration: none; color: #021659;"><b>Sahil Binjwe</b></a> 
                &  
                <a href="https://linkedin.com/in/shravani-suryawanshi-a935b4344" style="text-decoration: none; color: #021659;"><b>Shravani Suryawanshi</b></a>
            </p>
            """,
            unsafe_allow_html=True
    )


    ###### CODE FOR ADMIN SIDE (ADMIN) ######
    else:
        st.title("🚀 Admin Dashboard")
        st.markdown("---")
        st.markdown("### 🔐 Admin Login")
        #  Admin Login
        ad_user = st.text_input("👤 Username")
        ad_password = st.text_input("🔑 Password", type='password')

        if st.button('Login'):
            
            ## Credentials 
            if ad_user == 'sahilll' and ad_password == 'admin@sahil':
                
                ### Fetch miscellaneous data from user_data(table) and convert it into dataframe
                cursor.execute('''SELECT ID, ip_add, resume_score, convert(Predicted_Field using utf8), convert(User_level using utf8), city, state, country from user_data''')
                datanalys = cursor.fetchall()
                plot_data = pd.DataFrame(datanalys, columns=['Idt', 'IP_add', 'resume_score', 'Predicted_Field', 'User_Level', 'City', 'State', 'Country'])
                
                ### Total Users Count with a Welcome Message
                values = plot_data.Idt.count()
                st.success("Welcome SAHIL ! Total %d " % values + " User's Have Used Our Tool : )")                
                
                ### Fetch user data from user_data(table) and convert it into dataframe
                cursor.execute('''SELECT ID, sec_token, ip_add, act_name, act_mail, act_mob, convert(Predicted_Field using utf8), Timestamp, Name, Email_ID, resume_score, Page_no, pdf_name, convert(User_level using utf8), convert(Actual_skills using utf8), convert(Recommended_skills using utf8), convert(Recommended_courses using utf8), city, state, country, latlong, os_name_ver, host_name, dev_user from user_data''')
                data = cursor.fetchall()                

                st.markdown("### 📊 User Data")
                df = pd.DataFrame(data, columns=['ID', 'Token', 'IP Address', 'Name', 'Mail', 'Mobile Number', 'Predicted Field', 'Timestamp',
                                                 'Predicted Name', 'Predicted Mail', 'Resume Score', 'Total Page',  'File Name',   
                                                 'User Level', 'Actual Skills', 'Recommended Skills', 'Recommended Course',
                                                 'City', 'State', 'Country', 'Lat Long', 'Server OS', 'Server Name', 'Server User',])
                
                ### Viewing the dataframe
                st.dataframe(df)
                
                ### Downloading Report of user_data in csv file
                csv = df.to_csv(index=False)
                st.download_button("⬇️ Download User Data", data=csv, file_name="User_Data.csv", mime="text/csv")
                
                ### Fetch feedback data from user_feedback(table) and convert it into dataframe
                cursor.execute('''SELECT * from user_feedback''')
                data = cursor.fetchall()

                st.markdown("---")
                st.markdown("### 💬 User Feedback")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Feedback Score', 'Comments', 'Timestamp'])
                st.dataframe(df)

                ### query to fetch data from user_feedback(table)
                query = 'select * from user_feedback'
                plotfeed_data = pd.read_sql(query, con=engine)                        

                ### Analyzing All the Data's in pie charts

                # fetching feed_score from the query and getting the unique values and total value count 
                labels = plotfeed_data.feed_score.unique()
                values = plotfeed_data.feed_score.value_counts()
                
                # Pie chart for user ratings
                st.subheader("**User Rating's**")
                fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5 🤗", color_discrete_sequence=px.colors.sequential.Aggrnyl)
                st.plotly_chart(fig)

                # fetching Predicted_Field from the query and getting the unique values and total value count                 
                labels = plot_data.Predicted_Field.unique()
                values = plot_data.Predicted_Field.value_counts()

                # Pie chart for predicted field recommendations
                st.subheader("🎯 Predicted Field Recommendations")
                fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills 👽', color_discrete_sequence=px.colors.sequential.Aggrnyl_r)
                st.plotly_chart(fig)

                # fetching User_Level from the query and getting the unique values and total value count                 
                labels = plot_data.User_Level.unique()
                values = plot_data.User_Level.value_counts()

                # Pie chart for User's👨‍💻 Experienced Level
                st.subheader("💼 User Experience Levels")
                fig = px.pie(df, values=values, names=labels, title="Pie-Chart 📈 for User's 👨‍💻 Experienced Level", color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig)

                # fetching resume_score from the query and getting the unique values and total value count                 
                labels = plot_data.resume_score.unique()                
                values = plot_data.resume_score.value_counts()

                # Pie chart for Resume Score
                st.subheader("📑 Resume Score Distribution")
                fig = px.pie(df, values=values, names=labels, title='From 1 to 100 💯', color_discrete_sequence=px.colors.sequential.Agsunset)
                st.plotly_chart(fig)

                # fetching IP_add from the query and getting the unique values and total value count 
                labels = plot_data.IP_add.unique()
                values = plot_data.IP_add.value_counts()

                # Pie chart for Users
                st.subheader("**Pie-Chart for Users App Used Count**")
                fig = px.pie(df, values=values, names=labels, title='Usage Based On IP Address 👥', color_discrete_sequence=px.colors.sequential.matter_r)
                st.plotly_chart(fig)

                # fetching City from the query and getting the unique values and total value count 
                labels = plot_data.City.unique()
                values = plot_data.City.value_counts()

                # Create a subplot figure with 1 row and 3 columns

                from plotly.subplots import make_subplots

                # Define custom color palettes for each pie chart
                city_colors = px.colors.sequential.Blackbody_r  # Jet color scheme for City
                state_colors = px.colors.sequential.Blackbody  # PuBu_r for State
                country_colors = px.colors.sequential.Purpor_r  # Purpor_r for Country

                # Create a subplot figure with 1 row and 3 columns
                fig = make_subplots(rows=1, cols=3, subplot_titles=("City 🌆", "State 🚉", "Country 🌏"), specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]])

                # Pie chart for City with custom colors
                fig.add_trace(go.Pie(values=plot_data.City.value_counts().values, 
                                    labels=plot_data.City.value_counts().index, 
                                    name="City",
                                    marker=dict(colors=city_colors)),  # Applying custom colors
                            row=1, col=1)

                # Pie chart for State with custom colors
                fig.add_trace(go.Pie(values=plot_data.State.value_counts().values, 
                                    labels=plot_data.State.value_counts().index, 
                                    name="State",
                                    marker=dict(colors=state_colors)),  # Applying custom colors
                            row=1, col=2)

                # Pie chart for Country with custom colors
                fig.add_trace(go.Pie(values=plot_data.Country.value_counts().values, 
                                    labels=plot_data.Country.value_counts().index, 
                                    name="Country",
                                    marker=dict(colors=country_colors)),  # Applying custom colors
                            row=1, col=3)

                # Update layout
                fig.update_layout(title_text="Usage Distribution: City, State, and Country", showlegend=False)

                # Display in Streamlit
                st.subheader("**Geographical Usage Distribution**")
                st.plotly_chart(fig)


            ## For Wrong Credentials
            else:
                st.error("Wrong ID & Password Provided")

# Calling the main (run()) function to make the whole process run
run()
