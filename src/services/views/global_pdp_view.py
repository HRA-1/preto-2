"""
Global Explainer: Partial Dependence Plot View
변수별 영향 확인 시각화
"""

import streamlit as st
import matplotlib.pyplot as plt
import shap
from typing import List


def render_global_pdp(
    shap_values: shap.Explanation,
    top_features: List[str],
    selected_variable: str,
):
    """
    Partial Dependence Plot 렌더링

    Args:
        shap_values: 전역 SHAP 값 (퍼센트 단위)
        top_features: Top N 중요 변수 리스트
        selected_variable: 선택된 변수명 ("개요" 또는 실제 변수명)
    """
    st.title("퇴사 위험 패턴 - 변수별 영향 확인")

    # 변수가 선택되지 않은 경우 (개요)
    if selected_variable == "개요":
        st.info("상단의 **변수 선택** 드롭다운에서 분석할 변수를 선택하세요.")

        st.markdown("---")

        st.subheader("Partial Dependence Plot (PDP) 이란?")

        st.markdown("""
        PDP는 특정 변수의 값이 변함에 따라 **예측 결과(퇴사 확률)가 어떻게 변화하는지**를
        보여주는 그래프입니다.

        ### 그래프 구성
        - **X축**: 선택한 변수의 값
        - **Y축**: 퇴사 확률에 미치는 영향 (%p)
        - **점**: 각 직원의 데이터 포인트
        - **색상**: 다른 변수들과의 상호작용 효과

        ### 활용 방법
        1. 상단 드롭다운에서 **Top 5 중요 변수** 중 하나를 선택
        2. 해당 변수의 값에 따른 퇴사 확률 변화 패턴 확인
        3. 특정 구간에서 위험도가 급격히 변하는지 파악
        """)

        st.markdown("---")

        st.subheader("선택 가능한 변수 (Top 5)")

        for i, feature in enumerate(top_features, 1):
            st.markdown(f"{i}. **{feature}**")

        return

    # 변수가 선택된 경우 - PDP 렌더링
    st.markdown(f"선택된 변수: **{selected_variable}**")

    st.markdown("---")

    # PDP 생성
    fig, ax = plt.subplots()

    try:
        shap.plots.scatter(
            shap_values[:, selected_variable],
            color=shap_values,
            ax=ax,
            show=False,
        )
        plt.title(f"[{selected_variable}] 값에 따른 퇴사 확률 변화", fontsize=14)
        plt.ylabel("퇴사 확률 영향도 (%p)")
        plt.xlabel(selected_variable)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # 그래프 크기 조정을 위한 컬럼 생성
        col1, col2, col3 = st.columns([0.2, 0.5, 0.3])
        with col2:
            st.pyplot(fig, use_container_width=True)
    except Exception as e:
        st.error(f"그래프 생성 중 오류가 발생했습니다: {e}")
    finally:
        plt.close(fig)

    st.markdown("---")

    # 해석 가이드
    st.subheader("해석 가이드")

    st.markdown(f"""
    위 그래프는 **{selected_variable}** 값에 따른 퇴사 확률 변화를 보여줍니다.

    - 점들이 **위쪽**(양수)에 위치: 해당 값일 때 퇴사 확률이 **높아집니다**
    - 점들이 **아래쪽**(음수)에 위치: 해당 값일 때 퇴사 확률이 **낮아집니다**
    - **0 기준선**: 평균적인 영향 (영향 없음)
    - **색상 변화**: 다른 변수들과의 상호작용 효과를 나타냅니다

    ### 인사이트 도출 예시
    - 특정 구간에서 점들이 급격히 상승하면 → 해당 구간이 **위험 구간**
    - 특정 값 이상/이하에서 패턴이 변하면 → **임계점** 파악 가능
    """)