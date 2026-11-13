# BYM2 covariance for the province effect (Riebler et al., 2016): Sigma(phi) = (1 - phi) I + phi * Q_scaled^-,
# where Q is the ICAR precision of the within-country adjacency graph and Q^- its generalised inverse (sum-to-zero within
# each connected component), scaled so that the geometric mean of the marginal variances is 1 in each component.
suppressPackageStartupMessages(library(data.table))
M <- readRDS("out/p3_model_data.rds"); lv <- levels(factor(M$D$shapeID))
g <- readLines("out/p3_graph.adj"); n <- as.integer(g[1]); stopifnot(n == length(lv))
W <- matrix(0, n, n)
for (l in g[-1]) { v <- as.integer(strsplit(trimws(l), " +")[[1]]); if (length(v) > 2 && v[2] > 0) W[v[1], v[-(1:2)]] <- 1 }
W <- pmax(W, t(W)); Q <- diag(rowSums(W)) - W
comp <- igraph_free <- local({ cmp <- rep(NA_integer_, n); k <- 0
  for (s in 1:n) if (is.na(cmp[s])) { k <- k + 1; q <- s; cmp[s] <- k
    while (length(q)) { v <- q[1]; q <- q[-1]; nb <- which(W[v, ] > 0 & is.na(cmp)); cmp[nb] <- k; q <- c(q, nb) } }
  cmp })
Qg <- matrix(0, n, n)
for (k in unique(comp)) { i <- which(comp == k)
  if (length(i) == 1) { Qg[i, i] <- 0; next }
  e <- eigen(Q[i, i], symmetric = TRUE); keep <- e$values > 1e-8
  Gi <- e$vectors[, keep] %*% diag(1 / e$values[keep]) %*% t(e$vectors[, keep])
  Qg[i, i] <- Gi / exp(mean(log(diag(Gi)))) }
dimnames(Qg) <- list(lv, lv)
cat("components:", length(unique(comp)), " sizes:", paste(table(comp), collapse = " "), " isolated:", sum(rowSums(W) == 0), "\n")
cat("geometric mean marginal variance by component:", round(tapply(diag(Qg), comp, function(x) exp(mean(log(x)))), 3), "\n")
saveRDS(Qg, "out/bym2_Qginv_scaled.rds")
