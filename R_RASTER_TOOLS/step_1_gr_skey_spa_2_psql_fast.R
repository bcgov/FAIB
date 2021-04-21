library(raster)
library(sf)
library(RPostgreSQL)
library(raster)
library(keyring)
#

writeTable<-function(dataFrame,psTabName, fldTypes){
  conn<-dbConnect(dbDriver("PostgreSQL"),
                  host = key_get('dbhost', keyring = 'localpsql'),
                  user = key_get('dbuser', keyring = 'localpsql'),
                  dbname = 'prov_data',
                  password = key_get('dbpass', keyring = 'localpsql'),
                  port = "5432"
                  )
  on.exit(dbDisconnect(conn))
  dbWriteTable(conn,psTabName, dataFrame, field.types = fldTypes, overwrite = T)}

sendSQLstatement<-function(sql){
  conn<-dbConnect(dbDriver("PostgreSQL"),
                  host = key_get('dbhost', keyring = 'localpsql'),
                  user = key_get('dbuser', keyring = 'localpsql'),
                  dbname = 'prov_data',
                  password = key_get('dbpass', keyring = 'localpsql'),
                  port = "5432"
  )
  on.exit(dbDisconnect(conn))
  dbExecute(conn, statement = sql)
}

getExtent<-function(inSF, snapRaster){
  extent <- alignExtent(extent(inSF),snapRaster,snap='out' )
  return(extent)
}

cropRaster <- function(inTif, cropExtent,outTif){
  extent_str <- paste("-te", cropExtent[1], cropExtent[3], cropExtent[2], cropExtent[4] )
  res <- "-tr 100 100"
  print(extent_str)
  overwrite <- "-overwrite"
  system2('gdalwarp', args= c(extent_str,inTif,outTif, res,overwrite), stderr = TRUE)

}

writeSpaTbl2PG <- function(src, outTblName, lyr=NULL, where_clause=NULL,pk,srctype=NULL,select=NULL ){
  outName <- paste('-nln', outTblName)
  select <-''
  if( !is.null(select)){
    select <- sprintf('-select "%s"', select)
  }

  where <- ''
  if( !is.null(where_clause)){
    where <- where <- sprintf('-where "%s"', where_clause)
  }
  print(where)

    print('herererere')
    print(system2('ogr2ogr',args=c('-nlt MULTIPOLYGON',
                                   '-a_srs EPSG:3005',
                                   '-overwrite',
                                   '-gt 200000',
                                   where,
                                   select,
                                   outName,
                                   '-f PostgreSQL PG:dbname=prov_data',
                                   src,
                                   lyr), stderr = TRUE))


  sendSQLstatement(paste0("create index ", outTblName,"_ogc_inx",  " on ", outTblName, "(", pk,");"))
}

polygonizeinPG <- function(inRas,outLyrName,outField){
qry <- "
DROP FUNCTION IF EXISTS POLYGONIZE_TILED_RASTER;
CREATE OR REPLACE FUNCTION POLYGONIZE_TILED_RASTER(outTbl VARCHAR, srcRast VARCHAR, outFld VARCHAR DEFAULT 'val') RETURNS VARCHAR
AS $$
DECLARE
	qry VARCHAR;
	rast VARCHAR;
	qry2 VARCHAR;
BEGIN
	rast = 'rast';
	EXECUTE 'DROP TABLE IF EXISTS ' || outTbl || ';';

	qry = 'CREATE TABLE ' || outTbl || ' AS
with tbl1 as  (SELECT rid,RAST FROM ' || srcRast || '),
tbl2 as (SELECT rid,ST_Tile(RAST, 1,1) AS RAST FROM tbl1),
tbl3 as (select *, ROW_NUMBER() OVER () AS rid_tile from tbl2),
tbl4 as (select *, ROW_NUMBER() OVER (PARTITION BY rid ORDER BY rid_tile ) AS tile_id from tbl3),
tbl5 as (SELECT RID,rid_tile, tile_id, RID * 10000 + tile_id as ogc_fid,
		ST_ConvexHull(rast) AS geom,
		(ST_SummaryStats(rast)).sum AS ' || outFld || '
from tbl4)
select * from tbl5 where ' || outFld || ' is not null;';

	RAISE NOTICE '%', qry;
	EXECUTE qry;
	EXECUTE 'ALTER TABLE '  || outTbl || ' DROP CONSTRAINT IF EXISTS all_bc_gr_skey_pkey;';
	EXECUTE 'ALTER TABLE '  || outTbl || ' ADD CONSTRAINT all_bc_gr_skey_pkey PRIMARY KEY (ogc_fid);';
	--Create an index on the output raster
	EXECUTE 'DROP INDEX IF EXISTS IDX_' || outTbl || '_geom;';
	EXECUTE 'CREATE INDEX IDX_' || outTbl || '_geom ON ' || outTbl || ' USING GIST(geom);';
	RETURN outTbl;
END;
$$ LANGUAGE plpgsql;"
sendSQLstatement(qry)
qry2 <- paste0("SELECT POLYGONIZE_TILED_RASTER('", outLyrName,"', '",inRas,"','",outField,"')")
print(qry2)
sendSQLstatement(qry2)

}


