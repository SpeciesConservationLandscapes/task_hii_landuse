import argparse
import ee
from task_base import HIITask


class HIILanduse(HIITask):
    POPULATION_DENSITY_THRESHOLD = 1
    inputs = {
        "esacci": {
            "ee_type": HIITask.IMAGECOLLECTION,
            "ee_path": "ESA-CCI-LC-L4-LCCS",
            "maxage": 1,
        },
        "watermask": {
            "ee_type": HIITask.IMAGE,
            "ee_path": "projects/HII/v1/source/phys/watermask_jrc70_cciocean",
            "static": True,
        },
    }

    landuse_weighting = {
        "altered_landcover": [
            {"lc_category": "Cropland, rainfed", "lc_class": 10, "weight": 7,},
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
                "lc_category": "Cropland, irrigated or post-flooding",
                "lc_class": 20,
                "weight": 8,
            },
            {
                "lc_category": "Mosaic cropland (>50%) / natural vegetation (tree, shrub, herbaceous cover) (<50%)",
                "lc_class": 30,
                "weight": 6,
            },
            {"lc_category": "Urban areas", "lc_class": 190, "weight": 10,},
        ],
        "natural_landcover": [
            {
                "lc_category": "Mosaic natural vegetation (tree, shrub, herbaceous cover) (>50%) / cropland (<50%)",
                "lc_class": 40,
                "weight": 4,
            },
            {
                "lc_category": "Tree cover, broadleaved, evergreen, closed to open (>15%)",
                "lc_class": 50,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, broadleaved, deciduous, closed to open (>15%)",
                "lc_class": 60,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, broadleaved, deciduous, closed (>40%)",
                "lc_class": 61,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, broadleaved, deciduous, open (15‐40%)",
                "lc_class": 62,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, needleleaved, evergreen, closed to open (>15%)",
                "lc_class": 70,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, needleleaved, evergreen, closed (>40%)",
                "lc_class": 71,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, needleleaved, evergreen, open (15‐40%)",
                "lc_class": 72,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, needleleaved, deciduous, closed to open (>15%)",
                "lc_class": 80,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, needleleaved, deciduous, closed (>40%)",
                "lc_class": 81,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, needleleaved, deciduous, open (15‐40%)",
                "lc_class": 82,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, mixed leaf type (broadleaved and needleleaved)",
                "lc_class": 90,
                "weight": 0,
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
            {"lc_category": "Shrubland", "lc_class": 120, "weight": 4,},
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
            {"lc_category": "Grassland", "lc_class": 130, "weight": 4,},
            {"lc_category": "Lichens and mosses", "lc_class": 140, "weight": 0,},
            {
                "lc_category": "Sparse vegetation (tree, shrub, herbaceous cover) (<15%)",
                "lc_class": 150,
                "weight": 0,
            },
            {"lc_category": "Sparse tree (<15%)", "lc_class": 151, "weight": 0,},
            {"lc_category": "Sparse shrub (<15%)", "lc_class": 152, "weight": 0,},
            {
                "lc_category": "Sparse herbaceous cover (<15%)",
                "lc_class": 153,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, flooded, fresh or brakish water",
                "lc_class": 160,
                "weight": 0,
            },
            {
                "lc_category": "Tree cover, flooded, saline water",
                "lc_class": 170,
                "weight": 0,
            },
            {
                "lc_category": "Shrub or herbaceous cover, flooded, fresh/saline/brakish water",
                "lc_class": 180,
                "weight": 0,
            },
            {"lc_category": "Bare areas", "lc_class": 200, "weight": 4,},
            {"lc_category": "Consolidated bare areas", "lc_class": 201, "weight": 0,},
            {"lc_category": "Unconsolidated bare areas", "lc_class": 202, "weight": 0,},
            {"lc_category": "Water bodies", "lc_class": 210, "weight": 4,},
            {"lc_category": "Permanent snow and ice", "lc_class": 220, "weight": 0,},
        ],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.esacci, _ = self.get_most_recent_image(
            ee.ImageCollection(self.inputs["esacci"]["ee_path"])
        )
        self.watermask = ee.Image(self.inputs["watermask"]["ee_path"])

    def calc(self):
        pod_dens_threshold = self.population_density.gte(
            self.POPULATION_DENSITY_THRESHOLD
        )

        altered_from, altered_to = zip(
            *[
                (i["lc_class"], i["weight"])
                for i in self.landuse_weighting["altered_landcover"]
            ]
        )
        natural_from, natural_to = zip(
            *[
                (i["lc_class"], i["weight"])
                for i in self.landuse_weighting["natural_landcover"]
            ]
        )

        altered_lc_weighted = self.esacci.remap(altered_from, altered_to).rename(
            "altered"
        )
        natural_lc_weighted = (
            self.esacci.remap(natural_from, natural_to)
            .multiply(pod_dens_threshold)
            .rename("altered")
        )

        hii_landuse_driver = (
            altered_lc_weighted.addBands(natural_lc_weighted)
            .reduce(ee.Reducer.max())
            .unmask(0)
            .updateMask(self.watermask)
            .multiply(100)
            .int()
            .rename("hii_landuse_driver")
        )

        self.export_image_ee(
            hii_landuse_driver, f"driver/land_use",
        )

    def check_inputs(self):
        super().check_inputs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--taskdate")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite existing outputs instead of incrementing",
    )
    options = parser.parse_args()
    landuse_task = HIILanduse(**vars(options))
    landuse_task.run()
