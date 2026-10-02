import os
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
from urllib.parse import urlsplit

APP_DIR=Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0,str(APP_DIR))
from password_auth import hash_password, verify_password
from email_verification import (
    EmailProviderAuthError,
    EmailProviderResponseError,
    DEFAULT_FROM_ADDRESS,
    VERIFICATION_RECIPIENT,
    create_verification_code,
    hash_verification_code,
    send_verification_email,
    verify_verification_code,
)

DB=Path(os.environ.get('STUDENT_TRACKER_DB_PATH', APP_DIR/'leetcode_tracker.db')).expanduser()
GQL='https://leetcode.com/graphql'

st.set_page_config(page_title='LeetCode Student Tracker',page_icon='🏆',layout='wide')

if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def apply_theme(theme_name):
    if theme_name == 'light':
        color_scheme = 'light'
        primary_bg = '#f8fafc'
        secondary_bg = '#e2e8f0'
        panel_bg = '#ffffff'
        panel_soft = '#f1f5f9'
        text_color = '#0f172a'
        muted = '#475569'
        border = 'rgba(15, 23, 42, 0.10)'
        metric_bg = 'rgba(14, 165, 233, 0.08)'
        button_grad1 = '#0ea5e9'
        button_grad2 = '#2563eb'
        sidebar_bg = '#f8fafc'
        sidebar_text = '#0f172a'
    else:
        color_scheme = 'dark'
        primary_bg = '#020817'
        secondary_bg = '#0f172a'
        panel_bg = '#111827'
        panel_soft = '#1e293b'
        text_color = '#e2e8f0'
        muted = '#94a3b8'
        border = 'rgba(148, 163, 184, 0.2)'
        metric_bg = 'rgba(15, 118, 110, 0.12)'
        button_grad1 = '#0ea5e9'
        button_grad2 = '#2563eb'
        sidebar_bg = '#0f172a'
        sidebar_text = '#e2e8f0'

    st.markdown(f'''
    <style>
        :root {{
            --app-bg: {primary_bg};
            --app-bg-2: {secondary_bg};
            --panel-bg: {panel_bg};
            --panel-soft: {panel_soft};
            --text: {text_color};
            --muted: {muted};
            --border: {border};
            --accent: #0ea5e9;
            --sidebar-bg: {sidebar_bg};
            --sidebar-text: {sidebar_text};
        }}

        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stSidebar"], .main, .block-container {{
            background: linear-gradient(135deg, var(--app-bg) 0%, var(--app-bg-2) 35%, var(--panel-bg) 100%);
            color: var(--text) !important;
            color-scheme: {color_scheme};
        }}

        .stApp {{
            color: var(--text) !important;
        }}

        .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown strong,
        [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
        [data-testid="stTextInput"] label, [data-testid="stNumberInput"] label,
        [data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label,
        [data-testid="stDateInput"] label, [data-testid="stTimeInput"] label,
        [data-testid="stTextArea"] label, [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label, [data-testid="stFileUploader"] label,
        .stTabs [role="tab"], h1, h2, h3, h4, h5, h6 {{
            color: var(--text) !important;
        }}

        [data-testid="stDataFrameContainer"] *, [data-testid="stTable"] * {{
            color: var(--text) !important;
        }}

        .main .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }}

        [data-testid="stSidebar"] {{
            background: var(--sidebar-bg);
            color: var(--sidebar-text);
            border-right: 1px solid var(--border);
        }}

        [data-testid="stSidebar"] .stRadio > div {{
            gap: 0.55rem;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label {{
            background: rgba(14, 165, 233, 0.06);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.55rem 0.7rem;
            margin-bottom: 0.35rem;
            color: var(--sidebar-text);
            transition: all 0.2s ease;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            border-color: rgba(14, 165, 233, 0.8);
            transform: translateX(2px);
        }}

        [data-testid="stMetricValue"] {{
            font-size: 1.5rem !important;
            color: var(--text) !important;
        }}

        div[data-testid="stMetric"] {{
            background: {metric_bg};
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0.9rem 1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        }}

        div[data-testid="stMetricLabel"] {{
            color: var(--muted) !important;
        }}

        [data-testid="stDataFrame"] {{
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid var(--border);
            background: var(--panel-bg);
        }}

        .stAlert {{
            border-radius: 12px;
            border: 1px solid var(--border);
            background: var(--panel-soft);
            color: var(--text);
        }}

        .stButton > button {{
            background: linear-gradient(135deg, {button_grad1}, {button_grad2});
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            padding: 0.55rem 1rem;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}

        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 10px 22px rgba(14, 165, 233, 0.25);
        }}

        .stDownloadButton > button {{
            background: linear-gradient(135deg, #22c55e, #16a34a);
            border: none;
            border-radius: 10px;
            font-weight: 600;
        }}

        [data-baseweb="input"], [data-baseweb="textarea"],
        [data-baseweb="select"] > div, select {{
            border-radius: 8px;
            border: 1px solid var(--border) !important;
            background-color: var(--panel-soft) !important;
            color: var(--text) !important;
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="select"] [role="combobox"], select {{
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
            background-color: var(--panel-soft) !important;
            caret-color: var(--text) !important;
        }}

        input::placeholder, textarea::placeholder {{
            color: var(--muted) !important;
            -webkit-text-fill-color: var(--muted) !important;
            opacity: 1;
        }}

        [data-baseweb="input"]:focus-within,
        [data-baseweb="textarea"]:focus-within,
        [data-baseweb="select"]:focus-within,
        [data-testid="stNumberInput"] [data-baseweb="input"]:focus-within {{
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.18) !important;
        }}

        [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        [data-testid="stSidebar"] [data-testid="stNumberInput"] label,
        [data-testid="stSidebar"] [data-testid="stNumberInput"] input,
        [data-testid="stSidebar"] [data-testid="stRadio"] label {{
            color: var(--sidebar-text) !important;
            -webkit-text-fill-color: var(--sidebar-text) !important;
        }}

        [data-testid="stSidebar"] [data-testid="stNumberInput"] [data-baseweb="input"] {{
            background-color: var(--panel-soft) !important;
            border: 1px solid var(--border) !important;
        }}

        [data-testid="stSidebar"] [data-testid="stNumberInput"] input {{
            background-color: var(--panel-soft) !important;
        }}

        [data-testid="stSidebar"] [data-testid="stNumberInput"] button {{
            color: var(--sidebar-text) !important;
            background: var(--panel-soft) !important;
            border-color: var(--border) !important;
        }}

        [data-testid="stSidebar"] [data-testid="stNumberInput"] button svg {{
            fill: var(--sidebar-text) !important;
            stroke: var(--sidebar-text) !important;
        }}

        [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {{
            background-color: var(--panel-bg) !important;
            border: 1px solid var(--border) !important;
        }}

        [data-baseweb="popover"] *, [data-baseweb="menu"] *, [role="listbox"] * {{
            color: var(--text) !important;
        }}

        [role="option"] {{
            background-color: var(--panel-bg) !important;
            color: var(--text) !important;
        }}

        [role="option"]:hover, [role="option"][aria-selected="true"] {{
            background-color: var(--panel-soft) !important;
        }}

        input[type="checkbox"], input[type="radio"] {{
            accent-color: var(--accent);
        }}

        [data-testid="stFileUploaderDropzone"] {{
            background-color: var(--panel-soft) !important;
            border: 1px dashed var(--border) !important;
        }}

        [data-testid="stFileUploaderDropzone"] button {{
            color: var(--text) !important;
            background-color: var(--panel-bg) !important;
            border: 1px solid var(--border) !important;
        }}

        .stTabs [role="tablist"] {{
            gap: 0.5rem;
        }}

        .stTabs [role="tab"] {{
            background: var(--panel-soft);
            border: 1px solid var(--border);
            border-radius: 10px 10px 0 0;
            color: var(--muted) !important;
            padding: 0.5rem 0.8rem;
        }}

        .stTabs [role="tab"][aria-selected="true"] {{
            background: linear-gradient(180deg, rgba(14, 165, 233, 0.18), rgba(14, 165, 233, 0.08));
            color: var(--text) !important;
            border-bottom-color: transparent;
        }}

        .stMarkdown {{
            color: var(--text);
        }}

        .block-container {{
            max-width: 1500px !important;
        }}
    </style>
    ''', unsafe_allow_html=True)

