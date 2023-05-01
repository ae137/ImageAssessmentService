# ImageAssessmentService
This package provides a service for automatic image assessment. It uses the MUSIQ  algorithm 
(https://arxiv.org/abs/2108.05997, https://github.com/google-research/google-research/tree/master/musiq). Images are 
assessed based on aesthetic and technical aspects. This is achieved by running two flavors of the MUSIQ model: One for 
aesthetic assessment and one for technical assessment, with weights from Tensorflow Hub.

## Setup
### Install dependences
The dependencies of `imageassessmentservice` are listed in `requirements.txt`.

### Generating protobuf files
In case the protobuf files need to be re-generated, the following command can be used:
```bash
python -m grpc_tools.protoc -I protobufs --python_out=imageassessmentservice --grpc_python_out=imageassessmentservice protobufs/imageassessment.proto
```
This command needs to be executed in the root folder of the repository. 

I did not find a good way (yet) to generate up-to-date protobuf files during package installation.

## Assessing images by running the client and server
After setting up a Python environment containing the dependencies, the assessment server can be run by executing
```bash
python -m imageassessmentservice.server
```
The server will listen on port 50051 by default. The client can be run by executing
```bash
python -m imageassessmentservice.client images_source_folder ratings_target_file_path server_address
```
Here, `images_source_folder` is the folder containing the images to assess, `ratings_target_file_path` will contain the
ratings for all images and `server_address` is the IP address of the server where `imageassessment.server` is running.

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
* Images are assessed relative to each other -- the assessment results may be better when assessing larger amounts of 
    images
* Data is (currently) transferred between service and client without encryption