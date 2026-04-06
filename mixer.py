import pandas as pd

def merge_two_csv_files(file1, file2, output_file):
    # Read the CSV files into DataFrames
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    
    # Concatenate the DataFrames
    combined_df = pd.concat([df1, df2], ignore_index=True)
    
    # Save the combined DataFrame to a new CSV file
    combined_df.to_csv(output_file, index=False)
    print(f"Combined CSV file saved as: {output_file}")

# Prompt the user for file paths
file1 = input("Enter the path to the first CSV file: ")
file2 = input("Enter the path to the second CSV file: ")

# Set the output file name to 'train.csv'
output_file = 'train.csv'

# Call the function with user-provided file paths and fixed output file name
merge_two_csv_files(file1, file2, output_file)
