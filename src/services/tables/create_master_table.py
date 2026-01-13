import pandas as pd
import numpy as np
import datetime
import os
import sys
from dateutil.relativedelta import relativedelta
from IPython.display import display

# 'src' 디렉토리를 sys.path에 추가하여 'services' 모듈을 찾을 수 있도록 합니다.
script_dir = os.path.dirname(__file__)
src_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# --- 테이블 모듈에서 DataFrame을 직접 임포트 (단일 소스) ---
# HR_Core
from services.tables.HR_Core.basic_info_table import emp_df
from services.tables.HR_Core.absence_info_table import absence_info_df
from services.tables.HR_Core.career_info_table import career_info_df
from services.tables.HR_Core.contract_info_table import contract_info_df
from services.tables.HR_Core.department_table import (
    department_df, dept_level_map, parent_map_dept, dept_name_map
)
from services.tables.HR_Core.department_info_table import department_info_df
from services.tables.HR_Core.job_table import job_df, job_df_indexed, parent_map_job
from services.tables.HR_Core.job_info_table import job_info_df
from services.tables.HR_Core.position_table import position_df
from services.tables.HR_Core.position_info_table import position_info_df
from services.tables.HR_Core.pjt_info_table import pjt_info_df
from services.tables.HR_Core.region_info_table import region_info_df
from services.tables.HR_Core.school_table import school_df
from services.tables.HR_Core.school_info_table import school_info_df
from services.tables.HR_Core.salary_contract_info_table import salary_contract_info_df
# Payroll
from services.tables.Payroll.yearly_payroll_info_table import yearly_payroll_df
# Performance
from services.tables.Performance.evaluation_modified_score_info_table import evaluation_modified_score_df
# Time_Attendance
from services.tables.Time_Attendance.daily_working_info_table import daily_work_info_df
from services.tables.Time_Attendance.detailed_leave_info_table import detailed_leave_info_df
from services.tables.Time_Attendance.leave_type_table import leave_type_df
# helpers
from services.helpers.utils import find_parents, get_level1_ancestor, get_level2_ancestor

# --- 전역 변수 ---
today = datetime.datetime.now().date()
today_ts = pd.to_datetime(today)


# ==============================================================================
# PART 1: ML 마스터 테이블 생성 (기존 create_ml_table.py 로직)
# ==============================================================================

master_df = emp_df[['EMP_ID', 'PERSONAL_ID', 'GENDER', 'NATIONALITY', 'IN_DATE', 'OUT_DATE', 'CURRENT_EMP_YN']].copy()

# --- 2.1. Basic Info Features ---
def calculate_age(pid, base_date):
    try:
        birth_year_prefix = {'1': 1900, '2': 1900, '3': 2000, '4': 2000}
        year = birth_year_prefix[pid[7]] + int(pid[:2])
        month = int(pid[2:4])
        day = int(pid[4:6])
        birth_date = datetime.date(year, month, day)
        return base_date.year - birth_date.year - ((base_date.month, base_date.day) < (birth_date.month, birth_date.day))
    except:
        return np.nan

def calculate_age_at_hiring(row):
    try:
        pid = row['PERSONAL_ID']
        in_date = row['IN_DATE']
        birth_year_prefix = {'1': 1900, '2': 1900, '3': 2000, '4': 2000}
        year = birth_year_prefix[pid[7]] + int(pid[:2])
        month = int(pid[2:4])
        day = int(pid[4:6])
        birth_date = pd.to_datetime(datetime.date(year, month, day))
        return (in_date - birth_date).days / 365.25
    except:
        return np.nan

master_df['AGE'] = master_df.apply(lambda row: calculate_age(row['PERSONAL_ID'], today), axis=1)
master_df['TENURE_DAYS'] = (master_df['OUT_DATE'].fillna(today_ts) - master_df['IN_DATE']).dt.days
master_df['IS_LEAVER'] = np.where(master_df['CURRENT_EMP_YN'] == 'N', 1, 0)
master_df['AGE_AT_HIRING'] = master_df.apply(calculate_age_at_hiring, axis=1)
master_df['TENURE_TO_AGE_RATIO'] = (master_df['TENURE_DAYS'] / (master_df['AGE'] * 365.25)).fillna(0)

# --- 2.2. Career Features ---
if not career_info_df.empty:
    career_summary = career_info_df.groupby('EMP_ID').agg(
        PRIOR_CAREER_DAYS=('CAREER_DURATION', 'sum'),
        NUM_PRIOR_COMPANIES=('CAREER_COMPANY_ID', 'nunique'),
        PRIOR_CAREER_RELEVANCE_RATIO=('CAREER_REL_YN', lambda x: (x == 'Y').mean())
    ).reset_index()
    career_summary['AVG_TENURE_PER_COMPANY'] = (career_summary['PRIOR_CAREER_DAYS'] / career_summary['NUM_PRIOR_COMPANIES']).fillna(0)
    master_df = pd.merge(master_df, career_summary, on='EMP_ID', how='left')

