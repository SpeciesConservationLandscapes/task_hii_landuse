#!/bin/bash

docker run -it -v $PWD/.config:/root/.config scl3/task_hii_landuse python hii_landuse.py -r 'Afrotropic'
docker run -it -v $PWD/.config:/root/.config scl3/task_hii_landuse python hii_landuse.py -r 'Australasia'
docker run -it -v $PWD/.config:/root/.config scl3/task_hii_landuse python hii_landuse.py -r 'Indomalayan'
docker run -it -v $PWD/.config:/root/.config scl3/task_hii_landuse python hii_landuse.py -r 'Nearctic'
docker run -it -v $PWD/.config:/root/.config scl3/task_hii_landuse python hii_landuse.py -r 'Neotropic'
docker run -it -v $PWD/.config:/root/.config scl3/task_hii_landuse python hii_landuse.py -r 'Oceania'
docker run -it -v $PWD/.config:/root/.config scl3/task_hii_landuse python hii_landuse.py -r 'Palearctic'
docker run -it -v $PWD/.config:/root/.config scl3/task_hii_landuse python hii_landuse.py -r 'HighArctic'
