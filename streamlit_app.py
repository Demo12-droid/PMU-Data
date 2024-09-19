# import altair as alt
import pandas as pd
import streamlit as st
import boto3
from io import StringIO
import plotly.express as px

def authenticate(username, password):
	if st.secrets["username"] == username and st.secrets["password"] == password:
		return True
	return False
	
def logout():
	st.session_state.logged_in = False
	
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

if 'logged_in' not in st.session_state:
	st.session_state.logged_in = False

aws_access_key_id = st.secrets["aws_access_key_id"]
aws_secret_access_key = st.secrets["aws_secret_access_key"]
bucket_name = st.secrets["bucket_name"]
folder_name = st.secrets["folder_name"]
username = st.secrets["username"]
password = st.secrets["password"]


st.set_page_config(page_title="HYD PMU Data")

# UI for login
if not st.session_state.logged_in:
	st.title("Login")
	username = st.text_input("Username")
	password = st.text_input("Password", type="password")
	if st.button("Login"):
		if authenticate(username, password):
			st.session_state.logged_in = True
			st.rerun()
		else:
			st.error("Invalid username or password")


if st.session_state.logged_in:          

	# Show the page title and description.
	st.title("Hyderabad PMU Data")
	st.sidebar.title("Options")
	if st.sidebar.button("Logout"):
	    logout()
	    st.rerun()
	
	df = get_latest_file_from_s3(bucket_name, folder_name, aws_access_key_id , aws_secret_access_key)
	
	# Display the data as a table using `st.dataframe`.
	st.dataframe(
	df,
	use_container_width=True,
	column_config={"mac_id": st.column_config.TextColumn("mac_id")},
	)
	
	# Convert the 'timestamp' column to datetime if it's not already
	df['timestamp'] = pd.to_datetime(df['timestamp'])
	
	# Plot for timestamp vs battery_voltage
	fig1 = px.scatter(df, x='timestamp', y='battery_voltage', hover_data=['mac_id'],
		      title='Timestamp vs Battery Voltage',
		      labels={'timestamp': 'Timestamp', 'battery_voltage': 'Battery Voltage (V)'})
	
	# Plot for timestamp vs inverter_voltage
	fig2 = px.scatter(df, x='timestamp', y='inverter_voltage', hover_data=['mac_id'],
		      title='Timestamp vs Inverter Voltage',
		      labels={'timestamp': 'Timestamp', 'inverter_voltage': 'Inverter Voltage (V)'})
	
	# Plot for timestamp vs solar_voltage
	fig3 = px.scatter(df, x='timestamp', y='solar_voltage', hover_data=['mac_id'],
		      title='Timestamp vs Solar Voltage',
		      labels={'timestamp': 'Timestamp', 'solar_voltage': 'Solar Voltage (V)'})
	
	# Display the figures
	st.plotly_chart(fig1, use_container_width=True)
	st.plotly_chart(fig2, use_container_width=True)
	st.plotly_chart(fig3, use_container_width=True)
