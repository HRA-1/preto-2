import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
from IPython.display import display

# --- 데이터 로드 ---# HR Core
from services.tables.HR_Core.basic_info_table import emp_df
from services.tables.HR_Core.absence_info_table import absence_info_df
from services.tables.HR_Core.career_info_table import career_info_df
from services.tables.HR_Core.contract_info_table import contract_info_df
from services.tables.HR_Core.department_info_table import department_info_df
from services.tables.HR_Core.job_info_table import job_info_df
from services.tables.HR_Core.position_info_table import position_info_df
from services.tables.HR_Core.pjt_info_table import pjt_info_df
from services.tables.HR_Core.region_info_table import region_info_df
from services.tables.HR_Core.school_info_table import school_info_df
from services.tables.HR_Core.school_table import school_df
from services.tables.HR_Core.job_table import job_df
from services.tables.HR_Core.position_table import position_df
from services.tables.HR_Core.department_table import department_df

# Payroll
from services.tables.Payroll.yearly_payroll_info_table import yearly_payroll_df

# Performance
from services.tables.Performance.evaluation_modified_score_info_table import evaluation_modified_score_df

# Time_Attendance
from services.tables.Time_Attendance.daily_working_info_table import daily_work_info_df
from services.tables.Time_Attendance.detailed_leave_info_table import detailed_leave_info_df
from services.tables.Time_Attendance.leave_type_table import leave_type_df


today = datetime.datetime.now().date()
today_ts = pd.to_datetime(today)

# --- Feature Engineering ---

# 마스터 테이블의 기반이 될 직원 정보 복사 (+ PERSONAL_ID for age calculation)
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

# [NEW/MODIFIED] Department, Job 계층 구조 처리
# Department: Division/Office 단위로 상위 부서명 사용
dept_map = department_df.set_index('DEP_ID').to_dict('index')
def get_department_hierarchy(dep_id, dept_map):
    hierarchy = {'LATEST_DIVISION_NAME': 'Unknown', 'LATEST_OFFICE_NAME': 'Unknown'}
    if pd.isna(dep_id) or dep_id not in dept_map:
        return pd.Series(hierarchy)

    current_id = dep_id
    for _ in range(10): # 무한 루프 방지를 위한 최대 10단계 탐색
        if pd.isna(current_id) or current_id not in dept_map:
            break
        
        dep_info = dept_map[current_id]
        dep_name = dep_info.get('DEP_NAME', '')

        if 'Division' in dep_name and hierarchy['LATEST_DIVISION_NAME'] == 'Unknown':
            hierarchy['LATEST_DIVISION_NAME'] = dep_name
        if 'Office' in dep_name and hierarchy['LATEST_OFFICE_NAME'] == 'Unknown':
            hierarchy['LATEST_OFFICE_NAME'] = dep_name

        parent_id = dep_info.get('UP_DEP_ID')
        if pd.isna(parent_id) or parent_id == current_id:
            break
        current_id = parent_id
    return pd.Series(hierarchy)

dept_hierarchy_cols = master_df['LATEST_DEP_ID'].apply(lambda x: get_department_hierarchy(x, dept_map))
master_df = pd.concat([master_df, dept_hierarchy_cols], axis=1)

# Job: Job Level 1, 2 기준으로 직무명 사용
job_map = job_df.set_index('JOB_ID').to_dict('index')
def get_job_hierarchy(job_id, job_map):
    hierarchy = {'LATEST_JOB_L1_NAME': 'Unknown', 'LATEST_JOB_L2_NAME': 'Unknown'}
    if pd.isna(job_id) or job_id not in job_map:
        return pd.Series(hierarchy)

    # 현재 직무 및 상위 직무 탐색
    current_id = job_id
    for _ in range(10): # 무한 루프 방지
        if pd.isna(current_id) or current_id not in job_map:
            break
        
        job_info = job_map[current_id]
        job_level = job_info.get('JOB_LEVEL')
        job_name = job_info.get('JOB_NAME', 'Unknown')

        if job_level == 1 and hierarchy['LATEST_JOB_L1_NAME'] == 'Unknown':
            hierarchy['LATEST_JOB_L1_NAME'] = job_name
        if job_level == 2 and hierarchy['LATEST_JOB_L2_NAME'] == 'Unknown':
            hierarchy['LATEST_JOB_L2_NAME'] = job_name
        
        parent_id = job_info.get('UP_JOB_ID')
        if pd.isna(parent_id) or parent_id == current_id:
            break
        current_id = parent_id
    return pd.Series(hierarchy)

