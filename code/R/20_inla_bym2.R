# Confirmatory fully Bayesian fit of the analysis-plan model in R-INLA: negative binomial likelihood; cross-bases for temperature
# and rainfall (lags 0-6); ONI lags 0-6; country harmonics + province-specific random harmonic deviations; country-by-year iid;
# BYM2 on the province graph (mixing parameter estimated); province AR(1) over months; log population offset; PC priors.
# Then refits with the urbanisation interaction (standardised log built-up fraction). Run from the repository root after
# 01_prepare.R: Rscript code/R/20_inla_bym2.R  (about 8 hours on a laptop). Outputs: out/inla/
t_start <- Sys.time()
dir.create("out/inla", showWarnings = FALSE, recursive = TRUE)
log_con <- file("out/inla/inla_log.txt", open = "wt"); say <- function(...) { m <- paste0(format(Sys.time(), "%H:%M:%S"), "  ", ...); cat(m, "\n"); writeLines(m, log_con); flush(log_con) }
say("Start. R ", R.version.string)

repos <- c(CRAN = "https://cloud.r-project.org", INLA = "https://inla.r-inla-download.org/R/stable")
for (p in c("data.table", "dlnm", "Matrix", "sp", "fmesher")) if (!requireNamespace(p, quietly = TRUE)) install.packages(p, repos = repos["CRAN"])
if (!requireNamespace("INLA", quietly = TRUE)) {
  say("Installing INLA (large download, a few minutes)...")
  install.packages("INLA", repos = repos, dependencies = TRUE)
  if (!requireNamespace("INLA", quietly = TRUE)) {               # newest R versions sometimes need the testing build
    install.packages("INLA", repos = c(CRAN = "https://cloud.r-project.org", INLA = "https://inla.r-inla-download.org/R/testing"), dependencies = TRUE)
  }
}
suppressPackageStartupMessages({library(data.table); library(dlnm); library(INLA)})
say("INLA version ", as.character(packageVersion("INLA")))
inla.setOption(num.threads = paste0(max(1, parallel::detectCores() - 1), ":1"))

M <- readRDS("out/p3_model_data.rds"); D <- M$D; cb_t <- M$cb_t; cb_r <- M$cb_r; Om <- M$Om
stopifnot(isTRUE(M$HAS_POP), nrow(D) == 30576)
D[, `:=`(s1 = sin(2 * pi * month / 12), c1 = cos(2 * pi * month / 12), s2 = sin(4 * pi * month / 12), c2 = cos(4 * pi * month / 12))]
ctry <- factor(D$iso3)
H <- model.matrix(~ ctry * (s1 + c1 + s2 + c2), data = data.frame(ctry, D[, .(s1, c1, s2, c2)]))[, -1]
colnames(H) <- make.names(colnames(H))
dat <- data.table(y = D$dengue_cases, logpop = log(D$population), prov = D$prov_id, cy = D$cy_id, t = D$t - 12L,
                  p_s1 = D$prov_id, p_c1 = D$prov_id, p_s2 = D$prov_id, p_c2 = D$prov_id, s1 = D$s1, c1 = D$c1, s2 = D$s2, c2 = D$c2)
X <- cbind(as.data.table(unclass(cb_t)), as.data.table(unclass(cb_r)), as.data.table(Om), as.data.table(H))
setnames(X, make.names(names(X), unique = TRUE)); dat <- cbind(dat, X)
nT <- grep("^cbT", names(X), value = TRUE); nR <- grep("^cbR", names(X), value = TRUE)
fixed <- c(nT, nR, grep("^oni", names(X), value = TRUE), colnames(H))

pc_prec <- list(prec = list(prior = "pc.prec", param = c(0.5, 0.01)))
pc_bym2 <- list(prec = list(prior = "pc.prec", param = c(0.5, 0.01)), phi = list(prior = "pc", param = c(0.5, 2/3)))
pc_ar1  <- list(prec = list(prior = "pc.prec", param = c(0.5, 0.01)), rho = list(prior = "pc.cor1", param = c(0.7, 0.7)))
re <- c('f(prov, model = "bym2", graph = "out/p3_graph.adj", scale.model = TRUE, constr = TRUE, hyper = pc_bym2)',
        'f(cy, model = "iid", hyper = pc_prec)',
        'f(p_s1, s1, model = "iid", hyper = pc_prec)', 'f(p_c1, c1, model = "iid", hyper = pc_prec)',
        'f(p_s2, s2, model = "iid", hyper = pc_prec)', 'f(p_c2, c2, model = "iid", hyper = pc_prec)',
        'f(t, model = "ar1", replicate = prov, values = 1:156, hyper = pc_ar1)')

