# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "openai",
#   "scipy",
# ]
# ///

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import asyncio
import httpx

AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise ValueError("AIPROXY_TOKEN environment variable not set")

API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

def load_data(filename):
    return pd.read_csv(filename, encoding='utf-8', encoding_errors='replace')

def analyze_data(df):
    summary = df.describe(include='all')
    missing_values = df.isnull().sum()
    numeric_df = df.select_dtypes(include=['number'])
    correlation_matrix = numeric_df.corr()
    
    # Outlier detection: Using z-scores to identify outliers in numeric columns
    from scipy.stats import zscore
    z_scores = numeric_df.apply(zscore)
    outliers = (z_scores.abs() > 3).sum(axis=0)
    
    return summary, missing_values, correlation_matrix, outliers

def visualize_data(df):
    # Style settings
    sns.set(style="whitegrid")
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10

    # Density plot for the first numeric column
    numeric_columns = df.select_dtypes(include=['number']).columns
    if len(numeric_columns) > 0:
        plt.figure(figsize=(8, 6))
        sns.kdeplot(df[numeric_columns[0]], fill=True, color="skyblue", linewidth=2)
        plt.title(f'Density Plot of {numeric_columns[0]}', fontsize=16)
        plt.xlabel(numeric_columns[0], fontsize=14)
        plt.ylabel('Density', fontsize=14)
        plt.grid(True)
        plt.savefig('density_plot.png', bbox_inches='tight')
        plt.clf()

    # Scatter plot for the first two numeric columns
    if len(numeric_columns) > 1:
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x=numeric_columns[0], y=numeric_columns[1], data=df, color='green', edgecolor='black', s=100)
        plt.title(f'Scatter Plot of {numeric_columns[0]} vs {numeric_columns[1]}', fontsize=16)
        plt.xlabel(numeric_columns[0], fontsize=14)
        plt.ylabel(numeric_columns[1], fontsize=14)
        plt.grid(True)
        plt.savefig('scatter_plot.png', bbox_inches='tight')
        plt.clf()

    # Histogram for all numeric columns
    if len(numeric_columns) > 0:
        df[numeric_columns].hist(bins=20, color='orange', edgecolor='black', linewidth=1.2)
        plt.suptitle('Histograms of Numeric Columns', fontsize=16)
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        plt.savefig('histogram.png', bbox_inches='tight')
        plt.clf()

    # Select only numeric columns from the DataFrame
    numeric_df = df.select_dtypes(include=[float, int])
    # Calculate the correlation matrix on the numeric columns
    plt.figure(figsize=(10, 8))
    sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt='.2f', linewidths=0.5)
    plt.title("Correlation Matrix Heatmap", fontsize=16)
    plt.savefig('correlation_heatmap.png', bbox_inches='tight')
    plt.clf()


import httpx
import asyncio


