# How to filter Sketch Map Tool results in QGIS

We have uploaded two sketch maps together, both containing markings in blue and red. To 
avoid that users have to handle a lot of files in case of simultaneously uploaded sketch 
maps and sketch maps with markings in different colours, the Sketch Map Tool only provides 
a single output file (GeoJSON) for the vector data.

The marked sketch maps that have been uploaded look as follows:  
<img src="img/sketchmap1.jpg" width="500" alt="Sketch Map 1">
<img src="img/sketchmap2.jpg" width="500" alt="Sketch Map 2">

We want to use [QGIS](https://www.qgis.org/) to inspect the results for different sketch 
maps and different colours separately.

## 1. Import results
* Open QGIS and start a new project (`Project` -> `New`)
* Create a new vector layer (`Layer` -> `Add Layer` -> `Add Vector Layer`)
* Select under `Source` the GeoJSON (`vector-results.geojson`) you downloaded from the Sketch Map Tool
* Click on `Add` to add the new vector layer to your project

Our project now looks like this, we see all markings:  
![QGIS Screenshot](img/qgis1.jpg)

## 2. Filter by colour
Now we want to either see only red or blue markings.
* Right-Click on the layer in the layer view on the left (`vector-results`) and click on `Filter`
* Either paste the following filter expression directly in the field `Provider Specific Filter Expression`:
  ```
  "color" = 'blue'
  ```
  for all blue markings or
  ```
  "color" = 'red'
  ```
  for all red markings.
* Or: Build the filter expression by first double-clicking on `color` under `Fields`, then clicking on `=` under 
  `Operators`, and then after selecting `color` under `Fields` and clicking on `All` under `Values` double-clicking on
  `red` or `blue`, depending on which colour you want to select. Now the field under `Provider Specific Filter Expression`
  should contain the same expression as above.
* Then click `OK` to apply the filter.

Before clicking `OK`, the query builder looks like this:
![QGIS Screenshot](img/qgis2.jpg)

After applying the filter for blue markings, our project looks as follows:
![QGIS Screenshot](img/qgis3.jpg)

## 3. Filter by sketch map
To filter by sketch map, follow the same steps as under *2. Filter by colour*. Only this time the relevant field is 
`name` instead of `color` and the possible values are the filenames under which you uploaded the sketch maps. Therefore,
the filter expression looks like this:
```
"name" = 'your_filename.jpg'
```
As above, all possible values can be obtained by (when not having applied any filter before) selecting `name` under 
`Fields` and then clicking on `All` under `Values`, which shows a list of all names.

**Note**: If you already applied a filter that you want to undo, simply open the filter window again and either click on 
`Clear` or delete the query under `Provider Specific Filter Expression` and click `Ok`.  

## 4. Filter by colour and sketch map
To filter by colour and sketch map, you can combine multiple conditions in the filter expression by using `AND`:
```
"color" = 'blue' AND "name" = 'sketchmap1.jpg'
```

## 5. Advanced filtering
You can of course also use other operators shown in the filter window to compose more complex filter expressions, e.g.
```
"color" != 'blue' AND ("name" = 'sketchmap1.jpg' OR "name" = 'sketchmap2.jpg')
```

## 5. Export filtered layer
To export your filtered layer, e.g. all markings in only one colour, you proceed as follows:
* Right-click on the layer in the layer view on the left
* Hover over `Export` -> Click on `Save features as`
* Select the format you wish, e.g. `GeoJSON`, select a file path and name
* Click `Ok`