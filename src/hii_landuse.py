import argparse
import ee
from datetime import datetime, timezone
from task_base import EETask


class HIILanduse(EETask):
    ee_rootdir = "projects/HII/v1/sumatra_poc"
    ee_driverdir = "driver/landuse"
    # if input lives in ee, it should have an "ee_path" pointing to an ImageCollection/FeatureCollection
    inputs = {
        "gpw": {
            "ee_type": EETask.IMAGECOLLECTION,
            "ee_path": "CIESIN/GPWv411/GPW_Population_Density",
            "maxage": 5,  # years
        },
        # TODO: This should be an image collection, and in projects/HII/v1/source/phys
        # TODO: Replace source? How do we calculate beyond 2015?
        "esacci": {
            "ee_type": EETask.IMAGE,
            "ee_path": "users/aduncan/cci/ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v207",
        },
        # TODO: make sure this has a system:start_date or whatever we choose as reliable timestamp
        "watermask": {
            "ee_type": EETask.IMAGE,
            "ee_path": "projects/HII/v1/source/phys/watermask_jrc70_cciocean",
            "maxage": 20,
        },
    }
    scale = 300  # TODO: should this be default of 1000?
    gpw_cadence = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_aoi_from_ee("{}/sumatra_poc_aoi".format(self.ee_rootdir))

    def calc(self):
        gpw = ee.ImageCollection(self.inputs["gpw"]["ee_path"])
        watermask = ee.Image(self.inputs["watermask"]["ee_path"])
        esacci = ee.Image(self.inputs["esacci"]["ee_path"])
        ee_taskdate = ee.Date(self.taskdate.strftime(self.DATE_FORMAT))
        year = ee_taskdate.get("year")

        gpw_prior = gpw.filterDate(
            ee_taskdate.advance(-self.gpw_cadence, "year"), ee_taskdate
        ).first()
        gpw_later = gpw.filterDate(
            ee_taskdate, ee_taskdate.advance(self.gpw_cadence, "year")
        ).first()
        gpw_diff = gpw_later.subtract(gpw_prior)
        numerator = ee_taskdate.difference(gpw_prior.date(), "day")
        gpw_diff_fraction = gpw_diff.multiply(numerator.divide(self.gpw_cadence * 365))
        gpw_taskdate = gpw_prior.add(gpw_diff_fraction)
        gpw_taskdate_300m = gpw_taskdate.resample().reproject(
            crs=self.crs, scale=self.scale
        )

        popdens_oneplus = gpw_taskdate_300m.gte(1)
        yearband = ee.String("b").cat(ee.Number(year).subtract(1991).format())
        # TODO: once esacci is an image collection, use self.get_most_recent_image()
        # TODO: replace hardcoded arguments like multiply(10) with variables
        esacci_oneyear = esacci.select(yearband).multiply(popdens_oneplus.multiply(10))

        esacci_remap_input = [10, 11, 12, 20, 30, 40, 190, 1000, 1100, 1200, 1210, 1220, 1300]
        esacci_remap_output = [7, 7, 7, 8, 6, 4, 10, 4, 4, 4, 4, 4, 4]
        hii_landuse_driver = esacci_oneyear.remap(
            esacci_remap_input, esacci_remap_output, 0
        ).updateMask(watermask)

        self.export_image_ee(
            hii_landuse_driver, "{}/{}".format(self.ee_driverdir, "hii_landuse_driver")
        )

    def check_inputs(self):
        super().check_inputs()
        # add any task-specific checks here, and set self.status = self.FAILED if any fail


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--taskdate", default=datetime.now(timezone.utc).date())
    options = parser.parse_args()
    landuse_task = HIILanduse(**vars(options))
    landuse_task.run()
