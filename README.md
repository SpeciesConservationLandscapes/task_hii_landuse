HII LAND USE DRIVER
---------------

## What does this task do?

This task calculates the (unitless) "influence" of land use on the terrestrial surface as one of the key
drivers for a combined [Human Influence Index](https://github.com/SpeciesConservationLandscapes/task_hii_weightedsum). "Influence" is a pressure score based on a combination of land use/land cover and population density. Land cover classes associated with human altered land uses are given unique weights representing the human pressure associated with each land use, comparable to the logic followed by [Venter et al. 2016](https://www.nature.com/articles/sdata201667)). Natural land cover classes are only given weights if the population density in a given cell is greater than 0.

The source landcover data are from the [ESA CCI Landcover Dataset](http://www.esa-landcover-cci.org/). The population density cells are from the [Gridded Population of the World (GPW) dataset developed by the Centre for International Earth Science Information Network (CIESIN)](https://sedac.ciesin.columbia.edu/data/collection/gpw-v4). This dataset models the distribution of the global human population on a 5 year cadence beginning in 2000 at a spatial resolution of 30 arc-seconds (~1km).

For any given task date between two available GPW input images, the estimated population density is linearly interpolated to the specific task date. If the task date either precedes or is succeeds the available GPW images, the first or last available GPW image are used respectively. These values are bilinearly interpolated to an ~300m x 300m grid.


```
landuse_weighting = {
      "altered_landcover": [
          {
              "lc_category": "Cropland, rainfed",
              "lc_class": 10,
              "weight": 7,
          },
          {
              "lc_category": "Cropland, rainfed - Herbaceous cover",
              "lc_class": 11,
              "weight": 7,
          },
          {
              "lc_category": "Cropland, rainfed - Tree or shrub cover",
              "lc_class": 12,
              "weight": 7,
          },
          {
              "lc_category": "Mosaic cropland (>50%) / natural vegetation (tree, shrub, herbaceous cover) (<50%)",
              "lc_class": 20,
              "weight": 8,
          },
          {
              "lc_category": "Mosaic natural vegetation (tree, shrub, herbaceous cover) (>50%) / cropland (<50%)",
              "lc_class": 30,
              "weight": 6,
          },
          {
              "lc_category": "Mosaic tree and shrub (>50%) / herbaceous cover (<50%)",
              "lc_class": 100,
              "weight": 4,
          },
          {
              "lc_category": "Mosaic herbaceous cover (>50%) / tree and shrub (<50%)",
              "lc_class": 110,
              "weight": 4,
          },
          {
              "lc_category": "Urban areas",
              "lc_class": 190,
              "weight": 10,
          },
      ],
      "natural_landcover": [
          {
              "lc_category": "Shrubland - Evergreen shrubland",
              "lc_class": 121,
              "weight": 4,
          },
          {
              "lc_category": "Shrubland - Deciduous shrubland",
              "lc_class": 122,
              "weight": 4,
          },
          {
              "lc_category": "Grassland",
              "lc_class": 130,
              "weight": 4,
          },
```

Values are multiplied by 100 and converted to an integer for efficient exporting and storage in the Earth Engine HII Land Use Driver image collection ('projects/HII/v1/driver/land_use').

## Variables and Defaults

### Environment variables
```
SERVICE_ACCOUNT_KEY=<GOOGLE SERVICE ACCOUNT KEY>
```

### Class constants

```
scale = 300
POPULATION_DENSITY_THRESHOLD = 1
```

## Usage

```
/app # python hii_popdens.py --help
usage: task.py [-h] [-d TASKDATE]

optional arguments:
  -h, --help            show this help message and exit
  -d TASKDATE, --taskdate TASKDATE
```
