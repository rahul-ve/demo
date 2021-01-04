
library(cvTools)  # for CV
library(class)    # for KNN
library(MASS)      # for LDA and QDA
library(tree)      # for CART
library(rpart)     # CART
library(rpart.plot)  # CART
library(huxtable)      # pretry display of L. Reg variable selection






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



#####   LDA - cv


# The following function does crossvalidation using
# X - predictor matrix
# y - class matrix
# k - value of k in KNN
# V - number of CV folds
# seed - (optional) internally sets the seed.
cv.da = function(X,y,method=c("lda","qda"),V,seed=NA)
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
  test.error.da <- c()
  for (i in 1:V) 
  {
    # set the indices corresponding to the training and test sets
    testInds <- cvSets$subsets[which(cvSets$which==i)]
    trainInds <- (1:n)[-testInds]
    
    # Separate y and X into the training and test sets
    y.test <- y[testInds]
    X.test <- X[ testInds,]
    y.train <- y[trainInds]
    X.train <- X[trainInds,]
    
    # Do classification on ith fold
    if (method=="lda") {
      res <- lda(y~., data=X,subset=trainInds)
    }
    if (method=="qda") {
      res <- qda(y~., data=X,subset=trainInds)
    }
    results.da = predict(res, X.test)$class
    
    # Calcuate the test error for this fold
    test.error.da[i] <- sum(results.da!=y.test)
  }
  
  # Calculate the mean error over each fold
  cv.error = sum(test.error.da)/n
  
  # Return the results
  return(cv.error)          # this is for one iteration of v-fold CV
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


##### V-fold CV of CART

# The following function does cross-validation using
# X - predictor matrix
# y - class matrix
# V - number of CV folds
# seed - (optional) internally sets the seed.
cv.rpart = function(X,y,V,seed=NA)
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
    res.rpart <- rpart(as.factor(y.train) ~., data=X.train)
    res = predict(res.rpart, newdata=X.test, type = "class")
    
    # Calcuate the test error for this fold
    test.error[i] <- sum(res!=y.test)
  }
  
  # Calculate the mean error over each fold
  cv.error = sum(test.error)/n
  
  # Return the results
  return(cv.error)
}