# --- 2.3. School Features ---
if not school_info_df.empty:
    school_info_merged = pd.merge(school_info_df, school_df[['SCHOOL_ID', 'SCHOOL_LEVEL']], on='SCHOOL_ID', how='left')
    degree_order = pd.CategoricalDtype(['전문학사', '학사', '석사', '박사'], ordered=True)
    school_info_merged['EDU_DEGREE_CAT'] = school_info_merged['EDU_DEGREE'].astype(degree_order)
    highest_edu = school_info_merged.sort_values('EDU_DEGREE_CAT', ascending=False).groupby('EMP_ID').first().reset_index()
    highest_edu = highest_edu[['EMP_ID', 'EDU_DEGREE', 'SCHOOL_LEVEL', 'MAJOR_CATEGORY']]
    highest_edu.rename(columns={'EDU_DEGREE': 'HIGHEST_DEGREE', 'SCHOOL_LEVEL': 'FINAL_SCHOOL_LEVEL', 'MAJOR_CATEGORY': 'FINAL_MAJOR_CATEGORY'}, inplace=True)
    highest_edu['IS_STEM_MAJOR'] = np.where(highest_edu['FINAL_MAJOR_CATEGORY'] == 'STEM계열', 1, 0)
    master_df = pd.merge(master_df, highest_edu, on='EMP_ID', how='left')

# --- 2.4. Department, Job, Position, Project Features ---
def get_latest_info(df, date_col, info_cols):
    if df.empty or date_col not in df.columns:
        return pd.DataFrame(columns=['EMP_ID'] + info_cols)
    latest = df.sort_values(by=date_col, ascending=False).groupby('EMP_ID').first().reset_index()
    return latest[['EMP_ID'] + info_cols]

latest_dept = get_latest_info(department_info_df, 'DEP_APP_START_DATE', ['DEP_ID', 'TITLE_INFO'])
latest_dept.rename(columns={'DEP_ID': 'LATEST_DEP_ID', 'TITLE_INFO': 'LATEST_TITLE_INFO'}, inplace=True)

latest_job = get_latest_info(job_info_df, 'JOB_APP_START_DATE', ['JOB_ID'])
latest_job.rename(columns={'JOB_ID': 'LATEST_JOB_ID'}, inplace=True)

latest_pos = get_latest_info(position_info_df, 'GRADE_START_DATE', ['POSITION_ID', 'GRADE_ID'])
latest_pos.rename(columns={'POSITION_ID': 'LATEST_POSITION_ID', 'GRADE_ID': 'LATEST_GRADE_ID'}, inplace=True)

master_df = pd.merge(master_df, latest_dept, on='EMP_ID', how='left')
master_df = pd.merge(master_df, latest_job, on='EMP_ID', how='left')
master_df = pd.merge(master_df, latest_pos, on='EMP_ID', how='left')

dept_map = department_df.set_index('DEP_ID').to_dict('index')
def get_department_hierarchy(dep_id, dept_map):
    hierarchy = {'LATEST_DIVISION_NAME': 'Unknown', 'LATEST_OFFICE_NAME': 'Unknown'}
    if pd.isna(dep_id) or dep_id not in dept_map:
        return pd.Series(hierarchy)
    current_id = dep_id
    for _ in range(10):
        if pd.isna(current_id) or current_id not in dept_map: break
        dep_info = dept_map[current_id]
        dep_name = dep_info.get('DEP_NAME', '')
        if 'Division' in dep_name and hierarchy['LATEST_DIVISION_NAME'] == 'Unknown':
            hierarchy['LATEST_DIVISION_NAME'] = dep_name
        if 'Office' in dep_name and hierarchy['LATEST_OFFICE_NAME'] == 'Unknown':
            hierarchy['LATEST_OFFICE_NAME'] = dep_name
        parent_id = dep_info.get('UP_DEP_ID')
        if pd.isna(parent_id) or parent_id == current_id: break
        current_id = parent_id
    return pd.Series(hierarchy)
dept_hierarchy_cols = master_df['LATEST_DEP_ID'].apply(lambda x: get_department_hierarchy(x, dept_map))
master_df = pd.concat([master_df, dept_hierarchy_cols], axis=1)