job_hierarchy_cols = master_df['LATEST_JOB_ID'].apply(lambda x: get_job_hierarchy(x, job_map))
master_df = pd.concat([master_df, job_hierarchy_cols], axis=1)

if not department_info_df.empty:
    dept_summary = department_info_df.groupby('EMP_ID').agg(
        NUM_DEP_CHANGES=('DEP_ID', 'nunique'),
        AVG_DEP_TENURE_DAYS=('DEP_DURATION', 'mean')
    ).reset_index()
    last_dept_change_date = department_info_df.groupby('EMP_ID')['DEP_APP_START_DATE'].max().reset_index().rename(columns={'DEP_APP_START_DATE': 'LAST_DEP_CHANGE_DATE'})
    dept_summary = pd.merge(dept_summary, last_dept_change_date, on='EMP_ID', how='left')
    dept_summary['DAYS_SINCE_LAST_DEP_CHANGE'] = (today_ts - dept_summary['LAST_DEP_CHANGE_DATE']).dt.days
    master_df = pd.merge(master_df, dept_summary.drop(columns=['LAST_DEP_CHANGE_DATE']), on='EMP_ID', how='left')

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
    latest_payroll = yearly_payroll_df.sort_values('PAY_YEAR', ascending=False).groupby('EMP_ID').first().reset_index()
    latest_payroll.rename(columns={'TOTAL_PAY': 'LATEST_TOTAL_PAY'}, inplace=True)
    payroll_summary = yearly_payroll_df.groupby('EMP_ID').agg(
        AVG_YOY_GROWTH=('YOY_GROWTH', 'mean'),
        AVG_VARIABLE_PAY_RATIO=('VARIABLE_PAY_RATIO', 'mean')
    ).reset_index()
    master_df = pd.merge(master_df, latest_payroll[['EMP_ID', 'LATEST_TOTAL_PAY', 'PAY_YEAR']], on='EMP_ID', how='left')
    master_df = pd.merge(master_df, payroll_summary, on='EMP_ID', how='left')

# (수정 1) 연봉 연환산 (Prorating) 로직
def annualize_salary(row):
    # 연봉, 입사일, 급여지급연도 정보가 없으면 계산 불가
    if pd.isna(row['LATEST_TOTAL_PAY']) or pd.isna(row['IN_DATE']) or pd.isna(row['PAY_YEAR']):
        return row['LATEST_TOTAL_PAY']

    in_date = pd.to_datetime(row['IN_DATE'])
    pay_year = int(row['PAY_YEAR'])

    # 입사연도와 급여지급연도가 같은 경우 (중도 입사자)
    if in_date.year == pay_year:
        # 해당 연도 근무일수 계산
        year_end = pd.to_datetime(f'{pay_year}-12-31')
        days_worked = (year_end - in_date).days + 1

        # 근무일수가 0이거나 음수인 비정상적 경우 방지
        if days_worked <= 0:
            return np.nan

        # 연봉을 365일 기준으로 환산
        annualized_salary = (row['LATEST_TOTAL_PAY'] / days_worked) * 365
        return annualized_salary
    else:
        # 중도 입사자가 아니면 기존 연봉 사용
        return row['LATEST_TOTAL_PAY']

# IN_DATE, PAY_YEAR 컬럼이 master_df에 있어야 함 (이전 셀에서 로드됨)
# IN_DATE는 초기에 로드되므로, PAY_YEAR만 위에서 merge 했는지 확인
if 'PAY_YEAR' in master_df.columns:
    # 원본 LATEST_TOTAL_PAY를 복사해두고, 연환산된 값으로 덮어쓰기
    master_df['LATEST_TOTAL_PAY'] = master_df.apply(annualize_salary, axis=1)
