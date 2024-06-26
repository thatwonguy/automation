# import library
from typing import Union
from pydantic import BaseModel
import streamlit as st
import pymongo
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import toml
import pandas as pd
import pytz
from prefect import flow, task


# Initialize connection.
# Uses st.cache_resource to only run once.
def init_connection():
    uri = st.secrets['mongo']['uri']
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    return client

# Get the current date and time, this will be the data that we will be working with and can be replaced with any other data
def date():
    # get current date
    current_datetime = datetime.now()
    # format to provide standard time %I and AM or PM %p
    formatted_datetime = current_datetime.strftime("%m-%d-%Y %I:%M:%S.%f %p")
    print(formatted_datetime)
    return formatted_datetime

# Insert data into MongoDB
def insert_date(time, collection):
    data = {"timestamp": time}
    collection.insert_one(data)

# obtain the udpated database information for end-user viewing
# Uses st.cache_data to only rerun when the query changes
def get_data(collection):
    # Retrieve items from MongoDB collection
    items = collection.find()
    items = list(items)  # Convert cursor to list for compatibility with st.cache_data

    # Create DataFrame from items
    df = pd.DataFrame(items)

    # Convert 'timestamp' column to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Localize datetime to Eastern Standard Time (EST)
    eastern = pytz.timezone('US/Eastern')
    df['timestamp'] = df['timestamp'].dt.tz_localize(pytz.utc).dt.tz_convert(eastern)

    # Sort DataFrame by 'timestamp' column in descending order
    df = df.sort_values(by='timestamp', ascending=False)

    # Convert 'timestamp' column back to string with original format
    df['timestamp'] = df['timestamp'].dt.strftime('%m-%d-%Y %I:%M:%S.%f %p')

    del df['_id']

    # print results for user at end-location
    st.write("""This table is fully automated. 
                The timestamp (localized to US/Eastern time) data is being updated everytime the code is run.
                The data is stored and updated in a database.
                The latest update timestamp on the database is presented to the end user here.
                Prefect Automation and Orchestration is used to carry out the automation using cron scheduling, and 
                demonstrates that a no-touch solution is possible.""")

    # shows the df without the index column
    st.dataframe(df, width=1000, height=1000)

# entrypoint Prefect flow
@flow(log_prints=True)
def automate():
    # Initialize connection
    client = init_connection()
    
    # Global variables, specify db and collection to get and post to
    db = client["automation"]
    collection = db["date"]

    # Get new data
    formatted_datetime = date()

    # Insert data into database
    insert_date(formatted_datetime, collection)

    # Get data from database
    get_data(collection)

if __name__ == "__main__":
    automate()
