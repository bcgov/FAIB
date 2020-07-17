#-----------------------
# Define server function
server <- function(input, output, session) {
  onclick("menu", toggleElement(selector = ".navbar"))
  # 
  filemapBtn <- (actionButton("filemapBtn", "Upload Shapefile"))
  fb <- (actionButton("fb", "Filter"))
  filemap <- div(fileInput(placeholder = "shp,dbf,shx",width = 185 ,inputId = "filemap", label = "Upload Shapefile", multiple = TRUE, accept = c("shp","dbf", "shx", "sbn", "sbx", "prj", "xml")))
  filemap <- absolutePanel(filemap, right = -166, top = -100, fixed = FALSE, width = -200 , height = "100%")

  #----------------  
  # Reactive Values 
   valueModal<-reactiveValues(atTable=NULL)

  #Filter based on drawn value
  sp_from_draw <- function(){
    if(!is.null(input$map_draw_all_features) & !is.null(drawnPolys()) & !is.null(sp_samplePoints_r()) ){
      points <- st_intersection(lwgeom::st_make_valid(st_as_sf(drawnPolys())), sp_samplePoints_r())
      #points <- st_intersection(st_as_sf(drawnPolys()), sp_samplePoints_r())
      if(nrow(points) == 0){
        points <- NULL}
    }
    else { points <- NULL}
    points
  }
  #
  #Filter based on imported shape
  sp_from_imp <- function(){
    if(!is.null(impShp()) & !is.null(sp_samplePoints_r()) ) {
      points <- st_intersection(st_as_sf(impShp()), sp_samplePoints_r())
      if(nrow(points) == 0){
        points <- NULL}
    }
    else { points <- NULL}
    points
  }
  #
  sp_from_imp_and_draw <- function(){

    if(!is.null(sp_from_imp()) & !is.null(sp_from_draw()) & !is.null(sp_samplePoints_r())) {
      poly <- st_union(st_as_sf(drawnPolys()), st_as_sf(impShp()))
      points <- st_intersection(poly, sp_samplePoints_r())

      if(nrow(points) == 0){
        points <- NULL}
    }

    else if(is.null(impShp()) ){

      points <- sp_from_draw()}

    else if(is.null(drawnPolys())){
      points <- sp_from_imp()}

    else { points <- NULL}
    points
  }
  #
  #Filter based on map selection
  sp_samplePoints_r <-reactive({

    if(length(input$cbSType) > 0 & length(input$tsa) > 0 & length(input$species) > 0 & length(input$bec) > 0 & length(input$sts) > 0){
      if(input$prj == 'All'){
      spatial <- subset(sp_samplePoints, sampletype %in% input$cbSType & species_class %in% input$species & tsa_desc %in% input$tsa & bgc_zone %in% input$bec & samp_sts %in% input$sts )}
      if(input$prj == 'YSM Main'){
        spatial <- subset(sp_samplePoints, sampletype %in% input$cbSType & species_class %in% input$species & tsa_desc %in% input$tsa & bgc_zone %in% input$bec & ysm_main %in% "Y" & samp_sts %in% input$sts )}
      if(input$prj == 'Mat Main'){
        spatial <- subset(sp_samplePoints, sampletype %in% input$cbSType & species_class %in% input$species & tsa_desc %in% input$tsa & bgc_zone %in% input$bec & ysm_main %in% "N" & samp_sts %in% input$sts )}
      if(nrow(spatial) == 0){
        spatial <- NULL}
    }

    else {spatial <- NULL}

    spatial
  })
  #

  masterTable <- reactive({
    spatial <- NULL
    selected_groups <- input$map_groups
    drawL <- length(input$map_draw_all_features$features)
    impL <- length(impShp())
    if(input$shapeFilt == "Drawn Polygon") {
      spatial <- sp_from_draw()
    }

    else if(input$shapeFilt == "Shapefile") {
      spatial <- sp_from_imp()}

    else if(input$shapeFilt == "Both") {
      spatial <- sp_from_imp_and_draw()}

    else if(length(input$cbSType) > 0 & length(input$prj) > 0 & length(input$sts) > 0 & length(input$tsa) > 0 & length(input$species) > 0 & length(input$bec) > 0 & !is.null(sp_samplePoints_r())){
      spatial <- sp_samplePoints_r()
    }
    else {spatial <- NULL}
    spatial
  })


  drawnPolys<-reactive({
    if(!is.null(input$map_draw_all_features)){
      f<-input$map_draw_all_features
      if (length(f$features) > 0) {
        #get the lat long coordinates
        coordz<-lapply(f$features, function(x){unlist(x$geometry$coordinates)})
        Longitudes<-lapply(coordz, function(coordz) {coordz[seq(1,length(coordz), 2)] })
        Latitudes<-lapply(coordz, function(coordz)  {coordz[seq(2,length(coordz), 2)] })
        
        polys<-list()
        for (i in 1:length(Longitudes)){
          polys[[i]]<- Polygons(list(Polygon(cbind(Longitudes[[i]], Latitudes[[i]]))), ID=f$features[[i]]$properties$`_leaflet_id` )}
        
        spPolys<-SpatialPolygons(polys)
        proj4string(spPolys)<-"+proj=longlat +datum=WGS84 +no_defs +ellps=WGS84 +towgs84=0,0,0"
        
        #Extract the ID's from spPolys
        pid <- sapply(slot(spPolys, "polygons"), function(x) slot(x, "ID"))
        #create a data.frame
        p.df <- data.frame(ID=pid, row.names = pid)
        SPDF<-SpatialPolygonsDataFrame(spPolys, data=p.df)}
      
      else{
        SPDF<-NULL
      }
      
    }
    
    else{
      SPDF<-NULL
    }
    SPDF
  })
  # # 
  # # 
  #Data to be plotted on age/volume chart. Any record with age < 0 is removed
  noZerosPlotData <- reactive({
    if (!is.null(masterTable())){
      data <- subset(as.data.frame(masterTable()), tot_stand_age > 0)}
    else {
      data <- NULL}
    data
  })
  #
  #Import Shapefile as df
  impShp <- reactive({
    shpValid <- FALSE
    outShp <- NULL
    # shpdf is a data.frame with the name, size, type and datapath of the uploaded files
    if (!is.null(input$filemap)){
      shpValid <- TRUE
      shpdf <- input$filemap
      tempdirname <- dirname(shpdf$datapath[1])
      fileList <- list()
      i <- 1
      for (file in shpdf$datapath) {
        fileExt <- strsplit(file, "\\.")
        fileExt <-fileExt[[1]][length(fileExt[[1]])]
        fileList[[i]] <- fileExt
        i <- i + 1
        if (fileExt %in% c("shp","dbf", "shx", "sbn", "sbx", "prj", "xml"))
        {print ("shp ext is good")}
        else{
          shpValid <- FALSE
          showModal(warningModal)}
      }

      if(!"shp" %in% fileList | !"shp" %in% fileList | !"dbf" %in% fileList | !"shx" %in% fileList )
      { shpValid <- FALSE
      showModal(warningModal)}
      # if("shp" %in% fileList)
      # { print ("yes")}



      if (shpValid){
        # Rename files
        for(i in 1:nrow(shpdf)){
          file.rename(shpdf$datapath[i], paste0(tempdirname, "/", shpdf$name[i]))
        }
        tryCatch(
          {outShp <-  spTransform(readOGR(paste(tempdirname, shpdf$name[grep(pattern = "*.shp$", shpdf$name)], sep = "/")), CRS("+init=epsg:4326"))},
          error=function(cond) {
            shpValid <- FALSE
            showModal(warningModal)
            outShp <- NULL
            message("Here's the original error message:")

          },
          finally ={print ("shape done")}
        )
      }

    }
    if (!shpValid) {
      outShp = NULL

    }
    else{outShp}
    outShp
  })

  getOnclickCoord <- reactive({
    d <- event_data("plotly_click")
    if (is.null(d)) NULL
    else d$key})

  
  #--------  
  # Outputs 
  ## Create scatterplot object the plotOutput function is expecting
  ## set the pallet for mapping
  pal1 <- colorFactor(palette = c( "#e69f00", "#009e73","#f0e442", "#0072b2", '#d55e00', "#cc79a7"),  sp_samplePoints$sampletype)
  ## render the leaflet map  
  output$map <- renderLeaflet({ 
    m <- leaflet(sp_samplePoints, options = leafletOptions(doubleClickZoom= TRUE, minZoom = 5)) %>% 
      setView(-121.7476, 53.7267, 5) %>%
      setMaxBounds( lng1 = -142 
                    , lat1 = 46 
                    , lng2 = -112
                    , lat2 =  62 ) %>%
      addTiles() %>% 
      addProviderTiles("Esri.WorldTopoMap", group = "WorldTopo") %>%
      addProviderTiles("Esri.WorldImagery", group ="WorldImagery" ) %>%
      addCircleMarkers(  data=sp_samplePoints ,
                         radius = 6,
                         group = "points",
                         color = ~pal1(sampletype), 
                         stroke = FALSE, fillOpacity = 1,
                         clusterOptions = markerClusterOptions(disableClusteringAtZoom = 7), 
                         label = sp_samplePoints$samp_id, 
                         popup = paste(sep = "<br/>",
                                       paste(paste("<b>Sample ID</b> - ", sp_samplePoints$samp_id, "<br/>"),
                                             paste("<b>Sample Type</b> - ", sp_samplePoints$sampletype, "<br/>"),
                                             paste("<b>Bec Subzone</b> - ", sp_samplePoints$beclabel, "<br/>"), 
                                             paste("<b>YSM Main</b> - ", sp_samplePoints$ysm_main, "<br/>"),
                                             paste("<b>Last Measured Date</b> - ", sp_samplePoints$meas_dt, "<br/>"), 
                                             paste("<b># of measures</b> - ", sp_samplePoints$no_meas, "<br/>"),
                                             paste("<b>Species label</b> - ", sp_samplePoints$spc_label_live, "<br/>"), 
                                             paste("<b>Density #/ha</b> - ", round(sp_samplePoints$stemsha_liv, digits = 0), "<br/>"), 
                                             paste("<b>Basal area m2/ha</b> - ", round(sp_samplePoints$baha_liv, digits = 0), "<br/>"), 
                                             paste("<b>Total volume m3/ha</b> - ", round(sp_samplePoints$wsvha_liv, digits = 0), "<br/>"), 
                                             paste("<b>Total age yrs </b> - ", round(sp_samplePoints$tot_stand_age, digits = 0), "<br/>")))
      ) %>%
      addPolygons(data = tsa_sp, stroke = TRUE, color = "#3c8dbc", weight = 2,
                  opacity = 0.9, fill = TRUE, fillOpacity = 0.2, group ="TSA Boundaries",
                  popup = tsa_sp$administrative_area_name)%>%
      addScaleBar(position = "bottomright") %>%
      addControl(filemap,position="bottomleft") %>%
      addLegend("bottomright", pal = pal1, values = c("CMI","NFI","PSP","SUP", "VRI","YSM" ), title = "Sample Type", opacity = 1) %>%
    addDrawToolbar(
      editOptions = editToolbarOptions(edit = TRUE, remove = TRUE, selectedPathOptions = NULL,
                                       allowIntersection = FALSE),
      targetGroup='Drawn',
      polylineOptions = FALSE,
      circleOptions = FALSE,
      circleMarkerOptions = FALSE,
      rectangleOptions = FALSE,
      markerOptions = FALSE,
      singleFeature = FALSE,
      polygonOptions = myDrawPolygonOptions()) %>%
      
      
      addLayersControl(baseGroups = c("WorldTopo","WorldImagery"), overlayGroups = c('TSA Boundaries'), options = layersControlOptions(collapsed = FALSE)) %>%
      hideGroup(c('TSA Boundaries')) %>%
      mapOptions(zoomToLimits = "always")  %>%
       addEasyButton(easyButton(
         icon = 'ion-arrow-shrink',
         title = 'Zoom to Features',
         onClick = JS("function(btn, map) { 
       var groupLayer = map.layerManager.getLayerGroup('points');
        map.fitBounds(groupLayer.getBounds());}")  
       ))
    
    Sys.sleep(10)
    waiter::waiter_hide()
    return(m)

  })
  
  
  plotData <- function(data){
    output$age <- renderPlotly({
      if (!is.null(data)){

        key <- data$objectid

        p <- plot_ly(data,
                     x = data$tot_stand_age,
                     y = data$wsvha_liv,
                     color = factor(data$sampletype, levels = c("CMI","NFI","PSP","SUP", "VRI","YSM")),
                     colors = c( "#e69f00", "#009e73","#f0e442", "#0072b2", '#d55e00', "#cc79a7"),
                     hoverinfo = 'text',
                     text = data$sampletype,
                     key = ~key ,
                     type = "scatter",
                     mode = "markers")

        # ggplotly(p) %>%
        p %>%
          layout(  autosize=TRUE, dragmode = 'lasso', xaxis = (list(autorange = TRUE, title = "Age", automargin = TRUE)),
                   legend = list(orientation = 'h',  y = 100), margin = list(r = 20, b = 50, t = 50, pad = 4),
                   yaxis = (list(title = "Volume (m3)")))%>%
          config(displayModeBar = F)}

      else{


        p <- plot_ly(dummyData, x = dummyData$tot_stand_age,
                     y = dummyData$wsvha_liv,
                     type = "scatter",
                     mode = "markers") %>%
          layout(  autosize=TRUE, dragmode = 'lasso', xaxis = (list(range = c(0, 100), title = "Age", automargin = TRUE)),
                   legend = list(orientation = 'h',  y = 100), margin = list(r = 20, b = 50, t = 50, pad = 4),
                   yaxis = (list(range = c(0, 100),title = "Volume (m3)")))%>%
          config(displayModeBar = F)

        # ggplotly(p) %>%
        p} })
    
     }

  plotData(as.data.frame(noZerosPlotData())
           )

#   #-------
  # #OBSERVE
  observe(
    {
      row <- sp_samplePoints[which(sp_samplePoints$objectid == getOnclickCoord()),]
      coords <- st_coordinates(row)
      proxy <- leafletProxy('map')

      if (!is.null(getOnclickCoord())){
        proxy %>%
          setView(coords[1], coords[2], zoom = 15)}
    })
#   
  observe({
    if ("Select All" %in% input$tsa) {
      # choose all the choices _except_ "Select All"
      selected_choices <- setdiff(tsaBnds, "Select All")
      updateSelectInput(session, "tsa", selected = selected_choices)
    }
    if ("Select All" %in% input$species) {
      # choose all the choices _except_ "Select All"
      selected_choices <- setdiff(speciesLst, "Select All")
      updateSelectInput(session, "species", selected = selected_choices)
    }
    if ("Select All" %in% input$bec) {
      # choose all the choices _except_ "Select All"
      selected_choices <- setdiff(becLst, "Select All")
      updateSelectInput(session, "bec", selected = selected_choices)
    }

    if ("Clear All" %in% input$tsa) {
      # choose all the choices _except_ "Select All"
      selected_choices <- ""
      updateSelectInput(session, "tsa", selected = selected_choices)
    }
    if ("Clear All" %in% input$species) {
      # choose all the choices _except_ "Select All"
      selected_choices <- ""
      updateSelectInput(session, "species", selected = selected_choices)
    }
    if ("Clear All" %in% input$bec) {
      # choose all the choices _except_ "Select All"
      selected_choices <- ""
      updateSelectInput(session, "bec", selected = selected_choices)
    }
  })


  # New Feature plus show modal
  observeEvent(input$map_draw_new_feature, {
    proxy <- leafletProxy('map')
    proxy %>%
      addLayersControl(baseGroups = c("WorldTopo","WorldImagery" ), overlayGroups = c('TSA Boundaries','Drawn'), options = layersControlOptions(collapsed = FALSE))%>%
      showGroup(c('Drawn'))
    if(length(impShp()) > 0){
      proxy %>%
        addLayersControl(baseGroups = c("WorldTopo","WorldImagery" ), overlayGroups = c('TSA Boundaries','Shapefile','Drawn'), options = layersControlOptions(collapsed = FALSE))
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
    showModal(spHelpModal)
  })

  # Modal for labeling the drawn polygons
  warningModal = modalDialog(
    title = "Important message",
    "Shapefile not valid")

  #When shapefiles are upload
  observeEvent( impShp(), {
    if(!is.null(impShp())){
      proxy <- leafletProxy('map')
      proxy %>%
        clearGroup(group='Shapefile') %>%
        addPolygons( data=impShp(), group='Shapefile',stroke = TRUE, color = "#03F", weight = 5, opacity = 0.5) %>%
        addLayersControl(baseGroups = c("WorldTopo","WorldImagery" ), overlayGroups = c('TSA Boundaries','Shapefile'), options = layersControlOptions(collapsed = FALSE))%>%
        showGroup(c('Shapefile'))
      if(length(input$map_draw_all_features$features) > 0){
        proxy %>%
          addLayersControl(baseGroups = c("WorldTopo","WorldImagery" ), overlayGroups = c('TSA Boundaries','Shapefile', 'Drawn'), options = layersControlOptions(collapsed = FALSE))
      }
    }
  })
# 
# 
  observeEvent(input$db, {
      #Create a CSV to download
      output$downloadCSV <<- downloadHandler(
        filename = paste("bc_sample_data-", Sys.Date(), ".zip", sep=""),
        content = function(fname) {
          fs <- c("data_dictionary.csv", "bc_sample_data.csv")
          where <- toString(shQuote(masterTable()$samp_id))
          write.csv(read_feather("www//export_ground_samples")[read_feather("www\\export_ground_samples")$samp_id %in% masterTable()$samp_id,] , file = "bc_sample_data.csv")
          write.csv(read_feather("www//dataDict"), file = "data_dictionary.csv")

          zip(zipfile=fname, files=fs)
          if(file.exists(paste0(fname, ".zip"))) {file.rename(paste0(fname, ".zip"), fname)}
        },
        contentType = "application/zip")
      jsinject <- "setTimeout(function(){window.open($('#downloadCSV').attr('href'))}, 100);"
      session$sendCustomMessage(type = 'jsCode', list(value = jsinject))
    
  })
# 
  observeEvent(input$fb, {
    shinyjs::disable(input$fb)
    plotData(noZerosPlotData())
    proxy <- leafletProxy('map')
    proxy %>%
      clearMarkerClusters() %>%
      clearMarkers() %>%
      clearPopups()
    if (!is.null(masterTable())){
      proxy %>%
        addCircleMarkers( data=masterTable() ,
                          group = "points",
                          radius = 6,
                          color = ~pal1(sampletype),
                          stroke = FALSE, fillOpacity = 1,
                          clusterOptions = markerClusterOptions(disableClusteringAtZoom = 7),
                          label = masterTable()$samp_id
                          ,
                          popup = paste(
                            paste(paste("<b>Sample ID</b> - ", masterTable()$samp_id, "<br/>"),
                                  paste("<b>Sample Type</b> - ", masterTable()$sampletype, "<br/>"),
                                  paste("<b>Bec Subzone</b> - ", masterTable()$beclabel, "<br/>"),
                                  paste("<b>YSM Main</b> - ", masterTable()$ysm_main, "<br/>"),
                                  paste("<b>Last Measured Date</b> - ", masterTable()$meas_dt, "<br/>"),
                                  paste("<b># of measures</b> - ", masterTable()$no_meas, "<br/>"),
                                  paste("<b>Species label</b> - ", masterTable()$spc_label_live, "<br/>"),
                                  paste("<b>Density #/ha</b> - ", round(masterTable()$stemsha_liv, digits = 0), "<br/>"),
                                  paste("<b>Basal area m2/ha</b> - ", round(masterTable()$baha_liv, digits = 0), "<br/>"),
                                  paste("<b>Total volume m3/ha</b> - ", round(masterTable()$wsvha_liv, digits = 0), "<br/>"),
                                  paste("<b>Total age yrs </b> - ", round(masterTable()$tot_stand_age, digits = 0), "<br/>")
                            ))
        )

    }
    shinyjs::enable(input$fb)

  })
  

  
}

# mod_about_server <- function(input, output, session){
#   ns <- session$ns
# }
# 
# ## To be copied in the UI
# # mod_about_ui("about_ui_1")
# 
# ## To be copied in the server
# # callModule(mod_about_server, "about_ui_1")