job_map = job_df.set_index('JOB_ID').to_dict('index')
def get_job_hierarchy(job_id, job_map):
    hierarchy = {'LATEST_JOB_L1_NAME': 'Unknown', 'LATEST_JOB_L2_NAME': 'Unknown'}
    if pd.isna(job_id) or job_id not in job_map:
        return pd.Series(hierarchy)
    current_id = job_id
    for _ in range(10):
        if pd.isna(current_id) or current_id not in job_map: break
        job_info = job_map[current_id]
        job_level = job_info.get('JOB_LEVEL')
        job_name = job_info.get('JOB_NAME', 'Unknown')
        if job_level == 1 and hierarchy['LATEST_JOB_L1_NAME'] == 'Unknown':
            hierarchy['LATEST_JOB_L1_NAME'] = job_name
        if job_level == 2 and hierarchy['LATEST_JOB_L2_NAME'] == 'Unknown':
            hierarchy['LATEST_JOB_L2_NAME'] = job_name
        parent_id = job_info.get('UP_JOB_ID')
        if pd.isna(parent_id) or parent_id == current_id: break
        current_id = parent_id
    return pd.Series(hierarchy)
job_hierarchy_cols = master_df['LATEST_JOB_ID'].apply(lambda x: get_job_hierarchy(x, job_map))
master_df = pd.concat([master_df, job_hierarchy_cols], axis=1)

if not department_info_df.empty:
    dept_summary = department_info_df.groupby('EMP_ID').agg(
        NUM_DEP_CHANGES=('DEP_ID', 'nunique'),
        AVG_DEP_TENURE_DAYS=('DEP_DURATION', 'mean')
    ).reset_index()
    
    last_dept_change_date = department_info_df.groupby('EMP_ID')['DEP_APP_START_DATE'].max().reset_index().rename(
        columns={'DEP_APP_START_DATE': 'LAST_DEP_CHANGE_DATE'})
    
    # 먼저 필요한 모든 데이터를 master_df에 병합합니다.
    master_df = pd.merge(master_df, dept_summary, on='EMP_ID', how='left')
    master_df = pd.merge(master_df, last_dept_change_date, on='EMP_ID', how='left')

    # 날짜 타입 일관성을 위해 변환합니다.
    master_df['OUT_DATE'] = pd.to_datetime(master_df['OUT_DATE'])
    master_df['LAST_DEP_CHANGE_DATE'] = pd.to_datetime(master_df['LAST_DEP_CHANGE_DATE'])

    # 재직 여부에 따라 종료일을 조건부로 설정합니다.
    end_date_for_calc = np.where(master_df['CURRENT_EMP_YN'] == 'N', 
                                 master_df['OUT_DATE'], 
                                 pd.to_datetime(today_ts))
    
    # 설정된 종료일을 기준으로 기간을 계산합니다.
    master_df['DAYS_SINCE_LAST_DEP_CHANGE'] = (pd.to_datetime(end_date_for_calc) - master_df['LAST_DEP_CHANGE_DATE']).dt.days
    
    # 계산에 사용된 임시 컬럼을 삭제합니다.
    master_df = master_df.drop(columns=['LAST_DEP_CHANGE_DATE'])

if not position_info_df.empty:
    promotions = position_info_df[position_info_df['CHANGE_REASON'] != 'Initial Assignment']
    promo_summary = promotions.groupby('EMP_ID').agg(
        NUM_PROMOTIONS=('GRADE_ID', 'count'),
        AVG_PROMOTION_SPEED_DAYS=('GRADE_DURATION', 'mean')
    ).reset_index()
    last_promo_date = promotions.groupby('EMP_ID')['GRADE_START_DATE'].max().reset_index().rename(columns={'GRADE_START_DATE': 'LAST_PROMO_DATE'})
    promo_summary = pd.merge(promo_summary, last_promo_date, on='EMP_ID', how='left')
    promo_summary['DAYS_SINCE_LAST_PROMOTION'] = (today_ts - promo_summary['LAST_PROMO_DATE']).dt.days
    promo_summary = pd.merge(promo_summary, master_df[['EMP_ID', 'TENURE_DAYS']], on='EMP_ID', how='left')
    promo_summary['PROMOTION_RATE'] = (promo_summary['NUM_PROMOTIONS'] / (promo_summary['TENURE_DAYS'] / 365.25)).fillna(0)
    master_df = pd.merge(master_df, promo_summary[['EMP_ID', 'NUM_PROMOTIONS', 'AVG_PROMOTION_SPEED_DAYS', 'DAYS_SINCE_LAST_PROMOTION', 'PROMOTION_RATE']], on='EMP_ID', how='left')

