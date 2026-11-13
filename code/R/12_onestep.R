# Approximate one-step-ahead quantile residuals: the latent AR state is replaced by its one-step prediction rho * u(t-1)
# (conditional modes) and the predictive distribution is Poisson-lognormal with innovation SD sigma * sqrt(1 - rho^2).
# Reports PIT uniformity, lag-1 and lag-12 autocorrelation within province (consecutive months) and Moran's I by month.
suppressPackageStartupMessages({library(data.table); library(glmmTMB); library(spdep)})
f <- commandArgs(TRUE)[1]; if (is.na(f)) f <- "out/v2_primary.rds"
r <- readRDS(f); m <- r$m; M <- readRDS("out/p3_model_data.rds"); D <- M$D[r$keep]
stopifnot(nrow(D) == length(fitted(m)))
vc <- VarCorr(m)$cond; pv <- grep("^prov", names(vc)); ar <- vc[[pv[length(pv)]]]; rho <- attr(ar, "correlation")[1, 2]; sig <- attr(ar, "stddev")[1]
U <- as.matrix(ranef(m)$cond$prov[, grep("^tf", colnames(ranef(m)$cond$prov))])          # provinces x months
pi_ <- match(D$shapeID, rownames(U)); ti <- match(paste0("tf", D$t), colnames(U))
u_t <- U[cbind(pi_, ti)]; u_p <- ifelse(ti > 1, U[cbind(pi_, pmax(ti - 1, 1))], 0)
eta <- log(fitted(m)) - u_t + rho * u_p; s <- sig * sqrt(1 - rho^2)
gh <- statmod_gh <- local({ n <- 30; i <- 1:(n - 1); b <- sqrt(i / 2); J <- matrix(0, n, n); J[cbind(i, i + 1)] <- b; J[cbind(i + 1, i)] <- b
  e <- eigen(J, symmetric = TRUE); list(x = e$values * sqrt(2), w = e$vectors[1, ]^2) })    # Gauss–Hermite (probabilists')
y <- D$dengue_cases; ok <- !is.na(y)
P <- function(q) { out <- numeric(length(q)); for (k in seq_along(gh$x)) out <- out + gh$w[k] * ppois(q, exp(eta + s * gh$x[k])); out }
set.seed(7); lo <- ifelse(y > 0, P(y - 1), 0); hi <- P(y); pit <- lo + runif(length(y)) * (hi - lo)
pit <- pmin(pmax(pit, 1e-6), 1 - 1e-6); D[, q := qnorm(pit)]; D[!ok, q := NA]
setorder(D, shapeID, t)
a <- D[!is.na(q), { i1 <- which(diff(t) == 1); j12 <- match(t + 12, t)
  .(acf1 = cor(q[i1], q[i1 + 1]), acf12 = cor(q, q[j12], use = "complete.obs")) }, by = shapeID]
g <- readLines("out/p3_graph.adj"); lv <- levels(factor(M$D$shapeID))
nb <- lapply(strsplit(g[-1], " +"), function(v) { v <- as.integer(v[v != ""]); if (v[2] > 0) v[-(1:2)] else 0L })
class(nb) <- "nb"; attr(nb, "region.id") <- lv; W <- nb2listw(nb, style = "W", zero.policy = TRUE)
mi <- D[!is.na(q), { x <- rep(NA_real_, length(lv)); x[match(shapeID, lv)] <- q; okk <- !is.na(x)
  if (sum(okk) < 50) list(I = NA_real_) else list(I = moran.test(x[okk], subset(W, okk, zero.policy = TRUE), zero.policy = TRUE)$estimate[1]) }, by = .(year, month)]
h <- hist(pit[ok], breaks = seq(0, 1, .1), plot = FALSE)$counts / sum(ok)
out <- data.table(fit = basename(f), rho = rho, sigma = sig, pit_KS_D = unname(ks.test(pit[ok], "punif")$statistic),
                  pit_share_0.4_0.6 = mean(pit[ok] > .4 & pit[ok] < .6), pit_share_outer_10pct = mean(pit[ok] < .05 | pit[ok] > .95),
                  median_acf1 = median(a$acf1, na.rm = TRUE), iqr_acf1 = paste(round(quantile(a$acf1, c(.25, .75), na.rm = TRUE), 2), collapse = " to "),
                  median_acf12 = median(a$acf12, na.rm = TRUE), median_moran = median(mi$I, na.rm = TRUE),
                  share_months_moran_gt_0.2 = mean(mi$I > 0.2, na.rm = TRUE))
print(out); print(round(h, 3))
fwrite(a, sub("\\.rds$", "_acf_by_province.csv", f)); fwrite(mi, sub("\\.rds$", "_moran_by_month.csv", f)); fwrite(out, sub("\\.rds$", "_onestep.csv", f)); fwrite(data.table(bin = seq(.05, .95, .1), share = h), sub("\\.rds$", "_pit.csv", f))