apply_theme(st.session_state.theme)

# ---------- DB ----------
def conn():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB,timeout=30)
    c.execute('CREATE TABLE IF NOT EXISTS admin_users(account_id INTEGER PRIMARY KEY CHECK(account_id=1), username TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL, created_at TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS signup_email_rate_limit(recipient TEXT PRIMARY KEY, window_started_at REAL NOT NULL, last_sent_at REAL NOT NULL, send_count INTEGER NOT NULL)')
    c.execute('''CREATE TABLE IF NOT EXISTS students(
      student_id TEXT PRIMARY KEY, usn TEXT, name TEXT NOT NULL, section TEXT, batch TEXT,
      leetcode_username TEXT NOT NULL UNIQUE)''')
    cols={row[1] for row in c.execute('PRAGMA table_info(students)')}
    if 'batch' not in cols:
        c.execute('ALTER TABLE students ADD COLUMN batch TEXT')
    c.execute('''CREATE TABLE IF NOT EXISTS stats(
      student_id TEXT PRIMARY KEY, total_solved INTEGER DEFAULT 0,
      easy_solved INTEGER DEFAULT 0, medium_solved INTEGER DEFAULT 0,
      hard_solved INTEGER DEFAULT 0, total_submissions INTEGER DEFAULT 0,
      accepted_submissions INTEGER DEFAULT 0, acceptance_rate REAL DEFAULT 0,
      last_submission TEXT, leetcode_rank INTEGER, updated_at TEXT,
      data_status TEXT DEFAULT 'demo')''')
    c.execute('''CREATE TABLE IF NOT EXISTS submissions(
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, title TEXT,
      title_slug TEXT, difficulty TEXT, status TEXT, language TEXT,
      submitted_at TEXT, UNIQUE(student_id,title_slug,submitted_at,status))''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_activity(
      student_id TEXT, activity_date TEXT, submissions INTEGER DEFAULT 0,
      accepted INTEGER DEFAULT 0, PRIMARY KEY(student_id,activity_date))''')
    c.commit(); return c

def get_app_secret(name):
    try:
        value=st.secrets.get(name,'')
    except (FileNotFoundError,KeyError):
        value=''
    return str(value or os.environ.get(name,'')).strip()

