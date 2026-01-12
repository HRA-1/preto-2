"""
Global Explainer: Bar Plot + Beeswarm Plot View
핵심 퇴사요인 순위 및 요인별 위험 패턴 시각화
"""

import streamlit as st
import matplotlib.pyplot as plt
import shap


def render_global_bar_beeswarm(shap_values: shap.Explanation):
    """
    Bar Plot과 Beeswarm Plot을 렌더링

    Args:
        shap_values: 전역 SHAP 값 (퍼센트 단위)
    """
    st.title("퇴사 위험 패턴 - 주요 영향 변수")

    st.markdown("""
    XGBoost 모델과 SHAP 분석을 통해 퇴사에 영향을 미치는 핵심 요인을 파악합니다.
    """)

    st.markdown("---")

    # Bar Plot
    st.subheader("1. 핵심 퇴사요인 순위 (Bar Plot)")

    st.markdown("""
    각 변수가 퇴사 확률에 미치는 **평균 영향력 크기**를 보여줍니다.
    막대가 길수록 해당 변수가 퇴사 예측에 중요한 역할을 합니다.
    """)

    fig_bar, ax_bar = plt.subplots()
    shap.plots.bar(shap_values, max_display=10, show=False)
    plt.title("요인별 평균 영향력 크기 (Mean Absolute SHAP)", fontsize=14)
    plt.xlabel("평균 퇴사 확률 변동폭 (%p)")
    plt.tight_layout()
    
    # 그래프 크기 조정을 위한 컬럼 생성
    col1, col2, col3 = st.columns([0.2, 0.5, 0.3])
    with col2:
        st.pyplot(fig_bar, use_container_width=True)
    plt.close(fig_bar)

    st.markdown("---")

    # Beeswarm Plot
    st.subheader("2. 요인별 위험 패턴 (Beeswarm Plot)")

    st.markdown("""
    각 점은 한 명의 직원을 나타냅니다.
    - **X축**: 해당 변수가 퇴사 확률을 얼마나 높이거나 낮추는지 (%p)
    - **색상**: 빨강(변수 값이 높음) / 파랑(변수 값이 낮음)
    """)

    fig_bee, ax_bee = plt.subplots()
    shap.plots.beeswarm(
        shap_values,
        max_display=10,
        show=False,
        color_bar_label="변수 값 (빨강=높음, 파랑=낮음)",
    )
    plt.title("전사 퇴사 위험도 영향 요인 (단위: %p)", fontsize=14)
    plt.xlabel("퇴사 확률에 미치는 영향 (%p)")
    plt.tight_layout()

    # 그래프 크기 조정을 위한 컬럼 생성
    col1, col2, col3 = st.columns([0.2, 0.5, 0.3])
    with col2:
        st.pyplot(fig_bee, use_container_width=True)
    plt.close(fig_bee)

    st.markdown("---")

    # 해석 가이드
    with st.expander("해석 가이드", expanded=False):
        st.markdown("""
        ### Bar Plot 해석
        - 막대의 길이는 해당 변수의 **평균적인 영향력**을 나타냅니다.
        - 상위에 위치한 변수일수록 퇴사 예측에 중요합니다.

        ### Beeswarm Plot 해석
        - 점이 **오른쪽**에 위치: 퇴사 확률을 **높이는** 방향으로 영향
        - 점이 **왼쪽**에 위치: 퇴사 확률을 **낮추는** 방향으로 영향
        - **빨간 점**이 오른쪽에 몰려 있으면: 해당 변수 값이 높을 때 퇴사 위험 증가
        - **파란 점**이 오른쪽에 몰려 있으면: 해당 변수 값이 낮을 때 퇴사 위험 증가
        """)