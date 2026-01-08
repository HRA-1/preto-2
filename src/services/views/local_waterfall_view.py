"""
Local Explainer: Waterfall Plot View
개인별 위험도 산출 근거 시각화
"""

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import shap
from typing import Optional, Dict, Any

from services.ml.xai_service import XAIService


def render_local_waterfall(
    xai_service: XAIService,
    employee_info_df: pd.DataFrame,
    selected_employee: str,
    employee_risk_df: pd.DataFrame,
):
    """
    개인별 Waterfall Plot 렌더링

    Args:
        xai_service: XAIService 인스턴스
        employee_info_df: 직원 정보 데이터프레임
        selected_employee: 선택된 직원 사번 ("개요" 또는 실제 사번)
        employee_risk_df: 위험도 포함 재직자 데이터프레임
    """
    st.title("개인별 위험 사유 - 위험도 산출 근거")

    # 직원이 선택되지 않은 경우 (개요)
    if selected_employee == "개요":
        st.info("상단의 **인원 선택** 드롭다운에서 분석할 직원을 선택하세요.")

        st.markdown("---")

        st.subheader("퇴사 위험도 상위 직원 목록")

        st.markdown("""
        아래 목록은 **퇴사 가능성이 높은 순서**로 정렬된 재직자입니다.
        인원 선택 드롭다운에서 직원을 선택하면 상세 분석 결과를 확인할 수 있습니다.
        """)

        # 상위 20명 테이블 표시
        if not employee_risk_df.empty:
            display_df = employee_risk_df.head(20)[["사번", "PREDICTED_RISK"]].copy()
            display_df["퇴사 위험도"] = (
                (display_df["PREDICTED_RISK"] * 100).round(1).astype(str) + "%"
            )
            display_df = display_df[["사번", "퇴사 위험도"]]
            display_df = display_df.reset_index(drop=True)
            display_df.index = display_df.index + 1  # 1부터 시작
            display_df.index.name = "순위"

            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("재직자 데이터를 불러올 수 없습니다.")

        return

    # 직원이 선택된 경우 - 상세 분석
    st.markdown("---")

    # 위험도 정보 가져오기
    employee_risk_row = employee_risk_df[employee_risk_df["사번"] == selected_employee]

    if employee_risk_row.empty:
        st.error(f"사번 {selected_employee}의 데이터를 찾을 수 없습니다.")
        return

    risk_score = employee_risk_row["PREDICTED_RISK"].iloc[0]

    # 직원 정보 가져오기
    employee_info = xai_service.get_employee_info_for_display(
        selected_employee, employee_info_df
    )

    # 상단 메트릭 카드
    st.subheader(f"직원 정보: {selected_employee}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # 위험도에 따른 색상
        if risk_score >= 0.5:
            st.metric("퇴사 위험도", f"{risk_score * 100:.1f}%", delta="높음", delta_color="inverse")
        elif risk_score >= 0.2:
            st.metric("퇴사 위험도", f"{risk_score * 100:.1f}%", delta="중간", delta_color="off")
        else:
            st.metric("퇴사 위험도", f"{risk_score * 100:.1f}%", delta="낮음", delta_color="normal")

    with col2:
        st.metric("소속 본부", employee_info.get("소속 본부", "N/A"))

    with col3:
        st.metric("직무", employee_info.get("직무 중분류", "N/A"))

    with col4:
        st.metric("입사일자", str(employee_info.get("입사일자", "N/A")))

    st.markdown("---")

    # 상세 정보 테이블
    st.subheader("상세 정보")

    info_data = {
        "항목": ["이름", "사번", "소속 본부", "소속 실", "직무 대분류", "직무 중분류", "입사일자", "현재 계약연봉"],
        "내용": [
            employee_info.get("이름", "N/A"),
            employee_info.get("사번", "N/A"),
            employee_info.get("소속 본부", "N/A"),
            employee_info.get("소속 실", "N/A"),
            employee_info.get("직무 대분류", "N/A"),
            employee_info.get("직무 중분류", "N/A"),
            str(employee_info.get("입사일자", "N/A")),
            f"{employee_info.get('현재 계약연봉', 0):,.0f}원" if employee_info.get("현재 계약연봉") != "N/A" else "N/A",
        ],
    }
    info_df = pd.DataFrame(info_data)
    st.dataframe(info_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Waterfall Plot
    st.subheader("퇴사 위험도 구성 요인 (Waterfall Plot)")

    st.markdown(f"""
    아래 그래프는 **{selected_employee}** 직원의 퇴사 위험도가 어떤 요인들로 구성되는지 보여줍니다.
    """)

    # SHAP 값 계산
    with st.spinner("SHAP 분석 중..."):
        shap_values = xai_service.compute_local_shap_values(selected_employee)

    if shap_values is None:
        st.error("해당 직원의 SHAP 값을 계산할 수 없습니다.")
        return

    # Waterfall Plot 렌더링
    fig = plt.figure(figsize=(10, 6))

    try:
        shap.plots.waterfall(shap_values[0], max_display=10, show=False)
        plt.title(f"사번 {selected_employee}의 퇴사 위험도 구성 (%)", fontsize=14)
        plt.xlabel("퇴사 위험도 기여도 (%p)")
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Waterfall Plot 생성 중 오류가 발생했습니다: {e}")
    finally:
        plt.close(fig)

    st.markdown("---")

    # 해석 가이드
    st.subheader("해석 가이드")

    base_value = shap_values.base_values[0]

    st.markdown(f"""
    | 항목 | 값 |
    |------|-----|
    | **Base Value (평균 퇴사율)** | {base_value:.1f}% |
    | **최종 예측 퇴사율** | {risk_score * 100:.1f}% |
    | **차이** | {(risk_score * 100) - base_value:+.1f}%p |

    ### 그래프 읽는 방법
    - **빨간 막대**: 퇴사 확률을 **높이는** 요인
    - **파란 막대**: 퇴사 확률을 **낮추는** 요인
    - 막대 옆의 숫자: 해당 직원의 실제 변수 값
    - 막대의 길이: 해당 요인이 미치는 영향의 크기 (%p)
    """)

    # 주요 위험/보호 요인 분석
    with st.expander("주요 요인 상세 분석", expanded=False):
        shap_df = pd.DataFrame({
            "변수": shap_values.feature_names,
            "SHAP 값 (%p)": shap_values.values[0],
        })
        shap_df = shap_df.sort_values("SHAP 값 (%p)", key=abs, ascending=False)

        st.markdown("#### 퇴사 위험 증가 요인 (Top 5)")
        risk_factors = shap_df[shap_df["SHAP 값 (%p)"] > 0].head(5)
        if not risk_factors.empty:
            for _, row in risk_factors.iterrows():
                st.markdown(f"- **{row['변수']}**: +{row['SHAP 값 (%p)']:.2f}%p")
        else:
            st.markdown("해당 없음")

        st.markdown("#### 퇴사 위험 감소 요인 (Top 5)")
        protect_factors = shap_df[shap_df["SHAP 값 (%p)"] < 0].head(5)
        if not protect_factors.empty:
            for _, row in protect_factors.iterrows():
                st.markdown(f"- **{row['변수']}**: {row['SHAP 값 (%p)']:.2f}%p")
        else:
            st.markdown("해당 없음")
