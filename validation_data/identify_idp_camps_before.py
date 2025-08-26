# This script takes the input CSV file with IDP Camp data between 1 June, 2017 and 26 August, 2017
# and converts it into a locations CSV file for FabFlee. The input CSV has detailed camp data on admin4 
# (location) level. This script outputs a CSV file with admin1 & admin3 level data.

import os
import pandas as pd 

# Load the CSV file
filepath = os.getcwd()
input_filename = "/IDPCamp_Myanmar_detailed_before_270817.csv"
input_filepath = filepath + input_filename
df = pd.read_csv(input_filepath)

# Format date to datetime
# df['date'] = pd.to_datetime(df['date'], dayfirst=True)
# print(df.head())

# Convert idp column to numeric, coercing errors
df['idp'] = pd.to_numeric(df['idp'])
# print(df.head())

# Group by state, township, and date, and sum idp
df_grouped = (
    df.groupby(['state', 'township', 'date'], as_index=False)
      .agg({
          'idp': 'sum',
          'latitude_township': 'first',
          'longitude_township': 'first',
          'population': 'first'
      })
)
print(df_grouped.head())

# Rename columns for clarity
df_grouped = df_grouped.rename(columns={'idp': 'idp_total', 
                                        'latitude_township': 'latitude', 
                                        'longitude_township': 'longitude',
                                        'state': 'region',
                                        'township': '#name'
                                        })

# Add a 'country' column with a constant value
df_grouped['country'] = 'Myanmar'

# Re-order columns
df_grouped = df_grouped[['#name', 'region', 'country', 'latitude', 
                         'longitude', 'population', 'idp_total', 'date']]

# Save the grouped data to a new CSV file
output_filename = "/IDPCamp_admin3_before_event.csv"
output_filepath = filepath + output_filename
df_grouped.to_csv(output_filepath, index=False)
print("Grouped data saved to:", output_filepath)