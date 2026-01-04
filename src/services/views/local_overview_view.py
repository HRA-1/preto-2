"""
Local Explainer: Overview View
XAI 소개 및 Waterfall Plot 설명
"""

import streamlit as st


def render_local_overview():
    """
    XAI 소개 텍스트 렌더링
    개인별 위험 사유 분석 방법론 설명
    """
    st.title("개인별 위험 사유 - 개요")

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

    # Waterfall Plot 설명
    st.subheader("Waterfall Plot 이해하기")

    st.markdown("""
    **Waterfall Plot**은 개인의 퇴사 위험도가 어떻게 계산되었는지를
    시각적으로 보여주는 그래프입니다.
    """)

    st.markdown("""
    ### 구성 요소

    | 요소 | 설명 |
    |------|------|
    | **Base Value** | 전체 직원의 평균 퇴사 확률 (시작점) |
    | **빨간 막대** | 퇴사 확률을 **높이는** 요인 (오른쪽으로 이동) |
    | **파란 막대** | 퇴사 확률을 **낮추는** 요인 (왼쪽으로 이동) |
    | **최종 예측값** | 모든 요인을 합산한 최종 퇴사 위험도 |
    """)

    st.markdown("---")

    # 활용 방법
    st.subheader("활용 방법")

    st.markdown("""
    1. **상세 확인** 메뉴에서 **"위험도 산출 근거"**를 선택하세요.
    2. 상단의 **인원 선택** 드롭다운에서 분석할 직원을 선택하세요.
       - 목록은 **퇴사 위험도가 높은 순**으로 정렬되어 있습니다.
       - 형식: `이름 (위험도%)`
    3. 선택한 직원의 상세 정보와 **Waterfall Plot**을 확인하세요.
    """)

    st.markdown("---")

    # 주의사항
    with st.expander("주의사항", expanded=False):
        st.markdown("""
        - 예측 결과는 **과거 데이터 패턴**을 기반으로 하며, 절대적인 미래 예측이 아닙니다.
        - 개인의 퇴사 결정에는 모델이 파악하지 못하는 다양한 요소가 존재합니다.
        - 본 분석은 **참고 자료**로 활용하시고, 실제 인사 결정은 종합적인 판단이 필요합니다.
        - 개인정보 보호를 위해 접근 권한이 제한될 수 있습니다.
        """)