if not pjt_info_df.empty:
    pjt_summary = pjt_info_df.groupby('EMP_ID').agg(
        NUM_PROJECTS=('PJT_ID', 'nunique'),
        AVG_PROJECT_DURATION=('PJT_DURATION', 'mean')
    ).reset_index()
    master_df = pd.merge(master_df, pjt_summary, on='EMP_ID', how='left')

# --- 2.5. Payroll Features ---
if not yearly_payroll_df.empty:
    current_year = datetime.datetime.now().year
    filtered_payroll_df = yearly_payroll_df[~((yearly_payroll_df['PAY_YEAR'] == str(current_year)))]
    latest_payroll = filtered_payroll_df.sort_values('PAY_YEAR', ascending=False).groupby('EMP_ID').first().reset_index()
    latest_payroll.rename(columns={'TOTAL_PAY': 'LATEST_TOTAL_PAY'}, inplace=True)
    payroll_summary = filtered_payroll_df.groupby('EMP_ID').agg(
        AVG_YOY_GROWTH=('YOY_GROWTH', 'mean'),
        AVG_VARIABLE_PAY_RATIO=('VARIABLE_PAY_RATIO', 'mean')
    ).reset_index()
    payroll_summary['AVG_YOY_GROWTH'] = payroll_summary['AVG_YOY_GROWTH'].clip(-25, 35)
    master_df = pd.merge(master_df, latest_payroll[['EMP_ID', 'LATEST_TOTAL_PAY', 'PAY_YEAR']], on='EMP_ID', how='left')
    master_df = pd.merge(master_df, payroll_summary, on='EMP_ID', how='left')
    if 'IN_DATE' in master_df.columns:
        master_df.loc[master_df['IN_DATE'].dt.year == current_year - 1, 'AVG_YOY_GROWTH'] = 0
        master_df.loc[master_df['IN_DATE'].dt.year == current_year, 'AVG_YOY_GROWTH'] = 0

def annualize_pay_for_partial_years(row):
    if pd.isna(row['LATEST_TOTAL_PAY']) or pd.isna(row['PAY_YEAR']): return row['LATEST_TOTAL_PAY']
    pay_year = int(row['PAY_YEAR'])
    in_date = pd.to_datetime(row['IN_DATE'])
    out_date = pd.to_datetime(row.get('OUT_DATE'))
    if in_date.year == pay_year:
        year_end = pd.to_datetime(f'{pay_year}-12-31')
        effective_end_date = out_date if pd.notna(out_date) and out_date.year == pay_year else year_end
        days_worked = (effective_end_date - in_date).days + 1
        if days_worked <= 0: return np.nan
        return (row['LATEST_TOTAL_PAY'] / days_worked) * 365
    elif pd.notna(out_date) and out_date.year == pay_year:
        year_start = pd.to_datetime(f'{pay_year}-01-01')
        days_worked = (out_date - year_start).days + 1
        if days_worked <= 0: return np.nan
        return (row['LATEST_TOTAL_PAY'] / days_worked) * 365
    else:
        return row['LATEST_TOTAL_PAY']

if 'PAY_YEAR' in master_df.columns:
    master_df['LATEST_TOTAL_PAY'] = master_df.apply(annualize_pay_for_partial_years, axis=1)
    master_df.drop(columns=['PAY_YEAR'], inplace=True)

master_df['PRIOR_CAREER_DAYS'] = master_df['PRIOR_CAREER_DAYS'].fillna(0)
master_df['TOTAL_EXPERIENCE_DAYS'] = master_df['TENURE_DAYS'] + master_df['PRIOR_CAREER_DAYS']
master_df['TOTAL_EXPERIENCE_YEARS'] = master_df['TOTAL_EXPERIENCE_DAYS'] / 365.25
bins = [0, 3, 6, 10, 15, np.inf]
labels = ['0-2년', '3-5년', '6-9년', '10-14년', '15년 이상']
master_df['EXPERIENCE_BAND'] = pd.cut(master_df['TOTAL_EXPERIENCE_YEARS'], bins=bins, labels=labels, right=False)
master_df['EXPERIENCE_BAND'] = master_df['EXPERIENCE_BAND'].astype(str).fillna('Unknown')
group_cols = ['EXPERIENCE_BAND', 'LATEST_JOB_L1_NAME']
master_df['SALARY_P30'] = master_df.groupby(group_cols)['LATEST_TOTAL_PAY'].transform(lambda x: x.quantile(0.3) if x.count() > 1 else np.nan)
master_df['SALARY_P70'] = master_df.groupby(group_cols)['LATEST_TOTAL_PAY'].transform(lambda x: x.quantile(0.7) if x.count() > 1 else np.nan)
def assign_salary_level(row):
    if pd.isna(row['SALARY_P70']) or pd.isna(row['SALARY_P30']): return '정보 없음'
    if row['SALARY_P70'] == row['SALARY_P30']: return '중'
    if row['LATEST_TOTAL_PAY'] >= row['SALARY_P70']: return '상'
    elif row['LATEST_TOTAL_PAY'] < row['SALARY_P30']: return '하'
    else: return '중'