else:
    # PAY_YEAR 정보가 없으면 연환산 불가
    master_df['LATEST_TOTAL_PAY'] = master_df['LATEST_TOTAL_PAY']

# --- [NEW] 2.5.1. 경력 대비 연봉 수준(SALARY_LEVEL_VS_EXPERIENCE) 피처 생성 ---

# 1. 총 경력 연차 계산 (재직기간 + 이전 경력)
# master_df에 'PRIOR_CAREER_DAYS'와 'TENURE_DAYS'가 이미 있다고 가정합니다.
master_df['PRIOR_CAREER_DAYS'] = master_df['PRIOR_CAREER_DAYS'].fillna(0)
master_df['TOTAL_EXPERIENCE_DAYS'] = master_df['TENURE_DAYS'] + master_df['PRIOR_CAREER_DAYS']
master_df['TOTAL_EXPERIENCE_YEARS'] = master_df['TOTAL_EXPERIENCE_DAYS'] / 365.25

# 2. 경력 연차 구간 (Experience Band) 생성
# 경력 구간은 필요에 따라 조정할 수 있습니다.
bins = [0, 3, 6, 10, 15, np.inf]
labels = ['0-2년', '3-5년', '6-9년', '10-14년', '15년 이상']
master_df['EXPERIENCE_BAND'] = pd.cut(master_df['TOTAL_EXPERIENCE_YEARS'], bins=bins, labels=labels, right=False)
master_df['EXPERIENCE_BAND'] = master_df['EXPERIENCE_BAND'].astype(str).fillna('Unknown')


# 3. 그룹별(경력 구간 + 직무) 연봉 분위수 계산
# LATEST_JOB_L2_NAME이 가장 세분화된 직무로 가정합니다. 없다면 LATEST_JOB_L1_NAME 등을 사용할 수 있습니다.
group_cols = ['EXPERIENCE_BAND', 'LATEST_JOB_L1_NAME']

# 그룹별 연봉의 30%, 70% 지점을 계산하여 새로운 컬럼으로 추가
master_df['SALARY_P30'] = master_df.groupby(group_cols)['LATEST_TOTAL_PAY'].transform(lambda x: x.quantile(0.3) if x.count() > 1 else np.nan)
master_df['SALARY_P70'] = master_df.groupby(group_cols)['LATEST_TOTAL_PAY'].transform(lambda x: x.quantile(0.7) if x.count() > 1 else np.nan)

# 4. '경력 대비 연봉 수준' 피처 생성
def assign_salary_level(row):
    # 그룹의 데이터가 부족하여 분위수 계산이 안된 경우 '정보 없음' 처리
    if pd.isna(row['SALARY_P70']) or pd.isna(row['SALARY_P30']):
        return '정보 없음'
    # 그룹 내 연봉이 모두 동일한 경우 '중'으로 처리
    if row['SALARY_P70'] == row['SALARY_P30']:
        return '중'

    if row['LATEST_TOTAL_PAY'] >= row['SALARY_P70']:
        return '상'
    elif row['LATEST_TOTAL_PAY'] < row['SALARY_P30']:
        return '하'
    else:
        return '중'

master_df['SALARY_LEVEL_VS_EXPERIENCE'] = master_df.apply(assign_salary_level, axis=1)

# 임시로 사용한 컬럼들 삭제
master_df.drop(columns=['TOTAL_EXPERIENCE_DAYS', 'EXPERIENCE_BAND', 'SALARY_P30', 'SALARY_P70'], inplace=True)

