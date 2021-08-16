# EESD x IBOIS Scanned stones dataset

This repo contains a dataset of several stones' 3d representations acquired by scanning. The dataset is made available for visualisation, filtering and selection through a web application living online at: [https://epfl-ibois.github.io/eesd-ibois-scanned-stones-dataset](https://epfl-ibois.github.io/eesd-ibois-scanned-stones-dataset).

## Contributing to this dataset:

### Scans post-processing

The following steps come after the post-processing of the stone scans. You should have one or more Rhino files (*.3dm) containing reconstructed point clouds. Each of these reconstructed point clouds should correspond to a stone.

### Required software

- *Rhinoceros 3D*, version 7
- *Cockroach* plugin for Rhinoceros 3D
- *CockroachExtension* plugin for Rhinoceros 3D
- *Git* - [Setup instructions](https://docs.github.com/en/get-started/quickstart/set-up-git)

### Overview

The proposed contributing workflow is based on git's meaning you can:
1. *fork* this repo,
2. getting it updated using `CatalogueExport` command in Rhino
3. and update it online with a *pull request*.

If you are familiar with this workflow, you can fork and clone this repo and directly hop to [2. Generating data](#2-generating-data) section. Once locally updated, you can make a pull request to save changes to this repo.

### 1. *Fork* this repo: Getting a local copy of the catalogue

To update it with new objects, you will need to make a local copy of the catalogue. This copy will be modified when executing the `CatalogueExport` command from Rhinoceros 3D, adding new objects to it. Your updated local copy of the catalogue can be uploaded back to this repo (meaning it will also be live at https://epfl-ibois.github.io/eesd-ibois-scanned-stones-dataset).

1. Make sure you have installed the software listed above and have a GitHub account.
2. Fork this repo by following instructions at https://github.com/ibois-epfl/eesd-ibois-scanned-stones-dataset/fork
3. Clone it on your machine:
   1. Choose a directory to store the catalogue and open it
   2. Right-click in it and select *Git Bash Here*
   3. In the terminal, execute the command (replace your username):
        ```bash
        git clone https://github.com/YOUR-USERNAME/eesd-ibois-scanned-stones-dataset.git
        ```
   4. If requested, authenticate with your GitHub account

You now have a local copy of the catalogue on your machine.

Optionally, you can see the content of your local copy of the catalogue. For this you need to have [Node.js installed](https://nodejs.org/). Then, open a terminal at directory's root and execute:

```bash
npm install
npm start
```
Point your browser to http://localhost:5000 to see the Catalogue Explorer web app running locally. You should see the same as: https://epfl-ibois.github.io/eesd-ibois-scanned-stones-dataset

### 2. Generating data using `CatalogueExport` command in Rhino

3. Open your post-processed scan files on Rhino.
4. In Rhino, run the `CatalogueExport` command.
5. When prompted to choose the export directory, navigate to the root of the previously cloned repo.
6. Upon request select the point clouds to add to the catalogue (mouse drag).
7. Accept default processing parameters (hit Enter).
8. If you want to give a label to each stone, select the corresponding option in Rhino's command prompt (click on underlined `LabelEachItem` in the command prompt to toggle between "label + unique identifier" and "just unique identifier" options).
9.  You are then requested to provide a "DataTree branch" which is the location you want your exported objects to be stored in the catalogue tree. You can either specify a new or an existing branch.
10. If you chose to label each object at step 8, you will be prompted to provide a label for each stone.
11. The export process starts.

Repeat the process for each scan file. New items are incrementally added each time you run the `CatalogueExport` command on the same directory

Optionally, you can see the updated catalogue by running the following command in a terminal at folder's root.

```bash
npm start
```

### 3. Make a *pull request*: Upload your updated version of the catalogue

1. Open the root directory of the catalogue in File Explorer
2. Right-click in it and select *Git Bash Here*
3. In the terminal, execute the following:

    ```bash
    git add .
    git commit -a -m "catalogue updated"
    git push
    ```

4. Make a pull request by following instructions at (replace your username) https://github.com/YOUR-USERNAME/eesd-ibois-scanned-stones-dataset/pull/new/master
5. IBOIS team accepts the pull request finalising the update
6. The updated version of the catalogue is live at https://epfl-ibois.github.io/eesd-ibois-scanned-stones-dataset

### 4. Keep your forked and local version of the catalogue up-to-date

In case you forked and cloned this repo some time ago, it might be possible that someone else made changes to it. In that case, your forked and cloned versions of this repo are outdated and need to update them before you make changes to it.

To do so :
1. Go to (replace your username) https://github.com/YOUR-USERNAME/eesd-ibois-scanned-stones-dataset
2. Click on the *Fetch upstream* button and select *Fetch and merge*
3. Open the root directory of the catalogue in File Explorer
4. Right-click in it and select *Git Bash Here*
5. In the terminal, execute the following:

    ```bash
    git pull
    ```
6. Your local version is up-to-date, you can safely head to [2. Generating data](#2-generating-data) section and add new objects to the catalogue.

