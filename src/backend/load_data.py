import pandas as pd
import os
import glob


# ============================================================
# DATASET DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset"
)


# ============================================================
# LOAD ALL BUILDING DATASETS
# ============================================================

def load_data():

    dataframes = []

    # Find all CSV files in dataset folder
    csv_files = glob.glob(
        os.path.join(
            DATASET_DIR,
            "*.csv"
        )
    )

    for file_path in csv_files:

        filename = os.path.basename(
            file_path
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Do NOT load the combined file here.
        # Otherwise records would be duplicated.
        # ----------------------------------------------------

        if filename == "combined_sensor_data.csv":
            continue

        try:

            df = pd.read_csv(
                file_path
            )

            if df.empty:
                continue

            # ------------------------------------------------
            # Make sure Building_Type exists
            # ------------------------------------------------

            if "Building_Type" not in df.columns:

                building_name = filename.replace(
                    "_building_sensor_data.csv",
                    ""
                )

                df["Building_Type"] = (
                    building_name.title()
                )

            dataframes.append(
                df
            )

        except Exception as error:

            print(
                f"Could not load {filename}: {error}"
            )


    # ========================================================
    # NO DATA FOUND
    # ========================================================

    if not dataframes:

        print(
            "No building datasets found."
        )

        return pd.DataFrame()


    # ========================================================
    # COMBINE ALL DATASETS
    # ========================================================

    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )


    # ========================================================
    # REMOVE DUPLICATE RECORDS
    # ========================================================

    combined_df = combined_df.drop_duplicates(
        ignore_index=True
    )


    # ========================================================
    # RETURN DATA
    # ========================================================

    return combined_df


# ============================================================
# TEST WHEN RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    df = load_data()

    print(
        "Total records:",
        len(df)
    )

    print(
        "Total columns:",
        len(df.columns)
    )

    if not df.empty:

        print(
            "\nBuilding Distribution:"
        )

        print(
            df["Building_Type"].value_counts()
        )

        print(
            "\nDataset Columns:"
        )

        print(
            list(df.columns)
        )

        print(
            "\nFirst 5 Records:"
        )

        print(
            df.head()
        )