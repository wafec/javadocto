library(plyr)

filter_normal_set <- function(data) {
    significant <- subset(data, !((NWL == 0 & NEL == 0) & test_status=='PASS'))
    return(significant)
}

pass_versus_fail <- function(csv_file) {
  data <- read.csv(csv_file,head=TRUE,sep=",")
  significant <- filter_normal_set(data)
  count(significant, "test_status")
}

state_start_and_command_counting <- function(csv_file) {
  data <- read.csv(csv_file,head=TRUE,sep=",")
  data <- filter_normal_set(data)
  significant <- subset(data, test_status=='FAIL')
  if (length(significant) > 0) {
    res <- count(significant, c("CMD", "Ss", "Sd", "LSF", "http_code"))
  }
  return(res)
}

generate_start_command_table <- function(csv_file) {
  res <- state_start_and_command_counting(csv_file)
  attach(res)
  return(res[order(http_code,-freq),])
}

http_200_with_fail <- function(csv_file) {
  data <- read.csv(csv_file,head=TRUE,sep=",")
  data <- filter_normal_set(data)
  count(data, c("http_code", "test_status"))
}

count_activated <- function(csv_file) {
  data <-read.csv(csv_file,head=TRUE,sep=",")
  activated_len <- nrow(filter_normal_set(data))
  sprintf("%d/%d", activated_len, nrow(data))
}