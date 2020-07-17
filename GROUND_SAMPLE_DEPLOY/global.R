#-------------------------------------------------------------------------------------------------
# Copyright 2018 Province of British Columbia
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------
# Load packages
#-------------------------------------------------------------------------------------------------
library(shiny)
library(shinyjs)
library(shinydashboard)
library(shinydashboardPlus)
library(leaflet.extras)
library(leaflet)
library(sf)
library(ggplot2)
library(plotly)
library(lwgeom)
library(feather)
library(rgdal)
library(waiter)
library(gt)

#-------------------------------------------------------------------------------------------------
#Functions for retrieving data from the postgres server (vector, raster and tables)
#-------------------------------------------------------------------------------------------------
css_hide_errors <- function() {
  css_add("
.shiny-output-error {visibility: hidden;}
.shiny-output-error:before {visibility: hidden;}
")
}


css_add <- function(x) {
  shiny::tags$head(shiny::tags$style(shiny::HTML(x)))
}

waiter_html <- function(x){
  tagList(waiter::spin_chasing_dots(),
          br2(),
          h3(x))
}

br2 <- function() tagList(br(), br())

getSpatialQueryIaian<-function(sql){
  conn<-dbConnect(dbDriver("PostgreSQL"), host='206.12.91.188', dbname = 'iaian_apps', port='5432' ,user='appuser' ,password='sHcL5w9RTn8ZN3kc')
  on.exit(dbDisconnect(conn))
  st_read(conn, query = sql)
}


getTableQueryIaian<-function(sql){
  conn<-dbConnect(dbDriver("PostgreSQL"), host='206.12.91.188', dbname = 'iaian_apps', port='5432' ,user='appuser' ,password='sHcL5w9RTn8ZN3kc')
  on.exit(dbDisconnect(conn))
  dbGetQuery(conn, sql)
}



myDrawPolygonOptions <- function(allowIntersection = FALSE,
                                 guidelineDistance = 20,
                                 drawError = list(color = "#b00b00", timeout = 2500),
                                 shapeOptions = list(stroke = TRUE, color = '#003366', weight = 3,
                                                     fill = TRUE, fillColor = '#003366', fillOpacity = 0.1,
                                                     clickable = TRUE), metric = TRUE, zIndexOffset = 2000, repeatMode = FALSE, showArea = TRUE)
{
  if (isTRUE(showArea) && isTRUE(allowIntersection)) {
    warning("showArea = TRUE will be ignored because allowIntersection is TRUE")
  }
  
  list(
    allowIntersection = allowIntersection,
    drawError = drawError,
    guidelineDistance = guidelineDistance,
    shapeOptions = shapeOptions,
    metric = metric,
    zIndexOffset = zIndexOffset,
    repeatMode = repeatMode,
    showArea = showArea
  )
}

##Data objects

sp_samplePoints <- st_transform(st_as_sf(read_feather("www//spatial"), coords=c("bcalb_x","bcalb_y"),crs = 3005),4326)
tsa_sp <- st_transform(st_read("www//tsa_bnds_simp200.shp"),4326)
i <- sapply(sp_samplePoints, is.factor)
sp_samplePoints[i] <- lapply(sp_samplePoints[i], as.character)
#   
#----------------
#Non-Spatial 
sampleTypes <-  sort(unique(sp_samplePoints$sampletype))
tsaBnds <- sort(unique(sp_samplePoints$tsa_desc ))
speciesLst <- sort(unique(sp_samplePoints$species_class ))
becLst <- sort(unique(sp_samplePoints$bgc_zone ))
prjdes <- sort(unique(sp_samplePoints$project_design ))

dummyData <- head(subset(as.data.frame(sp_samplePoints), select = c(tot_stand_age, wsvha_liv)),1)
dummyData[,c("tot_stand_age", "wsvha_liv" )] <- 0
