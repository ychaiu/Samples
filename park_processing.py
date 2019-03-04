# Generate a cleaned parks layer to be used in parks analysis

# Load CPAD nightly holdings layer
# Include CFF 1
# Exclude in this order
	# No Access Access
	# Restricted Access
	# Unknown Access
	# Special Use: Golf Course, Cemetery, HOA, JUA
	# Planned Parks
# Check that there are no parks with CFF 2

import geopandas as gdp
import pandas as pd
import numpy as np
import os

# Declare filepaths here. Filename variables need to include the proper extension (".shp" or ".csv")

# park file to process
in_parks = r"C:\Users\Gorgonio.GREENINFO\Desktop\cpad_nightly_holdings\CPAD_nightly_Holdings\CPAD_Nightly_Holdings.shp" 

# folder for outputs
out_folder = r"C:\Users\Gorgonio.GREENINFO\Desktop\test" 

# filename of the output parks file
out_parks_filename = "parks_final.shp" 

# filename of the removed parks
out_removed_parks_filename = "removed_final.shp" 

# filename of the stats log
out_stats_filename = "stats_final.csv" 


exclude_queries = [
	['ACCESS_TYP == "No Public Access"', "No Public Access"],
	['ACCESS_TYP == "Restricted Access"', "Restricted Access"],
	['ACCESS_TYP == "Unknown Access"', "Unknown Access"],
	['SPEC_USE == "Golf Course"| SPEC_USE == "Cemetery"| SPEC_USE == "HOA"|SPEC_USE == "School JUA"', "Special Use"],
	['SPEC_USE == "Planned Park"', "Planned Park"]
]

def query_add_fields(dataframe, query, reason_value, action_value):
	"""Query input dataframe, add reason and action fields and populate."""

	df_query = dataframe.query(query)
	df_query.loc[:, 'REASON'] = reason_value
	df_query.loc[:, 'ACTION'] = action_value
	return df_query

def calculate_stats(stats_table, dataframe, reason_value):
	"""Calculate stats for each round of query."""

	if stats_table['ROUND'].empty:
		round_num = 1
	else:
		round_num = stats_table['ROUND'].max() + 1

	count = dataframe.shape[0]
	stats_table = stats_table.append({'ROUND':round_num,'REASON_REMOVED': reason_value, 'COUNT': count}, ignore_index=True, sort=False)

	print(stats_table)
	return stats_table

def exclude_parks(park_file):
	"""Iterate through park file and exclude records. Generate a shp and stats for excluded holdings."""

	print("Start!")

	# Set up geodataframes and tables for tracking removals
	removed = gdp.GeoDataFrame()
	stats_columns = ['ROUND', 'REASON_REMOVED', 'COUNT']
	stats = pd.DataFrame(columns=stats_columns)

	# read park_file input as a geopandas dataframe
	data = gdp.read_file(park_file)

	for query in exclude_queries:
		data_queried = data.query(query[0])
		data_queried = query_add_fields(data_queried, query[0], query[1], "None")
		removed = removed.append(data_queried, ignore_index = True)
		stats = calculate_stats(stats, data_queried, query[1])
		print("Finished excluding {}".format(query[1]))
		data = data.drop(data_queried.index)

	out_parks_path = os.path.join(out_folder, out_parks_filename)
	out_removed_parks_path = os.path.join(out_folder, out_removed_parks_filename)
	out_stats_path = os.path.join(out_folder, out_stats_filename)

	print("Exporting files")
	data.to_file(out_parks_path)
	removed = removed[['UNIT_NAME', 'HOLDING_ID', 'ACCESS_TYP', 'COUNTY','CFF', 'SPEC_USE', 'REASON', 'ACTION', 'geometry']]
	removed.to_file(out_removed_parks_path)
	stats.to_csv(out_stats_path)

	print("Finished!")

if __name__ == '__main__':
	
	exclude_parks(in_parks)
