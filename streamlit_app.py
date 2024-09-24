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
	
	# Get unique mac_id values
	unique_mac_ids = df["mac_id"].unique().tolist()
	mac_id_options = unique_mac_ids
	
	# Add a singleselect widget with a default selection of all mac_ids
	filtered_mac_id = st.selectbox(
	    "Select mac_id",
	    options=mac_id_options,
	    index=0,  # Default selected option
	    help="You can select a specific mac_id."
	)

	
	# Filter the dataframe based on the widget input and reshape it.
	df_filtered = df[df["mac_id"] == filtered_mac_id]

	
	
		
	# Convert the 'timestamp' column to datetime if it's not already
	df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='mixed')

	latest_entry = df.loc[[df_filtered['timestamp'].idxmax()]]

	# Display the data as a table using `st.dataframe`.
	st.dataframe(
	latest_entry,
	use_container_width=True,
	# column_config={"mac_id": st.column_config.TextColumn("mac_id")},
	)

	dt = pd.to_datetime(latest_entry["timestamp"].iloc[0])
	
	st.write(f"Latest : ",dt.strftime('%Y-%m-%d %H:%M:%S'))

	def get_indicator(value):
	    if value.strip().lower() == "t":  # Ensure that the string is stripped of whitespace before comparison
	        # Return an HTML image tag for the true value
	        return '<img src="image.png" alt="True" width="20" height="20">'
	    else:
	        # Return an HTML image tag for the false value
	        return '<img src="image_off.png" alt="False" width="20" height="20">'

	    
	# Layout
	col1, col2 = st.columns(2)
	
	with col1:
	    # Display Battery values in a text area (voltage and charge)
	    st.html(f"<div>Battery Status: {get_indicator(latest_entry['battery_status'].iloc[0]) }</div>")
	    battery_info = '\n'.join([f"Voltage: {v} \n Discharge Charge: {c}" for v, c in zip(latest_entry['battery_voltage'], latest_entry['battery_discharge_current'])])
	    st.text_area("Battery Info", battery_info, height=100, disabled=True)
	    
	    # Display Mains values in a text area (voltage and status)
	    st.write("Mains" + get_indicator(latest_entry['power_status'].iloc[0]), unsafe_allow_html=True)
	    mains_info = '\n'.join([f"Voltage: {v} \n Frequency: {f} \n Charging Current: {c}" for v, f, c in zip(latest_entry['mains_voltage'], latest_entry['mains_frequency'],latest_entry['mains_charging_current'])])
	    st.text_area("Mains Info", mains_info, height=100, disabled=True)
	
	with col2:
	    # Display Inverter values in a text area (voltage and charge)
	    st.write("Inverter" + get_indicator(latest_entry['inverter_status'].iloc[0]), unsafe_allow_html=True)
	    inverter_info = '\n'.join([f"Voltage: {v} \n Frequency: {c} \n Load Current: {l}" for v, c, l in zip(latest_entry['inverter_voltage'], latest_entry['inverter_frequency'],latest_entry["load_current_on_inverter"])])
	    st.text_area("Inverter Info", inverter_info, height=100, disabled=True)
	    
	    # Display Solar values in a text area (power and charge)
	    st.write("Solar" + get_indicator(latest_entry['solar_status'].iloc[0]), unsafe_allow_html=True)
	    solar_info = '\n'.join([f"Voltage: {v} \n Power Generation: {p} \n Charging Current: {c}" for v, p, c in zip(latest_entry['solar_voltage'], latest_entry['solar_charging_current'], latest_entry['solar_power_generation'])])
	    st.text_area("Solar Info", solar_info, height=100, disabled=True)
