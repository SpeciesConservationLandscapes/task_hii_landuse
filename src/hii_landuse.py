import argparse 
import ee
from datetime import datetime, timezone
from task_base import EETask


class HIILanduse(EETask):
    ee_rootdir = "projects/HII/v1/sumatra_poc"
    ee_driverdir = 'driver/landuse'
    # if input lives in ee, it should have an "ee_path" pointing to an ImageCollection/FeatureCollection
    inputs = {
        "gpw": {
            "ee_type": EETask.IMAGECOLLECTION,
            "ee_path": "CIESIN/GPWv411/GPW_Population_Density",
            "maxage": 5  # years
        },
        "esacci": {
            "ee_type": EETask.IMAGE,
            "ee_path": "users/aduncan/cci/ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v207"
        },
        "watermask": {
            "ee_type": EETask.IMAGE,
            "ee_path": "projects/HII/v1/source/phys/watermask_jrc70_cciocean",
        }
            }
    

    gpw_cadence = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_aoi_from_ee("{}/sumatra_poc_aoi".format(self.ee_rootdir))



    def calc(self):

        watermask = ee.Image(self.inputs['watermask']['ee_path'])
        ESACCI = ee.Image(self.inputs['esacci']['ee_path'])
        gpw = ee.ImageCollection(self.inputs['gpw']['ee_path'])

        ee_taskdate = ee.Date(self.taskdate.strftime(self.DATE_FORMAT))
        gpw_prior = gpw.filterDate(ee_taskdate.advance(-self.gpw_cadence, 'year'), ee_taskdate).first()
        gpw_later = gpw.filterDate(ee_taskdate, ee_taskdate.advance(self.gpw_cadence, 'year')).first()
        gpw_diff = gpw_later.subtract(gpw_prior)
        numerator = ee_taskdate.difference(gpw_prior.date(), 'day')
        gpw_diff_fraction = gpw_diff.multiply(numerator.divide(self.gpw_cadence * 365))
        gpw_taskdate = gpw_prior.add(gpw_diff_fraction)
        gpw_taskdate_300m = gpw_taskdate.resample().reproject(crs=self.crs, scale=self.scale)

        popdens_oneplus = gpw_taskdate_300m.gte(1)

        ee_taskdate = ee.Date(self.taskdate.strftime(self.DATE_FORMAT))
        year = ee_taskdate.get('year')
        yearband = ee.String('b').cat(ee.Number(year).subtract(1991).format())

        ESACCI_oneyear = ESACCI.select(yearband).aside(print)

        ESACCI_oneyear_postpopdens = ESACCI_oneyear.multiply(popdens_oneplus.multiply(10))


        ESACCI_remap_input =  [10,11,12,20,30,40,190,1000,1100,1200,1210,1220,1300]
        ESACCI_remap_output = [ 7, 7, 7, 8, 6, 4, 10,   4,   4,   4,   4,   4,   4]
        hii_landuse_driver = ESACCI_oneyear_postpopdens.remap(ESACCI_remap_input,ESACCI_remap_output,0)\
                                                .updateMask(watermask)
                                          

        self.export_image_ee(hii_landuse_driver, '{}/{}'.format(self.ee_driverdir, 'hii_landuse_driver'))

    def check_inputs(self):
        super().check_inputs()
        # add any task-specific checks here, and set self.status = self.FAILED if any fail


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--taskdate', default=datetime.now(timezone.utc).date())
    options = parser.parse_args()
    landuse_task = HIILanduse(**vars(options))
    landuse_task.run()
