# Generate a cleaned parks layer to be used in parks analysis

# Load CPAD nightly holdings layer
# Include CFF 1
# Exclude in this order
	# No Access, Restricted, Unknown
	# Special Use: Golf Course, Cemetery, HOA, JUA
	# Planned Parks
# Check that there are no parks with CFF 2

import geopandas as gdp
import pandas as pd
import os

# Declare filepaths here. Filename variables need to include the proper extension (".shp" or ".csv")
in_parks = r"C:\Users\Gorgonio.GREENINFO\Desktop\cpad_nightly_holdings\CPAD_nightly_Holdings\CPAD_Nightly_Holdings.shp" # park file to process
out_folder = r"C:\Users\Gorgonio.GREENINFO\Desktop\test" # folder for outputs
out_parks_filename = "parks_final.shp" # filename of the output parks file
out_removed_parks_filename = "removed_final.shp" # filename of the removed parks
out_stats_filename = "stats_final.csv" # filename of the stats log


def exclude_parks(park_file):
	"""Iterate through park file and exclude records. Generate a shp and stats for excluded holdings."""

	print("Start!")

	# Set up geodataframes and tables for tracking removals
	removed = gdp.GeoDataFrame()
	stats_columns = ['ROUND', 'REASON_REMOVED', 'COUNT']
	stats = pd.DataFrame(columns=stats_columns)

	# Exclude holdings where access is no public, restricted, or unknown.
	print("Excluding access")
	data = gdp.read_file(park_file)
	data_access_query = data.query('ACCESS_TYP == "No Public Access"| ACCESS_TYP == "Restricted Access"| ACCESS_TYP == "Unknown Access"')
	data_access_query.loc[:,'REASON'] = "Access"
	data_access_query.loc[:,'ACTION'] = "None"
	removed = removed.append(data_access_query, ignore_index=True)

	print("Calculating stats for access query")
	if stats['ROUND'].empty:
		round_num = 1
	else:
		round_num = stats['ROUND'].max() + 1

	queries = ['ACCESS_TYP == "No Public Access"', 'ACCESS_TYP == "Restricted Access"', 'ACCESS_TYP == "Unknown Access"']
	for query in queries:
		data_access_stats = data_access_query.query(query)
		count = data_access_stats.shape[0]
		reason = data_access_stats.iloc[0]['ACCESS_TYP']
		stats = stats.append({'ROUND':round_num,'REASON_REMOVED': reason, 'COUNT': count}, ignore_index=True)

	print("Removing parks by access")
	data = data.drop(data_access_query.index)

	# Exclude holdings where special use is golf course, cemetery, JUA, or HOA
	print("Excluding special use")
	data_spec_use_query = data.query('SPEC_USE == "Golf Course"| SPEC_USE == "Cemetery"| SPEC_USE == "HOA"|SPEC_USE == "School JUA"')
	data_spec_use_query.loc[:, 'REASON'] = "Special Use"
	data_spec_use_query.loc[:, 'ACTION'] = "None"
	data_spec_use_query.loc[(data_spec_use_query['SPEC_USE'] == "HOA") | (data_spec_use_query['SPEC_USE'] == "School JUA"), 'ACTION'] = "CPAD review needed. Access should be restricted."
	removed = removed.append(data_spec_use_query, ignore_index=True, sort=False)

	print("Calculating stats for special use query")
	if stats['ROUND'].empty:
		round_num = 1
	else:
		round_num = stats['ROUND'].max() + 1
	count = data_spec_use_query.shape[0]
	reason = "Special Use"
	stats = stats.append({'ROUND':round_num,'REASON_REMOVED': reason, 'COUNT': count}, ignore_index=True, sort=False)
 
 	print("Removing parks by special use")
	data = data.drop(data_spec_use_query.index)

	# Exclude planned parks
	data_pp_query= data.query('SPEC_USE == "Planned Park"')
	data_pp_query.loc[:, 'REASON'] = "Planned Park"
	data_pp_query.loc[:, 'ACTION'] = "None"
	removed = removed.append(data_pp_query, ignore_index=True, sort=False)

	print("Calculating stats for planned park query")
	if stats['ROUND'].empty:
	    round_num = 1
	else:
	    round_num = stats['ROUND'].max() + 1
	count = data_pp_query.shape[0]
	reason = "Planned Park"
	stats = stats.append({'ROUND':round_num,'REASON_REMOVED': reason, 'COUNT': count}, ignore_index=True, sort=False)

	print("Removing parks by planned parks")
	data = data.drop(data_pp_query.index)

	### 
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