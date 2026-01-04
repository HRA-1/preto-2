# HR Analytics XAI Dashboard 구현 계획

## 개요
preto-2 프로젝트에 XAI (Explainable AI) 대시보드를 구현합니다.
- **Global Explainer**: 퇴사 위험 패턴 (조직 전체)
- **Local Explainer**: 개인별 위험 사유 (개별 직원)

---

## 필터 구조

| Level | 위치 | 이름 | 옵션 |
|-------|------|------|------|
| L1 | Sidebar | 분석 관점 선택 | 개요, 퇴사 위험 패턴, 개인별 위험 사유 |
| L2 | Sidebar | 상세 확인 | L1에 따라 동적 |
| L3 | Main Top | 변수 선택 | 개요 + Top 5 변수 (PDP 뷰에서만 활성화) |
| L4 | Main Top | 인원 선택 | 개요 + 직원목록 (Waterfall 뷰에서만 활성화) |

### L2 옵션 (L1에 따라)
- **퇴사 위험 패턴**: 주요 영향 변수, 변수별 영향 확인
- **개인별 위험 사유**: 개요, 위험도 산출 근거

---

## 뷰 상태 및 시각화

| ViewState | 조건 | 시각화 |
|-----------|------|--------|
| PERSPECTIVE_OVERVIEW | L1=개요 | XAI 소개 페이지 |
| DETAIL_SELECTION | L1≠개요, L2=개요 | 상세 메뉴 선택 안내 |
| GLOBAL_BAR_BEESWARM | L1=퇴사위험패턴, L2=주요영향변수 | Bar Plot + Beeswarm Plot |
| GLOBAL_PDP | L1=퇴사위험패턴, L2=변수별영향확인 | Partial Dependence Plot |
| LOCAL_OVERVIEW | L1=개인별위험사유, L2=개요 | XAI/Waterfall 설명 |
| LOCAL_WATERFALL | L1=개인별위험사유, L2=위험도산출근거 | 개인정보 표 + Waterfall Plot |

---

## 구현할 파일

### 1. 신규 생성 파일

#### Config
- `src/services/config/xai_filters_config.py`
  - XAIViewState enum
  - ANALYSIS_PERSPECTIVES, DETAIL_VIEW_TITLES
  - get_xai_view_state(), should_show_variable_selector(), should_show_employee_selector()

#### ML Service
- `src/services/ml/__init__.py`
- `src/services/ml/xai_service.py`
  - XAIService 클래스: 모델 학습, SHAP explainer 생성
  - train_model(): XGBoost 분류기 학습
  - create_explainer(): SHAP TreeExplainer 생성
  - compute_global_shap_values(): 전역 SHAP 계산 (2000개 샘플)
  - compute_local_shap_values(): 개별 직원 SHAP 계산
  - get_active_employees_with_risk(): 재직자 위험도 순위
  - get_top_features(): Top 5 중요 변수 추출

#### XAI Views
- `src/services/xai_views/__init__.py`
- `src/services/xai_views/global_bar_beeswarm_view.py`
  - render_global_bar_beeswarm(): Bar Plot + Beeswarm Plot 렌더링
- `src/services/xai_views/global_pdp_view.py`
  - render_global_pdp(): Partial Dependence Plot 렌더링
- `src/services/xai_views/local_overview_view.py`
  - render_local_overview(): XAI 소개 텍스트 렌더링
- `src/services/xai_views/local_waterfall_view.py`
  - render_local_waterfall(): 직원 정보 + Waterfall Plot 렌더링

### 2. 수정할 파일

- `src/app.py` - 전체 재작성
  - Sidebar: L1(분석 관점), L2(상세 확인), 링크 섹션
  - Main: L3(변수 선택), L4(인원 선택), 콘텐츠 영역
  - ViewState 기반 조건부 렌더링

---

## 구현 순서

### Step 1: Config 모듈
```
src/services/config/xai_filters_config.py
```
- XAI 전용 필터 설정
- ViewState enum 및 상태 결정 함수

### Step 2: ML Service 모듈
```
src/services/ml/__init__.py
src/services/ml/xai_service.py
```
- notebooks의 로직을 서비스 클래스로 추출
- @st.cache_resource로 모델/explainer 캐싱

### Step 3: XAI View 모듈
```
src/services/xai_views/__init__.py
src/services/xai_views/global_bar_beeswarm_view.py
src/services/xai_views/global_pdp_view.py
src/services/xai_views/local_overview_view.py
src/services/xai_views/local_waterfall_view.py
```
- 각 뷰 상태별 렌더링 함수

### Step 4: Main App
```
src/app.py
```
- preto-1 패턴을 따라 전체 재작성
- 필터 UI + 상태 기반 콘텐츠 라우팅

---

## 주요 참조 파일

| 파일 | 용도 |
|------|------|
| `notebooks/tables/test_ml_shap_global.ipynb` | Global SHAP 로직 참조 |
| `notebooks/tables/test_ml_shap_local.ipynb` | Local SHAP 로직 참조 |
| `src/services/tables/create_ml_table.py` | master_df_encoded 데이터 |
| `src/services/tables/create_info_table.py` | employee_info_df 데이터 |
| `preto-1/src/app.py` | 앱 구조 패턴 참조 |

---

## 기술 사항

### 캐싱 전략
- `@st.cache_resource`: 모델, explainer, XAIService 인스턴스 (앱 레벨)
- `@st.cache_data`: 전역 SHAP 값 (사용자 레벨)
- Local SHAP: 직원 선택 시에만 계산 (lazy loading)

### 외부 링크
- 소개글 보기: https://lrl.kr/cYShq
- 설문 참여하기: https://lrl.kr/ciUO7

### 모델 설정
- XGBoost: n_estimators=70, max_depth=2, scale_pos_weight=70
- SHAP: TreeExplainer, feature_perturbation="interventional", model_output="probability"

---

## 디렉토리 구조 (최종)

```
src/
├── app.py                              # [수정] 메인 앱
├── services/
│   ├── config/
│   │   ├── dev_config.py              # [기존]
│   │   ├── filters_config.py          # [기존]
│   │   └── xai_filters_config.py      # [신규]
│   ├── ml/                            # [신규 디렉토리]
│   │   ├── __init__.py
│   │   └── xai_service.py
│   ├── xai_views/                     # [신규 디렉토리]
│   │   ├── __init__.py
│   │   ├── global_bar_beeswarm_view.py
│   │   ├── global_pdp_view.py
│   │   ├── local_overview_view.py
│   │   └── local_waterfall_view.py
│   ├── helpers/                       # [기존]
│   └── tables/                        # [기존]
```