# --- 2.6. Performance Features ---
if not evaluation_modified_score_df.empty:
    # EVAL_TIME을 datetime으로 변환
    eval_df = evaluation_modified_score_df.copy()
    eval_df['EVAL_DATE'] = pd.to_datetime(eval_df['EVAL_TIME'].str.replace('상반기', '-06-01').str.replace('하반기', '-12-01'))

    # 최신 평가 점수
    latest_eval = eval_df.sort_values('EVAL_DATE', ascending=False).groupby('EMP_ID').first().reset_index()
    latest_eval.rename(columns={'MODIFIED_SCORE': 'LATEST_EVAL_SCORE'}, inplace=True)

    # 전체 기간 평균 및 표준편차
    eval_summary = eval_df.groupby('EMP_ID').agg(
        AVG_EVAL_SCORE=('MODIFIED_SCORE', 'mean'),
        EVAL_SCORE_STDDEV=('MODIFIED_SCORE', 'std')
    ).reset_index()

    # 점수 변화 추이
    def calculate_trend(group):
        if len(group) < 2:
            return 0
        group['TIME_ORDINAL'] = group['EVAL_DATE'].map(datetime.datetime.toordinal)
        X = group['TIME_ORDINAL']
        y = group['MODIFIED_SCORE']
        return np.polyfit(X, y, 1)[0] * 365
    eval_trend = eval_df.groupby('EMP_ID').apply(calculate_trend).reset_index(name='EVAL_SCORE_TREND')

    # [NEW] 최근 1년 및 2년 평균 평가 점수
    one_year_ago = today_ts - pd.DateOffset(years=1)
    two_years_ago = today_ts - pd.DateOffset(years=2)

    eval_1y = eval_df[eval_df['EVAL_DATE'] >= one_year_ago]
    eval_2y = eval_df[eval_df['EVAL_DATE'] >= two_years_ago]

    eval_summary_1y = eval_1y.groupby('EMP_ID')['MODIFIED_SCORE'].mean().reset_index().rename(columns={'MODIFIED_SCORE': 'EVAL_SCORE_1Y'})
    eval_summary_2y = eval_2y.groupby('EMP_ID')['MODIFIED_SCORE'].mean().reset_index().rename(columns={'MODIFIED_SCORE': 'EVAL_SCORE_2Y'})

    # master_df에 병합
    master_df = pd.merge(master_df, latest_eval[['EMP_ID', 'LATEST_EVAL_SCORE']], on='EMP_ID', how='left')
    master_df = pd.merge(master_df, eval_summary, on='EMP_ID', how='left')
    master_df = pd.merge(master_df, eval_trend, on='EMP_ID', how='left')
    master_df = pd.merge(master_df, eval_summary_1y, on='EMP_ID', how='left') # New
    master_df = pd.merge(master_df, eval_summary_2y, on='EMP_ID', how='left') # New

# --- 2.7. Time & Attendance Features ---
if not daily_work_info_df.empty:
    work_df = daily_work_info_df.copy()
    work_df['DATE'] = pd.to_datetime(work_df['DATE'])

    # 전체 기간 평균 초과근무
    ta_summary = work_df.groupby('EMP_ID').agg(
        AVG_OVERTIME_MINUTES=('OVERTIME_MINUTES', 'mean'),
        AVG_NIGHT_WORK_MINUTES=('NIGHT_WORK_MINUTES', 'mean')
    ).reset_index()

    # [NEW] 최근 1년 및 2년 평균 초과근무
    one_year_ago = today_ts - pd.DateOffset(years=1)
    two_years_ago = today_ts - pd.DateOffset(years=2)

    work_1y = work_df[work_df['DATE'] >= one_year_ago]
    work_2y = work_df[work_df['DATE'] >= two_years_ago]

    overtime_summary_1y = work_1y.groupby('EMP_ID')['OVERTIME_MINUTES'].mean().reset_index().rename(columns={'OVERTIME_MINUTES': 'OVERTIME_1Y'})
    overtime_summary_2y = work_2y.groupby('EMP_ID')['OVERTIME_MINUTES'].mean().reset_index().rename(columns={'OVERTIME_MINUTES': 'OVERTIME_2Y'})

    # master_df에 병합
    master_df = pd.merge(master_df, ta_summary, on='EMP_ID', how='left')
    master_df = pd.merge(master_df, overtime_summary_1y, on='EMP_ID', how='left') # New
    master_df = pd.merge(master_df, overtime_summary_2y, on='EMP_ID', how='left') # New


