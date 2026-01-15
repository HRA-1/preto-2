"""
HR Analytics XAI Dashboard
퇴사 위험 분석을 위한 설명 가능한 AI 대시보드
"""

import streamlit as st
import streamlit_analytics2 as streamlit_analytics
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd

from services.config.xai_filters_config import (
    XAI_FILTER_PLACEHOLDERS,
    ANALYSIS_PERSPECTIVES,
    PERSPECTIVE_TITLES,
    DETAIL_VIEW_TITLES,
    XAIViewState,
    get_xai_view_state,
    should_show_variable_selector,
    should_show_employee_selector,
)
from services.ml.xai_service import get_xai_service
from services.views import (
    render_global_bar_beeswarm,
    render_global_pdp,
    render_local_overview,
    render_local_waterfall,
)

# ==============================================================================
# Page Configuration
# ==============================================================================

st.set_page_config(
    page_title="HR Analytics - XAI Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "HR Analytics XAI Dashboard - 퇴사 위험 분석",
    },
)


# ==============================================================================
# Korean Font Setup
# ==============================================================================


def set_korean_font():
    """Configure matplotlib for Korean text rendering"""
    font_names = [f.name for f in fm.fontManager.ttflist]
    if "NanumGothic" in font_names:
        plt.rcParams["font.family"] = "NanumGothic"
    elif "NanumBarunGothic" in font_names:
        plt.rcParams["font.family"] = "NanumBarunGothic"
    elif "Malgun Gothic" in font_names:
        plt.rcParams["font.family"] = "Malgun Gothic"
    elif "AppleGothic" in font_names:
        plt.rcParams["font.family"] = "AppleGothic"
    else:
        plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False


set_korean_font()


# ==============================================================================
# Cached Data Loading
# ==============================================================================


@st.cache_resource(show_spinner=False)
def initialize_xai_components():
    """
    XAI 컴포넌트 초기화 (앱 레벨 캐싱)
    - 모델 학습, SHAP explainer 생성, 전역 SHAP 값 계산
    - 앱 시작 시 1회만 실행됨
    """
    master_df_encoded = pd.read_csv('/app/src/services/tables/master_df_encoded.csv')
    employee_info_df = pd.read_csv('/app/src/services/tables/employee_info_df.csv')

    xai_service = get_xai_service(master_df_encoded)
    model = xai_service.train_model()
    explainer = xai_service.create_explainer(model)
    shap_values_global = xai_service.compute_global_shap_values(model, explainer)
    top_features = xai_service.get_top_features(shap_values_global, n=5)
    employee_risk_df = xai_service.get_active_employees_with_risk(model)

    return {
        "xai_service": xai_service,
        "model": model,
        "explainer": explainer,
        "shap_values_global": shap_values_global,
        "top_features": top_features,
        "employee_risk_df": employee_risk_df,
        "employee_info_df": employee_info_df,
    }


# ==============================================================================
# Overview Rendering
# ==============================================================================


def render_perspective_overview():
    """메인 XAI 대시보드 개요 페이지 렌더링"""
    st.title("HR Analytics - 퇴사 위험 분석 (XAI Dashboard)")

    st.markdown(
        """
    ## 환영합니다!

    본 대시보드는 **설명 가능한 인공지능(XAI)** 기술을 활용하여
    직원들의 퇴사 위험을 분석하고 그 원인을 설명합니다.

    ---

    ### 주요 기능

    #### 1. 퇴사 위험 패턴 (Global Explainer)
    조직 전체의 퇴사 위험 패턴을 분석합니다.
    - **주요 영향 변수**: 전사적으로 퇴사에 가장 큰 영향을 미치는 요인 순위
    - **변수별 영향 확인**: 각 변수가 퇴사 확률에 미치는 영향 상세 분석

    #### 2. 개인별 위험 사유 (Local Explainer)
    개별 직원의 퇴사 위험 요인을 분석합니다.
    - **개요**: XAI 분석 방법론 소개
    - **위험도 산출 근거**: 개별 직원의 퇴사 위험 요인 분석

    ---

    👈 **시작하려면 왼쪽 사이드바에서 분석 관점을 선택하세요.**
    """
    )


