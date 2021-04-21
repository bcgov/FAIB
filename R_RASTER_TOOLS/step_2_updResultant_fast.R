library(raster)
library(fasterize)
library(sf)
library(RPostgreSQL)
library(raster)
library(data.table)
library(fs)
library(ggplot2)
require(scales)
require(ggpubr)
library(data.table)
library(ETLUtils)
library(rgdal)
library(keyring)
# 
idir <- key_get('username', keyring = 'oracle')
orapass <- key_get('password', keyring = 'oracle')
orcleSrcGdal <- paste0('OCI:"',idir, '/',orapass,'@(DESCRIPTION = (ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(HOST = BCGW.BCGOV)(PORT = 1521)))(CONNECT_DATA = (SERVICE_NAME=IDWPROD1.BCGOV)))"')
oraTblNameGdal <- function(tableName){
  return( paste0('OCI:"',idir, '/',orapass,'@(DESCRIPTION = (ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(HOST = BCGW.BCGOV)(PORT = 1521)))(CONNECT_DATA = (SERVICE_NAME=IDWPROD1.BCGOV))):', tableName, '"')
  )}

writeTable<-function(dataFrame,psTabName, fldTypes){
  conn<-dbConnect(dbDriver("PostgreSQL"),
                  host = key_get('dbhost', keyring = 'localpsql'),
                  user = key_get('dbuser', keyring = 'localpsql'),
                  dbname = 'prov_data',
                  password = key_get('dbpass', keyring = 'localpsql'),
                  port = "5432"
  )
  on.exit(dbDisconnect(conn))
  dbWriteTable(conn,psTabName, dataFrame, field.types = fldTypes, overwrite = T, row.names = FALSE)
}

getTableQueryPsql<-function(sql){
  conn<-dbConnect(dbDriver("PostgreSQL"),
                  host = key_get('dbhost', keyring = 'localpsql'),
                  user = key_get('dbuser', keyring = 'localpsql'),
                  dbname = 'prov_data',
                  password = key_get('dbpass', keyring = 'localpsql'),
                  port = "5432"
  )
  on.exit(dbDisconnect(conn))
  dbGetQuery(conn, sql)}

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

copyTblToPG <- function(inDT, tblName, fieldTypes){
  stmt <- paste("drop table if exists", tblName, ";")
  print(stmt)
  sendSQLstatement(stmt)
  writeTable(inDT,tblName, fieldTypes) 
  
}

polygonizeToPG <- function(inRas, dbName, outLyrName,outField){
  pgConn <-  paste0('-f PostgreSQL PG:dbname=', dbName)
  gdal_poly <- Sys.which('gdal_polygonize.py')
  if(gdal_poly=='') stop('gdal_polygonize.py not found on system.')
  system2('python',args=c(gdal_poly,
                          inRas,
                          pgConn,
                          outLyrName,
                          outField), wait = TRUE,stderr = TRUE)
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
  print(paste('gdal_rasterize',value,proj,extent_str,cellSize,inLyr,src,spc,tifName,where,'-a_nodata 0'))
  print(system2('gdal_rasterize',args=c(value,proj,extent_str,cellSize,inLyr,src,spc,tifName,where,'-a_nodata 0'), stderr = TRUE))
  return(tifName)}

writeNoSpaTbl2PG <- function(src, outTblName, lyr=NULL, where_clause=NULL,pk,srctype,select=NULL ){
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
  if(tolower(srctype) == 'postgres'){
    return(outTblName)
    
  }
  else{
    print('herererere')
    print(system2('ogr2ogr',args=c('-nlt NONE',
                                   '-overwrite',
                                   '-gt 200000',
                                   where,
                                   select,
                                   outName,
                                   '-f PostgreSQL PG:dbname=prov_data',
                                   src,
                                   lyr), stderr = TRUE))}
  
  
  sendSQLstatement(paste0("create index ", outTblName,"_ogc_inx",  " on ", outTblName, "(", pk,");"))
}

