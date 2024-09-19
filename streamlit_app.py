# import altair as alt
import pandas as pd
import streamlit as st
import boto3
from io import StringIO

def get_latest_file_from_s3(bucket_name, folder_name, aws_access_key_id , aws_secret_access_key):
    try:
        # Create an S3 client using access keys
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

        # List the objects in the specified folder
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)

        # Check if the folder contains any files
        if 'Contents' in response:
            # Find the most recently uploaded file
            latest_object = max(response['Contents'], key=lambda obj: obj['LastModified'])
            latest_key = latest_object['Key']
            print(f"Latest file in the folder '{folder_name}': {latest_key}")

            # Get the object from S3
            csv_obj = s3_client.get_object(Bucket=bucket_name, Key=latest_key)
            body = csv_obj['Body'].read().decode('utf-8')

            # Use StringIO to convert the string data to a file-like object for pandas
            csv_data = StringIO(body)

            # Read the CSV into a DataFrame
            df = pd.read_csv(csv_data,index_col=False)

            return df
        else:
            print(f"No files found in folder '{folder_name}'.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Show the page title and description.
st.set_page_config(page_title="HYD PMU Data")
st.title("Hyderabad PMU Data")

aws_access_key_id = st.secrets["aws_access_key_id"]
aws_secret_access_key = st.secrets["aws_secret_access_key"]
bucket_name = st.secrets["bucket_name"]
folder_name = st.secrets["folder_name"]
username = st.secrets["username"]
password = st.secrets["password"]


df = get_latest_file_from_s3(bucket_name, folder_name, aws_access_key_id , aws_secret_access_key)

# Display the data as a table using `st.dataframe`.
st.dataframe(
    df,
    use_container_width=True,
    # column_config={"year": st.column_config.TextColumn("Year")},
)

# Display the data as an Altair chart using `st.altair_chart`.
df_chart = pd.melt(
    df_reshaped.reset_index(), id_vars="Timestamp", var_name="battery_volatge", value_name="battery_volatge"
)
chart = (
    alt.Chart(df_chart)
    .mark_line()
    .encode(
        x=alt.X("timestamp:N", title="Timestamp"),
        y=alt.Y("battery_voltage:Q", title="Battery Voltage"),
        color="genre:N",
    )
    .properties(height=320)
)
st.altair_chart(chart, use_container_width=True)