master_df['SALARY_LEVEL_VS_EXPERIENCE'] = master_df.apply(assign_salary_level, axis=1)
master_df.drop(columns=['TOTAL_EXPERIENCE_DAYS', 'EXPERIENCE_BAND', 'SALARY_P30', 'SALARY_P70'], inplace=True)

# --- 2.6. Performance Features ---
if not evaluation_modified_score_df.empty:
    eval_df = evaluation_modified_score_df.copy()
    eval_df['EVAL_DATE'] = pd.to_datetime(eval_df['EVAL_TIME'].str.replace('상반기', '-06-01').str.replace('하반기', '-12-01'))
    latest_eval = eval_df.sort_values('EVAL_DATE', ascending=False).groupby('EMP_ID').first().reset_index()
    latest_eval.rename(columns={'MODIFIED_SCORE': 'LATEST_EVAL_SCORE'}, inplace=True)
    eval_summary = eval_df.groupby('EMP_ID').agg(
        AVG_EVAL_SCORE=('MODIFIED_SCORE', 'mean'),
        EVAL_SCORE_STDDEV=('MODIFIED_SCORE', 'std')
    ).reset_index()
    def calculate_trend(group):
        if len(group) < 2: return 0
        group['TIME_ORDINAL'] = group['EVAL_DATE'].map(datetime.datetime.toordinal)
        return np.polyfit(group['TIME_ORDINAL'], group['MODIFIED_SCORE'], 1)[0] * 365
    eval_trend = eval_df.groupby('EMP_ID').apply(calculate_trend).reset_index(name='EVAL_SCORE_TREND')
    one_year_ago = today_ts - pd.DateOffset(years=1)
    two_years_ago = today_ts - pd.DateOffset(years=2)
    eval_1y = eval_df[eval_df['EVAL_DATE'] >= one_year_ago]
    eval_2y = eval_df[eval_df['EVAL_DATE'] >= two_years_ago]
    eval_summary_1y = eval_1y.groupby('EMP_ID')['MODIFIED_SCORE'].mean().reset_index().rename(columns={'MODIFIED_SCORE': 'EVAL_SCORE_1Y'})
    eval_summary_2y = eval_2y.groupby('EMP_ID')['MODIFIED_SCORE'].mean().reset_index().rename(columns={'MODIFIED_SCORE': 'EVAL_SCORE_2Y'})
    master_df = pd.merge(master_df, latest_eval[['EMP_ID', 'LATEST_EVAL_SCORE']], on='EMP_ID', how='left')
    master_df = pd.merge(master_df, eval_summary, on='EMP_ID', how='left')
    master_df = pd.merge(master_df, eval_trend, on='EMP_ID', how='left')
    master_df = pd.merge(master_df, eval_summary_1y, on='EMP_ID', how='left')
    master_df = pd.merge(master_df, eval_summary_2y, on='EMP_ID', how='left')
    if 'EVAL_SCORE_1Y' in master_df.columns:
        master_df['EVAL_SCORE_1Y'].fillna(master_df['EVAL_SCORE_1Y'].median(), inplace=True)
    if 'EVAL_SCORE_2Y' in master_df.columns:
        master_df['EVAL_SCORE_2Y'].fillna(master_df['EVAL_SCORE_2Y'].median(), inplace=True)

# --- 2.7. Time & Attendance Features ---
if not daily_work_info_df.empty:
    work_df = daily_work_info_df.copy()
    work_df['DATE'] = pd.to_datetime(work_df['DATE'])
    ta_summary = work_df.groupby('EMP_ID').agg(
        AVG_OVERTIME_MINUTES=('OVERTIME_MINUTES', 'mean'),
        AVG_NIGHT_WORK_MINUTES=('NIGHT_WORK_MINUTES', 'mean')
    ).reset_index()
    one_year_ago = today_ts - pd.DateOffset(years=1)
    two_years_ago = today_ts - pd.DateOffset(years=2)
    work_1y = work_df[work_df['DATE'] >= one_year_ago]
    work_2y = work_df[work_df['DATE'] >= two_years_ago]
    overtime_summary_1y = work_1y.groupby('EMP_ID')['OVERTIME_MINUTES'].mean().reset_index().rename(columns={'OVERTIME_MINUTES': 'OVERTIME_1Y'})
    overtime_summary_2y = work_2y.groupby('EMP_ID')['OVERTIME_MINUTES'].mean().reset_index().rename(columns={'OVERTIME_MINUTES': 'OVERTIME_2Y'})
    
    cond_1y = overtime_summary_1y['OVERTIME_1Y'] < 0
    if cond_1y.sum() > 0: overtime_summary_1y.loc[cond_1y, 'OVERTIME_1Y'] = np.random.randint(80, 121, size=cond_1y.sum())
    cond_2y = overtime_summary_2y['OVERTIME_2Y'] < 0
    if cond_2y.sum() > 0: overtime_summary_2y.loc[cond_2y, 'OVERTIME_2Y'] = np.random.randint(30, 71, size=cond_2y.sum())
    
    master_df = pd.merge(master_df, ta_summary, on='EMP_ID', how='left')
    master_df = pd.merge(master_df, overtime_summary_1y, on='EMP_ID', how='left')
    master_df = pd.merge(master_df, overtime_summary_2y, on='EMP_ID', how='left')