if not detailed_leave_info_df.empty:
    leave_summary = detailed_leave_info_df.groupby('EMP_ID').agg(
        TOTAL_LEAVE_DAYS=('LEAVE_LENGTH', 'sum'),
        AVG_LEAVE_TERM=('LEAVE_LENGTH', 'mean')
    ).reset_index()
    
    # '병휴가'라는 정확한 명칭이 데이터에 존재해야 합니다.
    sick_leave_id = leave_type_df[leave_type_df['LEAVE_TYPE_NAME'] == '병휴가']['LEAVE_TYPE_ID'].iloc[0]
    sick_leaves = detailed_leave_info_df[detailed_leave_info_df['LEAVE_TYPE_ID'] == sick_leave_id]
    
    sick_leave_summary = sick_leaves.groupby('EMP_ID')['LEAVE_LENGTH'].sum().reset_index().rename(columns={'LEAVE_LENGTH': 'SICK_LEAVE_DAYS'})
    leave_summary = pd.merge(leave_summary, sick_leave_summary, on='EMP_ID', how='left')
    
    # 병가 사용 비율 계산 (NaN 처리 포함)
    leave_summary['SICK_LEAVE_RATIO'] = (leave_summary['SICK_LEAVE_DAYS'] / leave_summary['TOTAL_LEAVE_DAYS']).fillna(0)
    
    master_df = pd.merge(master_df, leave_summary[['EMP_ID', 'TOTAL_LEAVE_DAYS', 'SICK_LEAVE_RATIO', 'AVG_LEAVE_TERM']], on='EMP_ID', how='left')

# --- 2.8. Absence Features ---
if not absence_info_df.empty:
    absence_summary = absence_info_df.groupby('EMP_ID').agg(
        TOTAL_ABSENCE_DAYS=('ABSENCE_DURATION', 'sum'),
        NUM_ABSENCES=('ABSENCE_ID', 'count')
    ).reset_index()
    master_df = pd.merge(master_df, absence_summary, on='EMP_ID', how='left')

# --- 3. 최종 마스터 테이블 생성 및 저장 ---

# --- 3.1. 데이터 정리 ---
# 날짜 및 임시 ID 데이터 제거
master_df = master_df.drop(columns=['IN_DATE', 'OUT_DATE', 'PERSONAL_ID'])

# Nationality: Korea / Other
master_df['NATIONALITY'] = np.where(master_df['NATIONALITY'] == 'Korea', 'Korea', 'Other')

# 나머지 ID성 컬럼 매핑
pos_name_map = position_df.set_index('POSITION_ID')['POSITION_NAME'].to_dict()
master_df['LATEST_POSITION_NAME'] = master_df['LATEST_POSITION_ID'].map(pos_name_map)

# 결측치 처리
for col in master_df.columns:
    if master_df[col].dtype == 'float64' or master_df[col].dtype == 'float32':
        master_df[col] = master_df[col].fillna(0)
    elif master_df[col].dtype == 'object':
        master_df[col] = master_df[col].fillna('Unknown')

# [MODIFIED] 범주형 변수 인코딩 (One-Hot Encoding)
categorical_cols = [
    'GENDER', 'NATIONALITY', 'HIGHEST_DEGREE', 'FINAL_MAJOR_CATEGORY', 'FINAL_SCHOOL_LEVEL',
    'LATEST_TITLE_INFO', 
    'SALARY_LEVEL_VS_EXPERIENCE',
    'LATEST_DIVISION_NAME', 'LATEST_OFFICE_NAME', # New
    'LATEST_JOB_L1_NAME', 'LATEST_JOB_L2_NAME', # New
    'LATEST_POSITION_NAME', 
]
categorical_cols_exist = [col for col in categorical_cols if col in master_df.columns]
master_df_encoded = pd.get_dummies(master_df, columns=categorical_cols_exist, drop_first=True)

# 불필요한 ID 컬럼 제거
id_cols_to_drop = ['LATEST_DEP_ID', 'LATEST_JOB_ID', 'LATEST_POSITION_ID', 'LATEST_GRADE_ID']
master_df_encoded = master_df_encoded.drop(columns=[col for col in id_cols_to_drop if col in master_df_encoded.columns])

