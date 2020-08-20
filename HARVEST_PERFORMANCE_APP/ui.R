# pageTitle <- "Timber Management Goals"
# sidebarWidth <- 300
# 
# # CSS Files
# cssFiles <- tags$head(
#   tags$link(rel = "stylesheet", type = "text/css", href = "css/main.css")
# )
# # JavaScript Files
# jsFiles <- tags$head(
#   tags$script(src = "js/google-analytics.js")
# )
# 
# ####################################################
# # UI ----
# ####################################################
# header <- dashboardHeader(
#   title = "Timber Management Goals",
#   titleWidth = 300,
#   .list = list(
#     tags$li(
#       class = "dropdown dummy",
#       bookmarkButton()
#     ),
#     tags$li(
#       class = "dropdown dummy",
#       uiOutput("language_selector")
#     )
#   )
# )
# 
# sidebar <- dashboardSidebar(
#   width = sidebarWidth,
#   sidebarMenuOutput("sidebar_menu")
# )
# 
# board.about <- tabItem(
#   tabName = "about",
#   uiOutput("about")
# )
# ####################################################
# # Tab Items for Distributions ----
# ####################################################
# # ???????????? ----
# ## Normal
# 
# body <- dashboardBody(
#   cssFiles,
#   jsFiles,
#   tabItem(tabName = "Timber Volume Flow Over Time")
#   
# )
# 
# ui <- function(req) {
#   dashboardPage(header, sidebar, body)
# }
# 
# pageTitle <- "Timber Management Goals"
# sidebarWidth <- 300
# 
# # CSS Files
# cssFiles <- tags$head(
#   tags$link(rel = "stylesheet", type = "text/css", href = "css/main.css")
# )
# # JavaScript Files
# jsFiles <- tags$head(
#   tags$script(src = "js/google-analytics.js")
# )

####################################################
# UI ----
####################################################

ui <- dashboardPage(
  dashboardHeader(title = "Timber Management Goals",
                  titleWidth = 300,
                  .list = list(
                    tags$li(
                      class = "dropdown dummy",
                      bookmarkButton()
                    ),
                    tags$li(
                      class = "dropdown dummy",
                      uiOutput("language_selector")
                    )
                  )),
  dashboardSidebar(
    width = 300,
    selectizeInput(
      'reg', 
      'Region', 
      choices = c("All", regs$name_reg),
      selected = "All", 
      multiple = TRUE, 
      options = list('plugins' = list('remove_button'), 'persist' = TRUE)
    ),
    uiOutput('distrs'),
    uiOutput('mus')

     ),
  dashboardBody(
    fluidRow(
      box(title = "Mill Proximity",
          solidHeader = T,
          width = 6,
          collapsible = T,
          plotlyOutput("mill_prox_plot")),
      box(title = "Slope", solidHeader = T,
          width = 6, collapsible = T,
          plotlyOutput("slope_plot"))
    ), # row
    fluidRow(
      box(title = "Age", solidHeader = T,
          width = 6, collapsible = T,
          plotlyOutput("age_plot")),
      box(title = "Volume per Hectare", solidHeader = T,
          width = 6, collapsible = T,
          plotOutput("vol_plot"))
    )
  ) # body
  
)