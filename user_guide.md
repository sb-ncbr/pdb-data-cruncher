# User guide

If at any point the aplication fails, check the `logs/` folder and its subfolders for information about
what happened, if anything needs to be done and how to recover. Take special care if a `CRITICAL` log level
is ever encountered, as that requires manual actions to avoid losing information.

1. [Package management](#package-management)
2. [Local development](#local-development)
   1. [Docker](#docker)
   2. [Local runtime](#local-runtime)
   3. [Code quality](#code-quality)

3. [Deployment](#deployment)
   1. [Creating Docker image](#creating-docker-image)
   2. [Deploy to Rancher](#deploy-to-rancher)
   3. [Managing files in the persistent storage](#managing-files-in-the-persistent-storage)
4. [Configuration](#configuration)
   1. [App flow control](#app-flow-control)
   2. [Data sources](#data-sources)
   3. [Tweaking the settings](#tweaking-the-settings)
   4. [Other relevant](#other-relevant)
5. [Logging levels](#logging-levels)
6. [App flow and error recovery](#app-flow-and-error-recovery)
   1. [Data download](#data-download)
   2. [Data extraction](#data-extraction)
   3. [Data archiving](#data-archiving)
   4. [Data transformation](#data-transformation)
   5. [Post transformation actions](#post-transformation-actions)

# Package management

The package versions are managed by [poetry](https://python-poetry.org/). The dependencies are defined in the file `pyproject.toml` (which also contains additional settings for tools such as pylint). A `poetry.lock` file should never be edited manually. It contains the result of dependency resolution. Whenever `pyproject.toml` is edited, a `poetry lock` should be called to update the lock to reflect the changes. When installing the packages, the lock is used to get a list of which packages are installed. E.g. when docker image is built, package versions are installed from this lock.

Useful commands:

- `poetry install` Installs the defined dependencies into current environment (poetry automatically creates its environment in the current location).
- `poetry add package-name` Installs a new package and adds it to the dependencies.
- `poetry update` Gets the latest versions of the dependencies in the `pyproject.toml` and updates the lock. It respects the version constaints given in the `pyproject.toml`. If no version is given, the newest is used if possible. Settings version to `package_name = "version"` will freeze the package to this version only.  Using `"^1.1"` permits any version that is `1.1` or greater, but less than `2.0`. See [Dependency specification](https://python-poetry.org/docs/dependency-specification/) for detailed syntax. `poetry update <package-name>` would update only the selected packages (and their dependencies, if needed).
- `poetry lock`  Recreates lock file based on current `pyproject.toml`.
- `poetry run <action-name>` Runs given thing with poetry environment active. E.g. `poetry run python3 <python-options>`  or `poetry run pylint <pylint-options>`.

Poetry is used in this project because it allows for straightforward package management, easily manages local environments, and because the lock file means you know exactly how the production looks like and you can recreate it exactly locally.

# Local development

You can run the app either in Docker, or in your local Python runtime.

## Docker

You need to have a [Docker engine](https://docs.docker.com/engine/install/) installed. Alternatively, you may want [Docker Desktop](https://www.docker.com/products/docker-desktop/) instead, as it comes with application and not only commandline tool.

To build and run the application, run one of these commands:

```bash
make docker
```

or

```bash
docker-compose build
docker-compose up [-d] --force-recreate --remove-orphans
```

If you include the `-d` flag, it will run detached and to access the logs, you will need to see the Docker Desktop app or run `docker logs <container-name>`.

This docker-compose command spins up a container with the application with additional settings defined in `docker-compose.yaml`. Before you run this command, you may want to edit the `volumes` paths inside. (Volumes bind your local storage to the container, acting as a persistent storage.) You may use the `environment` section to set custom environmental variables to configure the application.

Running the following command will stop and delete the container.

```bash
docker-compose down
```

You can edit the `command` in the `docker-compose.yaml` (see comments inside the file) to override which command gets run inside the container.

If you want to run tests, you can run one of these commands:

```bash
make tests
```

or

```bash
docker-compose -f tests/docker-compose.yaml build
docker-compose -f tests/docker-compose.yaml up
```

Beware, these commands need to be run from the root folder (do not run them from inside the tests folder).

The tests have their own different Docker image and docker-compose.yaml, located inside the `tests` folder. This is so that the production image located in the root folder does not contain needless data.

You can edit the `tests/docker-compose.yaml` to run something different than just the tests. Follow the comments inside the docker compose YAML to override the command it runs.

## Local runtime

The application was developed on Python 3.10. You should run it on this version or newer.

How to run the app:

1. Install dependencies with `poetry install`. (If you do not have poetry package manager, run `pip install poetry` first.)

2. You will most likely need to configure the application, at the very least the env variables containing data paths. Create a `.env` file in the root folder with the following content:

   ```yaml
   DATASET_ROOT_PATH=../dataset/
   OUTPUT_ROOT_PATH=../output/
   LOGS_ROOT_PATH=../logs/
   ```

   These example paths work if the data folders are located in the parent folder of the pdb-data-cruncher. The paths can be either full or relative to the inside of pdb-data-cruncher folder.

   Alternatively, if you're using PyCharm to develop, you can explicitely set which .env file to load in the configuration.

3. Run the application with:

   ```bash
   poetry run python3 src/main.py
   ```

## Code quality

Tools `pylint`, `flake8` and `black` are used to maintain higher standard of code quality.

I recommend using these tools before commiting. They promote code quality, higher degree of readability and often point out more serious underlying issues.

- `pylint` and `flake8` are good tools for pointing out bad practises, missing documentation or other deviations from the PEP8 code style. Occassionally, when exceptions make sense, you can use `pylint: disable=xxx` for Pylint and `noqa=xxx` for Flake8 to disable the warnings, but please do so with comments on why this is such a case.

  These tools only report the findings, but manual changes are needed. You can run them with `poetry run pylint src/` and `poetry run flake8 src/`, or via the respective `make` commands. If you need to run these in docker, see the [Docker](##docker) section on how to edit the test docker-compose to run these.

- `black` is a code formatter. Running it will reformat the code to follow its coding style. This is great do to when unusure of how to make the code in Python readable or to unify formatting. Using black means giving up a small portion of control over how the code looks like to achieve consistent style accross the whole code base. As a side-effect, it also fixes some of the issues pointed out by `flake8` and `pylint` automatically.

# Deployment

## Creating Docker image

Follow the steps to build new docker image from your local files.

1. Log into the CERIT's docker image harbor with:

   ```bash
   docker login cerit.io
   ```

   When asked for credentials, enter your CLI secret as a password (found in [hub.cerit.io](https://hub.cerit.io) in the User Profile section). See [CERIT harbor documentation](docs.cerit.io/docs/harbor.html) for more detailed instructions if needed.

2. Build the docker image locally by running:

    ```bash
    docker build -t cerit.io/your_cerit_repository_name/pdb-data-cruncher
    ```

3. Tag the image with new [semver](https://semver.org/) number (e.g. `v1.1`). (By default, the tag is `latest`. The tag can be named however you want, but following semver is a good practice.)

    ```bash
    docker tag cerit.io/your_cerit_repository_name/pdb-data-cruncher cerit.io/your_cerit_repository_name/pdb-data-cruncher:the_tag_name
    ```

4. Push the created docker image into the remote repository.

    ```bash
    docker push cerit.io/your_cerit_repository_name/pdb-data-cruncher:the_tag_name
    ```

Alternatively, you may run the following command instead of steps 2-4. Before doing so, you need to edit variables `CERIT_DOCKER_REPOSITORY_NAME` and `NEW_DOCKER_TAG` inside the [Makefile](./Makefile) to suit your configuration.

```bash
make docker-build-tag-push
```

Please note that any setting used in `docker-compose.yaml` or `local.env` is not used when building the image. To set environmental variables, you need to add them while setting up the deployment in Rancher.

## Deploy to Rancher

Useful links: [Rancher Dashboard](https://rancher.cloud.e-infra.cz/dashboard) | [Harbor](https://hub.cerit.io/) (image repository) | [Racher documentation](https://docs.cerit.io/docs/overview.html)

Two types of Rancher Workloads are relevant: CronJobs and Jobs. A Job starts its pod immediately, and when successfully finished, it never repeats. CronJob contains definition on how often it should run. At that time, it spawns its own Job to run.

To run the pdb-data-cruncher each week, a CronJob should be set up. Go to the CronJobs tab in the Workloads menu item in `kuba-cluster`, and press Create. From there, you can either fill in the form, or click "Edit as YAML" and paste in prepared configuration.

Beware, even though Rancher allows a creation of the Jobs and CronJobs via a form, it requires definition of a property `seccompProfile` that cannot be entered into the form. Because of this, I would recommend preparing and editing the YAML directly, skipping the UI form altogether.

A file `example_cronjob.yaml` contains a full configuration that works (at least for now, until they change the required security settings again). Before copy pasting it, see the comments inside, and edit the namespaces and the image name to your values. Everything else, including the mounted storage, should be prepared to run as-is. This CronJob is set up to save up to 5 succeeded and 5 failed runs, no need to delete the pods, it will do so when this amount is reached.

A Job deployment type is useful for one time fixes or running SSH copying until the post-transformation actions are implemented. See `example_job.yaml`, edit namespaces where comments indicate, and edit the image name. Depending on what task you need done, you may add environmental variables (where the comments indicate) to configure the application run.

<a id="empty-pod"></a>Alternatively, you may uncomment the command `tail -f /dev/null` part of the YAML. When it is run like that, the pod does not actually run the pdb-data-cruncher. Instead, the pod is created and runs infinitely. You may then find the pod in Pods, and select `Execute Shell` to get a shell inside the pod. From there, files can be inspected and commands can be run.

When using the Job, you will need to delete it afterwards. Take special care with pods running infinitely. They will not be deleted when you delete the Job itself, you need to go to Pods tab and delete them manually.

## Managing files in the persistent storage

The most straighforward way is via kubectl tool and "empty" pod.

1. Install [kubectl](https://kubernetes.io/docs/tasks/tools/) tool locally. kubectl is a commadline tool for accessing and managing kubernetes clusters.
2. Follow [this CERIT's guide](https://docs.cerit.io/docs/kubectl.html) on how to download and save the cluster configuration. That will allow you to access the cluster from your machine via terminal. Then do `kubectl config get-contexts` to check your connection works and that you have the correct cluster set as current. After that, run `kubectl config set-context --current --namespace=your-namespace` to switch to the namespace so you do not have to specify it after each command.
3. Create an "empty" pod running nothing endlessly (as described [in the previous section](#empty-pod)), that has access to the persistent storage.
4. Get a name of that pod (either from the Rancher UI, or by running `kubectl get pods`).
5. Use `kubectl cp <pod_name>:<path_to_folder_or_file_in_pod> <your_local_path>` to copy files from the pod to your machine, or put your local path first to achive the opposite.

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

# Logging levels

- `EXCEPTION` - Something broke in a way that was not expected. The highest severity, needs to be investigated as it is not supposed to happen. It most likely means the code logic is flawed.
- `CRITICAL` - A rare case that needs extra attention. Checking the logs and following the instructions is needed.
- `ERROR` - There is a serious issue with processing the data. Most likely means big chunk of protein data is missing, corrupted or otherwise wrong and cannot be processed. It should be noted and kept eye on during the next program run, investigated if needed.
- `WARNING` - Minor data issue (e.g. few non-critical values missing). Or situation that does not create problem for the code at all, but may be weird (e.g. multiple values of something where only one is expected). It may be good to review this level occassionally. It will not be spamed - minor issues get aggregated and logged only once on this level (and then in more defail on INFO level).
- `INFO` - Information about important milestones in code execution or detailed information about minor issues. May get cluttered, it is worth to search through it only when looking for something specific.
- `DEBUG` - More detail about the code execution, tasks started, configuration loaded, number of things processed, etc. Should be turned off for normal running.

# App flow and error recovery

This section serves as explanation of what each phase does, what files it needs to function, and what it creates.

As a general rule, any mentioned file/folder paths for source data represent the default paths, but may be configured (see [Configuration - Data Sources](##Data-sources)).

## Data download

The data download phase takes care of keeping up to date the source data, and storing the information about which structures/ligands to recalculate in next phase.

Data download is done as follows:

1. **Assert no lock is present.**

   Lock presence (existence of file `./logs/data_extraction_lock.txt`) indicates data extraction did not run fully and did not process the last download's ids to update list, so this is a safeguard against accidentally running download again and overwriting it.

2. **Make sure required folders are present.**

   Dataset folder itself needs to be present before the run, but all the folders for data to be downloaded will be created if they are missing. However, this will issue a warning - if the app is run for the first time over new storage, it can be ignored. But on subsequent download runs, this may indicate the path is configured incorrectly.

3. **Synchronize PDB mmCIF files for structures via rsync.**

   First, files in location `./dataset/gz_PDBe_mmCIF/` are synced to the rsync endpoint `rsync.rcsb.org::ftp_data/structures/divided/mmCIF/`. These files have `.cif.gz` extensions.

   The output of this operation is parsed to see which files were received or removed, and what are their PDB ids are. The log is also saved into its log subfolder.

   Based on the rsync log, received files are unzipped into plain `.cif` to folder `./dataset/PDBe_mmCIF/`. Those deleted are deleted from there as well. The list of ids that changed or were removed is saved for further processing.

   <u>*Alternative*</u> (for error recovery)

   If path to json with list of ids is passed via env variable `OVERRIDE_IDS_TO_DOWNLOAD_PATH`, rsync of PDB mmCIF files is not done. Instead, this json is loaded and ids inside will be used as ids that changed for next steps (both for downloading other http files and subsequent data extraction). 

4. **Update ligand .cif files.**

   This is done by downloading `components.cif` and `aa-variants-v1.cif` files from PDB, cutting them into individual ligand cifs, and comparing them to already saved cif files. If they differ, they are updated and the ids of those updated are saved for further processing. The same goes for those deleted (not present in either of big .cif files anymore).

5. **Synchronize validation report .xml files via rsync.**

   First, files in location `./dataset/gz_ValRep_XML` are synced to the rsync endpoint `rsync.rcsb.org::ftp/validation_reports/ `(filtered so only the xml files are synced). These files have `.xml.gz` extensions.

   The output of this operation is parsed to see which files were received or removed, and what are their PDB ids are.

   Based on the rsync log, received files are unzipped into plain `.cif` to folder `./dataset/ValRep_XML/`. Those deleted are deleted from there as well. The ids of updated files are added to the list of ids that updated during download to be recalculated during data extraction.

6. **Download files from ValidatorDB and PDBe REST API.**

   Download report from ValidatorDB (to `./dataset/MotiveValidator_JSON/`), and jsons from PDBe API from endpoints: summary, assembly, molecules, publications and related publications (to their respective folders in `./dataset/PDBe_REST_API_JSON`).

   Files are downloaded for: structure ids gotten as updated from sync of mmcif and for those that failed last time (loaded from persistent file `./dataset/download_failed_ids_to_retry.json`). Ids that fail are added to the failed ids json and saved for next time. Any that succeeded after previous fails are removed from failed ids json, and also added to the list of ids that updated during download to be recalculated during data extraction.

7. **Delete old files from ValidatorDB and PDBe REST API.**

   Delete those files for pdb ids that got removed during step 3. (sync of structure mmcifs).

8. **Save changed ids into json.**<a id="download-save-changed-ids"></a>

   Save structure and ligand ids that changed (updated or deleted) into a file `./dataset/download_changed_ids_to_update.json`. When data extraction is run, this file is the source of truth for which ids it updates and removes from crunched.csv.

9. **Create simple lock file.**

   Creates `./logs/data_extraction_lock.txt` to serve as a lock against next data download run. This file is deleted (released) upon successful data extraction run.

### Required files

- Folder `./dataset/` (or other path if dataset path is set by environmental variable `DATASET_ROOT_PATH`) needs to exist beforehand.

### Error recovery

What to do in the rare case that serious error happens to maintain data integrity.

In cases not mentioned here, follow the WARNING and ERROR levels of logs (stored in `./logs/filtered_log.txt` by default). None of them should require any changes and manual actions apart from those mentioned below.

- **App fails during the rsync of structure mmCIF files and no other actions are done.**

  1. Check the `logs/rsync_log_history/` for raw rsync log of the part that still managed to run. If there are any files that were still received, action needs to be taken.

  2. Check the files received were unzipped - if not, do so manually. Then, write the list of PDB ids of mmcifs that downloaded into a json file and pass its path via env variable `OVERRIDE_IDS_TO_DOWNLOAD_PATH`. Then, run the app again.

     <u>*Alternative*</u>

     Delete the received .cif.gz files from their folder, and run the app again without changes.

- **Download of ValidatorDB jsons or PDBe REST API jsons fails to load or save the file with failed downloads.**

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

- **Saving of the json with information about which structure and ligand ids changed failed.**

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

The data extraction phase takes list of structure and ligand ids that had changed during data download, extracts relevant protein data from their respective files, and updates crunched csv with this new data.

Data extraction is done as follows:

1. **Find which structure and ligand ids should be updated and deleted.**

   With default settings, it loads these lists created by the [download phase](#download-save-changed-ids). It does so from the location `./dataset/download_changed_ids_to_update.json`.

   *<u>Alternative</u>*

   If the `FORCE_COMPLETE_DATA_EXTRACTION` is set to true, it instead looks to the folder with structure mmCIF files (`./dataset/PDBe_mmCIF/` by default) and creates the list of structure ids to update from every structure it finds .cif file there for. In the same way, ligand ids to update are found (from every .cif file from `./dataset/ccd_CIF/` by default). Effectivelly, this means the app will run for **every** structure and ligand there is (assuming the data storage is up to date with PDBe). No structures or ligands are marked for deletion, but with this setting, any files that are normally only updated (crunched csv, ligand stats, ...) are recreated from scratch instead.

   *<u>Alternative</u>* <a id="data-extraction-step-1-alternative-b"></a>

   If the `OVERRIDE_IDS_TO_DOWNLOAD_PATH` is set, the ids will be loaded from this file instead. This may be used to define custom ids to update (in combination with skip data download option).

   This variable needs to contain path to json. Its content can look like this:

   ```json
   {
   	"structuresToUpdate": ["1dey", "7pin"],
   	"structuresToDelete": [],
   	"ligandsToUpdate": ["AOH"],
   	"ligandsToDelete": []
   }
   ```

2. **For changed ligand ids, find which structures contained these ligands in previous runs, and add these structure ids to the list of ids to update.**

   In between runs, file `./dataset/ligand_occurrence_in_structures.json` stores the information about which ligand ids were used for each structure id. For every ligand id to update, this file is searched for a list of structure ids that had used this ligand. These structure ids are then appended to the list of structures to update this run.

   (This is important because some of the collected protein data for a structure are dependant on ligand data - if the underlying ligand changed, the structure's data need to be recalculated.)

3. **For changed ligand ids, calculate their ligand stats and save the updated version.**

   Ligand stats are calculated for each ligand id (from their .cif file) and updated in the persistent ligand stats csv (default `./dataset/ligandStats.csv`).

4. **Load all ligand stats.**

   Load all ligand stats from the csv (`./dataset/ligandStats.csv` by default).

5. **For every updated structure id, run data extraction to acquire protein data:** <a id="data-extraction-step-5"></a>

   This is done in multiple processes (one for each structure id, up to maximum defined in configuration).

   1. **Load and parse structure's mmCIF.**

      Works with .cif file from PDBe.

   2. **Load and parse structure's ValidatorDB result.**

      Works with result.json file from ValidatorDB.

   3. **Load and parse structure's XML validation report.**

      Works with .xml file from PDBe.

   4. **Load and parse structure's files from PDBe REST API.**

      Works with assembly.json, summary.json and molecules.json from PDBe.

   5. **Calculate inferred protein data.**

      Calculates additional data by combining data from multiple sources.

6. **Go through the collected protein data and determine which are considered successful.**

   The acquired protein data structure is considered successful (thus fit for saving as valid result) if at least the parsing of data from .cif from PDBe was successful. ValidatorDB result, XML validation report and data from PDBe REST API may be missing or invalid (such event is still logged, but the data is saved in at least its partial form).

7. **For successful data, update which ligands they contain for future runs.** <a id="data-extraction-step-7"></a>

   Updates `./dataset/ligand_occurrence_in_structures.json` file with data loaded this run.

8. **Remove structures designated for removal from ligand occurence json.** <a id="data-extraction-step-8"></a>

   If any structures are removed, their entries are removed from `./dataset/ligand_occurrence_in_structures.json` file as well.

9. **Update crunched csv with successfull data, and delete data about structures to be deleted.** <a id="data-extraction-step-9"></a>

   1. **Load previous crunched csv, if such exists.**

      By default, `./output/data.csv` is loaded for the purpose of updating! The other files (crunched.csv and data.xlsx) are only output.

      *<u>Alternative</u>*

      In case of `FORCE_COMPLETE_DATA_EXTRACTION` set to true, this is skipped. New crunched csv is created, and the old one is overwritten!

   2. **For structure id from the list of ids that should be deleted, remove their rows from crunched csv.**

   3. **Update the crunched csv with the successful protein data.**

      These rows are completely replaced with new data.

   4. **Store updated csv.**

      It is stored in three files, as required by ValTrendsDB. `./output/data.csv`, `./output/YYYYMMDD_crunched.csv` and `./output/data.xlsx`.

10. **Delete crunched csv with old tiemstamp.**

    If there are any crunched csv following the format `YYYYMMDD_crunched.csv` in the output folder that do not have current formatted date, they are deleted.

11. **If overall successful, release (delete) lock from download phase.**

    Overall success is defined as:

    - ([Step 5](#data-extraction-step-5)) All collected protein data contain the part of data from PDBe mmCIFs (i.e. there was no unrecoverable error during the processing of the .cif file).
    - ([Step 7](#data-extraction-step-7) & [Step 8](#data-extraction-step-8)) Update of ligand occurence json was successful.
    - ([Step 9](#data-extraction-step-9)) Updating and saving of crunched csv (and its other versions) was successful.

    Releasing lock means deleting the file `./logs/data_extraction_lock.txt` that was created during download (to prevent accidental rerun and lost information). By deleting it, it signals that all the information from download (changed ids) was safely processed.

### Required files

Example of file structure (on default configuration) needed for successful aplication run.

All these files are created by either data download or previous data extraction phases. Unless you are running the app with skip download on or run data extraction only on, you do not have to worry about these details.

```
dataset/
    ccd_CIF/
        000.cif
        ...
    MotiveValidator_JSON/
  	    100d/
  	        result.json
  	    ...
    PDBe_mmCIF/
        100d.cif
        ...
    PDBe_REST_API_JSON/
        assembly/
        	100d.json
        	...
        molecules/
            100d.json
            ...
        summary/
            100d.json
            ...
    ValRep_XML/
        100d_validation.xml
        ...
    download_changed_ids_to_update.json
    ligand_occurence_in_structures.json
    ligandStats.csv [Optional]
    ligand_occurence_in_structures.json [Optional]
```

[Optional] = Not needed on the first run ever. But if not present on subsequent runs, something is wrong.

For the first run, make sure to create `dataset/ligand_occurence_in_structures.json` with `{}` as content.

### Error recovery

Multiple things can lead to the data extraction phase being considered unsuccessful and the app exiting with non-zero status code to indicate such. In such cases, simple lock is not released and future download phases are blocked unless the issue is resolved.

None of the issues that can arise is critical (i.e. that would result in the loss of cruical data with no option to reproduce the results), but they still need to be address.

In general, follow these steps:

1. See logs to find out what caused the errors. If possible, try to fix the cause.
2. Run the app again with either `SKIP_DATA_DOWNLOAD` set to true (this skips the download phase and lets extraction phase load the result from the *last* download phase, i.e. the same one as the last time when data extraction failed) or `RUN_DATA_EXTRACTION_ONLY` set to true.

If for some reason it is needed to only run a subset of ids to update, use `IDS_TO_REMOVE_AND_UPDATE_OVERRIDE_PATH` to define your own set of ids for the next run. See [here](#data-extraction-step-1-alternative-b) for example of such file.

In the worst case scenario of being aware that the crunched csvs are not up to date with downloaded data, but unable to assert which ones are wrong, option `FORCE_COMPLETE_DATA_EXTRACTION` set to true will force complete redo of the crunched csvs. In such case, no ids to update and delete are loaded from the download - instead, all .cif files in dataset are taken as structure ids to be updated. Beware, with this option on, the app will run significantly longer - use with caution.

If you are certain everything was created successfully, but the simple lock `./logs/data_extraction_lock.txt` was not removed for some reason, simply deleting the file will allow the next run to do download unblocked.

## Data archiving

Archives downloaded data into .7z archive to output folder. With default configuration, these are:

- `./dataset/ccd_CIF/` to `./output/rawccd.7z`
- `./dataset/MotiveValidator_JSON/` to `./output/rawvdb.7z`
- `./dataset/PDBe_mmCIF/` to `./output/rawpdbe.7z`
- `./dataset/PDBe_REST_API_JSON/` to `./output/rawrest.7z`
- `./dataset/ValRep_XML/` to `./output/rawvalidxml.7z`

The archiving is done by p7zip-full commandline tool. If such archive already exists, it simply updates it (or removes files when neccessary) without the need to recreate the whole archive from scratch.

### Required files

Example of file structure (on default configuration) needed for achiving.

All these files are created by data download.

```
dataset/
    ccd_CIF/
        000.cif
        ...
    MotiveValidator_JSON/
  	    100d/
  	        result.json
  	    ...
    PDBe_mmCIF/
        100d.cif
        ...
    PDBe_REST_API_JSON/
        assembly/
        	100d.json
        	...
        molecules/
            100d.json
            ...
        summary/
            100d.json
            ...
    ValRep_XML/
        100d_validation.xml
        ...
```

### Error recovery

In case of failure, simply run the phase again by setting `RUN_ZIPPING_FILES_ONLY` to true.

## Data transformation

This phase takes care of transforming the data from crunched csv into multiple output files - it creates default plot data, distribution data, and default plot settings; it updates factor hierarchy, Versions and VersionsKT.

It runs as follows:

1. It attempts to find the current crunched csv. It expects it in the output folder location, in format `YYYYMMDD_crunched.csv`, where the formatted date is current date.

   <u>*Alternative*</u>

   If `CRUNCHED_CSV_NAME_FOR_DATA_TRANSFORMATION` is set to path to another crunched csv, that csv is used instead.

2. Default plot data is created.

   Factor pairs to do the default plot data for are loaded from file `./dataset/autoplot.csv` (the name can be overwritten by `AUTOPLOT_CSV_NAME`). Following structure is expected in this file (columns `X` and `Y` need to be present, though they do not need to be the only columns nor do they need to be the first columns):

   ```
   X;Y
   resolution;releaseDate
   resolution;hetatmCount
   ```

   A list of bucket limits for each factor is taken from file `./dataset/3-Hranice-X_nazvy_promennych.csv` (the name can be overwritten by `X_PLOT_BUCKET_LIMITS_CSV_NAME`). The structure of the file is expected as follows:

   ```
   ;resolution;releaseDate
   1;-0.01;-0.01
   2;0.99;1994
   3;1.049;1995
   4;1.13;1996
   ```

   The second row is ignored and negative infinity is assumed. If any column has fewer buckets than the rest, `NA` in place of the missing values is expected.

   The following is done for each factor pair:

   1. Overall data statistics are calculated. This includes global min/max values for factors on x/y axes.
   2. Data is sorted based on their x value into buckets defined by the loaded bucket limits.
   3. If there are any empty buckets or buckets with less structures than 100, they get merged into their smaller neighbour bucket. This is done until all buckets have 100 hundered strucgtures or more, or until there is only one bucket (dataset this small should never occur though).
   4. For each of the resulting buckets, additional statistics are counted (such as y factor value average, min, max, etc.).

   All the collected information is saved into the folder `YYYYMMDD_DefaultPlotData/`, where each factor pair gets its JSON with collected information. The files inside have format `factor_on_x+factor_on_y.json`, e.g. `resultion+releaseDate.json`. Any old default plot data present in the output folder are then deleted.

3. Distribution data creation, for each factor name loaded from `nametranslations.json`.

   The following is done for each factor (except for a release date, which gets handled in straighforward way):

   1. The values for every structure for this factor are rounded (to 3 decimal significant places).
   2. The dataset is grouped into buckets based on the factor values.
   3. The buckets with the fewest structures inside are merged into their neighbour (creating buckets covering intervals instead of single values), as long as there is at most 200 buckets present.

   All the collected information is saved into the folder `YYYYMMDD_DistributionData/`, where each factor has its own JSON with collected information. The files are named as `factor_name.json`, e.g. `resolution.json`. Any old distribution data present in output folder are then deleted.

4. If `DATA_TRANSFORMATION_SKIP_PLOT_SETTINGS` is set to false,  the default plot settings are created. By default, this step is skipped. (This action is resource intesive while the results do not need to be recalculated often.)

   The information about which factor types can be on x-axis (so they need default plot settings created) and which can be on y-axis (so for a calculation of default plot settings for different factor, they can be on y-axis and need to be taken into an account).

   The requirements (by the ValTrendsDB) for the default plot settings are that a plot with buckets with the same width are made. The buckets do not need to cover the maximum range of x-axis factor. However, there need to be at most 50 buckets (by default), and each resulting bucket interval needs to have at least 50 structures (by default), for each combination of factors possible (i.e. the x-factor needs to have enough structures in each final bucket with any of the factors that are permissable on the y-axis; this may differ from factor to factor because not all factors have a value for each structure).

   For each factor on x-axis (except for a release date, which is created with respect to the fact that it represents a year), it is done as follows:

   1. Calculate minimum and maximum value on x, without outliers (that are defined as mean value plus/minus two times standard deviation; by default).
   2. Possible bucket size is determined in such a way that the resulting bucket count would be less than 50 and would cover the interval defined by adjusted minimum and maximum value. At the same time, the bucket size is allowed to be only one of the numbers from `[10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90]` times 10^n, to keep the bucket boundaries as short human-readable numbers.
   3. Test if every combination of this factor and any factor on y results in at least 50 structures in every bucket created like this. If not, make the bucket width slightly larger (move it to the next bucket base size from the list, e.g. 700 if 600 did not work out) and try again, until the requirements are met.

   After all the data is collected, one JSON `YYYYMMDD_DefaultPlotSettings.json` is created containing the resulting default plot setting for each factor. Old default plot settings are then deleted.

5. Update factor hierarchy.

   Factor hierarchy has three values that need adjusting for each factor: value range from, value range to, and slider step. These values are used to set the slider controlling which interval on x is displayed for ValTrendsDB plots.

   The rest of the file is unchanged, simply copied. This however means that there needs to be a previous file `YYYYMMDD_FactorHierarchy.json` in output location to run successfully.

   For each factor (except the release date, which follows a simplified version), the values are determined as follows:

   1. Get maximum value rounded up to two significant decimal places. Get minimum value rounded to the same precision at the maximum value. Determine the value range needed to cover with the slider step.
   2. By default, there should be min 100 steps on the slider, and 300 at most, with 200 the ideal count. Attempt to determine such slider step length that the step count it creates is close to 200 and the slider step is a nice number (similar as in plto settings, slider step value can only be `[10, 20, 25, 50]` times 10^n).
   3. Adjust the maximum value on x up so that the last step has the same length as the rest of them.

   If successful, the values are updated and saved into a factor hierarchy with current formatted date, and the old file is deleted.

6. Update version JSONs.

   For both `Versions.json` and `VersionsKT.json`, the same action is load. They are loaded, the first entry (the one with last datastamp of current data) is removed, and entry with current formatted data string is added.

### Required files

Example of file structure (on default configuration) needed for achiving.

```
dataset/
	3-Hranice-X_nazvy_promennych.csv
	autoplot.csv
output/
	YYYYMMDD_crunched.csv
	nametranslation.json
	YYYYMMDD_FactorHierarchy.json
	Versions.json
	VersionsKT.json
	YYYYMMDD_DefaultPlotSettings.json [Optional]
```

The timestamp in `YYYYMMDD_crunched.csv` represents the current formatted date. The file is matched based on `CURRENT_FORMATTED_DATE` env variable, which defaults to today.

In `YYYYMMDD_FactorHierarchy.json`, it represents any formatted date string, as it is used to find old version and update it.

`YYYYMMDD_DefaultPlotSettings.json` is marked optional as it is only relevant if environment variable `DATA_TRANSFORMATION_SKIP_PLOT_SETTINGS` is set to true. In such case, an older version of default plot settings (with any formatted date string) is taken and copied into filename with current formatted date string.

### Error recovery

None of the issues that can arise is critical (i.e. that would result in the loss of cruical data with no option to reproduce the results), but they still need to be address.

In general, follow these steps:

1. See logs to find out what caused the errors. If possible, try to fix the cause.
2. Run the app again with `RUN_DATA_TRANSFORMATION_ONLY` set to true. (Keep in mind that this will run only the data transformation; if there are any post-transformation actions set, the application needs to be afterwards run again with `RUN_POST_TRANSFORMATION_ACTIONS_ONLY` set to true.)

You may set `CRUNCHED_CSV_NAME_FOR_DATA_TRANSFORMATION` to a path to a different crunched csv if for any reason you need to run the data extraction over different crunched data.

## Post transformation actions

This phase only gets to run after all phases finish successfully in normal run, or when `RUN_POST_TRANSFORMATION_ACTIONS_ONLY` is set to true.

**Nothing happens in this phase!** Yet.

It is a code stub for future development, as a place for any actions that should happen after the app runs successfully (i.e. sending the newly created data to another location).

To add functionality to this phase, simply edit function `run_post_transformation_actions` in `src/post_transformation_actions.py`.
