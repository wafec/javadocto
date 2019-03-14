library(plyr)

pass_versus_fail <- function(csv_file) {
  data <- read.csv(csv_file,head=TRUE,sep=",")
  significant <- subset(data, NWL > 0 || NEL > 0)
  count(significant, "test_status")
}

state_start_and_command_counting <- function(csv_file) {
  data <- read.csv(csv_file,head=TRUE,sep=",")
  significant <- data[which(data$test_status=='FAIL'),]
  if (length(significant) > 0) {
    res <- count(significant, c("CMD", "Ss", "Sd", "LSF", "LSFm1"))
  }
  return(res)
}

http_200_with_fail <- function(csv_file) {
  data <- read.csv(csv_file,head=TRUE,sep=",")
  count(data, c("http_code", "test_status"))
}

count_activated <- function(csv_file) {
  data <-read.csv(csv_file,head=TRUE,sep=",")
  activated_len <- nrow(subset(data, NWL > 0 | NEL > 0))
  sprintf("%d/%d", activated_len, nrow(data))
}