clipPGrastUsingShape <- function(outRas,inRas,clipTbl,clipGeomFld){
  qry <- "
DROP FUNCTION IF EXISTS FAIB_RASTER_CLIP;
CREATE OR REPLACE FUNCTION FAIB_RASTER_CLIP(outRast VARCHAR, srcRast VARCHAR, clipper GEOMETRY) RETURNS VARCHAR
AS $$
DECLARE
	qry VARCHAR;
	rast VARCHAR;
	qry2 VARCHAR;
BEGIN
	rast = 'rast';
	EXECUTE 'DROP TABLE IF EXISTS ' || outRast || ';';

	qry = 'CREATE TABLE ' || outRast || ' AS
	select ROW_NUMBER() OVER () AS RID,a.*
from(
		SELECT ST_Tile(ST_CLIP(ST_TRANSFORM(SRC.RAST, 3005), ST_TRANSFORM($1, 3005)), 100,100,TRUE) AS RAST FROM
		(SELECT ST_UNION(RAST) RAST FROM  ' || srcRast || ' WHERE
		ST_INTERSECTS(ST_TRANSFORM($1, 3005), RAST)) SRC) a ;';
	--RAISE NOTICE '%', qry;
	RAISE NOTICE '%', qry;
	EXECUTE qry USING clipper;
	--Create an index on the output raster
	EXECUTE 'DROP INDEX IF EXISTS IDX_' || outRast || '_RAST;';
	EXECUTE 'CREATE INDEX IDX_' || outRast || '_RAST ON ' || outRast || ' USING GIST (ST_CONVEXHULL(RAST));';
	qry2 =  'SELECT AddRasterConstraints(''' || outRast || '''::name, '''|| rast ||'''::name);';
	RAISE NOTICE '%', qry2;
	EXECUTE qry2;
	RETURN outRast;
END;
$$ LANGUAGE plpgsql;"
  sendSQLstatement(qry)

  qry2 <- paste0("DROP TABLE IF EXISTS ", outRas,";")
  print(qry2)
  sendSQLstatement(qry2)


  clipper <- paste0("(SELECT ",clipGeomFld," FROM ", clipTbl, ")")
  qry3 <- paste0("SELECT FAIB_RASTER_CLIP('", outRas,"', '",inRas,"',", clipper, ");")
  print(qry3)
  sendSQLstatement(qry3)

}



createTIF <- function(pk, src, lyr, extent, where_clause=NULL, outName=NULL){
  value <- paste("-a", pk)
  tifName <- paste0( lyr, pk, ".tif")
  if( !is.null(outName)){
    tifName <- paste0( outName, ".tif")
  }
  
  proj <- "-a_srs EPSG:3005"
  extent_str <- paste("-te", extent[1], extent[3], extent[2], extent[4] )
  cellSize <- "-tr 100 100"
  inLyr <- sprintf('-l %s', lyr)
  where <- ''
  spc <- ' '
  if( !is.null(where_clause)){
    where <- where <- sprintf('-where "%s"', where_clause)
  }
  print(where)
  system2('gdal_rasterize',args=c(value,proj,extent_str,cellSize,inLyr,src,spc,tifName,where,'-a_nodata 0'), stderr = TRUE)
  return(tifName)}



#set working directed
setwd('D:/Projects/provDataProject')

# ####EXTENT#########################
dsn = "PG:dbname='prov_data' port=5432 host=localhost table='grskey_bc_land' mode=2"
ras <- readGDAL(dsn) # Get your file as SpatialGridDataFrame
ras2 <- raster(ras,1) # Convert the first Band to Raster
cropExtent <- extent(ras2)
## if file disapears than the extent is
#cropExtent <- c(273287.5,1870587.5,367787.5,1735787.5)
##xmin       : 273287.5
##xmax       : 1870587.5
##ymin       : 367787.5
##ymax       : 1735787.5
##############################################################################################
#
# Create gr_skey tif clipped by BC land data
bclandgdb <- 'W:\\for\\VIC\\HTS\\DAM\\WorkArea\\DATA\\Infrastructure\\BC_BASE_DATA.gdb'
bclandlyr <- 'BC_Lands_and_Islands'
grskeyRas <- 'S:\\FOR\\VIC\\HTS\\ANA\\workarea\\PROVINCIAL\\bc_01ha_gr_skey.tif'
grskeyClipRas <- 'bc_01ha_gr_skey_clip.tif'
outgrskeyRas <- 'bc_01ha_gr_skey_clip_land.tif'
extent_str <- paste("-projwin", cropExtent[1], cropExtent[4], cropExtent[2], cropExtent[3])
cmd <- paste('gdal_translate -a_srs EPSG:3005 -projwin_srs EPSG:3005 ', extent_str, grskeyRas,grskeyClipRas)
shell(cmd)
inRas <- createTIF('included',bclandgdb,bclandlyr, cropExtent)
cmd <-  paste0('gdal_calc.py -A ', inRas, ' -B ',grskeyClipRas, ' --outfile=',outgrskeyRas, ' --calc="A*B"')
shell(cmd)

#GR_SKEY_RASTER to PG
cmd<- paste0('raster2pgsql -s 3005 -d -C -r -P -I -M -t 100x100 ',outgrskeyRas, ' public.grskey_bc_land | psql -d prov_data')
shell(cmd)

#Polygonize
polygonizeinPG('grskey_bc_land','all_bc_gr_skey','gr_skey')

#Create all_bc_res
sendSQLstatement("drop table if exists all_bc_res")
sendSQLstatement("create table all_bc_res as select rid, tile_id,ogc_fid,gr_skey from all_bc_gr_skey ;")
sendSQLstatement("ALTER TABLE all_bc_res ADD CONSTRAINT all_bc_res_pkey PRIMARY KEY (ogc_fid);")
sendSQLstatement("drop index if exists all_bc_res_gr_skey_inx;")
print('Creating Index')
sendSQLstatement(paste0("create index all_bc_res_gr_skey_inx on all_bc_res(gr_skey);"))