def render_detail_selection(selected_perspective: str):
    """상세 뷰 선택 안내 페이지 렌더링"""
    st.title(PERSPECTIVE_TITLES.get(selected_perspective, selected_perspective))

    detail_options = ANALYSIS_PERSPECTIVES.get(selected_perspective, [])

    st.markdown("### 상세 분석 메뉴를 선택하세요")

    st.markdown("왼쪽 사이드바의 **상세 확인** 드롭다운에서 메뉴를 선택하세요.")

    st.markdown("---")

    # XAI 소개
    st.subheader("XAI (설명 가능한 인공지능) 란?")

    st.markdown("""
    **XAI(eXplainable AI)**는 인공지능 모델의 예측 결과를 사람이 이해할 수 있는
    형태로 설명해주는 기술입니다.

    본 대시보드에서는 **SHAP(SHapley Additive exPlanations)** 방법론을 활용하여
    각 직원의 퇴사 위험도가 **어떤 요인들에 의해 결정되었는지** 설명합니다.
    """)

    st.markdown("---")

    # 분석 방법 설명
    st.subheader("분석 방법")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 1. 퇴사 위험도 산출
        - 기존 퇴사자 데이터를 기반으로 **머신러닝 모델(XGBoost)** 학습
        - 재직 중인 직원들의 퇴사 가능성을 **0~100%**로 예측
        - 높은 확률일수록 퇴사 위험이 높음
        """)

    with col2:
        st.markdown("""
        #### 2. 위험 요인 분석
        - **SHAP 알고리즘**으로 각 직원별 위험 요인 분해
        - 어떤 요소가 퇴사 확률을 높이는지/낮추는지 파악
        - 개인 맞춤형 인사이트 제공
        """)

    st.markdown("---")

    for detail in detail_options:
        st.markdown(f"- **{detail}**: {DETAIL_VIEW_TITLES.get(detail, '')}")


# ==============================================================================
# Main Application
# ==============================================================================


def main():
    """Main application entry point"""

    with streamlit_analytics.track():
        # Initialize XAI components (cached)
        with st.spinner("XAI 모델을 초기화하는 중... (최초 1회만 실행됩니다)"):
            components = initialize_xai_components()

        # ================================================================
        # SIDEBAR - Level 1 & 2 Filters
        # ================================================================

        st.sidebar.title("HR Analytics")
        st.sidebar.markdown("### Insight Explainer")
        st.sidebar.markdown("---")

        # L1: Analysis Perspective Selection (분석 관점 선택)
        selected_perspective = st.sidebar.selectbox(
            "분석 관점 선택",
            options=list(ANALYSIS_PERSPECTIVES.keys()),
            index=0,
            format_func=lambda x: x if x == "개요" else f"📊 {x}",
        )

        # L2: Detail View Selection (상세 확인)
        if selected_perspective == XAI_FILTER_PLACEHOLDERS["level1_default"]:
            # L1이 "개요"인 경우: L2도 "개요"로 고정
            selected_detail = st.sidebar.selectbox(
                "상세 확인",
                options=[XAI_FILTER_PLACEHOLDERS["level2_overview"]],
                index=0,
            )
        else:
            # L1이 선택된 경우: 해당 관점의 상세 옵션 표시
            detail_options = [XAI_FILTER_PLACEHOLDERS["level2_overview"]] + ANALYSIS_PERSPECTIVES.get(
                selected_perspective, []
            )
            selected_detail = st.sidebar.selectbox(
                "상세 확인",
                options=detail_options,
                format_func=lambda x: DETAIL_VIEW_TITLES.get(x, x),
                index=0,
            )

        # ================================================================
        # SIDEBAR - Bottom Links
        # ================================================================

        st.sidebar.markdown("---")

        st.sidebar.markdown("#### 소개글 보기")
        st.sidebar.markdown(
            '<a href="https://lrl.kr/XrgX" target="_blank" style="color: #1E90FF; text-decoration: none;">📄 소개글 보기</a>',
            unsafe_allow_html=True,
        )

        st.sidebar.markdown("#### 설문 참여하기")
        st.sidebar.markdown(
            '<a href="https://lrl.kr/fG9te" target="_blank" style="color: #1E90FF; text-decoration: none;">📝 설문 참여하기</a>',
            unsafe_allow_html=True,
        )

        # ================================================================
        # MAIN AREA - Level 3 & 4 Filters (Conditional)
        # ================================================================

        view_state = get_xai_view_state(selected_perspective, selected_detail)

        # Filter row
        col_filter1, col_filter2 = st.columns([1, 1])

        # L3: Variable Selector (변수 선택) - PDP 뷰에서만 활성화
        selected_variable = XAI_FILTER_PLACEHOLDERS["variable_overview"]
        with col_filter1:
            if should_show_variable_selector(view_state):
                variable_options = [XAI_FILTER_PLACEHOLDERS["variable_overview"]] + components[
                    "top_features"
                ]
                selected_variable = st.selectbox(
                    "변수 선택",
                    options=variable_options,
                    index=0,
                )
            else:
                st.selectbox(
                    "변수 선택",
                    options=[XAI_FILTER_PLACEHOLDERS["variable_overview"]],
                    index=0,
                    disabled=True,
                )

        # L4: Employee Selector (인원 선택) - Waterfall 뷰에서만 활성화
        selected_employee = XAI_FILTER_PLACEHOLDERS["employee_overview"]
        with col_filter2:
            if should_show_employee_selector(view_state):
                employee_risk_df = components["employee_risk_df"]

                # Format employee options: "이름 (위험도%)" or "사번 (위험도%)"
                employee_options = [XAI_FILTER_PLACEHOLDERS["employee_overview"]]

                # employee_info_df와 조인하여 이름 가져오기
                employee_info_df = components["employee_info_df"]

                for _, row in employee_risk_df.iterrows():
                    emp_id = row["사번"]
                    risk_pct = row["PREDICTED_RISK"] * 100

                    # 이름 조회
                    emp_info = employee_info_df[employee_info_df["사번"] == emp_id]
                    if not emp_info.empty and "이름" in emp_info.columns:
                        name = emp_info["이름"].iloc[0]
                        label = f"{name} ({risk_pct:.1f}%)"
                    else:
                        label = f"{emp_id} ({risk_pct:.1f}%)"

                    employee_options.append((emp_id, label))

                selected_employee_tuple = st.selectbox(
                    "인원 선택",
                    options=employee_options,
                    format_func=lambda x: x[1] if isinstance(x, tuple) else x,
                    index=0,
                )

                selected_employee = (
                    selected_employee_tuple[0]
                    if isinstance(selected_employee_tuple, tuple)
                    else selected_employee_tuple
                )
            else:
                st.selectbox(
                    "인원 선택",
                    options=[XAI_FILTER_PLACEHOLDERS["employee_overview"]],
                    index=0,
                    disabled=True,
                )

        st.markdown("---")

        # ================================================================
        # MAIN CONTENT - State-based Rendering
        # ================================================================

        if view_state == XAIViewState.PERSPECTIVE_OVERVIEW:
            render_perspective_overview()

        elif view_state == XAIViewState.DETAIL_SELECTION:
            render_detail_selection(selected_perspective)

        elif view_state == XAIViewState.GLOBAL_BAR_BEESWARM:
            render_global_bar_beeswarm(components["shap_values_global"])

        elif view_state == XAIViewState.GLOBAL_PDP:
            render_global_pdp(
                components["shap_values_global"],
                components["top_features"],
                selected_variable,
            )

        elif view_state == XAIViewState.LOCAL_OVERVIEW:
            render_local_overview()

        elif view_state == XAIViewState.LOCAL_WATERFALL:
            render_local_waterfall(
                components["xai_service"],
                components["employee_info_df"],
                selected_employee,
                components["employee_risk_df"],
            )


if __name__ == "__main__":
    main()