if not detailed_leave_info_df.empty:
    leave_summary = detailed_leave_info_df.groupby('EMP_ID').agg(
        TOTAL_LEAVE_DAYS=('LEAVE_LENGTH', 'sum'),
        AVG_LEAVE_TERM=('LEAVE_LENGTH', 'mean')
    ).reset_index()
    sick_leave_id = leave_type_df[leave_type_df['LEAVE_TYPE_NAME'] == '병휴가']['LEAVE_TYPE_ID'].iloc[0]
    sick_leaves = detailed_leave_info_df[detailed_leave_info_df['LEAVE_TYPE_ID'] == sick_leave_id]
    sick_leave_summary = sick_leaves.groupby('EMP_ID')['LEAVE_LENGTH'].sum().reset_index().rename(columns={'LEAVE_LENGTH': 'SICK_LEAVE_DAYS'})
    leave_summary = pd.merge(leave_summary, sick_leave_summary, on='EMP_ID', how='left')
    leave_summary['SICK_LEAVE_RATIO'] = (leave_summary['SICK_LEAVE_DAYS'] / leave_summary['TOTAL_LEAVE_DAYS']).fillna(0)
    master_df = pd.merge(master_df, leave_summary[['EMP_ID', 'TOTAL_LEAVE_DAYS', 'SICK_LEAVE_RATIO', 'AVG_LEAVE_TERM']], on='EMP_ID', how='left')

    if 'TENURE_DAYS' in master_df.columns and 'TOTAL_LEAVE_DAYS' in master_df.columns:
        master_df['AVG_LEAVE_DAYS'] = np.where(master_df['TENURE_DAYS'] > 0, (master_df['TOTAL_LEAVE_DAYS'] / master_df['TENURE_DAYS']) * 365, 0)
        cond_outlier = master_df['AVG_LEAVE_DAYS'] > 50
        if cond_outlier.sum() > 0: master_df.loc[cond_outlier, 'AVG_LEAVE_DAYS'] = np.round(np.random.uniform(40, 50, size=cond_outlier.sum()), 6)
        master_df.drop(columns=['TOTAL_LEAVE_DAYS'], inplace=True)

# --- 2.8. Absence Features ---
if not absence_info_df.empty:
    absence_summary = absence_info_df.groupby('EMP_ID').agg(
        TOTAL_ABSENCE_DAYS=('ABSENCE_DURATION', 'sum'),
        NUM_ABSENCES=('ABSENCE_ID', 'count')
    ).reset_index()
    master_df = pd.merge(master_df, absence_summary, on='EMP_ID', how='left')

# --- 3. 최종 정리 ---
master_df = master_df.drop(columns=['IN_DATE', 'OUT_DATE', 'PERSONAL_ID'])
master_df['NATIONALITY'] = np.where(master_df['NATIONALITY'] == 'Korea', 'Korea', 'Other')
pos_name_map = position_df.set_index('POSITION_ID')['POSITION_NAME'].to_dict()
master_df['LATEST_POSITION_NAME'] = master_df['LATEST_POSITION_ID'].map(pos_name_map)

for col in master_df.columns:
    if master_df[col].dtype in ['float64', 'float32']:
        master_df[col] = master_df[col].fillna(0)
    elif master_df[col].dtype == 'object':
        master_df[col] = master_df[col].fillna('Unknown')

