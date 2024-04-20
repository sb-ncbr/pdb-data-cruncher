# User guide

TODO real table of contents

[toc]

## Local development

TODO

## Deployment

TODO

## Configuration

Configuration of the program is done by setting environmental variables. See [Local development](#local development) or [Deployment](#deployment) sections to see how to set those in each case.

Multiple things can be configured via environmental variables. This guide will only mention those that will most likely need setting or be otherwise useful. To see all the possible variables that can be set, check `src/config.py`. Config file is the source of truth for available environmental variables and their names.

### App flow control

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

### Data sources

- `DATASET_ROOT_PATH` Default: `./dataset`.

  Folder containing data to be used for creating output files. See TODO for detailed description of all it needs to contain for the app to work.

- `OUTPUT_ROOT_PATH` Default: `./output`.

  Folder containing the output data  - data needed by ValtrendsDB. See TODO for detailed descritpion of all it needs to contain, and what it creates.

- `LOGS_ROOT_PATH` Default: `./logs`.

  Folder where the logs from the run are stored, as well as the simple text lock if data extraction fails (to avoid accidental data download run after such event, which would lose information about what has changed).

- Most of the files and folders inside these three data sources containing input of some sort can have their names overridden. See `src/config.py` for the specific environment variable names if such action is needed.

### Tweaking the settings

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

### Other relevant

- `CURRENT_FORMATTED_DATE`. Default: Today in format `YYYYMMDD`. It may be useful to override it in rare cases. It controls which crunched.csv gets loaded during data transformation, and how output files are named.

## App flow & Error recovery

This section serves as explanation of what each phase does, what files it needs to function, and what it creates.

TODO

