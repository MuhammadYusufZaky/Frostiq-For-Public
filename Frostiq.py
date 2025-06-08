import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Interactive Media Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Interactive Media Intelligence Dashboard")

# --- 1. Upload Your CSV File ---
st.header("1. Upload Your CSV File")
st.markdown("Please upload a CSV file with the following columns: `Date`, `Platform`, `Sentiment`, `Location`, `Engagements`, `Media Type`.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Read the CSV into a pandas DataFrame
        df = pd.read_csv(uploaded_file)

        # --- 2. Clean the Data ---
        st.header("2. Data Cleaning Summary")

        # Keep track of cleaning stats
        original_rows = len(df)
        missing_engagements_count = 0
        invalid_date_count = 0

        # Normalize column names for robust processing
        # Create a mapping for robust column identification
        column_map = {
            'date': 'Date',
            'platform': 'Platform',
            'sentiment': 'Sentiment',
            'location': 'Location',
            'engagements': 'Engagements',
            'media type': 'Media Type'
        }
        
        # Rename columns based on normalized versions
        df.columns = [col.lower().strip() for col in df.columns]
        df = df.rename(columns=column_map)

        # Ensure all required columns exist, fill with empty string if not
        required_columns = ['Date', 'Platform', 'Sentiment', 'Location', 'Engagements', 'Media Type']
        for col in required_columns:
            if col not in df.columns:
                df[col] = '' # Add missing column with empty strings

        # Convert 'Date' to datetime, coercing errors to NaT
        initial_date_nulls = df['Date'].isnull().sum()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        invalid_date_count = df['Date'].isnull().sum() - initial_date_nulls # Count new NaT values

        # Fill missing 'Engagements' with 0 and convert to numeric
        # First, count how many were originally missing or non-numeric
        for index, row in df.iterrows():
            if pd.isna(row['Engagements']) or str(row['Engagements']).strip() == '':
                missing_engagements_count += 1
            else:
                try:
                    # Attempt to convert to numeric, if it fails, increment count
                    if not pd.api.types.is_numeric_dtype(type(row['Engagements'])):
                         float(row['Engagements'])
                except ValueError:
                    missing_engagements_count += 1
                    
        df['Engagements'] = pd.to_numeric(df['Engagements'], errors='coerce').fillna(0).astype(int)


        # Drop rows where 'Date' is NaT after coercion (invalid dates)
        df.dropna(subset=['Date'], inplace=True)

        cleaned_rows = len(df)

        st.write(f"Original rows: {original_rows}")
        st.write(f"Valid rows processed: {cleaned_rows}")
        st.write(f"Missing/Invalid 'Engagements' filled with 0: {missing_engagements_count}")
        st.write(f"Rows skipped due to invalid 'Date': {invalid_date_count}")

        if cleaned_rows == 0:
            st.warning("No valid data found after cleaning. Please check your CSV file and column headers.")
        else:
            st.success("Data cleaned successfully! Displaying charts.")

            # --- 3. Build 5 Interactive Charts using Plotly ---

            # --- Sentiment Breakdown (Pie Chart) ---
            st.header("3. Sentiment Breakdown")
            sentiment_counts = df['Sentiment'].value_counts().reset_index()
            sentiment_counts.columns = ['Sentiment', 'Count']
            fig_sentiment = px.pie(
                sentiment_counts,
                names='Sentiment',
                values='Count',
                title='Sentiment Breakdown',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_sentiment.update_traces(textinfo='percent+label', pull=[0.05 if s == sentiment_counts['Sentiment'].iloc[0] else 0 for s in sentiment_counts['Sentiment']])
            st.plotly_chart(fig_sentiment, use_container_width=True)

            st.subheader("Top 3 Insights:")
            total_sentiments = sentiment_counts['Count'].sum()
            insights = []
            if len(sentiment_counts) > 0:
                dominant_sentiment = sentiment_counts.iloc[0]
                insights.append(f"<li>The dominant sentiment is <b>{dominant_sentiment['Sentiment']}</b>, accounting for <b>{(dominant_sentiment['Count'] / total_sentiments * 100):.1f}%</b> of all mentions.</li>")
            if len(sentiment_counts) > 1:
                second_sentiment = sentiment_counts.iloc[1]
                insights.append(f"<li>The second most common sentiment is <b>{second_sentiment['Sentiment']}</b>, representing <b>{(second_sentiment['Count'] / total_sentiments * 100):.1f}%</b>.</li>")
            if len(sentiment_counts) > 2:
                third_sentiment = sentiment_counts.iloc[2]
                insights.append(f"<li>The third most common sentiment is <b>{third_sentiment['Sentiment']}</b>, representing <b>{(third_sentiment['Count'] / total_sentiments * 100):.1f}%</b>.</li>")
            st.markdown("<ul>" + "".join(insights) + "</ul>", unsafe_allow_html=True)

            # --- Engagement Trend over Time (Line Chart) ---
            st.header("4. Engagement Trend over Time")
            engagement_by_date = df.groupby(df['Date'].dt.date)['Engagements'].sum().reset_index()
            engagement_by_date.columns = ['Date', 'Total Engagements']
            fig_engagement_trend = px.line(
                engagement_by_date,
                x='Date',
                y='Total Engagements',
                title='Engagement Trend Over Time',
                markers=True,
                line_shape='linear',
                color_discrete_sequence=['#4f46e5'] # Indigo-600
            )
            st.plotly_chart(fig_engagement_trend, use_container_width=True)

            st.subheader("Top 3 Insights:")
            insights = []
            if len(engagement_by_date) > 0:
                max_engagement_row = engagement_by_date.loc[engagement_by_date['Total Engagements'].idxmax()]
                insights.append(f"<li>The peak engagement occurred on <b>{max_engagement_row['Date']}</b>, with a total of <b>{max_engagement_row['Total Engagements']:,}</b> engagements.</li>")

                avg_engagement = engagement_by_date['Total Engagements'].mean()
                insights.append(f"<li>The average daily engagement over the period is approximately <b>{avg_engagement:,.0f}</b>.</li>")

                if len(engagement_by_date) > 1:
                    start_engagement = engagement_by_date['Total Engagements'].iloc[0]
                    end_engagement = engagement_by_date['Total Engagements'].iloc[-1]
                    if end_engagement > start_engagement * 1.1:
                        insights.append('<li>There is an observable <b>upward trend</b> in engagements over the period.</li>')
                    elif end_engagement < start_engagement * 0.9:
                        insights.append('<li>There is an observable <b>downward trend</b> in engagements over the period.</li>')
                    else:
                        insights.append('<li>Engagements remained relatively <b>stable</b> throughout the period.</li>')
            st.markdown("<ul>" + "".join(insights) + "</ul>", unsafe_allow_html=True)


            # --- Platform Engagements (Bar Chart) ---
            st.header("5. Platform Engagements")
            platform_engagements = df.groupby('Platform')['Engagements'].sum().reset_index()
            platform_engagements = platform_engagements.sort_values(by='Engagements', ascending=False)
            fig_platform = px.bar(
                platform_engagements,
                x='Platform',
                y='Engagements',
                title='Platform Engagements',
                color_discrete_sequence=['#3b82f6'] # Blue-500
            )
            st.plotly_chart(fig_platform, use_container_width=True)

            st.subheader("Top 3 Insights:")
            insights = []
            if len(platform_engagements) > 0:
                most_engaging_platform = platform_engagements.iloc[0]
                insights.append(f"<li><b>{most_engaging_platform['Platform']}</b> is the most engaging platform, contributing <b>{most_engaging_platform['Engagements']:,}</b> total engagements.</li>")
            if len(platform_engagements) > 1:
                second_platform = platform_engagements.iloc[1]
                percentage_difference = ((most_engaging_platform['Engagements'] - second_platform['Engagements']) / second_platform['Engagements'] * 100) if second_platform['Engagements'] != 0 else float('inf')
                insights.append(f"<li><b>{most_engaging_platform['Platform']}</b> generated {'<b>' + str(percentage_difference:.1f) + '% more</b>' if percentage_difference > 0 else 'fewer'} engagements than the second most engaging platform, <b>{second_platform['Platform']}</b>.</li>")
            if len(platform_engagements) > 2:
                insights.append(f"<li>The top three platforms combined account for a significant portion of overall engagements.</li>")
            st.markdown("<ul>" + "".join(insights) + "</ul>", unsafe_allow_html=True)


            # --- Media Type Mix (Pie Chart) ---
            st.header("6. Media Type Mix")
            media_type_counts = df['Media Type'].value_counts().reset_index()
            media_type_counts.columns = ['Media Type', 'Count']
            fig_media_type = px.pie(
                media_type_counts,
                names='Media Type',
                values='Count',
                title='Media Type Mix',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig_media_type.update_traces(textinfo='percent+label', pull=[0.05 if mt == media_type_counts['Media Type'].iloc[0] else 0 for mt in media_type_counts['Media Type']])
            st.plotly_chart(fig_media_type, use_container_width=True)

            st.subheader("Top 3 Insights:")
            total_media_types = media_type_counts['Count'].sum()
            insights = []
            if len(media_type_counts) > 0:
                most_prevalent_media_type = media_type_counts.iloc[0]
                insights.append(f"<li>The most prevalent media type is <b>{most_prevalent_media_type['Media Type']}</b>, making up <b>{(most_prevalent_media_type['Count'] / total_media_types * 100):.1f}%</b> of the content.</li>")
            if len(media_type_counts) > 1:
                second_media_type = media_type_counts.iloc[1]
                insights.append(f"<li><b>{second_media_type['Media Type']}</b> is the second most used media type, comprising <b>{(second_media_type['Count'] / total_media_types * 100):.1f}%</b>.</li>")
            if len(media_type_counts) > 0 and (media_type_counts.iloc[0]['Count'] / total_media_types) < 0.5:
                insights.append('<li>The media mix is relatively diverse, with no single media type overwhelmingly dominating.</li>')
            elif len(media_type_counts) > 0:
                insights.append('<li>The media mix is dominated by a few key types, with a high concentration in the leading category.</li>')
            st.markdown("<ul>" + "".join(insights) + "</ul>", unsafe_allow_html=True)


            # --- Top 5 Locations (Bar Chart) ---
            st.header("7. Top 5 Locations (by Engagements)")
            engagements_by_location = df.groupby('Location')['Engagements'].sum().reset_index()
            engagements_by_location = engagements_by_location.sort_values(by='Engagements', ascending=False).head(5)
            fig_locations = px.bar(
                engagements_by_location,
                x='Location',
                y='Engagements',
                title='Top 5 Locations by Engagements',
                color_discrete_sequence=['#d946ef'] # Purple-500
            )
            st.plotly_chart(fig_locations, use_container_width=True)

            st.subheader("Top 3 Insights:")
            insights = []
            if len(engagements_by_location) > 0:
                highest_engagement_location = engagements_by_location.iloc[0]
                insights.append(f"<li><b>{highest_engagement_location['Location']}</b> is the highest-engagement location, with <b>{highest_engagement_location['Engagements']:,}</b> total engagements.</li>")
            if len(engagements_by_location) > 1:
                second_location = engagements_by_location.iloc[1]
                insights.append(f"<li>The top two locations, <b>{highest_engagement_location['Location']}</b> and <b>{second_location['Location']}</b>, together contribute a significant portion of overall engagements.</li>")
            if len(engagements_by_location) > 2:
                insights.append(f"<li>The top 5 locations highlight key geographic areas for media engagement, suggesting targeted outreach opportunities.</li>")
            st.markdown("<ul>" + "".join(insights) + "</ul>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred during processing: {e}")
        st.info("Please ensure your CSV file has the correct columns and data format.")
