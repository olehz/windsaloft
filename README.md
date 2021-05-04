# windsaloft

Convert a vectorial raster field into streamlines. The output is in a convenient GeoJSON format.


USAGE
=====

To create the streamlines, a vectorial field is needed:


	import numpy as np
	import geojson
	import pygrib
	import windsaloft

	grib = pygrib.open('data.grib2')

U/V Components

	u = grib.select(shortName='u')[0].values
	v = grib.select(shortName='v')[0].values

Convert GRIBs data to "standard" -180 to 180 extent global grids

	u = np.concatenate((u, u[:, :1]), axis=1)
	v = np.concatenate((v, v[:, :1]), axis=1)

Calculate streams

	feature_collection = windsaloft.jetstreams(u, v, pixel_dist=5, min_value=10, smooth=2, zigzag_degrees=45)

Write output to a file

	with open('streams.geojson', 'w') as fileout:
	    geojson.dump(feature_collection, fileout, sort_keys=True, separators=(',', ':'))