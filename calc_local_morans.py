import geopandas as gpd
from libpysal.weights import Queen, Rook
from esda.moran import Moran_Local
import pandas as pd
import sys
import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.lines as mlines

def calc_local_morans(input_shapefile, field_name, weight_type='queen'):
    """
    Parameters:
    - input_shapefile (str): Path to the input shapefile.
    - field_name (str): Name of the field/column to calculate Local Moran's I.
    - weight_type (str): Type of spatial weights ('queen' or 'rook').

    Returns:
    geopandas.GeoDataFrame: Original dataframe with additional LISA results (Local Moran's I, p-value, and cluster category).
    """
    # Load the shapefile
    try:
        shapefile_data = gpd.read_file(input_shapefile)
    except Exception as e:
        print(f"Failed to read shapefile: {e}")
        return None

    # Check if the field exists in the shapefile
    if field_name not in shapefile_data.columns:
        print(f"Field '{field_name}' not found in the shapefile attributes.")
        return None

    # Create a spatial weights matrix
    if weight_type.lower() == 'queen':
        weights = Queen.from_dataframe(shapefile_data, use_index=True)
    elif weight_type.lower() == 'rook':
        weights = Rook.from_dataframe(shapefile_data, use_index=True)
    else:
        print("Invalid weight type specified. Use 'queen' or 'rook'.")
        return None

    # Handle missing values
    shapefile_data[field_name] = shapefile_data[field_name].fillna(shapefile_data[field_name].mean())

    # Calculate Local Moran's I
    moran_loc = Moran_Local(shapefile_data[field_name], weights)

    # Add LISA results to the dataframe
    shapefile_data['LocMoranI'] = moran_loc.Is
    shapefile_data['p_value'] = moran_loc.p_sim
    shapefile_data['Z_score'] = moran_loc.z_sim

    #This segment classifies each observation based on the type of spatial association and its significance.
    #Define the cluster categories based on standard deviation of the z-scores
    #[moran_loc.q] refers to the quadrant categories of local spatial autocorrelation.

    sig = 1 * (moran_loc.p_sim < 0.05)          #Create a binary mask for significant results: 1-> sig ; 0->non-significant
    hotspot = 1 * (moran_loc.q == 1) * sig      #(High-High):1
    coldspot = 2 * (moran_loc.q == 3) * sig     #(Low-Low):2
    outlier1 = 3 * (moran_loc.q == 2) * sig     #(Low-High):3
    outlier2 = 4 * (moran_loc.q == 4) * sig      ##(High-Low):4

    categories = hotspot + coldspot + outlier1 + outlier2 #(holds 0,1,2,3, or 4)
    labels = ['Non-sig', 'Hotspot (High-High)', 'Coldspot(Low-Low)', 'outlier(Low-High)', 'outlier(High-Low)']

    # Map cluster categories to labels
    shapefile_data['LISA_Clust'] = pd.Categorical.from_codes(categories, labels, ordered=True)

    # Convert categorical labels to string to save in shapefile
    shapefile_data['LISA_Clust'] = shapefile_data['LISA_Clust'].astype(str)

   # Select only the desired columns: field_name and calculated fields
    result_data = shapefile_data[[field_name, 'LocMoranI', 'p_value', 'Z_score', 'LISA_Clust', 'geometry']]

    # Return the dataframe with added LISA results
    return result_data

########################################
def plot_lisa(data, field_name):
    """
    Plot the LISA categories with custom colors.
    Parameters:
    - data (GeoDataFrame): The GeoDataFrame with LISA results.
    - field_name (str): The field/column used for Moran's I calculation.
    """
    # Define custom colors for each category
    custom_colors = {
        'Non-sig': 'lightgrey',
        'Hotspot (High-High)': 'red',
        'Coldspot(Low-Low)': 'blue',
        'outlier(Low-High)': 'lightblue',
        'outlier(High-Low)': 'lightcoral'
    }

    # Create a color map based on LISA_Clust values
    color_map = data['LISA_Clust'].map(custom_colors)
 
     # Ensure all values in color_map are valid colors
    color_map = color_map.fillna('lightgrey')  # Default color for any missing category

    # Plot the data with custom colors
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))  # Increase the figsize for better visualization
    data.boundary.plot(ax=ax, linewidth=.1, color='k')
    data.assign(color=color_map).plot(ax=ax, color=color_map, edgecolor='grey', linewidth=0.5)

    # Set the extent of the plot to the extent of the data
    ax.set_xlim(data.total_bounds[0], data.total_bounds[2])
    ax.set_ylim(data.total_bounds[1], data.total_bounds[3])

    # Add legend
    legend_items = []
    for category, color in custom_colors.items():
        legend_item = mlines.Line2D([0], [0], color=color, lw=8, label=category)  # Increase `lw` for thicker lines
        legend_items.append(legend_item)
    
    # Add the legend with thicker items
    ax.legend(handles=legend_items, title='LISA Clusters', loc='lower left', bbox_to_anchor=(0.1, 0.4))
    
    ax.set_title(f'LISA Cluster Map for {field_name}', fontsize=15)
    ax.set_axis_off()
    plt.tight_layout()  # Adjust layout to avoid clipping
    plt.show()
########################################

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(json.dumps({"error": "Incorrect number of arguments provided."}))
        sys.exit(1)

    input_shapefile = sys.argv[1]
    field_name = sys.argv[2]
    weight_type = sys.argv[3]
    results = calc_local_morans(input_shapefile, field_name, weight_type)

    if results is not None:
        # Save results as GeoJSON
        geojson_output = "local_morans_results.geojson"
        results.to_file(geojson_output, driver="GeoJSON")
        print(f"Results saved as GeoJSON to {geojson_output}")

        
        # Save results as CSV (without geometry)
        csv_output = "local_morans_results.csv"
        results.drop(columns='geometry').to_csv(csv_output, index=False)
        print(f"Results saved as CSV to {csv_output}")

        plot_lisa(results, field_name)
    else:
        print(json.dumps({"error": "Calculation failed"}))
#################################################################