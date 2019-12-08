import ee
from task_base import EETask


class HIILanduse(EETask):
    ee_rootdir = "projects/HII/v1/sumatra_poc"
    ee_driverdir = 'driver/landuse'
    # if input lives in ee, it should have an "ee_path" pointing to an ImageCollection/FeatureCollection
    inputs = {
        "jrc": {
            "ee_type": EETask.IMAGE,
            "ee_path": "JRC/GSW1_0/GlobalSurfaceWater"
        },
        "caspian": {
            "ee_type": EETask.IMAGE,
            "ee_path": "users/aduncan/caspian"
        },
        "gpw_2015": {
            "ee_type": EETask.IMAGE,
            "ee_path": "CIESIN/GPWv411/GPW_Population_Density/gpw_v4_population_density_rev11_2015_30_sec"
        },
        "esacci": {
            "ee_type": EETask.IMAGE,
            "ee_path": "users/aduncan/cci/ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v207"
        },
        "ocean": {
            "ee_type": EETask.IMAGE,
            "ee_path": "users/aduncan/cci/ESACCI-LC-L4-WB-Ocean-Map-150m-P13Y-2000-v40",
        }
            }
    

    gpw_cadence = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_aoi_from_ee("{}/sumatra_poc_aoi".format(self.ee_rootdir))



    def calc(self):
        ESACCI = ee.Image(self.inputs['esacci']['ee_path']).select('b24')
        gpw_2015 = ee.Image(self.inputs['gpw_2015']['ee_path'])

        caspian = ee.FeatureCollection(self.inputs['caspian']['ee_path'])

        jrc = ee.Image(self.inputs['jrc']['ee_path'])\
                        .select('occurrence')\
                        .lte(75)\
                        .unmask(1)\
                        .multiply(ee.Image(0).clip(caspian).unmask(1))

        ocean = ee.Image(self.inputs['ocean']['ee_path'])




        gpw_300m = gpw_2015.resample().reproject(crs='EPSG:4326',scale=300)
        popdens_oneplus = gpw_300m.gte(1)

        ESACCI_oneyear_postpopdens = ESACCI.multiply(popdens_oneplus.multiply(10))


        ESACCI_remap_input =  [10,11,12,20,30,40,190,1000,1100,1200,1210,1220,1300]
        ESACCI_remap_output = [ 7, 7, 7, 8, 6, 4, 10,   4,   4,   4,   4,   4,   4]
        ESACCI_remapped = ESACCI_oneyear_postpopdens.remap(ESACCI_remap_input,ESACCI_remap_output,0)\
                                                .updateMask(jrc)\
                                                .updateMask(ocean)
                                          

        self.export_image_ee(ESACCI_remapped, '{}/{}'.format(self.ee_driverdir, 'hii_landuse_driver'))

    def check_inputs(self):
        super().check_inputs()
        # add any task-specific checks here, and set self.status = self.FAILED if any fail


if __name__ == "__main__":
    landuse_task = HIILanduse()
    landuse_task.run()
