
library(cvTools)  # for CV
library(class)    # for KNN

#library(huxtable)      # pretry display of L. Reg variable selection



##### ROC function

rocplot = function (pred, truth, ...)     {                     ## pred is the numerical scores/ fitted values of the model, truth  is the actual Y values from the test set
  predob = prediction (pred, truth )
  perf = performance (predob, "tpr", "fpr")           ## this calculates the pair ("tpr","fpr")   for each cutoff
  
  plot(perf, ...)              ## plots the ROC curve
}

## NOTE: taken from ISL pg 365


# to extract the legend from one of the ggplots
# taken from stackoverflow

g_legend<-function(a.gplot)     {
  tmp <- ggplot_gtable(ggplot_build(a.gplot))
  leg <- which(sapply(tmp$grobs, function(x) x$name) == "guide-box")
  legend <- tmp$grobs[[leg]]
  return(legend)
  }



#taken from https://stackoverflow.com/questions/13649473/add-a-common-legend-for-combined-ggplots/28594060#28594060
grid_arrange_shared_legend <- function(...) {
  plots <- list(...)
  g <- ggplotGrob(plots[[1]] + theme(legend.position="bottom"))$grobs
  legend <- g[[which(sapply(g, function(x) x$name) == "guide-box")]]
  lheight <- sum(legend$height)
  grid.arrange(
    do.call(arrangeGrob, lapply(plots, function(x)
      x + theme(legend.position="none"))),
    legend,
    ncol = 1,
    heights = unit.c(unit(1, "npc") - lheight, lheight))
}


#####  KNN-CV

cv.knn <- function(X,y,k=K,V)
{
  n <- length(y)          # we will be using whole data
  cvSets <- cvFolds(n, V)    # gives a single vector of V fold split, we can use R > 1 to get a matrix
  
  test.error.knn  <- c()
  for (cv in 1:V) 
  {
    testInds <- cvSets$subsets[which(cvSets$which==cv)] # we start with fold 1 as test set
    trainInds <- (1:n)[-testInds]             # those indicies that do not belong to the test-set are training set
    y.test <- y[testInds]
    y.train <- y[trainInds]
    X.test <- X[testInds,]
    X.train <- X[trainInds,]
    
    results.knn <- knn(train=X.train,test=X.test,cl=y.train,k=k)      # these are the KNN results for the given K
    test.error.knn[cv] <- sum(results.knn!=y.test)                   
    #   this is the misclassification error for the fold in this loop 
    # we pick the K that givs the lowest misclassfication error.
  }
  return(sum(test.error.knn)/n)                  # we sum all misclasification errors for all folds for this K
}




##### Logistic-Reg CV


cv.glm = function(X,y,V,seed=NA)
{
  # Set the seed
  if (!is.na(seed)) {
    set.seed(seed)
  }
  
  # Set n
  n = length(y)
  #print(str(y))
  # Split the data up into V folds
  cvSets <- cvFolds(n, V)
  
  # Loop through each fold and calculate the error for that fold
  test.errorLR <- c()
  for (i in 1:V) 
  {
    # set the indices corresponding to the training and test sets
    testInds <- cvSets$subsets[which(cvSets$which==i)]
    trainInds <- (1:n)[-testInds]
    
    X = data.frame(X)
    
    # Separate y and X into the training and test sets
    y.test <- y[testInds]
    X.test <- X[ testInds,]
    y.train <- y[trainInds]
    X.train <- X[trainInds,]
    
    # Do classification on ith fold
    res.glm <- glm(y.train ~., data=X.train, family=binomial)
    res = round(predict(res.glm, newdata=X.test, type="response"))
    #print(table(res, y.test))           
    # Calcuate the test error for this fold
    test.errorLR[i] <- sum(res != y.test)
    #print(test.errorLR[i])
  }
  
  # Calculate the mean error over each fold
  cv.error = sum(test.errorLR)/n
  
  # Return the results
  return(cv.error)
}


#####  LR with AIC/BIC
#####  CV error for Logistic Regression using BIC and AIC

cv.glm.backward = function(X,y,V,seed=NA,pen)
{
  # Set the seed
  if (!is.na(seed)) {
    set.seed(seed)
  }
  
  # Set n
  n = length(y)
  
  # Split the data up into V folds
  cvSets <- cvFolds(n, V)
  
  # Loop through each fold and calculate the error for that fold
  test.error <- c()
  for (i in 1:V) 
  {
    # set the indices corresponding to the training and test sets
    testInds <- cvSets$subsets[which(cvSets$which==i)]
    trainInds <- (1:n)[-testInds]
    
    X = data.frame(X)
    
    # Separate y and X into the training and test sets
    y.test <- y[testInds]
    X.test <- X[ testInds,]
    y.train <- y[trainInds]
    X.train <- X[trainInds,]
    
    # Do classification on ith fold
    full <- glm(y.train ~., data=X.train, family=binomial)
    res.step <- step(full,k=pen, trace=0)
    res = round(predict(res.step, newdata=X.test, type="response"))
    
    # Calcuate the test error for this fold
    test.error[i] <- sum(res!=y.test)
  }
  
  # Calculate the mean error over each fold
  cv.error = sum(test.error)/n
  
  # Return the results
  return(cv.error)
}