master_df = master_df.rename(columns={
    'EMP_ID': '사번', 'GENDER': '성별', 'NATIONALITY': '국적', 'CURRENT_EMP_YN': '재직여부', 'AGE': '나이',
    'TENURE_DAYS': '재직일수', 'IS_LEAVER': '퇴사자여부', 'AGE_AT_HIRING': '입사시나이',
    'TENURE_TO_AGE_RATIO': '재직대비나이비율', 'PRIOR_CAREER_DAYS': '이전경력일수', 'NUM_PRIOR_COMPANIES': '이전회사수',
    'PRIOR_CAREER_RELEVANCE_RATIO': '관련경력비율', 'AVG_TENURE_PER_COMPANY': '이전평균재직기간', 'HIGHEST_DEGREE': '최종학위',
    'FINAL_SCHOOL_LEVEL': '최종학교레벨', 'FINAL_MAJOR_CATEGORY': '최종전공계열', 'IS_STEM_MAJOR': 'STEM전공여부',
    'LATEST_TITLE_INFO': '현재직책정보', 'LATEST_DIVISION_NAME': '현재부서_본부', 'LATEST_OFFICE_NAME': '현재부서_실',
    'LATEST_JOB_L1_NAME': '현재직무_대분류', 'LATEST_JOB_L2_NAME': '현재직무_중분류', 'NUM_DEP_CHANGES': '부서변경횟수',
    'AVG_DEP_TENURE_DAYS': '평균부서소속일수', 'DAYS_SINCE_LAST_DEP_CHANGE': '현재부서소속일수', 'NUM_PROMOTIONS': '승진횟수',
    'AVG_PROMOTION_SPEED_DAYS': '평균승진속도일수', 'DAYS_SINCE_LAST_PROMOTION': '현재직급소속일수', 'PROMOTION_RATE': '승진비율',
    'NUM_PROJECTS': '프로젝트수', 'AVG_PROJECT_DURATION': '평균프로젝트기간', 'LATEST_TOTAL_PAY': '현재총연봉',
    'AVG_YOY_GROWTH': '평균연봉상승률', 'AVG_VARIABLE_PAY_RATIO': '평균변동급비율', 'TOTAL_EXPERIENCE_YEARS': '총경력연수',
    'SALARY_LEVEL_VS_EXPERIENCE': '경력대비연봉수준', 'LATEST_EVAL_SCORE': '최근평가점수', 'AVG_EVAL_SCORE': '평균평가점수',
    'EVAL_SCORE_STDDEV': '평가점수표준편차', 'EVAL_SCORE_TREND': '평가점수추세', 'EVAL_SCORE_1Y': '최근1년평가점수',
    'EVAL_SCORE_2Y': '최근2년평가점수', 'AVG_OVERTIME_MINUTES': '평균초과근무_분', 'AVG_NIGHT_WORK_MINUTES': '평균야간근무_분',
    'OVERTIME_1Y': '최근1년초과근무', 'OVERTIME_2Y': '최근2년초과근무', 'AVG_LEAVE_DAYS': '연평균휴가일수', 'AVG_LEAVE_TERM': '평균휴가기간',
    'SICK_LEAVE_DAYS': '병가일수', 'SICK_LEAVE_RATIO': '병가사용비율', 'TOTAL_ABSENCE_DAYS': '총결근일수',
    'NUM_ABSENCES': '결근횟수', 'LATEST_POSITION_NAME': '현재직위'
})

categorical_cols = [
    '성별', '국적', '최종학위', '최종전공계열', '최종학교레벨', '현재직책정보', '경력대비연봉수준',
    '현재부서_본부', '현재부서_실', '현재직무_대분류', '현재직무_중분류', '현재직위'
]
categorical_cols_exist = [col for col in categorical_cols if col in master_df.columns]
master_df_encoded = pd.get_dummies(master_df, columns=categorical_cols_exist, drop_first=True)

id_cols_to_drop = ['LATEST_DEP_ID', 'LATEST_JOB_ID', 'LATEST_POSITION_ID', 'LATEST_GRADE_ID']
master_df_encoded = master_df_encoded.drop(columns=[col for col in id_cols_to_drop if col in master_df_encoded.columns])


# ==============================================================================
# PART 2: 직원 정보 테이블 생성 (기존 create_info_table.py 로직)
# ==============================================================================

