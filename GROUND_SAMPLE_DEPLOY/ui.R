#-------------------------------------------------------------------------------------------------
# Define UI
ui <- tagList(  
  css_hide_errors(),
  tags$link(rel = "stylesheet", type = "text/css", href = "bcgov2.css"),
                  waiter::use_butler(),
                  waiter::use_waiter(),
                  waiter::waiter_show_on_load(html = waiter_html("Loading App")),
  shinyjs::useShinyjs(),
  gt::html("<header>
  <div class='banner'>
    <a href='https://gov.bc.ca' target=”_blank”>
      <img src='images/logo-banner.png' alt='Go to the Government of British Columbia website' />
    </a>
    <h2>Forest Inventory Sample Plots</h2>
  </div>
      <div class='other'>
      <a class='nav-btn'>
        <i class='fas fa-bars' id='menu' onclick='myFunction()'></i>
      </a>
    </div>
  </header>"),
  navbarPage(
    title = "",
             selected = "App",
             tabPanel(title = "App",
                      dashboardPage(
                        dashboardHeader(disable = TRUE),
                        
                        
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
                          column(width = 9, box(width=NULL,leafletOutput("map", height = 550)),
                                 boxPlus(height = 390, width=NULL,tabBox(width = NULL,
                                                                         # The id lets us use input$tabset1 on the server to find the current tab
                                                                         id = "tabset1", height = "0",
                                                                         tabPanel("Volume/Age",  plotlyOutput('age', height = "250px"))
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
                                    
                                    # checkboxGroupInput("prj2",
                                    #                    "Select Project Design",
                                    #                    choices = c("NONE","GRID","RANDOM"),
                                    #                    selected = c("NONE","GRID","RANDOM"),
                                    #                    inline = TRUE),
                                    radioButtons("prj",
                                                 "Select Project Design",
                                                 choices = c("All","YSM Main","Mat Main"),
                                                 selected = "All",
                                                 inline = TRUE)
                            ),
                            
                            boxPlus( 
                              closable = FALSE, 
                              status = "primary", 
                              solidHeader = TRUE, 
                              collapsible = FALSE,
                              collapsed = FALSE,
                              width = NULL,
                              actionButton("db", "Export Data as CSV", width="100%")
                            )
                            
                          )
                          )
                        )
                      )                      
                      
                      
                      ),
             tabPanel(title = "User Guide", wellPanel(
                      includeMarkdown("www//guide.md")
               )),
             tabPanel(title = "About", wellPanel(
                      includeMarkdown("www//about.md")
               ))),

tags$head(tags$script(HTML('
                           Shiny.addCustomMessageHandler("jsCode",
                           function(message) {
                           eval(message.value);
                           });'
))),

downloadLink("downloadCSV",label=""),

div(class = "footer",
    includeHTML("www/footer.html")
)
)
