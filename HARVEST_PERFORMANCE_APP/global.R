
# Any code in this file is guaranteed to be called before either
# ui.R or server.R

library(shiny)
library(shinydashboard)
library(rmarkdown)
library(RPostgreSQL)
library(dplyr)
library(tidyr)
library(plotly)
library(feather)
library(rintrojs)
library(shinyBS)
library(ggplot2)


bnds <- read_feather("www//bnds")
regs <- unique(bnds[c("org_unit_reg", "name_reg")]) 
distr <- unique(bnds[c("org_unit_distr", "name_distr")]) 
mu <- unique(bnds[c('management_unit')]) 

addOrgName <- function(inData){
  inData <- left_join(read_feather(paste0('www//',inData )),regs, by = 'org_unit_reg' )
  inData <- left_join(inData,distr, by = 'org_unit_distr' )
  return(inData)
}

millTHLB <- addOrgName('millTHLB') %>% mutate(type = 'VRI Profile >60yrs' ) %>% separate(mill_proximity,c(NA, "class"), sep = '_')
millFTEN <- addOrgName('millFTEN') %>% mutate(type = '5-year Harvested Blocks' ) %>% separate(mill_proximity,c(NA, "class"), sep = '_')
ageTHLB <- addOrgName('ageTHLB')%>% mutate(type = 'VRI Profile >60yrs' ) %>% mutate(class = age_class )
ageFTEN <- addOrgName('ageFTEN')%>% mutate(type = '5-year Harvested Blocks' ) %>% mutate(class = age_class )
profileTHLB <- addOrgName('profileTHLB')%>% mutate(type = 'VRI Profile >60yrs' )
profileFTEN <- addOrgName('profileFTEN')%>% mutate(type = '5-year Harvested Blocks' )
slopeTHLB <- addOrgName('slopeTHLB')%>% mutate(type = 'VRI Profile >60yrs' ) %>% mutate(class = slope )
slopeFTEN <- addOrgName('slopeFTEN')%>% mutate(type = '5-year Harvested Blocks' ) %>% mutate(class = slope )
volTHLB <- addOrgName('volTHLB') %>% mutate(type = 'THLB' )%>% separate(vol_ha,c(NA, "class"), sep = '_')
volFTEN <- addOrgName('volFTEN')%>% mutate(type = 'FTEN' )%>% separate(vol_ha,c(NA, "class"), sep = '_')
vqoTHLB <- addOrgName('vqoTHLB')%>% mutate(type = 'VRI Profile >60yrs' )%>% mutate(class = vqo )
vqoFTEN <- addOrgName('vqoFTEN')%>% mutate(type = '5-year Harvested Blocks' )%>% mutate(class = vqo )


# setPlotRatio <- function(inFC,sumField) {
#   total <- inFC %>% summarize(total = sum(.data[[sumField]]))
#   inFC['total'] = total[1][1]
#   inFC <- mutate(inFC, ratio = .data[[sumField]]/total)
#   return(inFC)
# }
# 
# volTHLB <- setPlotRatio(volTHLB,'area')
# volFTEN <- setPlotRatio(volFTEN,'area')
# 
# vol <- bind_rows(volTHLB, volFTEN)
# vol <- vol %>% group_by( type, class, age_class) %>% summarize(ratio = sum(ratio))
# 
# vol <- mutate(vol, test = type)
# 
# 
# ggplot(vol, aes(x = type, y = ratio, fill = age_class)) +
#   geom_bar(stat = 'identity', position = 'stack') + facet_grid(~ class) +
#  scale_y_continuous(labels = scales::percent_format(accuracy = 1))+
#   theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) + xlab('Volume (m3/ha)') +
#   theme(axis.title.y=element_blank()) +
#    scale_fill_discrete(name = '') +  theme(legend.position="top")
# 
# ggplotly(fig)
# 
# + scale_x_discrete()+
#   geom_bar(stat = 'identity', position = 'stack') + facet_grid(~ class) +
# theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))
# 
# ggplotly(fig)

# #
# p1 <- vol %>% filter('<150' %in% class) %>%
#   plot_ly(
#     y = ~type,
#     x = ~ratio,
#     color= ~age_class,
#     colors = 'Reds',
#     type = 'bar',
#     name = ~age_class,
#     orientation = 'h')  %>%
#   layout(xaxis = list(title = 'Percentage (%)'), yaxis = list(title = '<150',showticklabels = FALSE)) %>%  layout(xaxis = list(tickformat = "%"))
# p2 <- vol %>% filter('150-250' %in% class) %>%
#   plot_ly(
#     y = ~type,
#     x = ~ratio,
#     color= ~age_class,
#     colors = 'Reds',
#     type = 'bar',
#     showlegend=F,
#     orientation = 'h') %>%
#    layout(yaxis = list(title = '150-250'))
# p3 <- vol %>% filter('250-350' %in% class) %>%
#   plot_ly(
#     y = ~type,
#     x = ~ratio,
#     color= ~age_class,
#     colors = 'Reds',
#     type = 'bar',
#     showlegend=F,
#     orientation = 'h')%>%
#   layout(yaxis = list(title = '250-350'))
# p4 <- vol %>% filter('350-450' %in% class) %>%
#   plot_ly(
#    y = ~type,
#     x = ~ratio,
#     color= ~age_class,
#     colors = 'Reds',
#     type = 'bar',
#     showlegend=F,
#     orientation = 'h')%>%
#   layout(yaxis = list(title = '350-450'))
# 
# p5 <- vol %>% filter('450-550' %in% class) %>%
#   plot_ly(
#     y = ~type,
#     x = ~ratio,
#     color= ~age_class,
#     colors = 'Reds',
#     type = 'bar',
#     showlegend=F,
#     orientation = 'h') %>%
#   layout(yaxis = list(title = '450-550'))
# p6 <- vol %>% filter('550-650' %in% class) %>%
#   plot_ly(
#     y = ~type,
#     x = ~ratio,
#     color= ~age_class,
#     colors = 'Reds',
#     type = 'bar',
#     showlegend=F,
#     orientation = 'h')%>%
#   layout(yaxis = list(title = '550-650'))
# p7 <- vol %>% filter('650-750' %in% class) %>%
#   plot_ly(
#     y = ~type,
#     x = ~ratio,
#     color= ~age_class,
#     colors = 'Reds',
#     type = 'bar',
#     showlegend=F,
#     orientation = 'h')%>%
#   layout(yaxis = list(title = '650-750'))
# p8 <- vol %>% filter('750+' %in% class) %>%
#   plot_ly(
#     y = ~type,
#     x = ~ratio,
#     color= ~age_class,
#     colors = 'Reds',
#     type = 'bar',
#     showlegend=F,
#     orientation = 'h')%>%
#   layout(yaxis = list(title = '750+'))
# subplot(p1,p2,p3,p4,p5,p6,p7,p8,shareX = T, titleY = TRUE, nrows = 8 ) %>% layout(barmode = 'stack', orientation = 'h')
# 