rasterAsDT <- function(inRas, colName){
  inRas <- raster(inRas)
  rasDT <- as.data.table(as.data.frame(inRas),rownames= FALSE)
  colnames(rasDT) <- c(colName)
  id <- as.integer(rownames(rasDT))
  rasDT <- cbind(ogc_fid=id, rasDT)
  rasDT <- na.omit(rasDT, cols=colName)
  return(rasDT)
}

joinAttr <- function(tempTbl,nsTbl, pk, attrLst,suffix){
  outTbl <- paste0(tempTbl, "withattr")
  # sendSQLstatement(paste0("ALTER TABLE ",tempTbl, "  ADD PRIMARY KEY (ogc_fid);"))
  print('dropping Index')
  sendSQLstatement(paste0("drop index if exists ", tempTbl,pk, ";"))
  print('Creating Index')
  sendSQLstatement(paste0("create index ", tempTbl,pk,  " on ", tempTbl, "(", pk,");"))
  
  print("dropping table if exists")
  sendSQLstatement(paste0("drop table if exists ", tempTbl, "withAttr;"))
  
  #
  stmt <- paste0("
  create table ", outTbl, " as
  select a.*,", attrLst, "
  from ", tempTbl, " a left outer join ",nsTbl, " b on a.",pk," = b.",pk)
  
  if (is.na(attrLst) |  attrLst== '') {
    stmt <- paste0("
  create table ", outTbl, " as
  select a.* from", tempTbl, ";")
    sendSQLstatement(paste0("alter table ", tempTbl," rename column ", pk, " to ", pk, "_", suffix,";"))
    sendSQLstatement(paste0("alter table ", tempTbl," rename TO ", outTbl,";"))
    return(outTbl)
  }
  
  sendSQLstatement(stmt)
  sendSQLstatement(paste0("create index ", outTbl,"ogc_inx",  " on ", outTbl, "(ogc_fid);"))
  print(paste0("select column_name from information_schema.columns where table_name =", " '", outTbl, "';"))
  
  lyrCols <- getTableQueryPsql(paste0(" select column_name
                              from information_schema.columns 
                              where table_name =", " '", outTbl, "';"))
  lyrCol <- as.vector(lyrCols['column_name'])
  lyrCol <- lyrCol[ lyrCol != 'ogc_fid']
  lyrCol <- lyrCol[ lyrCol != pk]
  print(lyrCol)
  
  for (val in lyrCol){
    val2 <- paste0(val,"_", suffix )
    sendSQLstatement(paste0("alter table ", outTbl," rename column ", val, " to ", val2 , ";"))
  }
  print(lyrCol)
  
  sendSQLstatement(paste0("alter table ", outTbl," rename column ", pk, " to ", pk, "_", suffix,";"))
  sendSQLstatement(paste0("ALTER TABLE ",outTbl, "  ADD PRIMARY KEY (ogc_fid);"))
  print("GOT HERE CHECK")
  
  
}





createNewResulant  <- function(layer,pk,suffix){
  pk <- paste0(pk,"_", suffix)
  resCols <- getTableQueryPsql(paste0(" select column_name
                              from information_schema.columns
                              where table_name = 'all_bc_res' and column_name like '%_", suffix,"';"))
  
  print(resCols)
  
  if(is.data.frame(resCols) && nrow(resCols)> 0){
    for (i in 1:length(resCols$column_name)){
      val <- resCols$column_name[i]
      print(val)
      sendSQLstatement(paste0("alter table all_bc_res drop column ", val,";"))
    }
  }
  
  lyrCols <- getTableQueryPsql(paste0(" select column_name
                              from information_schema.columns 
                              where table_name =", " '", layer, "';"))
  lyrCol <- as.vector(lyrCols['column_name'])
  lyrCol <- lyrCol[ lyrCol != 'ogc_fid']
  lyrCol <- lyrCol[ lyrCol != pk]
  print(lyrCol)
  
  str <- paste0("b.",pk,",")
  for (i in seq_along(lyrCol))
  {
    str <- paste0(str,"b.",lyrCol[i], ",")
    
    print( str)
  }
  
  attrstr <- substr(str,1,nchar(str)-1)
  print (attrstr)
  
  sendSQLstatement(paste0("drop table if exists all_bc_res_temp;"))
  
  sendSQLstatement(paste0("create table all_bc_res_temp as
                   select a.*,",attrstr, "
                   from all_bc_res a
                   left outer join  ", layer, " b on a.ogc_fid = b.ogc_fid;"))
  
  sendSQLstatement(paste0("drop table if exists all_bc_res_old cascade;"))
  sendSQLstatement("ALTER TABLE all_bc_res RENAME TO all_bc_res_old;")
  sendSQLstatement("ALTER TABLE all_bc_res_temp RENAME TO all_bc_res;")
  sendSQLstatement("ALTER TABLE all_bc_res ADD PRIMARY KEY (ogc_fid);")
  
  
  
}

updateMetaTbl <- function(metaTbl,srctype,srcpath,srclyr,pk,addAttr,suffix,nsTblm,query ){
  
  query <- gsub("'","''",query)
  print(query)
  
  print(paste0(srcpath, '- 2'))
  print(paste0("DELETE FROM resultant_meta WHERE suffix = '", suffix,"';"))
  sendSQLstatement(paste0("DELETE FROM resultant_meta WHERE suffix = '", suffix,"';"))
  print(paste0("INSERT INTO resultant_meta (srctype, srcpath,srclyr,primarykey,additional_attributes,suffix,tblname,src_query)
                           VALUES ('",srctype,"','", srcpath,"','", srclyr,"','", pk,"','", addAttr,"','", suffix,"','", nsTblm,"','", query, "');"))
  sendSQLstatement(paste0("INSERT INTO resultant_meta (srctype, srcpath,srclyr,primarykey,additional_attributes,suffix,tblname,src_query)
                           VALUES ('",srctype,"','", srcpath,"','", srclyr,"','", pk,"','", addAttr,"','", suffix,"','", nsTblm,"','", query, "');"))
  
  # sendSQLstatement(paste0('INSERT INTO resultant_meta (srctype, srcpath,srclyr,primarykey,additional_attributes,suffix,tblname,src_query)
  #                         VALUES ('",srctype,"','", srcpath,"','", srclyr,"','", pk,"','", addAttr,"','", suffix,"','", nsTblm,"','", query, "');"))
}



updateFldTable <- function(nsTbl){
  sql <- "CREATE TABLE IF NOT EXISTS all_bc_res_flds (fldname varchar(100),srcTable varchar(100));"
  sendSQLstatement(sql)
  
  pk <- paste0(pk,"_", suffix)
  resCols <- getTableQueryPsql(paste0(" select column_name
                              from information_schema.columns 
                              where table_name = 'all_bc_res' and column_name like '%_", suffix,"';"))
  
  fldCols <- getTableQueryPsql(paste0("select fldname
                              from all_bc_res_flds;"))
  
  
  for (i in 1:nrow(resCols))
  { print(i)
    val <- resCols$column_name[[i]]
    fldCols <- getTableQueryPsql(paste0("select fldname
                              from all_bc_res_flds where fldname = '", val, "';"))
    
    if(is.data.frame(fldCols) && nrow(resCols)> 0){
      print(paste0("DELETE FROM all_bc_res_flds where fldname = '", val, "';"))
      sendSQLstatement(paste0("DELETE FROM all_bc_res_flds where fldname = '", val, "';"))
    }
    print(paste0("INSERT INTO all_bc_res_flds(fldname, srcTable) VALUES ('",val,"','",nsTbl,"');"))
    sendSQLstatement(paste0("INSERT INTO all_bc_res_flds(fldname, srcTable) VALUES ('",val,"','",nsTbl,"');"))
  }
}

rasToRows <- function(outLyrName,inRas,outField){
  qry <- "
DROP FUNCTION IF EXISTS TILED_RASTER_TO_ROWS;
CREATE OR REPLACE FUNCTION TILED_RASTER_TO_ROWS(outTbl VARCHAR, srcRast VARCHAR, templateRast VARCHAR, outFld VARCHAR DEFAULT 'val') RETURNS VARCHAR
AS $$
DECLARE
	qry VARCHAR;
	rast VARCHAR;
	qry2 VARCHAR;
BEGIN
	rast = 'rast';
	EXECUTE 'DROP TABLE IF EXISTS ' || outTbl || ';';
	
	qry = 'CREATE TABLE ' || outTbl || ' AS
with tbl1 as  ( select a.rid as rid, b.rast as rast from  ' || templateRast || ' a, ' || srcRast || ' b
      			WHERE ST_UpperLeftX(a.rast) = ST_UpperLeftX(b.rast) AND ST_UpperLeftY(a.rast) = ST_UpperLeftY(b.rast)
		  		order by a.rid ),
tbl2 as (SELECT rid,ST_Tile(RAST, 1,1) AS RAST FROM tbl1),
tbl3 as (select *, ROW_NUMBER() OVER () AS rid_tile from tbl2),
tbl4 as (select *, ROW_NUMBER() OVER (PARTITION BY rid ORDER BY rid_tile ) AS tile_id from tbl3),
tbl5 as (SELECT RID * 10000 + tile_id as ogc_fid,
		(ST_SummaryStats(rast)).sum AS ' || outFld || '
		from tbl4)
select ogc_fid, ' || outFld || ' from tbl5 where ' || outFld || ' is not null;';

		
	RAISE NOTICE '%', qry;
	EXECUTE qry;
	EXECUTE 'ALTER TABLE '  || outTbl || ' DROP CONSTRAINT IF EXISTS ' || outTbl || '_pkey;';
	EXECUTE 'ALTER TABLE '  || outTbl || ' ADD CONSTRAINT ' || outTbl || '_pkey PRIMARY KEY (ogc_fid);';
	--Create an index on the output raster
	EXECUTE 'DROP INDEX IF EXISTS IDX_' || outTbl || '_geom;';
	EXECUTE 'CREATE INDEX IDX_' || outTbl || '_geom ON ' || outTbl || '(OGC_FID);';
	RETURN outTbl;
END;
$$ LANGUAGE plpgsql;"
  sendSQLstatement(qry)
  qry2 <- paste0("SELECT TILED_RASTER_TO_ROWS('", outLyrName,"', '",inRas,"', 'grskey_bc_land','",outField,"')")
  print(qry2)
  sendSQLstatement(qry2)
  
}

#set working directed
setwd('D:/Projects/provDataProject')

# ####EXTENT#########################
dsn = "PG:dbname='prov_data' port=5432 host=localhost table='grskey_bc_land' mode=2"
ras <- readGDAL(dsn) # Get your file as SpatialGridDataFrame
ras2 <- raster(ras,1) # Convert the first Band to Raster
cropExtent <- extent(ras2) 
## if file disapears than the extent is
##xmin       : 273287.5
##xmax       : 1870587.5
##ymin       : 367787.5
##ymax       : 1735787.5
##############################################################################################
# inFile <- read.csv('W:\\FOR\\VIC\\HTS\\DAM\\WorkArea\\DATA\\OLD_GROWTH_2020\\prov_data_resultant.csv',stringsAsFactors=FALSE)
inFile <- read.csv('D:\\Projects\\provDataProject\\Tools\\prov_data_resultant_vri.csv',stringsAsFactors=FALSE)
for (row in 1:nrow(inFile)) {
  
  #Get inputs from input file
  inc <- gsub("[[:space:]]",'',tolower(inFile[row, "inc"])) ## Added inc field to csv,  1 = include(i.e. will not skip) 0 = not included (i.e. will skip)
  srctype <- gsub("[[:space:]]",'',tolower(inFile[row, "srctype"]))
  srcpath <- gsub("[[:space:]]",'',tolower(inFile[row, "srcpath"]))
  srclyr <- gsub("[[:space:]]",'',tolower(inFile[row, "srclyr"]))
  pk <- gsub("[[:space:]]",'',tolower(inFile[row, "primarykey"]))
  addAttr <- gsub("[[:space:]]",'',tolower(inFile[row, "additional_attributes"]))
  suffix <- gsub("[[:space:]]",'',tolower(inFile[row, "suffix"]))
  nsTblm <- gsub("[[:space:]]",'',tolower(inFile[row, "tblname"]))
  query <- tolower(inFile[row, "src_query"])
  if(tolower(inFile[row, "srcpath"])  == 'bcgw'){
    srcpath <- oraTblNameGdal(tolower(inFile[row, "srclyr"]))}
  if (query == '' || is.null(query) || is.na(query)) {
    # print("null is here")
    where_clause <- NULL
  }
  else {where_clause <- inFile[row, "src_query"]}
  
  if (inc == 1){
  
  if(tolower(srctype) != 'raster'){
    #Write none spatial table to postgres
    writeNoSpaTbl2PG(srcpath, nsTblm,srclyr,where_clause = where_clause,pk,srctype)
    print("wrote non spatial to postgres")
    
    #Create tif from input
    inRas <- createTIF(pk,srcpath, srclyr, cropExtent, where_clause = where_clause,outName =nsTblm)
    print("created Tiff")
    
    #Tif to PG Raster
    inRasNoTif <- paste0('ras_',substr(inRas,1,nchar(inRas)-4))
    print(inRasNoTif)
    cmd<-paste0('raster2pgsql -s 3005 -d -C -r -P -I -M -t 100x100 ',inRas,' ', inRasNoTif,' | psql -d prov_data')
    print(cmd)
    shell(cmd)
    file.remove(inRas)
    
    
  }
  else{ 
  # Crop raster to Extent 
  inRas <- paste0(srclyr,".tif")
  cropRaster(srcpath,cropExtent,inRas )
  print("cropped raster")
  
  #Tif to PG Raster
  inRasNoTif <- paste0('ras_',substr(inRas,1,nchar(inRas)-4))
  print(inRasNoTif)
  cmd<-paste0('raster2pgsql -s 3005 -d -I -C -M -t 100x100 ',inRas,' ', inRasNoTif,' | psql -d prov_data')
  print(cmd)
  shell(cmd)
  
  #Convert Raster to Non spatial table with gr_skey
  joinTbl <- paste0(srclyr, "_temp")
  rasToRows(joinTbl,inRasNoTif ,srclyr)
  
  #Join non spatial table to all_bc_res
  joinTblAttr <- paste0(joinTbl, "withattr")
  sendSQLstatement(paste0("drop table if exists ",joinTblAttr, ";"))
  sendSQLstatement(paste0("ALTER TABLE ",joinTbl ," RENAME TO ",joinTblAttr,";"))
  sendSQLstatement(paste0("alter table ", joinTblAttr," rename column ", srclyr, " to ", srclyr, "_", suffix,";"))
  createNewResulant(joinTblAttr,srclyr,suffix)
  print("created new resultant")
  
  #update meta data
  updateMetaTbl('resultant_meta',srctype,srcpath,srclyr,pk,addAttr,suffix,nsTblm,query )
  print("updated meta data table")
  sendSQLstatement(paste0("drop table if exists ",joinTbl, ";"))
  sendSQLstatement(paste0("drop table if exists ",joinTblAttr, ";"))
  print("deleted excess tables")
  gc()
  next

  }
  
  #Convert Raster to Non spatial table with gr_skey
  joinTbl <- paste0(nsTblm, "_temp")
  rasToRows(joinTbl,inRasNoTif ,pk)
  gc()
  
  #Join non spatial table to all_bc_res
  joinAttr(joinTbl,nsTblm,pk,addAttr,suffix )
  print("added attributes to join temp table")
  joinTblAttr <- paste0(joinTbl, "withattr")
  createNewResulant(joinTblAttr,pk,suffix)
  print("created new resultant")

  #Update Metadata tables
  updateFldTable(nsTblm)

  srcpath <- gsub("[[:space:]]",'',tolower(inFile[row, "srcpath"]))
  print('srcpath - 1')
  updateMetaTbl('resultant_meta',srctype,srcpath,srclyr,pk,addAttr,suffix,nsTblm,query )
  print("updated meta data table")

  sendSQLstatement(paste0("drop table if exists ",joinTbl, ";"))
  sendSQLstatement(paste0("drop table if exists ",joinTblAttr, ";"))
  print("deleted excess tables")
  gc()
  

}}


print(file.info('W:\\FOR\\VIC\\HTS\\DAM\\WorkArea\\Mcdougall\\Data\\Resultant_1.gdb')$ctime)
