import io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm

from market_data import get_fng_description


def _get_korean_font() -> fm.FontProperties:
    """OS별 한글 폰트 자동 선택 (Malgun Gothic → NanumGothic → 기본 폰트 순)"""
    available = {f.name for f in fm.fontManager.ttflist}
    for name in ['Malgun Gothic', 'AppleGothic', 'NanumGothic', 'NanumBarunGothic']:
        if name in available:
            return fm.FontProperties(family=name)
    return fm.FontProperties()


def generate_fear_greed_gauge_image(score):
    """공포·탐욕 지수 반원 게이지 이미지 생성 (직교좌표 기반)"""
    fp = _get_korean_font()

    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_facecolor('white')
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-0.65, 1.45)
    ax.set_aspect('equal')
    ax.axis('off')

    # 색상 세그먼트: (시작점수, 끝점수, 색상, 라벨)
    # 각도 변환: score=0 → 180°(좌), score=100 → 0°(우)
    OUTER_R = 1.0
    INNER_R = 0.55
    segments = [
        (0,   25,  '#d32f2f', '극도의\n공포'),
        (25,  45,  '#FF8C00', '공포'),
        (45,  55,  '#F9A825', '중립'),
        (55,  75,  '#7CB342', '탐욕'),
        (75,  100, '#2E7D32', '극도의\n탐욕'),
    ]

    for start_s, end_s, color, label in segments:
        # patches.Wedge는 직교좌표계 → theta1 < theta2 순서여야 함
        theta1 = 180 - end_s * 1.8
        theta2 = 180 - start_s * 1.8
        ax.add_patch(patches.Wedge(
            center=(0, 0), r=OUTER_R,
            theta1=theta1, theta2=theta2,
            width=OUTER_R - INNER_R,
            facecolor=color, edgecolor='white', linewidth=2,
        ))

        # 세그먼트 바깥쪽에 라벨 배치
        mid_angle = np.deg2rad(180 - (start_s + end_s) / 2 * 1.8)
        label_r = OUTER_R + 0.25
        ax.text(
            label_r * np.cos(mid_angle),
            label_r * np.sin(mid_angle),
            label, fontproperties=fp,
            ha='center', va='center', fontsize=9, color='#222222', linespacing=1.3,
        )

    # 내부 눈금 숫자 (0, 25, 50, 75, 100)
    for tick in [0, 25, 50, 75, 100]:
        tick_angle = np.deg2rad(180 - tick * 1.8)
        tick_r = INNER_R - 0.12
        ax.text(
            tick_r * np.cos(tick_angle),
            tick_r * np.sin(tick_angle),
            str(tick), ha='center', va='center', fontsize=8, color='#666666',
        )

    # 바늘
    needle_angle = np.deg2rad(180 - score * 1.8)
    needle_len = OUTER_R - 0.04
    ax.plot(
        [0, needle_len * np.cos(needle_angle)],
        [0, needle_len * np.sin(needle_angle)],
        color='#1a1a1a', lw=3, solid_capstyle='round', zorder=4,
    )
    ax.add_patch(plt.Circle((0, 0), 0.07, color='#1a1a1a', zorder=5))

    # 점수 (대형)
    ax.text(0, -0.2, str(score), ha='center', va='center',
            fontproperties=fp, fontsize=44, fontweight='bold', color='#1a1a1a')

    # 단계 텍스트
    ax.text(0, -0.48, get_fng_description(score), ha='center', va='center',
            fontproperties=fp, fontsize=12, color='#555555')

    img_data = io.BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight', dpi=150, facecolor='white')
    img_data.seek(0)
    plt.close(fig)
    return img_data