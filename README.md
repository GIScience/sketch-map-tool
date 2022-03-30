# Prototype release of the Sketch Map Tool
*Note: The sketch map generation and upload processing parts of the tool are not yet ready, but will follow in the 
coming weeks. For the moment you can already use the analyses part.*

Welcome to this repository containing the code of a prototype of the Sketch Map Tool.  
  
While we are working on a more polished and advanced version (including additional features, a better design, 
translations and a cleaner code base, tests for all features), we want to give you the opportunity to already use the 
core features of the Sketch Map Tool and build your own projects based on it. Therefore, we published this prototype 
version. Feel free to use it as permitted by the [GNU Affero General Public License v3.0](LICENSE). This license only
covers the Sketch Map Tool code and original resources, other parts might be licensed differently. You are, for example,
not allowed to use the included logos in any way without permission of the respective owner.
  
If you use this tool or parts of it for scientific purposes, please cite the paper in which the tool
was originally presented:  
> Klonner, C.; Hartmann, M.; Dischl, R.; Djami, L.; Anderson, L.; Raifer, M.; Lima-Silva, F.; Castro Degrossi, L.; Zipf, A.; Porto de Albuquerque, J. The Sketch Map Tool Facilitates the Assessment of OpenStreetMap Data for Participatory Mapping. ISPRS Int. J. Geo-Inf. 2021, 10, 130. https://doi.org/10.3390/ijgi10030130 
  
  
## Contents
1. [About the project](#information-about-the-project)
2. [Structure](#structure-of-the-project)
3. [How to install](#how-to-install)
4. [How to contribute](#how-to-contribute)
5. [Funders](#funders)
6. [Possible problems and their solutions](#possible-problems-and-their-solutions)


## Information about the project

This tool has been developed in the 
[Waterproofing Data Project](https://warwick.ac.uk/fac/arts/schoolforcross-facultystudies/igsd/research/waterproofingdata/)
at [GIScience of Heidelberg University](https://www.geog.uni-heidelberg.de/gis/index_en.html) with the support of 
multiple [funders](#funders). 
It was developed to provide a tool that supports the whole workflow of using sketch maps in the field, e.g. for flood 
mapping. This workflow typically consists of three parts:  
* Before a study is conducted, the data on which the maps are based are inspected to assess whether using maps based on
them might cause any problems, e.g. they are outdated or incomplete. In our case the maps are based on [OpenStreetMap](https://www.openstreetmap.org/)
Data  
--> **Analyze OSM data**
* To carry out the actual study, sketch maps need to be printed. This should be possible in small as well as large paper 
formats to allow for group mappings. Thus generating maps in high resolution is necessary.  
--> **Generate sketch maps**
* After participants have marked areas or points of interest on the sketch maps, the maps need to be digitised, 
georeferenced, and the markings need to be detected  
--> **Automatically georeference uploaded sketch maps and detect markings on them**  
  
**For more information about the tool and its origin, you can take a look at the [paper in which it was presented](https://www.mdpi.com/2220-9964/10/3/130)**
## Structure of the project

The tool has been realized as a web application using [Flask](https://flask.palletsprojects.com/), the Jinja templates 
are stored under [templates](templates), the three different main parts are located under [analyses](analyses),
printer (not available yet), and upload_handling (not available yet).

## How to install
### 0. Download the project
Of course, you need to download the project with all of its files first. You can either do so via `git clone`
or simply download everything as a ZIP folder from the repository website and extract this ZIP at a location of your 
choice.

### 1. Installation using Docker
To make the installation more easy, we created a [Dockerfile](Dockerfile) based on which you can build a container 
running the tool. 
#### 1a. Install Docker
If you do not have Docker installed, you can, for example, install it with [Docker Desktop](https://www.docker.com/get-started/).

#### 1b. Build the image
Start your commandline/terminal and go to the directory in which the file `Dockerfile` is stored.  
There, run:
```
docker build -t sketch-map-tool .
```
This might take some time, as all dependencies are downloaded and installed.

#### 1c. Start a container
To actually run the Sketch Map Tool on your localhost, execute the command
```
docker run -p 8000:8080 --name sketch-maps sketch-map-tool
```
After some time you should see the following , if not: Wait a minute and try it again  
```
INFO:waitress:Serving on http://0.0.0.0:8080
```
or something similar. As soon as you see these outputs, the Sketch Map Tool is ready:  
Simply open [localhost:8000](localhost:8000) in a browser of your choice.  
  
When you want to exit the sketch map tool, simply run (in another terminal / cmd window)
```
docker stop sketch-maps
```  
If you want to start the container again, you can do so with  
```
docker start sketch-maps
```
If you want to execute the `run` command again, at first remove the existing container with
```
docker rm sketch-maps
```


## Funders  
![](static/img/logo_fona.png)
![](static/img/logo_bmbf.png)
![](static/img/logo_belmont_forum.png)
![](static/img/logo_norface.png)
![](static/img/logo_drk.png)



## Possible problems and their solutions
If the map is not displayed correctly, please check the browser console whether `leaflet-geoman.min.js` could not be 
loaded. This might be caused by an update changing the hash of the file.  
In this case you need to update the integrity attribute (or of course simply remove it if you want)