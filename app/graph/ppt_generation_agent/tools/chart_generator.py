import os
import uuid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from app.core.logger import get_logger

logger = get_logger(__name__)

# Professional color palette
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72', 
    'accent': '#F18F01',
    'success': '#C73E1D',
    'dark': '#1B1B3A',
    'palette': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3BCEAC', '#6B2D5C', '#0EAD69', '#FF6B6B']
}

def generate_chart(data: dict, output_dir: str) -> str:
    """
    Generates various chart types from structured data.
    
    Supported types: bar, line, pie, donut, funnel, timeline, horizontal_bar, stacked_bar
    """
    try:
        chart_type = data.get("type", "bar").lower()
        title = data.get("title", "Chart")
        labels = data.get("labels", [])
        values = data.get("values", [])
        x_label = data.get("x_label", "")
        y_label = data.get("y_label", "")
        colors = data.get("colors", COLORS['palette'][:len(labels)])

        if not labels and chart_type != "timeline":
            logger.warning("No labels provided for chart generation.")
            return None

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('#FAFAFA')
        ax.set_facecolor('#FAFAFA')

        if chart_type == "bar":
            bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5)
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02, 
                       f'{val:,.0f}' if isinstance(val, (int, float)) else str(val),
                       ha='center', va='bottom', fontsize=11, fontweight='bold')
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)

        elif chart_type == "horizontal_bar":
            y_pos = np.arange(len(labels))
            bars = ax.barh(y_pos, values, color=colors, edgecolor='white', linewidth=1.5)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels)
            for bar, val in zip(bars, values):
                ax.text(val + max(values)*0.02, bar.get_y() + bar.get_height()/2,
                       f'{val:,.0f}' if isinstance(val, (int, float)) else str(val),
                       va='center', fontsize=11, fontweight='bold')
            ax.set_xlabel(y_label, fontsize=12)

        elif chart_type == "line":
            ax.plot(labels, values, marker='o', markersize=10, linewidth=3, color=COLORS['primary'])
            ax.fill_between(labels, values, alpha=0.3, color=COLORS['primary'])
            for i, val in enumerate(values):
                ax.annotate(f'{val:,.0f}' if isinstance(val, (int, float)) else str(val),
                           (labels[i], val), textcoords="offset points", xytext=(0,10),
                           ha='center', fontsize=10, fontweight='bold')
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)

        elif chart_type == "pie":
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                               colors=colors, explode=[0.02]*len(values),
                                               shadow=True, startangle=90)
            for autotext in autotexts:
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')

        elif chart_type == "donut":
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                               colors=colors, explode=[0.02]*len(values),
                                               startangle=90, pctdistance=0.75)
            centre_circle = plt.Circle((0, 0), 0.50, fc='#FAFAFA')
            ax.add_patch(centre_circle)
            total = sum(values)
            ax.text(0, 0, f'Total\n{total:,.0f}', ha='center', va='center', fontsize=14, fontweight='bold')

        elif chart_type == "funnel":
            # Funnel chart
            widths = np.array(values) / max(values)
            y_positions = np.arange(len(labels))[::-1]
            for i, (label, width, val) in enumerate(zip(labels, widths, values)):
                left = (1 - width) / 2
                ax.barh(y_positions[i], width, left=left, height=0.7, 
                       color=colors[i % len(colors)], edgecolor='white', linewidth=2)
                ax.text(0.5, y_positions[i], f'{label}\n{val:,.0f}', 
                       ha='center', va='center', fontsize=11, fontweight='bold', color='white')
            ax.set_xlim(0, 1)
            ax.set_ylim(-0.5, len(labels) - 0.5)
            ax.axis('off')

        elif chart_type == "timeline":
            # Timeline/Roadmap chart
            milestones = data.get("milestones", [])
            if not milestones:
                milestones = [{"date": l, "event": v} for l, v in zip(labels, values)]
            
            y_pos = 0
            for i, m in enumerate(milestones):
                color = colors[i % len(colors)]
                ax.scatter(i, y_pos, s=200, color=color, zorder=3)
                ax.annotate(m.get("date", f"Q{i+1}"), (i, y_pos - 0.15), ha='center', fontsize=10, fontweight='bold')
                ax.annotate(m.get("event", ""), (i, y_pos + 0.15), ha='center', fontsize=9, 
                           wrap=True, bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.3))
            ax.plot(range(len(milestones)), [y_pos]*len(milestones), 'k-', linewidth=2, zorder=1)
            ax.set_ylim(-0.5, 0.5)
            ax.axis('off')

        else:
            logger.warning(f"Unsupported chart type: {chart_type}. Defaulting to bar.")
            bars = ax.bar(labels, values, color=COLORS['palette'][:len(labels)])

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
        plt.close()
        
        logger.info(f"Chart saved to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        import traceback
        traceback.print_exc()
        return None
