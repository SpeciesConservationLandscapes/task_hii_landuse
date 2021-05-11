import argparse
import ee
from datetime import datetime, timezone
from task_base import HIITask


class HIILanduse(HIITask):
    scale = 300
    POPULATION_DENSITY_THRESHOLD = 1
    gpw_cadence = 5
    inputs = {
        "esacci": {
            "ee_type": HIITask.IMAGECOLLECTION,
            "ee_path": "projects/HII/v1/source/lc/ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v207",
            "maxage": 3,
        },
        "gpw": {
            "ee_type": HIITask.IMAGECOLLECTION,
            "ee_path": "CIESIN/GPWv411/GPW_Population_Density",
            "maxage": 5,  # years
        },
        "watermask": {
            "ee_type": HIITask.IMAGE,
            "ee_path": "projects/HII/v1/source/phys/watermask_jrc70_cciocean",
            "static": True,
        },
    }

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
        ],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.esacci, _ = self.get_most_recent_image(
            ee.ImageCollection(self.inputs["esacci"]["ee_path"])
        )
        self.gpw = ee.ImageCollection(self.inputs["gpw"]["ee_path"])
        self.watermask = ee.Image(self.inputs["watermask"]["ee_path"])
        self.ee_taskdate = ee.Date(self.taskdate.strftime(self.DATE_FORMAT))

    def gpw_earliest(self):
        return self.gpw.sort("system:time_start").first()

    def gpw_latest(self):
        return self.gpw.sort("system:time_start", False).first()

    def gpw_interpolated(self):
        gpw_prev = self.gpw.filterDate(
            self.ee_taskdate.advance(-self.gpw_cadence, "year"), self.ee_taskdate
        ).first()
        gpw_next = self.gpw.filterDate(
            self.ee_taskdate, self.ee_taskdate.advance(self.gpw_cadence, "year")
        ).first()

        gpw_delta_days = gpw_next.date().difference(gpw_prev.date(), "day")
        taskdate_delta_days = self.ee_taskdate.difference(gpw_prev.date(), "day")

        gpw_diff = gpw_next.subtract(gpw_prev)

        gpw_daily_change = gpw_diff.divide(gpw_delta_days)
        gpw_change = gpw_daily_change.multiply(taskdate_delta_days)

        return gpw_prev.add(gpw_change)

    def calc(self):
        gpw_taskdate = None
        ee_taskdate_millis = self.ee_taskdate.millis()
        gpw_first_date = ee.Date(
            self.gpw.sort("system:time_start").first().get("system:time_start")
        ).millis()
        gpw_last_date = ee.Date(
            self.gpw.sort("system:time_start", False).first().get("system:time_start")
        ).millis()
        start_test = ee_taskdate_millis.lt(gpw_first_date)
        end_test = ee_taskdate_millis.gt(gpw_last_date)
        interpolate_test = start_test.eq(0).And(end_test.eq(0))
        if interpolate_test.getInfo():
            gpw_taskdate = self.gpw_interpolated()
        elif end_test.getInfo():
            gpw_taskdate = self.gpw_latest()
        elif start_test.getInfo():
            gpw_taskdate = self.gpw_earliest()
        else:
            raise Exception("no valid GPW image")

        pod_dens_threshold = gpw_taskdate.gte(self.POPULATION_DENSITY_THRESHOLD)
        altered_from = []
        altered_to = []
        natural_from = []
        natural_to = []

        altered_remap = self.landuse_weighting["altered_landcover"]
        natural_remap = self.landuse_weighting["natural_landcover"]

        for i in altered_remap:
            altered_from.append(i["lc_class"])
            altered_to.append(i["weight"])

        for i in natural_remap:
            natural_from.append(i["lc_class"])
            natural_to.append(i["weight"])

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
            .muliplty(100)
            .int()
            .rename("hii_landuse_driver")
        )

        self.export_image_ee(
            hii_landuse_driver,
            f"driver/land_use",
        )

    def check_inputs(self):
        super().check_inputs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--taskdate", default=datetime.now(timezone.utc).date())
    options = parser.parse_args()
    landuse_task = HIILanduse(**vars(options))
    landuse_task.run()
