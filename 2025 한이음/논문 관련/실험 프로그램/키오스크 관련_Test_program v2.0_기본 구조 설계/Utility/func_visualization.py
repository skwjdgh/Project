import matplotlib.pyplot as plt
import seaborn as sns
import platform
import logging

# Set Korean font for plotting
try:
    if platform.system() == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif platform.system() == 'Darwin': # macOS
        plt.rc('font', family='AppleGothic')
    else: # Linux
        plt.rc('font', family='NanumGothic')
    plt.rcParams['axes.unicode_minus'] = False # Fix for minus sign not showing
except Exception as e:
    logging.warning(f"Failed to set Korean font for plots. Korean text may appear broken. Error: {e}")


def plot_accuracy_results(summary_df, output_path):
    """Creates and saves a bar chart for accuracy results per condition."""
    plt.figure(figsize=(12, 7))
    ax = sns.barplot(x='condition', y='accuracy', data=summary_df, palette='viridis', order=['A (Baseline)', 'B (Tokenization)', 'C (Noise Cancellation)', 'D (Tokenization + NC)'])
    plt.title('STT Keyword Recognition Accuracy by Condition', fontsize=16, pad=20)
    plt.xlabel('Experiment Condition', fontsize=12)
    plt.ylabel('Accuracy (%)', fontsize=12)
    plt.ylim(0, 105)
    # Add accuracy values on top of each bar
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', fontsize=11, color='black', xytext=(0, 5), textcoords='offset points')
    plt.xticks(rotation=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_data_distribution(dist_df, category_name, output_path):
    """Creates and saves a pie chart for data distribution."""
    if dist_df.empty:
        return
    plt.figure(figsize=(10, 8))
    # Show top 10 items if there are too many
    if len(dist_df) > 10:
        dist_df = dist_df.nlargest(10, 'count')
    plt.pie(dist_df['count'], labels=dist_df['item'], autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title(f'Input Data Distribution: {category_name.capitalize()}', fontsize=16)
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