fit <- function(rhs, data) {
  f <- as.formula(paste("y ~ 1 +", paste(c(rhs, re), collapse = " + ")))
  inla(f, family = "nbinomial", data = data, offset = data$logpop,
       control.fixed = list(prec.intercept = 0.001, prec = 0.01, correlation.matrix = TRUE),
       control.inla = list(int.strategy = "eb"),
       control.compute = list(waic = TRUE, dic = TRUE, cpo = FALSE, config = FALSE, return.marginals.predictor = FALSE),
       control.predictor = list(compute = TRUE, link = 1), inla.mode = "compact", verbose = FALSE)
}
cp_from <- function(m, cb, names_main, ref, at, names_int = NULL, u = 0) {
  b <- m$summary.fixed$mean; names(b) <- rownames(m$summary.fixed)
  V <- m$misc$lincomb.derived.covariance.matrix
  if (is.null(V)) { S <- inla.posterior.sample(500, m, selection = setNames(as.list(rep(0, length(c(names_main, names_int)))), c(names_main, names_int)))
                    V <- cov(t(sapply(S, function(s) s$latent[, 1]))) ; rownames(V) <- colnames(V) <- c(names_main, names_int) }
  cf <- b[names_main]; vv <- V[names_main, names_main]
  if (!is.null(names_int)) { cf <- cf + u * b[names_int]; vv <- vv + u^2 * V[names_int, names_int] + u * (V[names_main, names_int] + V[names_int, names_main]) }
  crosspred(cb, coef = cf, vcov = vv, model.link = "log", cen = ref, at = at, cumul = TRUE)
}
fmt <- function(cp, x) { x <- as.character(x); sprintf("%.2f (%.2f-%.2f)", cp$allRRfit[x], cp$allRRlow[x], cp$allRRhigh[x]) }

# ---------------- primary model with BYM2 ----------------
say("Fitting primary BYM2 model (can take 10-60 minutes)...")
t0 <- Sys.time(); m1 <- fit(fixed, dat); say("Primary fitted in ", round(difftime(Sys.time(), t0, units = "mins"), 1), " min")
kt <- round(M$kt, 1); kr <- round(M$kr)
at_t <- sort(unique(c(round(seq(16, 30.5, 0.1), 1), kt))); at_r <- sort(unique(c(seq(0, 500, 2), kr)))
cT <- cp_from(m1, cb_t, nT, M$ref_t, at_t); cR <- cp_from(m1, cb_r, nR, M$ref_r, at_r)
res <- data.table(model = "INLA BYM2 primary", T_P10 = fmt(cT, kt[1]), T_P90 = fmt(cT, kt[3]), R_P10 = fmt(cR, kr[1]), R_P90 = fmt(cR, kr[3]),
                  waic = m1$waic$waic, dic = m1$dic$dic)
say("Temperature P10 ", res$T_P10, "  P90 ", res$T_P90, " | Rainfall P10 ", res$R_P10, "  P90 ", res$R_P90)
hp <- data.table(parameter = rownames(m1$summary.hyperpar), m1$summary.hyperpar[, c("mean", "0.025quant", "0.975quant")])
fwrite(hp, "out/inla/hyperparameters_primary.csv"); fwrite(res, "out/inla/cumulative_RR_primary.csv")
fwrite(rbind(data.table(exposure = "temperature", value = cT$predvar, RR = cT$allRRfit, lo = cT$allRRlow, hi = cT$allRRhigh),
             data.table(exposure = "rainfall", value = cR$predvar, RR = cR$allRRfit, lo = cR$allRRlow, hi = cR$allRRhigh)), "out/inla/curves_primary.csv")
sp <- m1$summary.random$prov; fwrite(data.table(prov_id = 1:196, total = sp$mean[1:196], structured = sp$mean[197:392]), "out/inla/spatial_effects.csv")
fwrite(data.table(fitted = m1$summary.fitted.values$mean), "out/inla/fitted_primary.csv")
say("Hyperparameters:"); for (i in seq_len(nrow(hp))) say("  ", hp$parameter[i], ": ", signif(hp$mean[i], 3), " (", signif(hp$`0.025quant`[i], 3), "-", signif(hp$`0.975quant`[i], 3), ")")

# ---------------- urbanisation interaction with BYM2 ----------------
say("Fitting urbanisation interaction under BYM2...")
lb <- log(D$built_fraction); u <- (lb - mean(lb)) / sd(lb); qs <- quantile(u, c(.25, .75))
UT <- as.data.table(unclass(cb_t) * u); UR <- as.data.table(unclass(cb_r) * u)
setnames(UT, paste0("uT", seq_len(ncol(UT)))); setnames(UR, paste0("uR", seq_len(ncol(UR))))
dat3 <- cbind(dat, UT, UR, u = u)
t0 <- Sys.time(); m3 <- fit(c(fixed, "u", names(UT), names(UR)), dat3); say("Urban model fitted in ", round(difftime(Sys.time(), t0, units = "mins"), 1), " min")
ratio <- function(cb, ni, ref, x) {      # ratio of cumulative RRs, P75 vs P25 of built-up fraction
  cp <- cp_from(m3, cb, ni, ref, x); du <- qs[2] - qs[1]
  data.table(value = x, ratio = exp(cp$allfit * du), lo = exp((cp$allfit - 1.96 * cp$allse) * du), hi = exp((cp$allfit + 1.96 * cp$allse) * du)) }
ur <- rbind(cbind(exposure = "temperature", ratio(cb_t, names(UT), M$ref_t, kt[c(1, 3)])), cbind(exposure = "rainfall", ratio(cb_r, names(UR), M$ref_r, kr[c(1, 3)])))
fwrite(ur, "out/inla/urban_ratio_P75_P25.csv"); fwrite(data.table(model = c("primary", "urban"), waic = c(m1$waic$waic, m3$waic$waic)), "out/inla/waic.csv")
for (i in seq_len(nrow(ur))) say("Urban ratio ", ur$exposure[i], " ", ur$value[i], ": ", sprintf("%.2f (%.2f-%.2f)", ur$ratio[i], ur$lo[i], ur$hi[i]))
say("DONE in ", round(difftime(Sys.time(), t_start, units = "mins"), 1), " min. Outputs in out/inla/"); close(log_con)