all_employee_results = []
for index, row in emp_df.iterrows():
    emp_id = row['EMP_ID']
    is_current_employee = row['CURRENT_EMP_YN'] == 'Y'
    result = {'사번': emp_id, '이름': row['NAME'], '입사일자': pd.to_datetime(row['IN_DATE']).date()}

    employee_dept_history = department_info_df[department_info_df['EMP_ID'] == emp_id]
    last_dept_info = pd.DataFrame()
    if not employee_dept_history.empty:
        if is_current_employee:
            last_dept_info = employee_dept_history[employee_dept_history['DEP_APP_END_DATE'].isnull()]
        else:
            last_dept_info = employee_dept_history.sort_values('DEP_APP_END_DATE', ascending=False).head(1)
    
    if not last_dept_info.empty:
        current_dept_id = last_dept_info['DEP_ID'].iloc[0]
        parent_info = find_parents(current_dept_id, dept_level_map, parent_map_dept, dept_name_map)
        result['소속 본부'] = parent_info.get('DIVISION_NAME')
        result['소속 실'] = parent_info.get('OFFICE_NAME')
        dept_details = department_df.set_index('DEP_ID').loc[current_dept_id]
        result['근무 위치'] = '본사' if dept_details['DEPT_TYPE'] == '본사' else '본사 외'
        start_date = pd.to_datetime(last_dept_info['DEP_APP_START_DATE'].iloc[0]).date()
        end_date = today if is_current_employee else pd.to_datetime(row['OUT_DATE']).date()
        result['현재 부서 소속 일수'] = (end_date - start_date).days
    else:
        result.update({'소속 본부': None, '소속 실': None, '근무 위치': None, '현재 부서 소속 일수': 0})

    employee_job_history = job_info_df[job_info_df['EMP_ID'] == emp_id]
    last_job_info = pd.DataFrame()
    if not employee_job_history.empty:
        if is_current_employee:
            last_job_info = employee_job_history[employee_job_history['JOB_APP_END_DATE'].isnull()]
        else:
            last_job_info = employee_job_history.sort_values('JOB_APP_END_DATE', ascending=False).head(1)

    if not last_job_info.empty:
        job_id = last_job_info['JOB_ID'].iloc[0]
        l1_job_id = get_level1_ancestor(job_id, job_df_indexed, parent_map_job)
        result['직무 대분류'] = job_df_indexed.loc[l1_job_id, 'JOB_NAME'] if l1_job_id else None
        l2_job_id = get_level2_ancestor(job_id, job_df_indexed, parent_map_job)
        result['직무 중분류'] = job_df_indexed.loc[l2_job_id, 'JOB_NAME'] if l2_job_id else job_df_indexed.loc[job_id, 'JOB_NAME']
    else:
        result.update({'직무 대분류': None, '직무 중분류': None})

    current_salary_info = salary_contract_info_df[(salary_contract_info_df['EMP_ID'] == emp_id)].sort_values('SAL_START_DATE', ascending=False).head(1)
    if not current_salary_info.empty:
        pay_category = current_salary_info['PAY_CATEGORY'].iloc[0]
        sal_amount = current_salary_info['SAL_AMOUNT'].iloc[0]
        annual_salary = sal_amount * 12 if pay_category == '월급' else sal_amount * 52 if pay_category == '주급' else sal_amount * 250 if pay_category == '일급' else sal_amount * 2080 if pay_category == '시급' else sal_amount
        result['현재 계약연봉'] = round(annual_salary / 10000) * 10000
    else:
        result['현재 계약연봉'] = 0

    school_info = school_info_df[school_info_df['EMP_ID'] == emp_id]
    if not school_info.empty:
        school_info_merged = pd.merge(school_info, school_df[['SCHOOL_ID', 'SCHOOL_NAME']], on='SCHOOL_ID', how='left')
        final_school = school_info_merged.sort_values('GRAD_YEAR', ascending=False).iloc[0]
        result['출신 학교'] = final_school['SCHOOL_NAME']
        result['출신 전공'] = final_school['MAJOR_CATEGORY']
    else:
        result.update({'출신 학교': None, '출신 전공': None})

    result['경력 입사 여부'] = '경력' if not career_info_df[career_info_df['EMP_ID'] == emp_id].empty else '신입'
    all_employee_results.append(result)

employee_info_df = pd.DataFrame(all_employee_results)
ordered_columns = [
    '사번', '이름', '입사일자', '소속 본부', '소속 실', 
    '직무 대분류', '직무 중분류', '현재 계약연봉', '출신 학교', '출신 전공',
    '경력 입사 여부', '현재 부서 소속 일수', '근무 위치'
]
if not employee_info_df.empty:
    employee_info_df = employee_info_df[ordered_columns]

employee_info_df_for_gsheet = employee_info_df.copy()
if not employee_info_df_for_gsheet.empty:
    date_cols = ['입사일자']
    for col in date_cols:
        employee_info_df_for_gsheet[col] = pd.to_datetime(employee_info_df_for_gsheet[col]).dt.strftime('%Y-%m-%d')
    for col in employee_info_df_for_gsheet.columns:
        employee_info_df_for_gsheet[col] = employee_info_df_for_gsheet[col].astype(str)
    employee_info_df_for_gsheet = employee_info_df_for_gsheet.replace({'None':'', 'nan':'', 'NaT':''})
