#-------------------------------------------------------------------------------------------------
# Define UI
ui <- tagList(dashboardPage(
  dashboardHeader(
    title = "BC Sample Plots"),
  
  
  #sidebar content
  dashboardSidebar(disable = TRUE 
  ),
  
  #body content
  dashboardBody(
    tags$head(tags$style(HTML('
      .content-wrapper  {
                              font-weight: normal;
                              font-size: 14px;
                              }'))),
    
    fluidRow(  tags$head(
      tags$style(HTML('#samplePlotsHelp{color:black}'))
    ),
    column(width = 9, box(width=NULL,leafletOutput("map", height = 670)),
        boxPlus(height = 390, width=NULL,tabBox(width = NULL,
            # The id lets us use input$tabset1 on the server to find the current tab
           id = "tabset1", height = "0",
          tabPanel("Volume/Age",  plotlyOutput('age', height = "300px"))
    ))
    ),
    
    column(
      tags$head(tags$style(HTML("#tsa ~ .selectize-control 
                                          .selectize-input {
                                         max-height: 90px;
                                         overflow-y: auto;}
                                         .selectize-dropdown-content {
                                          max-height: 90px;
                                          overflow-y: auto;}
                                         "))),
      tags$head(tags$style(HTML("#bec ~ .selectize-control 
                                          .selectize-input {
                                         max-height: 90px;
                                         overflow-y: auto;}
                                         .selectize-dropdown-content {
                                          max-height: 90px;
                                          overflow-y: auto;}
                                         "))),
      tags$head(tags$style(HTML("#species ~ .selectize-control 
                                          .selectize-input {
                                         max-height: 90px;
                                         overflow-y: auto;}
                                         .selectize-dropdown-content {
                                          max-height: 90px;
                                          overflow-y: auto;}
                                         "))),
      width = 3,height = 400,
      boxPlus(width=NULL,
              title = "Filter Data ",  
              closable = FALSE, 
              status = "primary", 
              solidHeader = TRUE, 
              collapsible = FALSE,
              collapsed = FALSE,
              actionButton("fb", "Filter", width = "100%"),
              radioButtons("shapeFilt",
                           "Select Shape Filter",
                           choices = c("None","Drawn Polygon", "Shapefile", "Both"),
                           selected = "None",
                           inline = FALSE),
              checkboxGroupInput("cbSType",
                                 actionLink("samplePlotsHelp", "Select Sample Type ",icon =icon("info-circle")),
                                 choices = sampleTypes,
                                 selected = sampleTypes,
                                 inline = TRUE),
              checkboxGroupInput("sts",
                                 "Select Sample Status",
                                 choiceNames = c("Active","Inactive"),
                                 choiceValues = c("A","I"),
                                 selected = c("A","I"),
                                 inline = TRUE),
              
              selectizeInput(
                "tsa",
                "Select TSA",
                choices = c("Clear All","Select All", tsaBnds),
                selected = tsaBnds,
                multiple = TRUE, 
                options = list('plugins' = list('remove_button'), placeholder = 'Select a Timber Supply Area', 'persist' = TRUE)),
              selectizeInput(
                "species",
                "Select Leading Species",
                choices = c("Clear All","Select All",speciesLst),
                selected = speciesLst,
                multiple = TRUE,
                options = list('plugins' = list('remove_button'), placeholder = 'Select a Species', 'persist' = TRUE)),
              selectizeInput("bec",
                             "Select Bec Zone",
                             choices = c("Clear All","Select All",becLst),
                             selected = becLst,
                             multiple = TRUE,
                             options = list('plugins' = list('remove_button'), placeholder = 'Select a BEC Zone', 'persist' = TRUE)),
              
              checkboxGroupInput("prj",
                                 "Select Project Design",
                                 choices = c("NONE","GRID","RANDOM"),
                                 selected = c("NONE","GRID","RANDOM"),
                                 inline = TRUE)
      ),
      
      boxPlus( 
        title = "Export Data as a CSV ",  
        closable = FALSE, 
        status = "primary", 
        solidHeader = TRUE, 
        collapsible = FALSE,
        collapsed = FALSE,
        width = NULL,
        checkboxInput("terms",
                      label = actionLink("termsMod","I Agree to Terms and Conditions")),
        actionButton("db", "Export", width="100%")
      )
      
    )
    )
  )
),  
tags$footer(actionLink("contactUs", "Contact Us ", onclick = "window.open('https://www2.gov.bc.ca/gov/content/industry/forestry/managing-our-forest-resources/forest-inventory/ground-sample-inventories')" ), 
            align = "center",
            style = "
                bottom:0;
                width:100%;
                height:40px;   /* Height of the footer */
                color: white;
                padding:10px;
                background-color: #367fa9;
                z-index: 2000;
                font-family:sans-serif;"),
tags$footer(
  tags$style(HTML('#contactUs{color:white}'))
),
tags$head(tags$script(HTML('
                           Shiny.addCustomMessageHandler("jsCode",
                           function(message) {
                           eval(message.value);
                           });'
))), downloadLink("downloadCSV",label="")
)
