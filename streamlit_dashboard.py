"""
CloudMart Resource Tagging Interactive Dashboard
Week 10 Activity - Task Sets 4 and 5
Streamlit Application for Cost Visibility and Tag Remediation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import io

# Page configuration
st.set_page_config(
    page_title="CloudMart Cost Governance Dashboard",
    page_icon="☁️",
    layout="wide"
)

@st.cache_data
def load_data(filepath='cloudmart_multi_account.csv'):
    """Load and prepare the dataset"""
    # Use na_values parameter to treat empty strings as NaN
    df = pd.read_csv(filepath, na_values=['', ' '])
    # Remove duplicates
    df = df.drop_duplicates()

    # Calculate tag completeness score
    tag_fields = ['Department', 'Project', 'Environment', 'Owner', 'CostCenter']
    df['TagCompletenessScore'] = df[tag_fields].notna().sum(axis=1)
    df['TagCompletenessPercentage'] = (df['TagCompletenessScore'] / len(tag_fields)) * 100

    return df

def create_tagged_pie_chart(df):
    """Task 4.1: Pie chart of tagged vs untagged resources"""
    tagged_counts = df['Tagged'].value_counts()

    fig = px.pie(
        values=tagged_counts.values,
        names=tagged_counts.index,
        title='Tagged vs Untagged Resources',
        color=tagged_counts.index,
        color_discrete_map={'Yes': '#2ecc71', 'No': '#e74c3c'}
    )
    fig.update_traces(textposition='inside', textinfo='percent+label+value')
    return fig

def create_cost_by_department_chart(df):
    """Task 4.2: Bar chart of cost per department by tagging status"""
    dept_cost = df.groupby(['Department', 'Tagged'])['MonthlyCostUSD'].sum().reset_index()

    fig = px.bar(
        dept_cost,
        x='Department',
        y='MonthlyCostUSD',
        color='Tagged',
        title='Cost per Department by Tagging Status',
        barmode='group',
        color_discrete_map={'Yes': '#2ecc71', 'No': '#e74c3c'},
        labels={'MonthlyCostUSD': 'Monthly Cost (USD)', 'Tagged': 'Tagging Status'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def create_cost_by_service_chart(df):
    """Task 4.3: Horizontal bar chart of total cost per service"""
    service_cost = df.groupby('Service')['MonthlyCostUSD'].sum().sort_values(ascending=True)

    fig = px.bar(
        x=service_cost.values,
        y=service_cost.index,
        orientation='h',
        title='Total Cost by Service',
        labels={'x': 'Monthly Cost (USD)', 'y': 'Service'},
        color=service_cost.values,
        color_continuous_scale='Blues'
    )
    return fig

def create_cost_by_environment_chart(df):
    """Task 4.4: Visualize cost by environment"""
    env_cost = df.groupby('Environment')['MonthlyCostUSD'].sum()

    fig = px.pie(
        values=env_cost.values,
        names=env_cost.index,
        title='Cost Distribution by Environment',
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    fig.update_traces(textposition='inside', textinfo='percent+label+value')
    return fig

def calculate_metrics(df):
    """Calculate key metrics for dashboard"""
    total_resources = len(df)
    tagged_resources = len(df[df['Tagged'] == 'Yes'])
    untagged_resources = len(df[df['Tagged'] == 'No'])

    total_cost = df['MonthlyCostUSD'].sum()
    tagged_cost = df[df['Tagged'] == 'Yes']['MonthlyCostUSD'].sum()
    untagged_cost = df[df['Tagged'] == 'No']['MonthlyCostUSD'].sum()

    avg_completeness = df['TagCompletenessScore'].mean()

    return {
        'total_resources': total_resources,
        'tagged_resources': tagged_resources,
        'untagged_resources': untagged_resources,
        'tagging_rate': (tagged_resources / total_resources * 100) if total_resources > 0 else 0,
        'total_cost': total_cost,
        'tagged_cost': tagged_cost,
        'untagged_cost': untagged_cost,
        'untagged_cost_pct': (untagged_cost / total_cost * 100) if total_cost > 0 else 0,
        'avg_completeness': avg_completeness
    }

def main():
    """Main dashboard application"""

    # Title and header
    st.title("☁️ CloudMart Cost Governance Dashboard")
    st.markdown("### Resource Tagging and Cost Visibility Analysis")

    # Sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Overview & Analytics", "Tag Remediation Workflow"]
    )

    # Load data
    try:
        df = load_data()
    except FileNotFoundError:
        st.error("Dataset file 'cloudmart_multi_account.csv' not found. Please ensure it's in the same directory.")
        return

    if page == "Overview & Analytics":
        show_analytics_page(df)
    else:
        show_remediation_page(df)

def show_analytics_page(df):
    """Task Set 4: Visualization Dashboard"""

    st.header("📊 Cost & Tagging Analytics")

    # Task 4.5: Interactive filters
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filters")

    # Get unique values for filters
    all_services = ['All'] + sorted(df['Service'].dropna().unique().tolist())
    all_regions = ['All'] + sorted(df['Region'].dropna().unique().tolist())
    all_departments = ['All'] + sorted(df['Department'].dropna().unique().tolist())
    all_environments = ['All'] + sorted(df['Environment'].dropna().unique().tolist())

    selected_service = st.sidebar.selectbox("Service", all_services)
    selected_region = st.sidebar.selectbox("Region", all_regions)
    selected_department = st.sidebar.selectbox("Department", all_departments)
    selected_environment = st.sidebar.selectbox("Environment", all_environments)

    # Apply filters
    filtered_df = df.copy()
    if selected_service != 'All':
        filtered_df = filtered_df[filtered_df['Service'] == selected_service]
    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['Region'] == selected_region]
    if selected_department != 'All':
        filtered_df = filtered_df[filtered_df['Department'] == selected_department]
    if selected_environment != 'All':
        filtered_df = filtered_df[filtered_df['Environment'] == selected_environment]

    if len(filtered_df) == 0:
        st.warning("No resources match the selected filters. Please adjust your selection.")
        return

    # Calculate metrics
    metrics = calculate_metrics(filtered_df)

    # Display key metrics
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Resources",
            f"{metrics['total_resources']:,}",
            delta=f"{metrics['tagging_rate']:.1f}% Tagged"
        )

    with col2:
        st.metric(
            "Untagged Resources",
            f"{metrics['untagged_resources']:,}",
            delta=f"-{100-metrics['tagging_rate']:.1f}%",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            "Total Monthly Cost",
            f"${metrics['total_cost']:,.2f}",
            delta=f"${metrics['tagged_cost']:,.2f} Tagged"
        )

    with col4:
        st.metric(
            "Untagged Cost",
            f"${metrics['untagged_cost']:,.2f}",
            delta=f"{metrics['untagged_cost_pct']:.1f}% of Total",
            delta_color="inverse"
        )

    st.markdown("---")

    # Visualizations
    st.subheader("📊 Visualizations")

    # Task 4.1: Tagged vs Untagged pie chart
    col1, col2 = st.columns(2)
    with col1:
        fig1 = create_tagged_pie_chart(filtered_df)
        st.plotly_chart(fig1, width='stretch')

    # Task 4.4: Cost by environment
    with col2:
        fig4 = create_cost_by_environment_chart(filtered_df)
        st.plotly_chart(fig4, width='stretch')

    # Task 4.2: Cost by department
    fig2 = create_cost_by_department_chart(filtered_df)
    st.plotly_chart(fig2, width='stretch')

    # Task 4.3: Cost by service
    fig3 = create_cost_by_service_chart(filtered_df)
    st.plotly_chart(fig3, width='stretch')

    # Additional insights
    st.markdown("---")
    st.subheader("🔍 Detailed Analysis")

    tab1, tab2, tab3 = st.tabs(["By Department", "By Service", "By Environment"])

    with tab1:
        dept_analysis = filtered_df.groupby('Department').agg({
            'ResourceID': 'count',
            'MonthlyCostUSD': 'sum',
            'Tagged': lambda x: (x == 'Yes').sum() / len(x) * 100
        }).round(2)
        dept_analysis.columns = ['Resource Count', 'Total Cost (USD)', 'Tagging Rate (%)']
        dept_analysis = dept_analysis.sort_values('Total Cost (USD)', ascending=False)
        st.dataframe(dept_analysis, width='stretch')

    with tab2:
        service_analysis = filtered_df.groupby('Service').agg({
            'ResourceID': 'count',
            'MonthlyCostUSD': 'sum',
            'Tagged': lambda x: (x == 'Yes').sum() / len(x) * 100
        }).round(2)
        service_analysis.columns = ['Resource Count', 'Total Cost (USD)', 'Tagging Rate (%)']
        service_analysis = service_analysis.sort_values('Total Cost (USD)', ascending=False)
        st.dataframe(service_analysis, width='stretch')

    with tab3:
        env_analysis = filtered_df.groupby('Environment').agg({
            'ResourceID': 'count',
            'MonthlyCostUSD': 'sum',
            'Tagged': lambda x: (x == 'Yes').sum() / len(x) * 100
        }).round(2)
        env_analysis.columns = ['Resource Count', 'Total Cost (USD)', 'Tagging Rate (%)']
        env_analysis = env_analysis.sort_values('Total Cost (USD)', ascending=False)
        st.dataframe(env_analysis, width='stretch')

def show_remediation_page(df):
    """Task Set 5: Tag Remediation Workflow"""

    st.header("🔧 Tag Remediation Workflow")

    # Calculate before metrics
    before_metrics = calculate_metrics(df)

    st.subheader("📊 Before Remediation")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Untagged Resources", f"{before_metrics['untagged_resources']:,}")
    with col2:
        st.metric("Untagged Cost", f"${before_metrics['untagged_cost']:,.2f}")
    with col3:
        st.metric("Avg Tag Completeness", f"{before_metrics['avg_completeness']:.2f}/5")

    st.markdown("---")

    # Task 5.1: Editable table for untagged resources
    st.subheader("🖊️ Edit Untagged Resources")
    st.info("💡 Edit the table below to add missing tags. Mark 'Tagged' as 'Yes' after completing all required fields.")

    # Filter untagged or incomplete resources
    untagged_df = df[df['Tagged'] == 'No'].copy()

    if len(untagged_df) == 0:
        st.success("🎉 All resources are properly tagged!")
        return

    # Select columns for editing
    edit_columns = [
        'ResourceID', 'Service', 'Region', 'Department', 'Project',
        'Environment', 'Owner', 'CostCenter', 'MonthlyCostUSD', 'Tagged'
    ]

    # Task 5.2: Editable data editor
    edited_df = st.data_editor(
        untagged_df[edit_columns],
        width='stretch',
        num_rows="fixed",
        column_config={
            "ResourceID": st.column_config.TextColumn("Resource ID", disabled=True),
            "Service": st.column_config.TextColumn("Service", disabled=True),
            "Region": st.column_config.TextColumn("Region", disabled=True),
            "MonthlyCostUSD": st.column_config.NumberColumn("Monthly Cost", format="$%.2f", disabled=True),
            "Department": st.column_config.TextColumn("Department", required=True),
            "Project": st.column_config.TextColumn("Project", required=True),
            "Environment": st.column_config.SelectboxColumn(
                "Environment",
                options=["Prod", "Dev", "Test"],
                required=True
            ),
            "Owner": st.column_config.TextColumn("Owner", required=True),
            "CostCenter": st.column_config.TextColumn("Cost Center", required=True),
            "Tagged": st.column_config.SelectboxColumn(
                "Tagged",
                options=["Yes", "No"],
                required=True
            )
        },
        hide_index=True
    )

    # Create updated full dataset
    remediated_df = df.copy()
    for idx, row in edited_df.iterrows():
        mask = remediated_df['ResourceID'] == row['ResourceID']
        for col in edit_columns:
            if col in edited_df.columns:
                remediated_df.loc[mask, col] = row[col]

    # Recalculate tag completeness
    tag_fields = ['Department', 'Project', 'Environment', 'Owner', 'CostCenter']
    remediated_df['TagCompletenessScore'] = remediated_df[tag_fields].notna().sum(axis=1)
    remediated_df['TagCompletenessPercentage'] = (remediated_df['TagCompletenessScore'] / len(tag_fields)) * 100

    # Task 5.4: Compare before and after
    st.markdown("---")
    st.subheader("📈 After Remediation (Preview)")

    after_metrics = calculate_metrics(remediated_df)

    col1, col2, col3 = st.columns(3)

    with col1:
        improvement = before_metrics['untagged_resources'] - after_metrics['untagged_resources']
        st.metric(
            "Untagged Resources",
            f"{after_metrics['untagged_resources']:,}",
            delta=f"-{improvement}" if improvement > 0 else "0",
            delta_color="inverse"
        )

    with col2:
        cost_improvement = before_metrics['untagged_cost'] - after_metrics['untagged_cost']
        st.metric(
            "Untagged Cost",
            f"${after_metrics['untagged_cost']:,.2f}",
            delta=f"-${cost_improvement:,.2f}" if cost_improvement > 0 else "$0.00",
            delta_color="inverse"
        )

    with col3:
        completeness_improvement = after_metrics['avg_completeness'] - before_metrics['avg_completeness']
        st.metric(
            "Avg Tag Completeness",
            f"{after_metrics['avg_completeness']:.2f}/5",
            delta=f"+{completeness_improvement:.2f}" if completeness_improvement > 0 else "0.00"
        )

    # Comparison chart
    st.subheader("📊 Before vs After Comparison")

    comparison_data = pd.DataFrame({
        'Metric': ['Untagged Resources', 'Untagged Cost ($)', 'Tagging Rate (%)'],
        'Before': [
            before_metrics['untagged_resources'],
            before_metrics['untagged_cost'],
            before_metrics['tagging_rate']
        ],
        'After': [
            after_metrics['untagged_resources'],
            after_metrics['untagged_cost'],
            after_metrics['tagging_rate']
        ]
    })

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Before', x=comparison_data['Metric'], y=comparison_data['Before'], marker_color='#e74c3c'))
    fig.add_trace(go.Bar(name='After', x=comparison_data['Metric'], y=comparison_data['After'], marker_color='#2ecc71'))
    fig.update_layout(barmode='group', title='Before vs After Remediation')
    st.plotly_chart(fig, width='stretch')

    # Task 5.3: Download updated dataset
    st.markdown("---")
    st.subheader("💾 Download Remediated Dataset")

    # Create CSV buffer
    csv_buffer = io.StringIO()
    remediated_df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    st.download_button(
        label="📥 Download Remediated Dataset (CSV)",
        data=csv_data,
        file_name="cloudmart_remediated.csv",
        mime="text/csv",
        help="Download the updated dataset with tag remediation changes"
    )

    # Task 5.5: Impact discussion
    st.markdown("---")
    st.subheader("💡 Impact of Improved Tagging")

    st.markdown("""
    ### How Improved Tagging Affects Accountability and Reports:

    #### 1. **Enhanced Cost Visibility**
    - Clear attribution of costs to departments and projects
    - Accurate budget tracking and forecasting
    - Identification of cost optimization opportunities

    #### 2. **Improved Accountability**
    - Resource ownership is clearly defined
    - Teams are responsible for their cloud spending
    - Easier to identify and eliminate waste

    #### 3. **Better Decision Making**
    - Data-driven insights into resource utilization
    - Informed decisions about resource scaling
    - Strategic planning based on accurate cost data

    #### 4. **Simplified Compliance & Auditing**
    - Easy to demonstrate resource governance
    - Automated compliance reporting
    - Clear audit trails for all resources

    #### 5. **Operational Efficiency**
    - Faster troubleshooting with proper resource identification
    - Automated resource lifecycle management
    - Streamlined cost allocation and chargeback processes
    """)

if __name__ == "__main__":
    main()
