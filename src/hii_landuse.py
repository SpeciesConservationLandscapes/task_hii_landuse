import argparse
import ee
from datetime import datetime, timezone
from task_base import HIITask


class HIILanduse(HIITask):

    ee_rootdir = "projects/HII/v1"
    ee_driverdir = "driver/landuse"
    inputs = {
        "gpw": {
            "ee_type": HIITask.IMAGECOLLECTION,
            "ee_path": f"{ee_rootdir}/misc/gpw_interpolated",
            "maxage": 1,
        },

        "esacci": {
            "ee_type": HIITask.IMAGECOLLECTION,
            "ee_path": "projects/HII/v1/source/lc/ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v207",
            "maxage": 3,
        },
        "watermask": {
            "ee_type": HIITask.IMAGE,
            "ee_path": "projects/HII/v1/source/phys/watermask_jrc70_cciocean",
            "static": True,
        },
    }
    scale = 300
    gpw_cadence = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.realm = kwargs.pop("realm", None)
        self.set_aoi_from_ee('projects/HII/v1/source/realms/' + self.realm)  

    def calc(self):


        gpw, gpw_date = self.get_most_recent_image(ee.ImageCollection(self.inputs["gpw"]["ee_path"]))
        esacci, esacci_date = self.get_most_recent_image(ee.ImageCollection(self.inputs["esacci"]["ee_path"]))
        watermask = ee.Image(self.inputs["watermask"]["ee_path"])
        ee_taskdate = ee.Date(self.taskdate.strftime(self.DATE_FORMAT))


        popdens_oneplus = gpw.gte(1)

        esacci_10 = esacci.eq(10) # Cropland, rainfed
        esacci_11 = esacci.eq(11) # Cropland, rainfed - Herbaceous cover
        esacci_12 = esacci.eq(12) # Cropland, rainfed - Tree or shrub cover
        esacci_20 = esacci.eq(20) # Cropland,irrigated or post‐flooding
        esacci_30 = esacci.eq(30) # Mosaic cropland (>50%) / natural vegetation (tree, shrub, herbaceous cover) (<50%)
        esacci_40 = esacci.eq(40) # Mosaic natural vegetation (tree, shrub, herbaceous cover) (>50%) / cropland (<50%)
        esacci_190 = esacci.eq(190) # Urban areas

        # note that since all of Sumatra is popdens <1 this always applies... maybe increase threshold? 
        esacci_100 = esacci.eq(100).multiply(popdens_oneplus) # Mosaic tree and shrub (>50%) / herbaceous cover (<50%)
        esacci_110 = esacci.eq(110).multiply(popdens_oneplus) # Mosaic herbaceous cover (>50%) / tree and shrub (<50%)
        esacci_120 = esacci.eq(120).multiply(popdens_oneplus) # Shrubland
        esacci_121 = esacci.eq(121).multiply(popdens_oneplus) # Shrubland - Evergreen shrubland
        esacci_122 = esacci.eq(122).multiply(popdens_oneplus) # Shrubland - Deciduous shrubland
        esacci_130 = esacci.eq(130).multiply(popdens_oneplus) # Grassland


        hii_landuse_driver = esacci_10.multiply(7)\
                                .add(esacci_11.multiply(7))\
                                .add(esacci_12.multiply(7))\
                                .add(esacci_20.multiply(8))\
                                .add(esacci_30.multiply(6))\
                                .add(esacci_40.multiply(4))\
                                .add(esacci_190.multiply(10))\
                                .add(esacci_100.multiply(4))\
                                .add(esacci_110.multiply(4))\
                                .add(esacci_120.multiply(4))\
                                .add(esacci_121.multiply(4))\
                                .add(esacci_122.multiply(4))\
                                .add(esacci_130.multiply(4))\
                                .updateMask(watermask)
                                
        self.export_image_ee(
            hii_landuse_driver, "{}/{}".format(self.ee_driverdir, "aois/" + self.realm)
        )

    def check_inputs(self):
        super().check_inputs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--realm", default='Afrotropic')
    parser.add_argument("-d", "--taskdate", default=datetime.now(timezone.utc).date())
    options = parser.parse_args()
    landuse_task = HIILanduse(**vars(options))
    landuse_task.run()
