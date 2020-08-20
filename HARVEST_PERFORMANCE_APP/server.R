

server <- function(input, output, session) {
  ###########################################################################
  # Settings
  ###########################################################################
  i18n <- reactive({
    selected <- input$selected_language
    if (length(selected) > 0 && selected %in% translator$languages) {
      translator$set_translation_language(selected)
    }
    translator
  })
  
  ###########################################################################
  # Reactive
  ###########################################################################
  distrR <- reactive({
    if('All' %in%  input$reg){
      distrs <- c('All',sort(distinct(bnds, name_distr)$name_distr))
    }
    else{
    distrs <- c('All',sort(distinct( bnds %>% filter(name_reg %in% input$reg), name_distr)$name_distr ))}

    return(distrs)
  })
  
  muR <- reactive({
    if('All' %in%  input$distr){
      mus <- c('All',sort(distinct(bnds %>% filter(name_distr %in% distrR()), management_unit)$management_unit))
    }
    
    else{    
      mus <-  c('All',sort(distinct(bnds %>% filter(name_distr %in% input$distr), management_unit)$management_unit))}
    return(mus)
  })
  
  

  # #####OUTPUTS
  
  output$distrs <- renderUI({
    mydata <- distrR()
    selectizeInput(
      'distr',
      'District',
      choices = mydata,
      selected = "All",
      multiple = TRUE, 
      options = list('plugins' = list('remove_button'), 'persist' = TRUE)
    )
  })
  
  output$mus <- renderUI({
    mydata <- muR()
    selectizeInput(
      'mu', 
      'Management Unit', 
      choices = mydata, 
      selected = "All" ,
      multiple = TRUE,
      options = list('plugins' = list('remove_button'), 'persist' = TRUE)
    )
  })
  

  # output$agePlot <- renderPlotly({
  #   ageClass <- ageClass %>% filter(management_unit %in% input$mu)
  #   ageClass$age_class <- factor(ageClass$age_class, levels = c("40 to 60","60 to 80","80 to 100","100 to 120","120 to 140","140 to 250", '250+'))
  #   fig <- plot_ly(ageClass, x = ~age_class, y = ~ratio, type = 'bar', name = ~class)
  #   fig <- fig %>% layout(yaxis = list(title = 'Percentage (%)'), barmode = 'group', xaxis = list(title = 'Age Class')) %>%  layout(yaxis = list(tickformat = "%"))
  #   fig <- fig %>% layout(legend = list(orientation = 'h',y = 100))
  #   ggplotly(fig)
  # })
  # 
  
  
  filterPlotlyData <- function(inTHLB, inFTEN){
    
    if('All' %in%  input$reg){
      inTHLB <- inTHLB
      inFTEN <- inFTEN
    }
    else{
      inTHLB <- inTHLB %>% filter(name_reg %in% input$reg)
      inFTEN <- inFTEN %>% filter(name_reg %in% input$reg)}
    
    if('All' %in%  input$distr){
      inTHLB <- inTHLB%>% filter(name_distr %in% distrR())
      inFTEN <- inFTEN%>%filter(name_distr %in% distrR())
    }
    else{
      inTHLB <- inTHLB %>% filter(name_distr %in% input$distr)
      inFTEN <- inFTEN %>% filter(name_distr %in% input$distr)}
    # 
    if('All' %in%  input$mu){
      inTHLB <- inTHLB%>% filter(management_unit %in% muR())
      inFTEN <- inFTEN %>% filter(management_unit %in% muR())
    }
    else{
      inTHLB <- inTHLB %>% filter(management_unit %in% input$mu)
      inFTEN <- inFTEN %>% filter(management_unit %in% input$mu)}
    # 


    
    return(list(inTHLB, inFTEN))
  }
  
  setPlotRatio <- function(inFC,sumField) {
    total <- inFC %>% summarize(total = sum(.data[[sumField]]))
    inFC['total'] = total[1][1]
    inFC <- mutate(inFC, ratio = .data[[sumField]]/total)
    return(inFC)
  }

  output$mill_prox_plot <- renderPlotly({
    inputs <- filterPlotlyData(millTHLB,millFTEN)
    millTHLB <- inputs[[1]]
    millFTEN <- inputs[[2]]

    millTHLB <- setPlotRatio(millTHLB,'area')
    millFTEN <- setPlotRatio(millFTEN,'area')

    millProx <- bind_rows(millTHLB, millFTEN)
    millProx <- millProx %>% group_by( type, class) %>% summarize(ratio = sum(ratio))

    millProx$class <- factor(millProx$class, levels = c("0 to 33km","33 to 66km","66 to 99km",">99km"))
    fig <- plot_ly(millProx, x = ~class, y = ~ratio, type = 'bar', name = ~type)
    fig <- fig %>% layout(yaxis = list(title = 'Percentage (%)'), barmode = 'group', xaxis = list(title = 'Mill Proximity')) %>%  layout(yaxis = list(tickformat = "%"))
    fig <- fig %>% layout(legend = list(orientation = 'h',y = 100))
    ggplotly(fig)
  })
  
  output$slope_plot <- renderPlotly({
    inputs <- filterPlotlyData(slopeTHLB,slopeFTEN)
    slopeTHLB <- inputs[[1]]
    slopeFTEN <- inputs[[2]]
    
    slopeTHLB <- setPlotRatio(slopeTHLB,'area')
    slopeFTEN <- setPlotRatio(slopeFTEN,'area')
    
    slope <- bind_rows(slopeTHLB, slopeFTEN)
    slope <- slope %>% group_by( type, class) %>% summarize(ratio = sum(ratio))
    
    # slope$class <- factor(slope$class, levels = c("0 to 33km","33 to 66km","66 to 99km",">99km"))
    fig <- plot_ly(slope, x = ~class, y = ~ratio, type = 'bar', name = ~type)
    fig <- fig %>% layout(yaxis = list(title = 'Percentage (%)'), barmode = 'group', xaxis = list(title = 'Slope (%)')) %>%  layout(yaxis = list(tickformat = "%"))
    fig <- fig %>% layout(legend = list(orientation = 'h',y = 100))
    ggplotly(fig)
  })
  
  output$age_plot <- renderPlotly({
    inputs <- filterPlotlyData(ageTHLB,ageFTEN)
    ageTHLB <- inputs[[1]]
    ageFTEN <- inputs[[2]]
    
    ageTHLB <- setPlotRatio(ageTHLB,'area')
    ageFTEN <- setPlotRatio(ageFTEN,'area')
    
    age <- bind_rows(ageTHLB, ageFTEN)
    age <- age %>% group_by( type, class) %>% summarize(ratio = sum(ratio))
    
    age$class <- factor(age$class, levels = c("40 to 60","60 to 80","80 to 100","100 to 120", "120 to 140", "140 to 250", "250+"))
    fig <- plot_ly(age, x = ~class, y = ~ratio, type = 'bar', name = ~type)
    fig <- fig %>% layout(yaxis = list(title = 'Percentage (%)'), barmode = 'group', xaxis = list(title = 'Age (years)')) %>%  layout(yaxis = list(tickformat = "%"))
    fig <- fig %>% layout(legend = list(orientation = 'h',y = 100))
    ggplotly(fig)
  })
  
  output$vol_plot <- renderPlot({
    inputs <- filterPlotlyData(volTHLB,volFTEN)
    volTHLB <- inputs[[1]]
    volFTEN <- inputs[[2]]
    
    volTHLB <- setPlotRatio(volTHLB,'area')
    volFTEN <- setPlotRatio(volFTEN,'area')
    
    vol <- bind_rows(volTHLB, volFTEN)
    vol <- vol %>% group_by( type, class, age_class) %>% summarize(ratio = sum(ratio))
    
    ggplot(vol, aes(x = type, y = ratio, fill = age_class)) + 
      geom_bar(stat = 'identity', position = 'stack') + facet_grid(~ class) +
      scale_y_continuous(labels = scales::percent_format(accuracy = 1))+
      theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) + xlab('Volume (m3/ha)') +
      theme(axis.title.y=element_blank()) +
      scale_fill_discrete(name = '') +  theme(legend.position="top")

  })
  
  ####OBSERVE
  
  observe({
    selected_choices <- "All"

    if (length(input$mu) == 0  ){
      updateSelectInput(session, "mu", selected = selected_choices)
    }

    if (length(input$reg) == 0  ){
      updateSelectInput(session, "reg", selected = selected_choices)
    }

    if (length(input$distr) == 0  ){
      updateSelectInput(session, "distr", selected = selected_choices)
    }
    

    # 
    if (first(input$reg) == 'All' && length(input$reg) > 1) {
      updateSelectInput(session, "reg", selected = setdiff(input$reg,'All'))
    }
    
    if (first(input$distr) == 'All' && length(input$distr) > 1) {
      updateSelectInput(session, "distr", selected = setdiff(input$distr,'All'))
    }
    
    if (first(input$mu) == 'All' && length(input$mu) > 1) {
      updateSelectInput(session, "mu", selected = setdiff(input$mu,'All'))
    }

    # 
    if (last(input$mu) == 'All' && length(input$mu) > 1) {
      updateSelectInput(session, "mu", selected = selected_choices)
    }
    if (last(input$reg) == 'All' && length(input$reg) > 1) {
      updateSelectInput(session, "reg", selected = selected_choices)
    }
    if (last(input$distr) == 'All' && length(input$distr) > 1) {
      updateSelectInput(session, "distr", selected = selected_choices)
    }

    # 
    if (length(input$mu) >= length(mu$management_unit)) {
      updateSelectInput(session, "mu", selected = selected_choices)
    }
    if (length(input$reg) >= length(regs$name_reg)) {
        updateSelectInput(session, "reg", selected = selected_choices)
    }
    if (length(input$distr) >= length(distr$name_distr)) {
      updateSelectInput(session, "distr", selected = selected_choices)
    }

    
    
  })
  
  # observe({
  #   cat(slope()$name)
  # })

}