
import pandas as pd
import datetime
import os
import sys

# 'src' 디렉토리를 sys.path에 추가하여 'services' 모듈을 찾을 수 있도록 합니다.
script_dir = os.path.dirname(__file__)
src_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# --- 테이블 모듈에서 DataFrame을 직접 임포트 ---
# HR_Core
from services.tables.HR_Core.basic_info_table import emp_df as basic_info_df
from services.tables.HR_Core.department_table import (
    department_df, dept_level_map, parent_map_dept, dept_name_map
)
from services.tables.HR_Core.department_info_table import department_info_df
from services.tables.HR_Core.school_table import school_df
from services.tables.HR_Core.school_info_table import school_info_df
from services.tables.HR_Core.job_table import job_df, job_df_indexed, parent_map_job
from services.tables.HR_Core.job_info_table import job_info_df
from services.tables.HR_Core.salary_contract_info_table import salary_contract_info_df
from services.tables.HR_Core.career_info_table import career_info_df
# helpers
from services.helpers.utils import find_parents, get_level1_ancestor, get_level2_ancestor

# --- 모든 직원에 대한 정보 통합 ---
all_employee_results = []
today = datetime.datetime.now().date()

for index, row in basic_info_df.iterrows():
    emp_id = row['EMP_ID']
    is_current_employee = row['CURRENT_EMP_YN'] == 'Y'

    # --- 1. 기본 정보 ---
    result = {
        '사번': emp_id,
        '이름': row['NAME'],
        '입사일자': pd.to_datetime(row['IN_DATE']).date(),
    }

    # --- 2. 부서 및 근무지 정보 (퇴사자 처리 로직 추가) ---
    employee_dept_history = department_info_df[department_info_df['EMP_ID'] == emp_id]
    last_dept_info = pd.DataFrame()

    if not employee_dept_history.empty:
        if is_current_employee:
            # 재직중인 경우, 종료일이 없는 현재 부서 정보
            last_dept_info = employee_dept_history[employee_dept_history['DEP_APP_END_DATE'].isnull()]
        else:
            # 퇴사한 경우, 마지막 부서 정보
            last_dept_info = employee_dept_history.sort_values('DEP_APP_END_DATE', ascending=False).head(1)
    
    if not last_dept_info.empty:
        current_dept_id = last_dept_info['DEP_ID'].iloc[0]
        parent_info = find_parents(current_dept_id, dept_level_map, parent_map_dept, dept_name_map)
        
        # '소속 본부'를 Division으로 명확히 지정
        result['소속 본부'] = parent_info.get('DIVISION_NAME')
        result['소속 실'] = parent_info.get('OFFICE_NAME')

        dept_details = department_df.set_index('DEP_ID').loc[current_dept_id]
        result['근무 위치'] = '본사' if dept_details['DEPT_TYPE'] == '본사' else '본사 외'

        start_date = pd.to_datetime(last_dept_info['DEP_APP_START_DATE'].iloc[0]).date()
        
        # 재직중이면 today, 퇴사자면 퇴사일자를 기준으로 계산
        if is_current_employee:
            end_date = today
        else:
            end_date = pd.to_datetime(row['OUT_DATE']).date()
        
        result['현재 부서 소속 일수'] = (end_date - start_date).days
    else:
        result['소속 본부'] = None
        result['소속 실'] = None
        result['근무 위치'] = None
        result['현재 부서 소속 일수'] = 0

    # --- 3. 직무 정보 (퇴사자 처리 로직 추가) ---
    employee_job_history = job_info_df[job_info_df['EMP_ID'] == emp_id]
    last_job_info = pd.DataFrame()

    if not employee_job_history.empty:
        if is_current_employee:
            # 재직중인 경우, 종료일이 없는 현재 직무 정보
            last_job_info = employee_job_history[employee_job_history['JOB_APP_END_DATE'].isnull()]
        else:
            # 퇴사한 경우, 마지막 직무 정보
            last_job_info = employee_job_history.sort_values('JOB_APP_END_DATE', ascending=False).head(1)

    if not last_job_info.empty:
        job_id = last_job_info['JOB_ID'].iloc[0]
        
        l1_job_id = get_level1_ancestor(job_id, job_df_indexed, parent_map_job)
        result['직무 대분류'] = job_df_indexed.loc[l1_job_id, 'JOB_NAME'] if l1_job_id else None
            
        l2_job_id = get_level2_ancestor(job_id, job_df_indexed, parent_map_job)
        result['직무 중분류'] = job_df_indexed.loc[l2_job_id, 'JOB_NAME'] if l2_job_id else job_df_indexed.loc[job_id, 'JOB_NAME']
    else:
        result['직무 대분류'] = None
        result['직무 중분류'] = None

    # --- 4. 연봉 정보 ---
    current_salary_info = salary_contract_info_df[
        (salary_contract_info_df['EMP_ID'] == emp_id)
    ].sort_values('SAL_START_DATE', ascending=False).head(1)

    if not current_salary_info.empty:
        pay_category = current_salary_info['PAY_CATEGORY'].iloc[0]
        sal_amount = current_salary_info['SAL_AMOUNT'].iloc[0]
        annual_salary = 0

        if pay_category == '월급':
            annual_salary = sal_amount * 12
        elif pay_category == '주급':
            annual_salary = sal_amount * 52
        elif pay_category == '일급':
            annual_salary = sal_amount * 250
        elif pay_category == '시급':
            annual_salary = sal_amount * 2080
        else:
            annual_salary = sal_amount
        
        result['현재 계약연봉'] = round(annual_salary / 10000) * 10000
    else:
        result['현재 계약연봉'] = 0

    # --- 5. 학력 정보 ---
    school_info = school_info_df[school_info_df['EMP_ID'] == emp_id]
    if not school_info.empty:
        school_info_merged = pd.merge(school_info, school_df[['SCHOOL_ID', 'SCHOOL_NAME']], on='SCHOOL_ID', how='left')
        final_school = school_info_merged.sort_values('GRAD_YEAR', ascending=False).iloc[0]
        
        result['출신 학교'] = final_school['SCHOOL_NAME']
        result['출신 전공'] = final_school['MAJOR_CATEGORY']
    else:
        result['출신 학교'] = None
        result['출신 전공'] = None

    # --- 6. 경력 입사 여부 ---
    career_history = career_info_df[career_info_df['EMP_ID'] == emp_id]
    result['경력 입사 여부'] = '경력' if not career_history.empty else '신입'
    
    all_employee_results.append(result)

# --- 최종 DataFrame 생성 ---
employee_info_df = pd.DataFrame(all_employee_results)

# 컬럼 순서 정리
ordered_columns = [
    '사번', '이름', '입사일자', '소속 본부', '소속 실', 
    '직무 대분류', '직무 중분류', '현재 계약연봉', '출신 학교', '출신 전공',
    '경력 입사 여부', '현재 부서 소속 일수', '근무 위치'
]
if not employee_info_df.empty:
    employee_info_df = employee_info_df[ordered_columns]

# Google Sheets용 복사본 생성 (다른 테이블들과 형식 일치)
employee_info_df_for_gsheet = employee_info_df.copy()
if not employee_info_df_for_gsheet.empty:
    date_cols = ['입사일자']
    for col in date_cols:
        employee_info_df_for_gsheet[col] = pd.to_datetime(employee_info_df_for_gsheet[col]).dt.strftime('%Y-%m-%d')
    for col in employee_info_df_for_gsheet.columns:
        employee_info_df_for_gsheet[col] = employee_info_df_for_gsheet[col].astype(str)
    employee_info_df_for_gsheet = employee_info_df_for_gsheet.replace({'None':'', 'nan':'', 'NaT':''})
