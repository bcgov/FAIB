#-------------------------------------------------------------------------------------------------
# Define UI
ui <- tagList(  
  css_hide_errors(),
  tags$link(rel = "stylesheet", type = "text/css", href = "bcgov2.css"),
                  # waiter::use_butler(),
                  # waiter::use_waiter(),
                  # waiter::waiter_show_on_load(html = waiter_html("Loading App")),
  shinyjs::useShinyjs(),
  extendShinyjs(text = js_code, functions = c("openURL")),
  gt::html("<header>
  <div class='banner'>
    <a href='https://gov.bc.ca' target=”_blank”>
      <img src='images/logo-banner.png' alt='Go to the Government of British Columbia website' />
    </a>
    <h2>Timber Harvesting Land Base Data Locator</h2>
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
                          column(width = 9, box(width=NULL,leafletOutput("map", height = 625))
                          ),
                          
                          column(
                            tags$head(tags$style(HTML("#tsa ~ .selectize-control 
                                          .selectize-input {
                                         max-height: 400px;
                                         overflow-y: auto;}
                                         .selectize-dropdown-content {
                                          max-height: 400px;
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
                                    selectizeInput(
                                      "tsa",
                                      "Select TSA",
                                      choices = c("Clear All","Select All", tsaBnds),
                                      selected = tsaBnds,
                                      multiple = TRUE, 
                                      options = list('plugins' = list('remove_button'), placeholder = 'Select a TSA'))
                            ),
                            
                            boxPlus( 
                              closable = FALSE, 
                              status = "primary", 
                              solidHeader = TRUE, 
                              collapsible = FALSE,
                              collapsed = FALSE,
                              width = NULL,
                              actionButton("db", "Download Selected", width="100%")
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
