#-----------------------
# Define server function
server <- function(input, output, session) {
  onclick("menu", toggleElement(selector = ".navbar"))
  # 
  fb <- (actionButton("fb", "Filter"))
  sp_samplePoints_r <-reactive({

    if( length(input$tsa) > 0){
        spatial <- subset(tsa_sp, tsa_number_description %in% input$tsa)
      if(nrow(spatial) == 0){
        spatial <- NULL}
    }
    
    else {spatial <- NULL}
    
    spatial
  })
  
  

  #--------  
  # Outputs 
  ## render the leaflet map  
  output$map <- renderLeaflet({ 
    m <- leaflet(options = leafletOptions(doubleClickZoom= TRUE, minZoom = 5)) %>% 
      setView(-121.7476, 53.7267, 5) %>%
      setMaxBounds( lng1 = -142 
                    , lat1 = 46 
                    , lng2 = -112
                    , lat2 =  62 ) %>%
    addTiles() %>%
      addPolygons(data = tsa_sp, stroke = TRUE, color = "#3c8dbc", weight = 2,
                  opacity = 0.9, fill = TRUE, fillOpacity = 0.2, group ="TSA Boundaries",
                  popup = paste(sep = "<br/>",
                                paste(paste("<b>TSA Name</b> - ", tsa_sp$tsa_number_description, "<br/>"),
                                      paste("<b>TSA Number</b> - ", tsa_sp$tsa_number_string, "<br/>"),
                                      paste0("<a href = ", tsa_sp$data_link, ">Download ",tsa_sp$tsa_number_description, " THLB</a>")))) %>%
      # addScaleBar(position = "bottomright") %>%
      # addControl(filemap,position="bottomleft") %>%

      mapOptions(zoomToLimits = "always") %>%
       addEasyButton(easyButton(
         icon = 'ion-arrow-shrink',
         title = 'Zoom to Features',
         onClick = JS("function(btn, map) {
       var groupLayer = map.layerManager.getLayerGroup('points');
        map.fitBounds(groupLayer.getBounds());}")
       ))
    # 
    # # Sys.sleep(10)
    # # waiter::waiter_hide()
    # # return(m)

  })
  
#   #-------
  # #OBSERVE
  
  observe({
    if ("Select All" %in% input$tsa) {
      # choose all the choices _except_ "Select All"
      selected_choices <- setdiff(tsaBnds, "Select All")
      updateSelectInput(session, "tsa", selected = selected_choices)
    }
    if ("Clear All" %in% input$tsa || length(input$tsa)==0) {
      # choose all the choices _except_ "Select All"
      selected_choices <- ""
      updateSelectInput(session, "tsa", selected = selected_choices)
    }
    
    })

#   
  observe({
    if ("Select All" %in% input$tsa) {
      # choose all the choices _except_ "Select All"
      selected_choices <- setdiff(tsaBnds, "Select All")
      updateSelectInput(session, "tsa", selected = selected_choices)
    }

    if ("Clear All" %in% input$tsa) {
      # choose all the choices _except_ "Select All"
      selected_choices <- ""
      updateSelectInput(session, "tsa", selected = selected_choices)
    }
    
  })

# 
  # Help for Plots
  spHelpModal = modalDialog(
    title = HTML("<h2><b>Sample Types</b></h2>"),
    easyClose = TRUE,
    fade = FALSE,
    HTML("<h4><b>Provincial Change Monitoring Inventory (CMI) plots:</b></h4>
          Provide statistically-sound, point-in-time and change estimates of vegetation attributes over existing sampled areas of the province with fixed-radius plots located on the 20 km by 20 km NFI grid.

          <h4><b>Provincial Young Stand Monitoring (YSM) plots:</b></h4> Monitor the growth and health of young (15-50 years old) stands using fixed-radius plots located on an intensification of the 20 km by 20 km NFI grid.

    <h4><b>National Forest Inventory (NFI) plots:</b></h4> A stratified subset of CMI plots that have been selected across national Ecozone boundaries and that contribute towards Canada's National Forest Inventory program.
    
    <h4><b>Supplemental Samples (SUP) plots:</b></h4> Samples on a 10*20km grid across the mature population.  

    <h4><b>Permanent Sample Plots (PSP):</b></h4> Subjectively located fixed-area permanent plots, valued for their long-term re-measurement data to support development of growth-and-yield models in unmanaged stands across a range of stand and ecosystem types.  Also referred to as Growth and Yield (GY) plots.

    <h4><b>Vegetation Resource Inventory (VRI) plots:</b></h4> Temporary 5-point cluster plots used to audit and/or adjust photo-interpreted spatial inventory attributes, sampled from area-specific project implementation plans.  Also referred to as VRI-phase II ground plots.<br><br>
    <a href='https://www2.gov.bc.ca/gov/content/industry/forestry/managing-our-forest-resources/forest-inventory/ground-sample-inventories' target=”_blank”>For More Info</a>.")
  )




  observeEvent(input$samplePlotsHelp, {
    showModal(spHelpModal)})
  
  observeEvent(input$tsa, {
    shinyjs::disable(input$tsa)
    proxy <- leafletProxy('map')
    proxy %>%
      clearShapes() %>%
      clearPopups()
    if (!is.null(sp_samplePoints_r())){
      proxy %>%
      addPolygons(data = sp_samplePoints_r(), stroke = TRUE, color = "#3c8dbc", weight = 2,
                    opacity = 0.9, fill = TRUE, fillOpacity = 0.2, group ="TSA Boundaries",
                    popup = paste(sep = "<br/>",
                                  paste(paste("<b>TSA Name</b> - ", tsa_sp$tsa_number_description, "<br/>"),
                                        paste("<b>TSA Number</b> - ", tsa_sp$tsa_number_string, "<br/>"),
                                        paste0("<a href = ", tsa_sp$data_link, ">Download ",tsa_sp$tsa_number_description, " THLB</a>"))))
      
    }
    else{
      proxy %>%
        clearShapes() %>%
        clearPopups()    
    }
    shinyjs::enable(input$fb)
    
  },ignoreNULL  = F)


  observeEvent(input$db, {
    for (i in input$tsa){

      dataLink <- as.vector(subset(tsa_sp, tsa_sp$tsa_number_description == i)$data_link)[1]
      cat(dataLink)
      Sys.sleep(1)
      js$openURL(dataLink)
      Sys.sleep(5)                #Short delay of 1 second

      }

    })


# 


  

  
}


