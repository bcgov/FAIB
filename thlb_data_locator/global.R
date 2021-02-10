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

js_code <- "
shinyjs.openURL = function(url) {
  window.open(url,'_blank');
}
"

##Data objects
tsa_sp <- st_transform(st_read("www//tsa_2_1.gdb","tsa_sp_simp_1000_diss" ),4326)

#   
#----------------
#Non-Spatial 
tsaBnds <- sort(as.vector(as.data.frame(tsa_sp)$tsa_number_description))


