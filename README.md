# ImageAssessmentService
This package provides a service for automatic image assessment. It uses the MUSIQ algorithm
(https://arxiv.org/abs/2108.05997, https://github.com/google-research/google-research/tree/master/musiq). Images are
assessed based on aesthetic and technical aspects. This is achieved by running two flavors of the MUSIQ model: One for
aesthetic assessment and one for technical assessment, with weights from Tensorflow Hub.

## Setup
### Building the package
The package can be built by running the following command in the root folder of the repository:
```bash
make build
```
This will create Python modules from the Protobuf files, build the package and create `build` and `dist` folders containing the built package.

### Installing dependencies
The dependencies of `imageassessmentservice` are listed in `requirements.txt`. They can be installed by running the
following command in the root folder of the repository:
```bash
make deps
```
This step is only required if the package is not installed via `pip` or for development.

### Installing the package
The package can be installed by running the following command in the root folder of the repository:
```bash
make install-all
```
but `pip install .` also works if the package was built separably.

### Cleaning up
The `build` and `dist` folders can be removed together with the modules that are generated from Protobuf files by running the following command in the root folder of the repository:
```bash
make clean
```

## Assessing images by running the client and server
After setting up a Python environment containing the dependencies, the assessment server can be run by executing
```bash
python -m imageassessmentservice.server
```
The server will listen on port 50051 by default. The client can be run by executing
```bash
python -m imageassessmentservice.client images_source_folder ratings_target_file_path [server_address]
```
Here, `images_source_folder` is the folder containing the images to assess, `ratings_target_file_path` will contain the
ratings for all images and `server_address` is the IP address of the server where `imageassessment.server` is running. `server_address` is optional and defaults to `localhost`.

## Making use of image ratings
This package provides two options for making use of the image ratings: Sorting the images in folders according to their
rating or storing the ratings in a Digikam database.

### Sorting images in folders
If images should be sorted in folders according to their rating, run
```bash
python -m imageassessmentservice.process sort ratings_target_file_path source_folder target_folder
```
This creates sub-folders in `target_folder` and then copies the images into them according to
their relative path with respect to `source_folder`.

### Storing ratings in Digikam database
The command line tool `process` can also be used to store the ratings in a database for the photo management program
Digikam (https://www.digikam.org/). The program already contains an Image Quality Sorter
(https://docs.digikam.org/en/maintenance_tools/maintenance_quality.html)
which is based on YoloV3 and yields pretty good results. In case a more powerful GPU is available, this
package allows to further improve the results by rating images based on aesthetic and technical aspects with a
state-of-the-art algorithm. Writing the ratings to Digikam's SQLite database has been tested with version 8.0.0.

In order to store the ratings from `imageassessmentservice.client` in the Digikam database, run
```bash
python -m imageassessmentservice.process digikam path_to_digikam4.db ratings_target_file_path
```
where `path_to_digikam4.db` is the path to the Digikam database file and `ratings_target_file_path` is the path to the
file containing the ratings as described above. The ratings are stored in the database in the `ImageProperties` table.

## Notes
Please keep the following aspects in mind when using this code:
* Images are assessed relative to each other -- the assessment results may be more representative when assessing larger amounts of
    images
* Data is (currently) transferred between service and client without encryption

