import argparse
import ee
from datetime import datetime, timezone
from task_base import EETask


class HIILanduse(EETask):
    ee_rootdir = "projects/HII/v1/sumatra_poc"
    ee_driverdir = "driver/landuse"
    inputs = {
        "gpw": {
            "ee_type": EETask.IMAGECOLLECTION,
            "ee_path": f"{ee_rootdir}/misc/gpw_interpolated",
            "maxage": 1,
        },
        # I replaced source in aduncan/ with projects/HII/v1/source/phys and temporarily assigned 1992-01-01 00:00:00
        # TODO: Replace source? How do we calculate beyond 2015? How do we calculate at a resolution < 1 year?
        #  Also this failed with taskdate=2010-01-01 because "Pattern 'b29' did not match any bands"
        "esacci": {
            "ee_type": EETask.IMAGE,
            "ee_path": "projects/HII/v1/source/phys/ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v207",
            "maxage": 30,
        },
        # TODO: assign actual date to this source. I temporarily assigned 1992-01-01 00:00:00.
        "watermask": {
            "ee_type": EETask.IMAGE,
            "ee_path": "projects/HII/v1/source/phys/watermask_jrc70_cciocean",
            "maxage": 30,
        },
    }
    scale = 300
    gpw_cadence = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_aoi_from_ee("{}/sumatra_poc_aoi".format(self.ee_rootdir))

    def calc(self):
        gpw, gpw_date = self.get_most_recent_image(ee.ImageCollection(self.inputs["gpw"]["ee_path"]))
        watermask = ee.Image(self.inputs["watermask"]["ee_path"])
        esacci = ee.Image(self.inputs["esacci"]["ee_path"])
        ee_taskdate = ee.Date(self.taskdate.strftime(self.DATE_FORMAT))
        # TODO: see above -- need a source that will work after 2015
        year = ee_taskdate.get("year")
        if year.getInfo() > 2015:
            year = ee.Number(2015)
        else:
            year = ee.Number(year)

        popdens_oneplus = gpw.gte(1)
        yearband = ee.String("b").cat(year.subtract(1991).format())
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--taskdate", default=datetime.now(timezone.utc).date())
    options = parser.parse_args()
    landuse_task = HIILanduse(**vars(options))
    landuse_task.run()
