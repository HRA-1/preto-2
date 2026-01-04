"""
XAI Service Module
XGBoost 모델 학습 및 SHAP 분석을 위한 서비스 클래스
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import shap
from typing import List, Optional, Dict, Any


class XAIService:
    """
    XAI 대시보드용 ML 서비스 클래스

    - XGBoost 분류기 학습
    - SHAP TreeExplainer 생성
    - Global/Local SHAP 값 계산
    """

    def __init__(self, master_df_encoded: pd.DataFrame):
        """
        XAIService 초기화

        Args:
            master_df_encoded: ML용 인코딩된 마스터 데이터프레임
        """
        self.master_df_encoded = master_df_encoded.copy()
        self._preprocess_data()

        # 캐시용 변수
        self._model = None
        self._explainer = None
        self._shap_values_global = None
        self._top_features = None
        self._employee_risk_df = None

    def _preprocess_data(self):
        """데이터 전처리: 타입 변환 및 결측치 처리"""
        # 데이터 타입 정리
        for col in self.master_df_encoded.columns:
            if self.master_df_encoded[col].dtype == "object" and col not in [
                "사번",
                "재직여부",
                "퇴사자여부",
            ]:
                self.master_df_encoded[col] = pd.to_numeric(
                    self.master_df_encoded[col], errors="coerce"
                )

        # 결측치 처리
        self.master_df_encoded.fillna(
            self.master_df_encoded.median(numeric_only=True), inplace=True
        )

        # 피처 컬럼 정의
        self.drop_cols = ["사번", "재직여부", "퇴사자여부"]
        self.feature_cols = [
            col for col in self.master_df_encoded.columns if col not in self.drop_cols
        ]

    def _create_balanced_dataset(self) -> tuple:
        """
        학습용 균형 데이터셋 생성 (1:6 비율)

        Returns:
            tuple: (X_train, y_train)
        """
        df_leavers = self.master_df_encoded[self.master_df_encoded["퇴사자여부"] == 1]
        df_active = self.master_df_encoded[self.master_df_encoded["퇴사자여부"] == 0]

        n_leavers = len(df_leavers)
        n_required_active = n_leavers * 6

        # 재직자 오버샘플링
        df_active_oversampled = df_active.sample(
            n=n_required_active, replace=True, random_state=42
        )

        balanced_df = (
            pd.concat([df_leavers, df_active_oversampled], axis=0)
            .sample(frac=1, random_state=42)
            .reset_index(drop=True)
        )

        X_train = balanced_df[self.feature_cols].astype(float)
        y_train = balanced_df["퇴사자여부"].astype(float)

        return X_train, y_train

    def train_model(self) -> xgb.XGBClassifier:
        """
        XGBoost 분류기 학습

        Returns:
            xgb.XGBClassifier: 학습된 모델
        """
        if self._model is not None:
            return self._model

        X_train, y_train = self._create_balanced_dataset()

        weight_ratio = 70

        self._model = xgb.XGBClassifier(
            n_estimators=weight_ratio,
            max_depth=2,
            learning_rate=0.1,
            scale_pos_weight=weight_ratio,
            random_state=42,
            min_child_weight=10,
            use_label_encoder=False,
            eval_metric="logloss",
        )
        self._model.fit(X_train, y_train)

        return self._model

    def create_explainer(self, model: xgb.XGBClassifier = None) -> shap.TreeExplainer:
        """
        SHAP TreeExplainer 생성

        Args:
            model: XGBoost 모델 (None이면 내부 모델 사용)

        Returns:
            shap.TreeExplainer: SHAP explainer
        """
        if self._explainer is not None:
            return self._explainer

        if model is None:
            model = self.train_model()

        X_train, _ = self._create_balanced_dataset()
        background_data = shap.sample(X_train, 100)

        self._explainer = shap.TreeExplainer(
            model,
            data=background_data,
            feature_perturbation="interventional",
            model_output="probability",
        )

        return self._explainer

    def compute_global_shap_values(
        self,
        model: xgb.XGBClassifier = None,
        explainer: shap.TreeExplainer = None,
        n_samples: int = 2000,
    ) -> shap.Explanation:
        """
        전역 SHAP 값 계산

        Args:
            model: XGBoost 모델
            explainer: SHAP explainer
            n_samples: 샘플 수 (기본 2000)

        Returns:
            shap.Explanation: SHAP 값 (퍼센트 단위)
        """
        if self._shap_values_global is not None:
            return self._shap_values_global

        if model is None:
            model = self.train_model()
        if explainer is None:
            explainer = self.create_explainer(model)

        X_train, _ = self._create_balanced_dataset()
        X_sample = X_train.sample(n=min(n_samples, len(X_train)), random_state=42)

        shap_values = explainer(X_sample)

        # 확률 -> 퍼센트 변환
        shap_values.values = shap_values.values * 100
        shap_values.base_values = shap_values.base_values * 100

        self._shap_values_global = shap_values

        return shap_values

    def compute_local_shap_values(
        self,
        employee_id: str,
        model: xgb.XGBClassifier = None,
        explainer: shap.TreeExplainer = None,
    ) -> Optional[shap.Explanation]:
        """
        개별 직원 SHAP 값 계산

        Args:
            employee_id: 직원 사번
            model: XGBoost 모델
            explainer: SHAP explainer

        Returns:
            shap.Explanation: SHAP 값 (퍼센트 단위) 또는 None
        """
        if model is None:
            model = self.train_model()
        if explainer is None:
            explainer = self.create_explainer(model)

        employee_data = self.master_df_encoded[
            self.master_df_encoded["사번"] == employee_id
        ]

        if employee_data.empty:
            return None

        X_employee = employee_data[self.feature_cols].astype(float).values

        shap_values = explainer(X_employee)

        # 확률 -> 퍼센트 변환
        shap_values.values = shap_values.values * 100
        shap_values.base_values = shap_values.base_values * 100

        return shap_values

    def get_active_employees_with_risk(
        self, model: xgb.XGBClassifier = None
    ) -> pd.DataFrame:
        """
        재직자 목록을 퇴사 위험도 순으로 정렬하여 반환

        Args:
            model: XGBoost 모델

        Returns:
            pd.DataFrame: 사번, 위험도 등 포함된 데이터프레임
        """
        if self._employee_risk_df is not None:
            return self._employee_risk_df

        if model is None:
            model = self.train_model()

        active_employees = self.master_df_encoded[
            self.master_df_encoded["재직여부"] == "Y"
        ].copy()

        if active_employees.empty:
            return pd.DataFrame()

        X_active = active_employees[self.feature_cols].astype(float)
        probs = model.predict_proba(X_active)[:, 1]

        active_employees["PREDICTED_RISK"] = probs
        self._employee_risk_df = active_employees.sort_values(
            by="PREDICTED_RISK", ascending=False
        )

        return self._employee_risk_df

    def get_top_features(
        self, shap_values: shap.Explanation = None, n: int = 5
    ) -> List[str]:
        """
        Top N 중요 변수 추출

        Args:
            shap_values: SHAP 값 (None이면 전역 값 사용)
            n: 추출할 변수 수

        Returns:
            List[str]: 중요 변수 이름 리스트
        """
        if self._top_features is not None and len(self._top_features) >= n:
            return self._top_features[:n]

        if shap_values is None:
            shap_values = self.compute_global_shap_values()

        mean_abs_shap = np.abs(shap_values.values).mean(0)
        top_indices = np.argsort(mean_abs_shap)[-n:][::-1]

        self._top_features = [shap_values.feature_names[i] for i in top_indices]

        return self._top_features

    def get_employee_info_for_display(
        self, employee_id: str, employee_info_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        대시보드 표시용 직원 정보 조회

        Args:
            employee_id: 직원 사번
            employee_info_df: 직원 정보 데이터프레임

        Returns:
            Dict: 직원 정보 딕셔너리
        """
        employee_info = employee_info_df[employee_info_df["사번"] == employee_id]

        if employee_info.empty:
            return {}

        row = employee_info.iloc[0]

        return {
            "사번": employee_id,
            "이름": row.get("이름", "N/A"),
            "입사일자": row.get("입사일자", "N/A"),
            "소속 본부": row.get("소속 본부", "N/A"),
            "소속 실": row.get("소속 실", "N/A"),
            "직무 대분류": row.get("직무 대분류", "N/A"),
            "직무 중분류": row.get("직무 중분류", "N/A"),
            "현재 계약연봉": row.get("현재 계약연봉", "N/A"),
        }


def get_xai_service(master_df_encoded: pd.DataFrame) -> XAIService:
    """
    XAIService 인스턴스 생성 팩토리 함수

    Args:
        master_df_encoded: ML용 인코딩된 마스터 데이터프레임

    Returns:
        XAIService: 서비스 인스턴스
    """
    return XAIService(master_df_encoded)