def reserve_signup_email_slot():
    now=time.time()
    c=conn()
    try:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT window_started_at,last_sent_at,send_count FROM signup_email_rate_limit WHERE recipient=?',(VERIFICATION_RECIPIENT,)).fetchone()
        if row is None:
            c.execute('INSERT INTO signup_email_rate_limit VALUES(?,?,?,1)',(VERIFICATION_RECIPIENT,now,now))
        elif now-row[0]>=3600:
            c.execute('UPDATE signup_email_rate_limit SET window_started_at=?,last_sent_at=?,send_count=1 WHERE recipient=?',(now,now,VERIFICATION_RECIPIENT))
        elif now-row[1]<60:
            c.rollback()
            return False,max(1,int(60-(now-row[1])))
        elif row[2]>=5:
            c.rollback()
            return False,max(1,int(3600-(now-row[0])))
        else:
            c.execute('UPDATE signup_email_rate_limit SET last_sent_at=?,send_count=send_count+1 WHERE recipient=?',(now,VERIFICATION_RECIPIENT))
        c.commit()
        return True,0
    finally:
        c.close()

def start_signup_email_verification(username,password=None,password_hash=None):
    api_key=get_app_secret('RESEND_API_KEY')
    sender=get_app_secret('RESEND_FROM_EMAIL') or DEFAULT_FROM_ADDRESS
    if not api_key:
        return None,'Configure RESEND_API_KEY in Streamlit Cloud Secrets first.'
    allowed,retry_after=reserve_signup_email_slot()
    if not allowed:
        return None,f'Please wait {retry_after} seconds before requesting another code.'
    code=create_verification_code()
    try:
        send_verification_email(code,api_key,sender)
    except EmailProviderAuthError:
        return None,'Resend rejected the API key. Check RESEND_API_KEY in Streamlit Cloud Secrets.'
    except EmailProviderResponseError as error:
        return None,f'Resend rejected the email request (HTTP {error.status_code}). Check the API key and verified sender address.'
    except requests.RequestException as error:
        return None,f'Could not reach the Resend HTTPS API ({type(error).__name__}). Check Cloud logs and try again.'
    salt,digest=hash_verification_code(code)
    now=time.time()
    return {
        'username':username,
        'password_hash':password_hash or hash_password(password),
        'code_salt':salt,
        'code_digest':digest,
        'expires_at':now+600,
        'sent_at':now,
        'attempts':0,
    },None

