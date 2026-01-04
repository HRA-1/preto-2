"""
XAI Dashboard Filter Configuration
XAI 대시보드용 필터 설정 및 상태 관리
"""

from enum import Enum
from typing import List, Dict

# ==============================================================================
# Filter Placeholders
# ==============================================================================

XAI_FILTER_PLACEHOLDERS = {
    "level1_default": "개요",
    "level2_overview": "개요",
    "variable_overview": "개요",
    "employee_overview": "개요",
}

# ==============================================================================
# Level 1: Analysis Perspective (분석 관점)
# ==============================================================================

ANALYSIS_PERSPECTIVES: Dict[str, List[str]] = {
    "개요": [],  # Placeholder for initial XAI introduction
    "퇴사 위험 패턴": ["주요 영향 변수", "변수별 영향 확인"],
    "개인별 위험 사유": ["개요", "위험도 산출 근거"],
}

PERSPECTIVE_TITLES: Dict[str, str] = {
    "퇴사 위험 패턴": "Global Explainer - 조직 전체 퇴사 위험 패턴 분석",
    "개인별 위험 사유": "Local Explainer - 개인별 퇴사 위험 분석",
}

# ==============================================================================
# Level 2: Detail View Options
# ==============================================================================

DETAIL_VIEW_TITLES: Dict[str, str] = {
    "주요 영향 변수": "핵심 퇴사요인 순위 및 패턴",
    "변수별 영향 확인": "변수별 Partial Dependence Plot",
    "개요": "XAI 분석 소개",
    "위험도 산출 근거": "개인별 Waterfall Plot",
}

# ==============================================================================
# View State Enum
# ==============================================================================


class XAIViewState(Enum):
    """XAI Dashboard UI States"""

    PERSPECTIVE_OVERVIEW = "perspective_overview"  # L1=개요
    DETAIL_SELECTION = "detail_selection"  # L1 selected, L2=개요 (퇴사 위험 패턴만)
    GLOBAL_BAR_BEESWARM = "global_bar_beeswarm"  # Bar + Beeswarm
    GLOBAL_PDP = "global_pdp"  # PDP with variable selector
    LOCAL_OVERVIEW = "local_overview"  # XAI intro text
    LOCAL_WATERFALL = "local_waterfall"  # Waterfall with employee selector


# ==============================================================================
# State Determination Functions
# ==============================================================================


def get_xai_view_state(selected_perspective: str, selected_detail: str) -> XAIViewState:
    """
    Determine current UI state based on filter selections

    Args:
        selected_perspective: L1 선택값 (분석 관점)
        selected_detail: L2 선택값 (상세 확인)

    Returns:
        XAIViewState: 현재 UI 상태
    """
    # L1이 "개요"인 경우
    if selected_perspective == XAI_FILTER_PLACEHOLDERS["level1_default"]:
        return XAIViewState.PERSPECTIVE_OVERVIEW

    # L2가 "개요"인 경우 (퇴사 위험 패턴에서만 해당)
    if (
        selected_perspective == "퇴사 위험 패턴"
        and selected_detail == XAI_FILTER_PLACEHOLDERS["level2_overview"]
    ):
        return XAIViewState.DETAIL_SELECTION

    # Global Explainer views
    if selected_perspective == "퇴사 위험 패턴":
        if selected_detail == "주요 영향 변수":
            return XAIViewState.GLOBAL_BAR_BEESWARM
        elif selected_detail == "변수별 영향 확인":
            return XAIViewState.GLOBAL_PDP

    # Local Explainer views
    if selected_perspective == "개인별 위험 사유":
        if selected_detail == "개요":
            return XAIViewState.LOCAL_OVERVIEW
        elif selected_detail == "위험도 산출 근거":
            return XAIViewState.LOCAL_WATERFALL

    return XAIViewState.PERSPECTIVE_OVERVIEW


def should_show_variable_selector(state: XAIViewState) -> bool:
    """
    L3 Variable selector only active for PDP view

    Args:
        state: 현재 XAIViewState

    Returns:
        bool: 변수 선택 드롭다운 표시 여부
    """
    return state == XAIViewState.GLOBAL_PDP


def should_show_employee_selector(state: XAIViewState) -> bool:
    """
    L4 Employee selector only active for Waterfall view

    Args:
        state: 현재 XAIViewState

    Returns:
        bool: 인원 선택 드롭다운 표시 여부
    """
    return state == XAIViewState.LOCAL_WATERFALL


def is_perspective_placeholder(perspective: str) -> bool:
    """
    Check if L1 selection is placeholder

    Args:
        perspective: L1 선택값

    Returns:
        bool: 플레이스홀더 여부
    """
    return perspective == XAI_FILTER_PLACEHOLDERS["level1_default"]


def is_detail_placeholder(detail: str) -> bool:
    """
    Check if L2 selection is placeholder/overview

    Args:
        detail: L2 선택값

    Returns:
        bool: 플레이스홀더 여부
    """
    return detail == XAI_FILTER_PLACEHOLDERS["level2_overview"]
