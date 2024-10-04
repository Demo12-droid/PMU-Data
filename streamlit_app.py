import pandas as pd
import streamlit as st
import boto3
from io import StringIO

def authenticate(username, password):
    if st.secrets["username"] == username and st.secrets["password"] == password:
        return True
    return False

def logout():
    st.session_state.logged_in = False

def get_latest_file_from_s3(bucket_name, folder_name, aws_access_key_id, aws_secret_access_key):
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
            df = pd.read_csv(csv_data, index_col=False)

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
    st.title("Hyderabad PMU Data")
    st.sidebar.title("Options")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

    df = get_latest_file_from_s3(bucket_name, folder_name, aws_access_key_id, aws_secret_access_key)

    st.dataframe(df, use_container_width=True)
    # Get unique mac_id values
    unique_mac_ids = df["mac_id"].unique().tolist()
    
    # Add a single-select widget with a default selection of the first mac_id
    filtered_mac_id = st.selectbox("Select mac_id", options=unique_mac_ids, index=0, help="You can select a specific mac_id.")

    # Filter the dataframe based on the selected mac_id
    df_filtered = df[df["mac_id"] == filtered_mac_id]

    # Convert the 'timestamp' column to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    latest_entry = df_filtered.loc[df_filtered['timestamp'].idxmax()]

    # Display the latest entry as a table
    # st.dataframe(latest_entry, use_container_width=True)

    dt = pd.to_datetime(latest_entry["timestamp"])
    st.write(f"Latest: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

    def get_indicator(value):
        return "image.png" if value.strip().lower() == "t" else "image_off.png"

    # Layout for displaying battery and mains information
    col1, col2 = st.columns(2)

    # Battery Status
    with col1:
        battery_col1, battery_col2 = st.columns([0.5,0.5])
        with battery_col1:
            st.markdown("**Battery Status:**")
        with battery_col2:
            st.image(get_indicator(latest_entry['battery_status']), width=40)  # Display the image

        battery_info = f"Voltage: {latest_entry['battery_voltage']} V\nDischarge Charge: {latest_entry['battery_discharge_current']} A"
        st.text_area("Battery Info", battery_info, height=100, disabled=True)

        # Mains Status
        mains_col1, mains_col2 = st.columns([0.5,0.5])
        with mains_col1:
            st.markdown("**Mains Status:**")
        with mains_col2:
            st.image(get_indicator(latest_entry['power_status']), width=40)  # Display the image

        mains_info = f"Voltage: {latest_entry['mains_voltage']} V\nFrequency: {latest_entry['mains_frequency']} Hz\nCharging Current: {latest_entry['mains_charging_current']} A"
        st.text_area("Mains Info", mains_info, height=100, disabled=True)

    # Inverter and Solar Info
    with col2:
        # Inverter Info
        inverter_col1, inverter_col2 = st.columns([0.5,0.5])
        with inverter_col1:
            st.markdown("**Inverter Status:**")
        with inverter_col2:
            st.image(get_indicator(latest_entry['inverter_status']), width=40)  # Display the image

        inverter_info = f"Voltage: {latest_entry['inverter_voltage']} V\nFrequency: {latest_entry['inverter_frequency']} Hz\nLoad Current: {latest_entry['load_current_on_inverter']} A"
        st.text_area("Inverter Info", inverter_info, height=100, disabled=True)

        # Solar Info
        solar_col1, solar_col2 = st.columns([0.5,0.5])
        with solar_col1:
            st.markdown("**Solar Status:**")
        with solar_col2:
            st.image(get_indicator(latest_entry['solar_status']), width=40)  # Display the image

        solar_info = f"Voltage: {latest_entry['solar_voltage']} V\nPower Generation: {latest_entry['solar_power_generation']} W\nCharging Current: {latest_entry['solar_charging_current']} A"
        st.text_area("Solar Info", solar_info, height=100, disabled=True)