def seed_demo():
    c=conn()
    if c.execute('SELECT COUNT(*) FROM students').fetchone()[0]: c.close(); return
    rows=[
      ('S001','1CM23AI001','Aarav','A','2023','aarav_demo'),('S002','1CM23AI002','Ananya','A','2023','ananya_demo'),
      ('S003','1CM23AI003','Arjun','A','2024','arjun_demo'),('S004','1CM23AI004','Diya','A','2024','diya_demo'),
      ('S005','1CM23AI005','Kiran','A','2025','kiran_demo'),('S006','1CM23AI006','Meera','A','2025','meera_demo'),
      ('S007','1CM23AI007','Rahul','B','2023','rahul_demo'),('S008','1CM23AI008','Priya','B','2023','priya_demo'),
      ('S009','1CM23AI009','Rohan','B','2024','rohan_demo'),('S010','1CM23AI010','Sneha','B','2024','sneha_demo'),
      ('S011','1CM23AI011','Vivek','B','2025','vivek_demo'),('S012','1CM23AI012','Nisha','B','2025','nisha_demo')]
    c.executemany('INSERT INTO students(student_id,usn,name,section,batch,leetcode_username) VALUES(?,?,?,?,?,?)',rows)
    import random; random.seed(7); now=datetime.now(timezone.utc)
    for i,r in enumerate(rows):
        total=random.randint(12,140); easy=random.randint(5,max(6,total//2)); hard=random.randint(0,max(1,total//8)); medium=max(0,total-easy-hard)
        days=random.randint(0,16); last=now-timedelta(days=days,hours=random.randint(0,18)); subs=total+random.randint(10,90); acc=min(subs,total+random.randint(0,25)); rate=round(acc/subs*100,2)
        c.execute('INSERT INTO stats VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(r[0],total,easy,medium,hard,subs,acc,rate,last.isoformat(),random.randint(10000,2500000),now.isoformat(),'demo'))
        for d in range(30):
            if random.random()<.45:
                day=(now-timedelta(days=d)).date().isoformat(); n=random.randint(1,6); a=random.randint(0,n)
                c.execute('INSERT OR REPLACE INTO daily_activity VALUES(?,?,?,?)',(r[0],day,n,a))
    c.commit(); c.close()
if not DB.exists():
    seed_demo()

PROFILE='''query userProfile($username:String!){matchedUser(username:$username){username profile{ranking reputation} submitStats{acSubmissionNum{difficulty count submissions} totalSubmissionNum{difficulty count submissions}}}}'''
RECENT='''query recentSubmissionList($username:String!,$limit:Int!){recentSubmissionList(username:$username,limit:$limit){title titleSlug timestamp statusDisplay lang}}'''

def normalize_username(value):
    username=str(value or '').strip()
    if 'leetcode.com' in username:
        url=username if '://' in username else 'https://'+username
        username=urlsplit(url).path
    username=username.strip('/')
    if username.startswith('u/'):
        username=username[2:]
    if '/' in username:
        username=username.rsplit('/',1)[-1]
    return username

def username_key(value):
    return normalize_username(value).casefold()

def next_student_id():
    c=conn(); count=c.execute('SELECT COUNT(*) FROM students').fetchone()[0]; c.close();
    return f'S{count+1:03d}'

def prepare_student_import(incoming,existing_students):
    existing_usernames={username_key(username) for _,username in existing_students}
    existing_ids={student_id for student_id,_ in existing_students}
    seen_usernames=set(); seen_ids=set(); added=[]
    duplicate_usernames=0; duplicate_ids=0; invalid_rows=0
    for values in incoming.itertuples(index=False,name=None):
        values=tuple('' if pd.isna(value) else str(value).strip() for value in values)
        student=(values[0],values[1],values[2],values[3],values[4],normalize_username(values[5]))
        if not student[0] or not student[2] or not student[5]:
            invalid_rows+=1
            continue
        key=username_key(student[5])
        if key in existing_usernames or key in seen_usernames:
            duplicate_usernames+=1
            continue
        if student[0] in existing_ids or student[0] in seen_ids:
            duplicate_ids+=1
            continue
        added.append(student); seen_usernames.add(key); seen_ids.add(student[0])
    return added,duplicate_usernames,duplicate_ids,invalid_rows

def profile_url(value):
    return f"https://leetcode.com/u/{quote(normalize_username(value),safe='')}/"

def kolkata_time(value):
    if pd.isna(value) or value == '':
        return value
    if isinstance(value, str):
        text=value.strip()
        if not text:
            return value
        try:
            dt=datetime.fromisoformat(text.replace('Z','+00:00'))
        except ValueError:
            return value
    elif isinstance(value, datetime):
        dt=value
    else:
        return value
    if dt.tzinfo is None:
        dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')

def linked_profiles(data):
    linked=data.copy()
    if 'last_submission' in linked.columns:
        linked['last_submission']=linked['last_submission'].apply(kolkata_time)
    linked['leetcode_username']=linked['leetcode_username'].apply(profile_url)
    return linked

PROFILE_LINK_CONFIG={'leetcode_username':st.column_config.LinkColumn('LeetCode Username',display_text=r'https://leetcode\.com/u/([^/]+)/?')}

def gql(q,v):
    r=requests.post(GQL,json={'query':q,'variables':v},headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0','Referer':'https://leetcode.com/'},timeout=20)
    try: j=r.json()
    except ValueError as ex:
        try: r.raise_for_status()
        except requests.HTTPError as http_ex: raise RuntimeError(f'LeetCode returned HTTP {r.status_code} without a GraphQL response') from http_ex
        raise RuntimeError('LeetCode returned an invalid JSON response') from ex
    if j.get('errors'):
        messages=[error.get('message',str(error)) if isinstance(error,dict) else str(error) for error in j['errors']]
        raise RuntimeError('; '.join(messages))
    r.raise_for_status()
    return j.get('data',{})

@st.cache_data(ttl=900)
def fetch_profile(u):
    user=gql(PROFILE,{'username':u}).get('matchedUser')
    if not user: raise ValueError('LeetCode user not found: '+u)
    ac={x['difficulty']:x for x in user['submitStats']['acSubmissionNum']}; tot={x['difficulty']:x for x in user['submitStats']['totalSubmissionNum']}
    return dict(total_solved=ac.get('All',{}).get('count',0),easy_solved=ac.get('Easy',{}).get('count',0),medium_solved=ac.get('Medium',{}).get('count',0),hard_solved=ac.get('Hard',{}).get('count',0),total_submissions=tot.get('All',{}).get('submissions',0),accepted_submissions=ac.get('All',{}).get('submissions',0),acceptance_rate=round(ac.get('All',{}).get('submissions',0)/tot.get('All',{}).get('submissions',1)*100,2),leetcode_rank=user.get('profile',{}).get('ranking'))

@st.cache_data(ttl=900)
def fetch_recent(u): return gql(RECENT,{'username':u,'limit':20}).get('recentSubmissionList') or []

def sync_one(sid,u):
    u=normalize_username(u)
    p=fetch_profile(u); rec=fetch_recent(u); last=None
    if rec:
        ts=[int(x['timestamp']) for x in rec if x.get('timestamp')]
        if ts: last=datetime.fromtimestamp(max(ts),timezone.utc).isoformat()
    now=datetime.now(timezone.utc).isoformat(); c=conn()
    c.execute('''INSERT INTO stats VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(student_id) DO UPDATE SET total_solved=excluded.total_solved,easy_solved=excluded.easy_solved,medium_solved=excluded.medium_solved,hard_solved=excluded.hard_solved,total_submissions=excluded.total_submissions,accepted_submissions=excluded.accepted_submissions,acceptance_rate=excluded.acceptance_rate,last_submission=excluded.last_submission,leetcode_rank=excluded.leetcode_rank,updated_at=excluded.updated_at,data_status='live' ''',(sid,p['total_solved'],p['easy_solved'],p['medium_solved'],p['hard_solved'],p['total_submissions'],p['accepted_submissions'],p['acceptance_rate'],last,p['leetcode_rank'],now,'live'))
    for x in rec:
        ts=x.get('timestamp'); submitted=datetime.fromtimestamp(int(ts),timezone.utc).isoformat() if ts else None
        c.execute('INSERT OR IGNORE INTO submissions(student_id,title,title_slug,difficulty,status,language,submitted_at) VALUES(?,?,?,?,?,?,?)',(sid,x.get('title',''),x.get('titleSlug',''),'Unknown',x.get('statusDisplay',''),x.get('lang',''),submitted))
        if submitted:
            day=submitted[:10]; ok=1 if x.get('statusDisplay')=='Accepted' else 0
            c.execute('''INSERT INTO daily_activity VALUES(?,?,1,?) ON CONFLICT(student_id,activity_date) DO UPDATE SET submissions=submissions+1,accepted=accepted+excluded.accepted''',(sid,day,ok))
    c.commit(); c.close()

def load():
    c=conn(); q='''SELECT s.*,st.total_solved,st.easy_solved,st.medium_solved,st.hard_solved,st.total_submissions,st.accepted_submissions,st.acceptance_rate,st.last_submission,st.leetcode_rank,st.updated_at,st.data_status FROM students s LEFT JOIN stats st ON s.student_id=st.student_id'''; d=pd.read_sql_query(q,c); c.close(); return d

def enrich(d,active=2,attention=7):
    d=d.copy(); now=datetime.now(timezone.utc)
    def days(x):
        if not isinstance(x,str) or not x:return None
        try:return round((now-datetime.fromisoformat(x.replace('Z','+00:00'))).total_seconds()/86400,1)
        except:return None
    d['days_since_activity']=d.last_submission.apply(days)
    d['activity_status']=d.days_since_activity.apply(lambda x:'No data' if x is None else ('Active' if x<=active else ('Needs Attention' if x<=attention else 'Inactive')))
    for col in ['total_solved','easy_solved','medium_solved','hard_solved','total_submissions','accepted_submissions']: d[col]=pd.to_numeric(d[col],errors='coerce').fillna(0)
    d['difficulty_score']=d.easy_solved+2*d.medium_solved+3*d.hard_solved
    return d

# ---------- UI ----------
st.sidebar.title('⚙️ Controls')
st.session_state.theme = st.sidebar.radio('Theme', ['dark', 'light'], index=0 if st.session_state.theme == 'dark' else 1, horizontal=True)
page=st.sidebar.radio('Navigate',['Overview','Students','Leaderboard','Analytics','Data Management'])
active=st.sidebar.number_input('Active ≤ days',1,30,2); attention=st.sidebar.number_input('Needs Attention ≤ days',2,60,7)
apply_theme(st.session_state.theme)
df=enrich(load(),active,attention)
st.title('🏆 LeetCode Student Tracker')
st.caption('Faculty dashboard for student problem-solving activity, difficulty distribution, recorded submission activity and leaderboard.')

if page=='Overview':
    st.subheader('Class Overview'); a,b,c,d,e=st.columns(5)
    a.metric('Students',len(df)); b.metric('Active',(df.activity_status=='Active').sum()); c.metric('Needs Attention',(df.activity_status=='Needs Attention').sum()); d.metric('Inactive',(df.activity_status=='Inactive').sum()); e.metric('Total Solved',int(df.total_solved.sum()))
    st.info('“Last active” is represented as the latest recorded submission when the public recent-submission feed exposes a timestamp. A complete lifetime attempted-problem count is not inferred from the profile alone.')
    x,y=st.columns(2)
    with x:
        q=pd.DataFrame({'Difficulty':['Easy','Medium','Hard'],'Solved':[int(df.easy_solved.sum()),int(df.medium_solved.sum()),int(df.hard_solved.sum())]}); st.plotly_chart(px.bar(q,x='Difficulty',y='Solved',text_auto=True,title='Class Difficulty Distribution'),use_container_width=True)
    with y:
        q=df.activity_status.value_counts().rename_axis('Status').reset_index(name='Students'); st.plotly_chart(px.pie(q,names='Status',values='Students',title='Activity Status'),use_container_width=True)
    st.subheader('⚠ Needs Attention'); w=df[df.activity_status.isin(['Needs Attention','Inactive'])]; st.dataframe(linked_profiles(w[['usn','name','section','leetcode_username','total_solved','last_submission','activity_status']]),use_container_width=True,hide_index=True,column_config=PROFILE_LINK_CONFIG)

elif page=='Students':
    sec=st.selectbox('Section',['All']+sorted(df.section.dropna().unique().tolist())); batch=st.selectbox('Batch',['All']+sorted(df.batch.dropna().unique().tolist())); term=st.text_input('Search student / USN / LeetCode username')
    v=df.copy();
    if sec!='All':v=v[v.section==sec]
    if batch!='All':v=v[v.batch==batch]
    if term:
        t=term.lower(); v=v[v.name.str.lower().str.contains(t,na=False)|v.usn.str.lower().str.contains(t,na=False)|v.leetcode_username.str.lower().str.contains(t,na=False)]
    st.dataframe(linked_profiles(v[['usn','name','section','batch','leetcode_username','total_solved','easy_solved','medium_solved','hard_solved','total_submissions','acceptance_rate','last_submission','activity_status','data_status']]),use_container_width=True,hide_index=True,column_config=PROFILE_LINK_CONFIG)
    if len(v):
        sid=st.selectbox('Open student',v.student_id.tolist(),format_func=lambda z:v.loc[v.student_id==z,'name'].iloc[0]); r=v[v.student_id==sid].iloc[0]
        st.markdown(f"### {r['name']} · [{r['leetcode_username']}]({profile_url(r['leetcode_username'])})"); a,b,c,d,e=st.columns(5); a.metric('Solved',int(r.total_solved)); b.metric('Easy',int(r.easy_solved)); c.metric('Medium',int(r.medium_solved)); d.metric('Hard',int(r.hard_solved)); e.metric('Acceptance',f"{float(r.acceptance_rate):.1f}%")
        last_submission_display=kolkata_time(r.last_submission) if pd.notna(r.last_submission) else 'No recorded submission'
        st.write(f"**Last submission:** {last_submission_display} | **Status:** {r.activity_status}")
        q=pd.DataFrame({'Difficulty':['Easy','Medium','Hard'],'Solved':[r.easy_solved,r.medium_solved,r.hard_solved]}); st.plotly_chart(px.bar(q,x='Difficulty',y='Solved',text_auto=True,title='Student Difficulty Profile'),use_container_width=True)
        c=conn(); act=pd.read_sql_query('SELECT activity_date,submissions,accepted FROM daily_activity WHERE student_id=? ORDER BY activity_date',c,params=(sid,)); sub=pd.read_sql_query('SELECT title,difficulty,status,language,submitted_at FROM submissions WHERE student_id=? ORDER BY submitted_at DESC LIMIT 20',c,params=(sid,)); c.close()
        if len(act):st.plotly_chart(px.line(act,x='activity_date',y='submissions',markers=True,title='Recorded Daily Submissions'),use_container_width=True)
        st.subheader('Recent Recorded Submissions'); st.dataframe(sub,use_container_width=True,hide_index=True)

elif page=='Leaderboard':
    st.subheader('🏆 Leaderboard'); mode=st.selectbox('Metric',['Total Problems Solved','Difficulty Score','Weekly Solved','Consistency / Activity']); sec=st.selectbox('Section',['All']+sorted(df.section.dropna().unique().tolist())); lb=df.copy()
    if sec!='All':lb=lb[lb.section==sec]
    if mode=='Total Problems Solved':lb['leaderboard_score']=lb.total_solved; label='Solved'
    elif mode=='Difficulty Score':lb['leaderboard_score']=lb.difficulty_score; label='Score'
    elif mode=='Consistency / Activity':lb['leaderboard_score']=lb.days_since_activity.fillna(30).apply(lambda x:max(0,30-x))*2+lb.total_solved*.1; label='Activity Score'
    else:
        c=conn(); cutoff=(datetime.now(timezone.utc)-timedelta(days=7)).date().isoformat(); w=pd.read_sql_query('SELECT student_id,SUM(accepted) solved FROM daily_activity WHERE activity_date>=? GROUP BY student_id',c,params=(cutoff,)); c.close(); lb=lb.merge(w,on='student_id',how='left'); lb['solved']=lb.solved.fillna(0); lb['leaderboard_score']=lb.solved; label='Solved This Week'
    lb=lb.sort_values(['leaderboard_score','total_solved'],ascending=False).reset_index(drop=True); lb['Rank']=lb.index+1
    top=lb.head(3); cols=st.columns(3); medals=['🥇','🥈','🥉']
    for col,(_,r),m in zip(cols,top.iterrows(),medals):
        with col: st.metric(f'{m} {r.name}',f"{r.leaderboard_score:.0f}"); st.caption(f"{r.leetcode_username} · {r.activity_status}")
    show=['Rank','name','usn','section','leetcode_username','total_solved','easy_solved','medium_solved','hard_solved','leaderboard_score','last_submission','activity_status']; st.dataframe(linked_profiles(lb[show]),use_container_width=True,hide_index=True,column_config=PROFILE_LINK_CONFIG)
    st.download_button('⬇️ Download Leaderboard CSV',lb[show].to_csv(index=False).encode('utf-8'),'leetcode_leaderboard.csv','text/csv')

elif page=='Analytics':
    st.subheader('📊 Analytics'); x,y=st.columns(2)
    with x:
        q=df.sort_values('total_solved',ascending=False); st.plotly_chart(px.bar(q,x='name',y='total_solved',color='section',title='Problems Solved by Student'),use_container_width=True)
    with y:
        q=pd.DataFrame({'Difficulty':['Easy']*len(df)+['Medium']*len(df)+['Hard']*len(df),'Solved':list(df.easy_solved)+list(df.medium_solved)+list(df.hard_solved)}); st.plotly_chart(px.box(q,x='Difficulty',y='Solved',title='Difficulty Distribution Across Students'),use_container_width=True)
    c=conn(); act=pd.read_sql_query('SELECT activity_date,SUM(submissions) submissions,SUM(accepted) accepted FROM daily_activity GROUP BY activity_date ORDER BY activity_date',c); c.close()
    if len(act):st.plotly_chart(px.line(act,x='activity_date',y=['submissions','accepted'],markers=True,title='Class Recorded Submission Activity'),use_container_width=True)

else:
    st.subheader('🛠️ Data Management'); st.write('Upload CSV columns: `student_id, usn, name, section, batch, leetcode_username`. The username field can contain a username or LeetCode profile URL.')
    c=conn()
    admin_account_count=c.execute('SELECT COUNT(*) FROM admin_users').fetchone()[0]
    c.close()
    if st.session_state.get('profile_admin_username'):
        st.success(f"Signed in as {st.session_state['profile_admin_username']}")
        if st.button('Log Out of Profile Management'):
            st.session_state.pop('profile_admin_username',None)
            st.rerun()
    else:
        if st.session_state.pop('admin_signup_success',False):
            st.success('Administrator account created. Sign in with your new credentials.')
        if st.session_state.pop('clear_signup_inputs',False):
            for key in ('admin_signup_username','admin_signup_password','admin_signup_confirmation'):
                st.session_state.pop(key,None)
        if st.session_state.pop('signup_code_expired',False):
            st.warning('The verification code expired. Request a new one to continue signup.')
        sign_in_tab, sign_up_tab=st.tabs(['Sign In','Sign Up'])
        with sign_in_tab:
            with st.form('profile_admin_login'):
                login_username=st.text_input('Username',key='admin_login_username')
                login_password=st.text_input('Password',type='password',key='admin_login_password')
                login_admin=st.form_submit_button('Sign In')
            if login_admin:
                c=conn()
                account=c.execute('SELECT username,password_hash FROM admin_users WHERE username=?',(login_username.strip(),)).fetchone()
                c.close()
                if account and verify_password(login_password,account[1]):
                    st.session_state['profile_admin_username']=account[0]
                    st.rerun()
                else:
                    st.error('Incorrect username or password.')
        with sign_up_tab:
            if admin_account_count:
                st.info('The administrator account is already registered. Sign in to continue.')
            else:
                pending_signup=st.session_state.get('pending_admin_signup')
                if pending_signup and time.time()>=pending_signup['expires_at']:
                    st.session_state.pop('pending_admin_signup',None)
                    st.session_state['signup_code_expired']=True
                    st.rerun()
                if pending_signup and pending_signup['attempts']>=5:
                    st.session_state.pop('pending_admin_signup',None)
                    st.error('Too many incorrect codes. Start signup again to request a new code.')
                    pending_signup=None
                if pending_signup:
                    st.info(f"Enter the six-digit code sent to {VERIFICATION_RECIPIENT}. It expires in 10 minutes.")
                    with st.form('verify_admin_email_code'):
                        entered_code=st.text_input('Email verification code',max_chars=6)
                        verify_code=st.form_submit_button('Verify Code and Create Account')
                        resend_code=st.form_submit_button('Resend Code')
                    if resend_code:
                        new_pending,error=start_signup_email_verification(pending_signup['username'],password_hash=pending_signup['password_hash'])
                        if error:
                            st.error(error)
                        else:
                            pending_signup.update(new_pending)
                            st.session_state['pending_admin_signup']=pending_signup
                            st.success(f'A new verification code was sent to {VERIFICATION_RECIPIENT}.')
                            st.rerun()
                    elif verify_code:
                        if verify_verification_code(entered_code,pending_signup['code_salt'],pending_signup['code_digest']):
                            c=conn()
                            account_created=False
                            account_exists=False
                            try:
                                c.execute('BEGIN IMMEDIATE')
                                account_exists=c.execute('SELECT 1 FROM admin_users LIMIT 1').fetchone() is not None
                                if not account_exists:
                                    c.execute('INSERT INTO admin_users(account_id,username,password_hash,created_at) VALUES(1,?,?,?)',(pending_signup['username'],pending_signup['password_hash'],datetime.now(timezone.utc).isoformat()))
                                    c.commit()
                                    account_created=True
                                else:
                                    c.rollback()
                            except sqlite3.IntegrityError:
                                c.rollback()
                                account_exists=True
                            finally:
                                c.close()
                            if account_created:
                                st.session_state.pop('pending_admin_signup',None)
                                st.session_state['admin_signup_success']=True
                                st.rerun()
                            if account_exists:
                                st.session_state.pop('pending_admin_signup',None)
                                st.error('An administrator account already exists. Sign in to continue.')
                        else:
                            pending_signup['attempts']+=1
                            st.session_state['pending_admin_signup']=pending_signup
                            if pending_signup['attempts']>=5:
                                st.session_state.pop('pending_admin_signup',None)
                                st.error('Too many incorrect codes. Start signup again to request a new code.')
                            else:
                                st.error(f"Incorrect code. {5-pending_signup['attempts']} attempt(s) remaining.")
                else:
                    st.info('Create the first administrator account. Email verification is required; signup closes after the account is created.')
                    with st.form('profile_admin_signup'):
                        signup_username=st.text_input('Choose a username',max_chars=64,key='admin_signup_username')
                        signup_password=st.text_input('Choose a password (at least 12 characters)',type='password',key='admin_signup_password')
                        signup_confirmation=st.text_input('Confirm password',type='password',key='admin_signup_confirmation')
                        request_signup_code=st.form_submit_button('Send Verification Code')
                    if request_signup_code:
                        username=signup_username.strip()
                        if len(username)<3:
                            st.error('Username must contain at least 3 characters.')
                        elif len(signup_password)<12:
                            st.error('Password must contain at least 12 characters.')
                        elif signup_password!=signup_confirmation:
                            st.error('Passwords do not match.')
                        else:
                            pending_signup,error=start_signup_email_verification(username,signup_password)
                            if error:
                                st.error(error)
                            else:
                                st.session_state['pending_admin_signup']=pending_signup
                                st.session_state['clear_signup_inputs']=True
                                st.success(f'A verification code was sent to {VERIFICATION_RECIPIENT}.')
                                st.rerun()
    profile_admin_authorized=bool(st.session_state.get('profile_admin_username'))
    if not profile_admin_authorized:
        st.info('Sign in as the administrator to add, delete, or import student profiles.')
    st.subheader('Add One Student')
    with st.form('add_student_form', clear_on_submit=True):
        generated_student_id=next_student_id()
        a,b=st.columns(2)
        student_id=a.text_input('Student ID', value=generated_student_id)
        usn=b.text_input('USN (optional)')
        name=a.text_input('Name')
        section=a.text_input('Section (optional)')
        batch=b.text_input('Batch (optional)')
        leetcode_username=st.text_input('LeetCode Username or Profile URL',placeholder='https://leetcode.com/u/username/')
        add_student=st.form_submit_button('Add Student',disabled=not profile_admin_authorized)
    if add_student and profile_admin_authorized:
        student=(student_id.strip(),usn.strip(),name.strip(),section.strip(),batch.strip(),normalize_username(leetcode_username))
        if not student[0] or not student[2] or not student[5]:
            st.error('Student ID, name, and LeetCode username are required.')
        else:
            c=conn()
            try:
                usernames={username_key(row[0]) for row in c.execute('SELECT leetcode_username FROM students')}
                if username_key(student[5]) in usernames:
                    st.warning('This LeetCode username is already registered (1 existing username). Student was not added.')
                else:
                    c.execute('INSERT INTO students(student_id,usn,name,section,batch,leetcode_username) VALUES(?,?,?,?,?,?)',student)
                    c.commit()
                    st.success(f'Added {student[2]}. Use Live Data Sync below to fetch their profile.')
            except sqlite3.IntegrityError:
                st.error('That Student ID is already registered; student was not added.')
            finally:
                c.close()
    st.subheader('Delete Student')
    if len(df):
        with st.form('delete_student_form'):
            delete_id=st.selectbox('Student to delete',df.student_id.tolist(),format_func=lambda sid:f"{df.loc[df.student_id==sid,'name'].iloc[0]} ({sid})")
            confirm_delete=st.checkbox('Permanently delete this student and their recorded activity')
            delete_student=st.form_submit_button('Delete Student',disabled=not profile_admin_authorized)
        if delete_student and profile_admin_authorized:
            if not confirm_delete:
                st.warning('Check the confirmation box before deleting a student.')
            else:
                c=conn()
                try:
                    c.execute('DELETE FROM daily_activity WHERE student_id=?',(delete_id,))
                    c.execute('DELETE FROM submissions WHERE student_id=?',(delete_id,))
                    c.execute('DELETE FROM stats WHERE student_id=?',(delete_id,))
                    c.execute('DELETE FROM students WHERE student_id=?',(delete_id,))
                    c.commit()
                    st.success('Student and recorded activity deleted.')
                finally:
                    c.close()
    else:
        st.caption('No students are currently available to delete.')
    st.divider()
    st.subheader('Bulk Upload')
    st.caption('Duplicate usernames are skipped and counted. Add mode keeps the existing roster; replace mode clears it before importing.')
    template=pd.DataFrame([{'student_id':'S001','usn':'1CM23AI001','name':'Student Name','section':'A','batch':'2024','leetcode_username':'leetcode_username'}]); st.download_button('Download CSV Template',template.to_csv(index=False).encode('utf-8'),'students_template.csv','text/csv')
    up=st.file_uploader('Upload student CSV',type='csv')
    if up:
        incoming=pd.read_csv(up); required=['student_id','usn','name','section','batch','leetcode_username']; missing=set(required)-set(incoming.columns)
        if missing: st.error('Missing columns: '+', '.join(sorted(missing)))
        else:
            st.dataframe(incoming,use_container_width=True,hide_index=True)
            import_mode=st.selectbox('Import mode',['Add new students','Replace student list'])
            if st.button('Process Student CSV',disabled=not profile_admin_authorized) and profile_admin_authorized:
                c=conn()
                try:
                    existing=c.execute('SELECT student_id,leetcode_username FROM students').fetchall() if import_mode=='Add new students' else []
                    added,duplicate_usernames,duplicate_ids,invalid_rows=prepare_student_import(incoming[required],existing)
                    if added:
                        if import_mode=='Replace student list':
                            c.execute('DELETE FROM daily_activity'); c.execute('DELETE FROM submissions'); c.execute('DELETE FROM stats'); c.execute('DELETE FROM students')
                        c.executemany('INSERT INTO students(student_id,usn,name,section,batch,leetcode_username) VALUES(?,?,?,?,?,?)',added)
                        c.commit()
                except Exception:
                    c.rollback()
                    raise
                finally:
                    c.close()
                st.success(f'Added {len(added)} student(s).')
                if duplicate_usernames:
                    st.warning(f'{duplicate_usernames} row(s) with usernames already present were skipped.')
                if duplicate_ids:
                    st.warning(f'{duplicate_ids} row(s) with student IDs already present were skipped.')
                if invalid_rows:
                    st.warning(f'{invalid_rows} row(s) missing a required field were skipped.')
                if added:
                    st.info('Use Live Data Sync below to fetch public profile statistics.')
    st.divider(); st.subheader('🔄 Live Data Sync'); st.warning('Live sync requires each student to have a real, exact LeetCode username. The built-in *_demo usernames are placeholders and will return “That user does not exist.” The collector uses LeetCode public GraphQL responses; fields and availability can change. Use conservative sync intervals and do not bypass access controls or rate limits.')
    if st.button('Sync All Students'):
        c=conn(); ss=pd.read_sql_query('SELECT student_id, name, leetcode_username FROM students',c); c.close(); out=[]
        for _,r in ss.iterrows():
            try: sync_one(r.student_id,r.leetcode_username); out.append([r.name,'OK'])
            except Exception as ex: out.append([r.name,'ERROR: '+str(ex)[:120]])
        st.dataframe(pd.DataFrame(out,columns=['Student','Result']),use_container_width=True,hide_index=True); st.success('Sync completed. Refresh the page to view updated data.')