async def generate_story(summary, missing_values, correlation_matrix,outliers):
    prompt = f"""
    You are a data analyst with expertise in exploratory data analysis (EDA). Given the following summary of a dataset, please provide a comprehensive analysis focusing on the following aspects:

    ### 1. **Data Quality:**
       - **Missing Values**: Identify columns with missing values, the percentage of missing data in each column, and any patterns you notice in the missingness (e.g., is it random or systematic?). Suggest methods to handle missing data, such as imputation, deletion, or other techniques.
       - **Outliers**: Based on the descriptive statistics and visualizations, identify any columns or data points that show extreme values or outliers. Discuss how these might affect your analysis and suggest approaches for handling them (e.g., capping, transformation, or removal).
       - **Data Types**: Ensure that the data types of each column are appropriate for their respective values. Highlight any mismatches or anomalies, such as numerical values stored as strings, and recommend corrections if needed.

    ### 2. **Dataset Summary (Descriptive Statistics)**:
       - **Overview**: Provide an interpretation of the descriptive statistics for both numerical and categorical columns. Highlight any significant observations, such as:
         - Measures of central tendency (mean, median) and spread (standard deviation, interquartile range).
         - Any columns with highly skewed distributions, unusual values, or other anomalies.
         - Differences between numerical and categorical columns, including the number of unique values and their distribution.
       - **Statistical Insights**: Based on the descriptive statistics, identify any patterns that suggest potential relationships, trends, or further investigation areas.
       
    Dataset Summary (Descriptive Statistics):
    {summary}

    ### 3. **Correlation Matrix:**
       - **Variable Relationships**: Discuss the correlation matrix and any strong correlations (positive or negative) between variables. Identify pairs of variables with high correlation and consider whether this suggests multicollinearity or a strong relationship that could influence modeling.
       - **Unexpected Findings**: Point out any surprising correlations or lack thereof. Are there variables that should logically correlate but do not? Could this indicate issues with data collection or transformation?

    Correlation Matrix:
    {correlation_matrix}

    ### 4. **Visualization Analysis:**
    Analyze and interpret the following visualizations in the context of the data:

    1. **Density Plot**: 
       - Explain the distribution of the first numeric column. Is the distribution bell-shaped, skewed, or multimodal? Are there any indications of non-normality, such as long tails or multiple peaks?
       - Discuss how the shape of the distribution might affect statistical analyses or modeling. For example, a skewed distribution might require transformation (e.g., log or square root).
       - If applicable, compare the density plot to known distributions (e.g., normal, exponential) to check for fit.

    2. **Scatter Plot**: 
       - Discuss the relationship between the first two numeric columns. Is there a linear, nonlinear, or no clear relationship? Are there any visible clusters, trends, or outliers?
       - If a linear relationship exists, quantify the strength of the correlation (based on the correlation matrix) and whether it aligns with the visual pattern.
       - Identify any outliers or points that don’t follow the general trend, and discuss possible reasons for these discrepancies.

    3. **Histogram**:
       - Describe the distribution of all numeric columns. Are any columns normally distributed, skewed, or exhibit unusual peaks or gaps?
       - Discuss the width of the bins and how it affects the granularity of the distribution. Consider suggesting adjustments if the histogram fails to capture the nuances of the data.
       - Mention any columns that may require data transformation (e.g., log transformation for highly skewed data) to normalize their distribution.

    Missing Values:
    {missing_values}

    ### 5. **Recommendations for Further Exploration and Data Cleaning:**
       - **Exploration**: Based on your insights from the dataset summary, correlation matrix, and visualizations, recommend further steps for exploration. For example, do any variables warrant deeper investigation, or is there a need for feature engineering to improve the data quality or predictive power?
       - **Data Cleaning**: Provide suggestions for addressing issues identified during the analysis, such as handling missing values, outliers, data transformations, or correcting data type mismatches.
       - **Statistical Modeling**: Based on the relationships found in the correlation matrix and scatter plot, suggest appropriate modeling techniques or transformations that might improve the performance of any predictive models.

    Please ensure that your analysis is detailed and provides actionable insights for further improving the data quality and preparing the dataset for more advanced analyses or modeling tasks.

    Outliers:
    {outliers}
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a data analyst with expertise in dataset exploration."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(API_URL, headers=headers, json=data)
        response_data = response.json()
    
    return response_data['choices'][0]['message']['content']



def save_readme(story):
    with open('README.md', 'w') as f:
        f.write("# Automated Data Analysis Report\n")
        f.write("This report presents a detailed analysis of the dataset, including descriptive statistics, data visualizations, and key insights.\n\n")
        
        # Write the generated story
        f.write("## Insights from Dataset Analysis\n")
        f.write(story)
        
        # Add visualizations section
        f.write("\n## Visualizations\n")
        
        f.write("\n### 1. Density Plot\n")
        f.write("This plot shows the distribution of the first numeric column. It helps in understanding the shape of the distribution (e.g., normal, skewed, etc.).\n")
        f.write("![Density Plot](density_plot.png)\n")
        
        f.write("\n### 2. Scatter Plot\n")
        f.write("This plot illustrates the relationship between the first two numeric columns. It can show if there is any correlation or a specific trend.\n")
        f.write("![Scatter Plot](scatter_plot.png)\n")
        
        f.write("\n### 3. Histogram\n")
        f.write("This plot provides a view of the distribution of all numeric columns in the dataset. It is useful to identify data patterns such as skewness or outliers.\n")
        f.write("![Histogram](histogram.png)\n")
        
        f.write("\n### 4. Correlation Heatmap\n")
        f.write("This heatmap visualizes the correlations between numeric columns in the dataset.\n")
        f.write("![Correlation Heatmap](correlation_heatmap.png)\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    df = load_data(filename)
    summary, missing_values, correlation_matrix, outliers = analyze_data(df)
    visualize_data(df)
    story = asyncio.run(generate_story(summary, missing_values, correlation_matrix, outliers))
    save_readme(story)

if __name__ == "__main__":
    main()
