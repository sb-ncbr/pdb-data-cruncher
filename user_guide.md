# User guide

TODO real table of contents

[toc]

# Local development

TODO

# Deployment

TODO

# Configuration

The default configuration is sufficient for the application to run.

Configuration of the program is done by setting environmental variables. See [Local development](#local development) or [Deployment](#deployment) sections to see how to set those in each case.

Multiple things can be configured via environmental variables. This guide will only mention those that will most likely need setting or be otherwise useful. To see all the possible variables that can be set, check `src/config.py`. Config file is the source of truth for available environmental variables and their names.

## App flow control

These options will be useful for rerunning only certain parts of the app after partial failures.

Note that at most one of `RUN_ACTION_NAME_ONLY` can be present during single run.

* ` RUN_DATA_DOWNLOAD_ONLY` Default: ` False`.

  When set to True, only the download phase will be run. This may be useful for running selective download if mmcif rsync partially failed.

* `OVERRIDE_IDS_TO_DOWNLOAD_PATH` Default: `None`.

  When path to json file is given, rsync of mmcif archive files will not be run. Instead, the list of ids inside the json file will be used to determine which rest/vdb files to download and they will also be saved as the updated ids for future data extraction.

  Example content of the json file:

  ```json
  [
      "1dey",
      "7pin"
  ]
  ```

* `SKIP_DATA_DOWNLOAD ` Default: `False `.

  When set to True, download phase will be skipped, but all other phases will be run as usual. See TODO for more information.

* ` RUN_DATA_EXTRACTION_ONLY` Default: `False `.

  When set to True, only data extraction (the process of converting source .cif .xml .json files to crunched.csv) is run. See TODO for more information.

* ` FORCE_COMPLETE_DATA_EXTRACTION` Default: ` False`.

  In the default mode, the data extraction only parses files for those structure ids determined by what was updated during download phase. However, if it happened that some information has been lost and it cannot be determined which ids should have been updated but are not, this option is the last resort.

  When set to True, *all* structures will be parsed again, and crunched.csv will be calculated anew. Beware, this is significantly time consuming. In ideal case, this should not be needed.

* ` IDS_TO_REMOVE_AND_UPDATE_OVERRIDE_PATH` Default: `None `.

  If path to json file is given, data extraction will get the list of which ids to update from this file instead of the download result json.

  Example content of such json:

  ```json
  {
  	"structuresToUpdate": ["1dey", "7pin"],
  	"structuresToDelete": [],
  	"ligandsToUpdate": [],
  	"ligandsToDelete": []
  }
  ```

* ` RUN_ZIPPING_FILES_ONLY` Default: `False `.

  If set to True, only data archiving phase is run (this takes the cifs, xmls and json from dataset and stores them into their respective .7z archive).

* ` RUN_DATA_TRANSFORMATION_ONLY` Default: `False `.

  If set to True, only data transformation phase is run. (The phase consists of taking crunched.csv and creating all the other output files from it.)

* ` CRUNCHED_CSV_NAME_FOR_DATA_TRANSFORMATION` Default: ` ""`.

  If set, this crunched csv will be used as a base for data transformation calculations. If not set, `YYYYMMDD_crunched.csv` located in output files folder is used.

* ` DATA_TRANSFORMATION_SKIP_PLOT_SETTINGS` Default: `True `.

  If set to True (default), the creation of default plot settings is skipped during data transformation. Creating default plot settings is time consuming operation that does not need to be run every time. If you wish to run it, set this environmental variable to False and run data transformation.

* `RUN_POST_TRANSFORMATION_ACTIONS_ONLY` Default: `False`.

  If set to True, only post transformations actions will be run.

## Data sources

- `DATASET_ROOT_PATH` Default: `./dataset`.

  Folder containing data to be used for creating output files. See TODO for detailed description of all it needs to contain for the app to work.

- `OUTPUT_ROOT_PATH` Default: `./output`.

  Folder containing the output data  - data needed by ValtrendsDB. See TODO for detailed descritpion of all it needs to contain, and what it creates.

- `LOGS_ROOT_PATH` Default: `./logs`.

  Folder where the logs from the run are stored, as well as the simple text lock if data extraction fails (to avoid accidental data download run after such event, which would lose information about what has changed).

- Most of the files and folders inside these three data sources containing input of some sort can have their names overridden. See `src/config.py` for the specific environment variable names if such action is needed.

## Tweaking the settings

- `LOGGING_DEBUG` Default: `False`. If set to true, more logs will be produced. Relevant mostly for debugging.

- `MAX_PROCESS_COUNT` Default: `8`. Data extraction can run in multiple processes, this sets the limit on how may it can spawn.

- `DEFAULT_PLOT_SETTINGS_MAX_BUCKET_COUNT` Default: `50`.

  When counting default plot settings, this value is used as the starting bucket count. If this bucket count does not fit the other requirements (at least n values in each bucket for each factor combination), bigger bucket size (thus less buckets) is tried.

  Beware, setting this value higher will make the calculation even slower (more possibilities to go through).

- `DEFAULT_PLOT_SETTINGS_MIN_BUCKET_COUNT`  Default: `50`.

  When counting default plot settings, this value determines how many values there need to be for each factor pair for a bucket to be valid.

  Beware, setting this value higher will make the calculation even slower and the resulting buckets even smaller. Setting it too high may result in graphs consisting of only a bucket or two.

- `DEFAULT_PLOT_SETTINGS_STD_OUTLIER_MULTIPLIER` Default: `2`.

  When counting default plot settings and its buckets, outlier values are not considered (if they were, buckets on the edges of the graph would always have too little values to be valid, resulting in the whole graph being one bucket as the only valid option).

  Outliers to ignore are determined as: `value < mean_value - THIS_MULTIPLIER * std` or `value > mean_value + THIS_MULTIPLIER * std`, where std represents standard deviation.

- `DEFAULT_PLOT_SETTINGS_ALLOWED_BUCKET_BASE_SIZES` Default: `[10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90]`.

  When constructing the buckets for default plot settings, emphasis is put on creating them in such a way that they are rounded numbers, easy to display. To achieve this, only bucket sizes that are number from this list times 10^n are considered.

  Beware, putting too many values into this list will increase the run time (as more possibilities need to be tried before finding a value that works).

- `FACTOR_HIERARCHY_MIN_INTERVAL_COUNT` Default: `100`.

  When updating slider size and bounds for factor hierarchy, the app attempts to cut the whole interval into intervals of nice size. This determines the minimal interval count.

- `FACTOR_HIERARCHY_IDEAL_INTERVAL_COUNT` Default: `200`.

  When updating slider size and bounds for factor hierarchy, the app attempts to cut the whole interval into intervals of nice size. This determines the ideal number of intervals (while determining the size, it will try to match it closest to this number, while respecting min/max values).

- `FACTOR_HIERARCHY_MAX_INTERVAL_COUNT` Default: `300`.

  When updating slider size and bounds for factor hierarchy, the app attempts to cut the whole interval into intervals of nice size. This determines the maximum interval count.

- `FACTOR_HIERARCHY_ALLOWED_SLIDER_BASE_SIZES` Default: `[10, 20, 25, 50]`

  When updating slider size and bounds for factor hierarchy, these are the only allowed "base" slider sizes. Slider steps will always be one of these numbers times 10^n. This ensures the number is nice for displaying and readability. The slider max and min values will be multiplications of the slider base.

## Other relevant

- `CURRENT_FORMATTED_DATE`. Default: Today in format `YYYYMMDD`. It may be useful to override it in rare cases. It controls which crunched.csv gets loaded during data transformation, and how output files are named.

# App flow and error recovery

This section serves as explanation of what each phase does, what files it needs to function, and what it creates.

As a general rule, any mentioned file/folder paths for source data represent the default paths, but may be configured (see [Configuration - Data Sources](##Data-sources)).

## Data download

The data download phase takes care of keeping up to date the source data, and storing the information about which structures/ligands to recalculate in next phase.

Data download is done as follows:

1. Assert no lock is present.

   Lock presence (existence of file `./logs/data_extraction_lock.txt`) indicates data extraction did not run fully and did not process the last download's ids to update list, so this is a safeguard against accidentally running download again and overwriting it.

2. Make sure required folders are present.

   Dataset folder itself needs to be present before the run, but all the folders for data to be downloaded will be created if they are missing. However, this will issue a warning - if the app is run for the first time over new storage, it can be ignored. But on subsequent download runs, this may indicate the path is configured incorrectly.

3. Synchronize PDB mmCIF files for structures via rsync.

   First, files in location `./dataset/gz_PDBe_mmCIF/` are synced to the rsync endpoint `rsync.rcsb.org::ftp_data/structures/divided/mmCIF/`. These files have `.cif.gz` extensions.

   The output of this operation is parsed to see which files were received or removed, and what are their PDB ids are.

   Based on the rsync log, received files are unzipped into plain `.cif` to folder `./dataset/PDBe_mmCIF/`. Those deleted are deleted from there as well. The list of ids that changed or were removed is saved for further processing.

   <u>*Alternative*</u> (for error recovery)

   If path to json with list of ids is passed via env variable `OVERRIDE_IDS_TO_DOWNLOAD_PATH`, rsync of PDB mmCIF files is not done. Instead, this json is loaded and ids inside will be used as ids that changed for next steps (both for downloading other http files and subsequent data extraction). 

4. Update ligand .cif files.

   This is done by downloading `components.cif` and `aa-variants-v1.cif` files from PDB, cutting them into individual ligand cifs, and comparing them to already saved cif files. If they differ, they are updated and the ids of those updated are saved for further processing. The same goes for those deleted (not present in either of big .cif files anymore).

5. Synchronize validation report .xml files via rsync.

   First, files in location `./dataset/gz_ValRep_XML` are synced to the rsync endpoint `rsync.rcsb.org::ftp/validation_reports/ `(filtered so only the xml files are synced). These files have `.xml.gz` extensions.

   The output of this operation is parsed to see which files were received or removed, and what are their PDB ids are.

   Based on the rsync log, received files are unzipped into plain `.cif` to folder `./dataset/ValRep_XML/`. Those deleted are deleted from there as well. The ids of updated files are added to the list of ids that updated during download to be recalculated during data extraction.

6. Download files from ValidatorDB and PDBe REST API.

   Download report from ValidatorDB (to `./dataset/MotiveValidator_JSON/`), and jsons from PDBe API from endpoints: summary, assembly, molecules, publications and related publications (to their respective folders in `./dataset/PDBe_REST_API_JSON`).

   Files are downloaded for: structure ids gotten as updated from sync of mmcif and for those that failed last time (loaded from persistent file `./dataset/download_failed_ids_to_retry.json`). Ids that fail are added to the failed ids json and saved for next time. Any that succeeded after previous fails are removed from failed ids json, and also added to the list of ids that updated during download to be recalculated during data extraction.

7. Delete old files from ValidatorDB and PDBe REST API.

   Delete those files for pdb ids that got removed during step 3. (sync of structure mmcifs).

8. Save changed ids into json.

   Save structure and ligand ids that changed (updated or deleted) into a file `./dataset/download_changed_ids_to_update.json`. When data extraction is run, this file is the source of truth for which ids it updates and removes from crunched.csv.

9. Create simple lock file.

   Creates `./logs/data_extraction_lock.txt` to serve as a lock against next data download run. This file is deleted (released) upon successful data extraction run.

### Required files

- Folder `./dataset/` (or other path if dataset path is set by environmental variable `DATASET_ROOT_PATH`) needs to exist beforehand.

### Error recovery

What to do in the rare case that serious error happens to maintain data integrity.

In cases not mentioned here, follow the WARNING and ERROR levels of logs (stored in `./logs/filtered_log.txt` by default). None of them should require any changes and manual actions apart from those mentioned below.

- App fails during the rsync of structure mmCIF files and no other actions are done.

  1. Check the logs for raw rsync log of the part that still managed to run. If there are any files that were still received, action needs to be taken.

  2. Check the files received were unzipped - if not, do so manually. Then, write the list of PDB ids of mmcifs that downloaded into a json file and pass its path via env variable `OVERRIDE_IDS_TO_DOWNLOAD_PATH`. Then, run the app again.

     <u>*Alternative*</u>

     Delete the received .cif.gz files from their folder, and run the app again without changes.

- Download of ValidatorDB jsons or PDBe REST API jsons fails to load or save the file with failed downloads.

  1. Check the logs for what happened. There should be CRITICAL level log with the json with failed ids json included. Copy this.

  2. If it failed only during saving the file, simply paste the json into the appropriate file (by default it is `./dataset/download_failed_ids_to_retry.json`).

     If it failed during loading the file with failed ids to retry, try to locate it and identify the issue. If such file exists, you need to add into it the ids that failed this run (from the json from the logs).

     Example of the `download_failed_ids_to_retry.json`:
     (the numbers after the ids indicate how many times in row it failed, only informative function)

     ```json
     {
     	"RestSummary": {},
     	"RestMolecules": {},
     	"RestAssembly": {},
     	"RestPublications": {
     		"21bi": 3,
     		"31bi": 3,
     		"41bi": 3
     	},
     	"RestRelatedPublications": {},
     	"ValidatorDbReport": {}
     }
     ```

  3. Save the file. Download phase can now be considered successful and the rest of the program may continue. Run the app again with the environment variable `SKIP_DATA_DOWNLOAD` set to `True`.

- Saving of the json with information about which structure and ligand ids changed failed.

  1. See the logs. Under ERROR log level, there will be printed a list of changed structures and changed ligands that would have been written into the json file, had it not failed.

  2. Locate the file (default `./dataset/download_changed_ids_to_update.json`) or create it if it does not exist. Add to it the received/deleted structure/ligand ids as mentioned in the log.

     Example of how it may look:

     ```json
     {
     	"structuresToUpdate": ["1dey", "7pin"],
     	"structuresToDelete": [],
     	"ligandsToUpdate": ["AOH", "L53"],
     	"ligandsToDelete": []
     }
     ```

  3. Save the file. Download phase can now be considered successful and the rest of the program may continue. Run the app again with the environment variable `SKIP_DATA_DOWNLOAD` set to `True`.

## Data extraction

## Data archiving

## Data transformation

## Post transformation actions



