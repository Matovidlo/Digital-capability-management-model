# Digital capability managment model (DCMM)
This project is built on top of the knowledge gathered from the book Digital capability management model.
The goal is to create Information system (IS) that gathers from various sources (e.g Github, Jira etc.) information about company current development status.
After retrieving relevant information from these sources the information system allows users to show different metrics and visualisations.
These visualisations helps the company to understand their strong and weak sides and where they should put more focus.
The main problem in past was that higher management does not understand the development life cycle of software/hardware product.
So, if we asked anyone from management what IT is doing not a single person was able to respond correctly.
This is due to missing knowledge and awareness of the company solutions.
## Installation
The installation can be either done with help of creating docker containers that
automatically executes the application.

`docker-compose up -d`

`docker-compose exec mongo python3 /home/insert_model.py`

In web browser there is accessible ip address on localhost with web server where results of the process could be found.

`http://localhost:8000`

In case of executing the program on live system there needs to be installed 
python3 and pip. After installation, install all the python requirements

`pip3 install -r requirements.txt`

After installation the software executes in following steps:
- Execute `python3 src/dataset_prepation.py` which executes creation of machine learning model used for automatic detection of DCMM entities.
- Execute `docker-compose run --rm mongo` in order to create mongodb service. 
  In case of provinding own mongodb execute `python3 insert_model.py`.
- Now model in is NoSQL mongo database, execute the program itself has both CLI and GUI. CLI is executed with own options as follow `python3 src/classifcation_scheduler.py`.
- Django migration database
- When you do not want to work with CLI, run django server, `python3 django-web/manage.py`.
## Configuration
In order to be able to execute particular things there are two possibilities.
First one is that the task is executed on website which executes external docker container rutine.
When the repository is big or too many issues are present inside the repository
the execution of program takes time.

## Configuration constants
The program contains python script of different constants that user can adjust based on the problem that is solving.
The file can be found in `src/constants.py`