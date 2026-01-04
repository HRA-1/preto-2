# XAI Service Module

XAI 대시보드용 ML 서비스 모듈입니다. 노트북에서 개발된 SHAP 분석 로직을 서비스 클래스로 캡슐화하였습니다.

## 노트북과의 관계

이 모듈은 아래 노트북의 로직을 그대로 서비스화한 것입니다:

| 노트북 | XAIService 메서드 |
|--------|-------------------|
| `test_ml_shap_global.ipynb` | `compute_global_shap_values()`, `get_top_features()` |
| `test_ml_shap_local.ipynb` | `compute_local_shap_values()`, `get_active_employees_with_risk()` |

---

## 기본 사용법

### 노트북 방식 (기존)

```python
# test_ml_shap_global.ipynb 에서 발췌
import xgboost as xgb
import shap
from services.tables.create_ml_table import master_df_encoded

# 데이터 준비
df_leavers = master_df_encoded[master_df_encoded['퇴사자여부'] == 1]
df_active = master_df_encoded[master_df_encoded['퇴사자여부'] == 0]
n_required_active = len(df_leavers) * 6
df_active_oversampled = df_active.sample(n=n_required_active, replace=True, random_state=42)
balanced_df = pd.concat([df_leavers, df_active_oversampled], axis=0).sample(frac=1, random_state=42)

# 모델 학습
model = xgb.XGBClassifier(
    n_estimators=70, max_depth=2, learning_rate=0.1,
    scale_pos_weight=70, random_state=42, min_child_weight=10,
    use_label_encoder=False, eval_metric='logloss'
)
model.fit(X_train, y_train)

# SHAP 계산
background_data = shap.sample(X_train, 100)
explainer = shap.TreeExplainer(model, data=background_data,
    feature_perturbation="interventional", model_output="probability")
shap_values = explainer(X_sample)
```

### XAIService 방식 (신규)

```python
from services.ml import get_xai_service
from services.tables.create_ml_table import master_df_encoded

# 서비스 초기화 (모든 설정이 캡슐화됨)
xai_service = get_xai_service(master_df_encoded)

# 모델 학습 (내부적으로 동일한 파라미터 사용)
model = xai_service.train_model()

# SHAP explainer 생성
explainer = xai_service.create_explainer()

# Global SHAP 계산
shap_values = xai_service.compute_global_shap_values()
```

---

## 주요 메서드

### 1. `train_model()`
XGBoost 분류기를 학습합니다.

```python
model = xai_service.train_model()
```

**파라미터** (노트북과 동일):
- `n_estimators=70`
- `max_depth=2`
- `scale_pos_weight=70`
- `learning_rate=0.1`
- `min_child_weight=10`
- `random_state=42`

---

### 2. `create_explainer()`
SHAP TreeExplainer를 생성합니다.

```python
explainer = xai_service.create_explainer()
```

**설정** (노트북과 동일):
- `feature_perturbation="interventional"`
- `model_output="probability"`
- Background data: 100 samples

---

### 3. `compute_global_shap_values()`
전체 데이터에 대한 SHAP 값을 계산합니다.

```python
shap_values_global = xai_service.compute_global_shap_values()

# 결과는 퍼센트(%) 단위로 변환됨
print(shap_values_global.base_values[0])  # 예: 14.28 (%)
```

**노트북 대응 코드**:
```python
# 노트북에서는 이렇게 했음
shap_values_global.values = shap_values_global.values * 100
shap_values_global.base_values = shap_values_global.base_values * 100
```

---

### 4. `compute_local_shap_values(employee_id)`
특정 직원의 SHAP 값을 계산합니다.

```python
shap_values_local = xai_service.compute_local_shap_values("E00001")

# Waterfall plot 그리기
import shap
shap.plots.waterfall(shap_values_local[0], max_display=10)
```

---

### 5. `get_active_employees_with_risk()`
재직자를 퇴사 위험도 순으로 정렬합니다.

```python
risk_df = xai_service.get_active_employees_with_risk()

# 상위 10명 확인
print(risk_df[['사번', 'PREDICTED_RISK']].head(10))
```

**출력 예시**:
```
     사번  PREDICTED_RISK
411  E00412           0.95
966  E00967           0.80
111  E00112           0.79
```

---

### 6. `get_top_features(n=5)`
SHAP 중요도 상위 N개 변수를 반환합니다.

```python
top_5 = xai_service.get_top_features(n=5)
print(top_5)
# ['재직일수', '나이', '현재총연봉', ...]
```

---

## 시각화 예제

### Bar Plot + Beeswarm Plot

```python
import matplotlib.pyplot as plt
import shap

shap_values = xai_service.compute_global_shap_values()

# Bar Plot
fig, ax = plt.subplots(figsize=(10, 6))
shap.plots.bar(shap_values, max_display=10, show=False)
plt.title("핵심 퇴사요인 순위")
plt.show()

# Beeswarm Plot
fig, ax = plt.subplots(figsize=(12, 8))
shap.plots.beeswarm(shap_values, max_display=10, show=False)
plt.title("요인별 위험 패턴")
plt.show()
```

### Partial Dependence Plot

```python
top_features = xai_service.get_top_features(n=5)

for feature in top_features:
    fig = plt.figure(figsize=(10, 6))
    shap.plots.scatter(shap_values[:, feature], color=shap_values, show=False)
    plt.title(f"[{feature}] 값에 따른 퇴사 확률 변화")
    plt.show()
```

### Waterfall Plot (개인별)

```python
# 위험도 1위 직원 분석
risk_df = xai_service.get_active_employees_with_risk()
top_emp_id = risk_df.iloc[0]['사번']

shap_values_local = xai_service.compute_local_shap_values(top_emp_id)

fig = plt.figure(figsize=(10, 6))
shap.plots.waterfall(shap_values_local[0], max_display=10, show=False)
plt.title(f"사번 {top_emp_id}의 퇴사 위험도 구성")
plt.show()
```

---

## Streamlit 앱에서 사용 (캐싱)

```python
import streamlit as st
from services.ml import get_xai_service
from services.tables.create_ml_table import master_df_encoded

@st.cache_resource
def initialize_xai():
    """앱 시작 시 1회만 실행됨"""
    xai_service = get_xai_service(master_df_encoded)
    model = xai_service.train_model()
    explainer = xai_service.create_explainer()
    shap_values_global = xai_service.compute_global_shap_values()

    return {
        'service': xai_service,
        'model': model,
        'explainer': explainer,
        'shap_values': shap_values_global,
    }

# 사용
components = initialize_xai()
shap.plots.bar(components['shap_values'])
```

---

## 파라미터 비교표

| 항목 | 노트북 | XAIService |
|------|--------|------------|
| 데이터 비율 (퇴사:재직) | 1:6 | 1:6 |
| random_state | 42 | 42 |
| n_estimators | 70 | 70 |
| max_depth | 2 | 2 |
| scale_pos_weight | 70 | 70 |
| learning_rate | 0.1 | 0.1 |
| min_child_weight | 10 | 10 |
| SHAP background samples | 100 | 100 |
| Global SHAP samples | 2000 | 2000 |
| feature_perturbation | interventional | interventional |
| model_output | probability | probability |

**동일한 random_state를 사용하므로 결과가 완전히 동일합니다.**
