# Paper 3 – step 2: primary model (RQ1–RQ2), urbanisation interaction (RQ3), attributable cases (RQ4), diagnostics
# Needs R-INLA:  install.packages("INLA", repos = c(getOption("repos"), INLA = "https://inla.r-inla-download.org/R/stable"), dep = TRUE)
# Run:  Rscript 01_prepare.R && Rscript 02_fit_inla.R      (set P3_DIR to this folder if running from elsewhere)
suppressPackageStartupMessages({library(data.table); library(dlnm); library(INLA)})
setwd(Sys.getenv("P3_DIR", "."))
M <- readRDS("out/p3_model_data.rds"); list2env(M, environment())
inla.setOption(num.threads = "4:1")

D[, y := dengue_cases]
dat <- cbind(D[, .(y, prov_id, prov_id2 = prov_id, prov_ar = prov_id, ctry_id, month, cy_id, t, year_c)],
             as.data.table(cb_t), as.data.table(cb_r), as.data.table(Om))
if (HAS_POP) dat[, logpop := log(D$population)]

pc_prec <- list(prec = list(prior = "pc.prec", param = c(0.5, 0.01)))          # P(sd > 0.5) = 0.01
pc_bym2 <- list(prec = list(prior = "pc.prec", param = c(0.5, 0.01)), phi = list(prior = "pc", param = c(0.5, 2/3)))
pc_ar1  <- list(prec = list(prior = "pc.prec", param = c(0.5, 0.01)), rho = list(prior = "pc.cor1", param = c(0.7, 0.7)))

rhs_climate <- c(colnames(cb_t), colnames(cb_r))
rhs_oni     <- colnames(Om)
re <- c('f(month, model = "rw2", cyclic = TRUE, replicate = ctry_id, scale.model = TRUE, constr = TRUE, hyper = pc_prec)',
        'f(cy_id, model = "iid", hyper = pc_prec)',
        'f(prov_id, model = "bym2", graph = "out/p3_graph.adj", scale.model = TRUE, constr = TRUE, hyper = pc_bym2)',
        'f(t, model = "ar1", replicate = prov_ar, hyper = pc_ar1)',
        if (!HAS_POP) 'f(prov_id2, year_c, model = "iid", hyper = pc_prec)')     # interim province trend, no offset
make_formula <- function(extra = NULL, oni = TRUE)
  as.formula(paste("y ~ 1 +", paste(c(rhs_climate, if (oni) rhs_oni, extra, re), collapse = " + ")))

fit <- function(f, data = dat) inla(f, family = "nbinomial", data = data,
  offset = if (HAS_POP) data$logpop else NULL,
  control.inla = list(strategy = "adaptive"),
  control.fixed = list(correlation.matrix = TRUE, prec.intercept = 1, prec = 1),
  control.predictor = list(link = 1, compute = TRUE),
  control.compute = list(dic = TRUE, waic = TRUE, cpo = TRUE, config = TRUE, return.marginals.predictor = FALSE),
  verbose = FALSE)

extract_cb <- function(m, cb, prefix, argref, at = NULL) {     # cumulative and lag-specific predictions from INLA
  ix <- grep(paste0("^", prefix), rownames(m$summary.fixed))
  coef <- m$summary.fixed$mean[ix]; names(coef) <- rownames(m$summary.fixed)[ix]
  V <- m$misc$lincomb.derived.covariance.matrix[ix, ix]
  crosspred(cb, coef = coef, vcov = V, model.link = "log", cen = argref, at = at, bylag = 0.25, cumul = TRUE)
}
summ <- function(cp, at) data.table(value = at, RR = cp$allRRfit[as.character(at)],
                                    lo = cp$allRRlow[as.character(at)], hi = cp$allRRhigh[as.character(at)])

# ======================= RQ1–RQ2: primary model =======================
t0 <- Sys.time(); m1 <- fit(make_formula()); cat("Primary model fitted in", round(difftime(Sys.time(), t0, units = "mins"), 1), "min\n")
saveRDS(m1, "out/m1_primary.rds")
at_t <- round(seq(quantile(D$power_tmean_c, .01), quantile(D$power_tmean_c, .99), by = 0.1), 1)
at_r <- round(seq(0, quantile(D$power_precip_mm, .99), by = 2))
cpT <- extract_cb(m1, cb_t, "cbT", ref_t, at = sort(unique(c(at_t, round(kt, 1)))))
cpR <- extract_cb(m1, cb_r, "cbR", ref_r, at = sort(unique(c(at_r, round(kr)))))
res <- rbind(cbind(exposure = "temperature", summ(cpT, round(kt[c(1, 3)], 1))),
             cbind(exposure = "rainfall",    summ(cpR, round(kr[c(1, 3)]))))
fwrite(res, "out/rq1_rq2_cumulative_RR_P10_P90.csv")
saveRDS(list(T = cpT, R = cpR), "out/crosspred_primary.rds")
fwrite(data.table(model = "primary", waic = m1$waic$waic, p_eff = m1$waic$p.eff, dic = m1$dic$dic,
                  logscore = -mean(log(m1$cpo$cpo), na.rm = TRUE), cpo_failures = sum(m1$cpo$failure > 0, na.rm = TRUE)),
       "out/model_fit_primary.csv")

# ---- diagnostics: residual autocorrelation and PIT ----
D[, fitted := m1$summary.fitted.values$mean]
D[, pres := (y - fitted) / sqrt(fitted + fitted^2 / m1$summary.hyperpar$mean[1])]
acf1 <- D[!is.na(pres), .(acf1 = cor(pres[-1], pres[-.N], use = "complete.obs")), by = shapeID]
fwrite(acf1, "out/diag_residual_acf1_by_province.csv")
fwrite(data.table(pit = m1$cpo$pit), "out/diag_pit.csv")
cat("Median residual lag-1 autocorrelation:", round(median(acf1$acf1, na.rm = TRUE), 3), "\n")

# ======================= Sensitivity: model without ONI =======================
m1b <- fit(make_formula(oni = FALSE)); saveRDS(m1b, "out/m1b_noONI.rds")
fwrite(rbind(cbind(exposure = "temperature", summ(extract_cb(m1b, cb_t, "cbT", ref_t, at = round(kt, 1)), round(kt[c(1, 3)], 1))),
             cbind(exposure = "rainfall",    summ(extract_cb(m1b, cb_r, "cbR", ref_r, at = round(kr)), round(kr[c(1, 3)])))),
       "out/sens_noONI_cumulative_RR.csv")

# ======================= RQ3: continuous built-up fraction =======================
if (HAS_POP) {
  u <- as.numeric(scale(D$built_fraction))
  q <- quantile(u, c(.25, .75), na.rm = TRUE)
  cbTu <- cb_t * u; cbRu <- cb_r * u
  colnames(cbTu) <- paste0("cbTu.", seq_len(ncol(cbTu))); colnames(cbRu) <- paste0("cbRu.", seq_len(ncol(cbRu)))
  dat3 <- cbind(dat, as.data.table(cbTu), as.data.table(cbRu), u = u)
  m3 <- fit(make_formula(extra = c("u", colnames(cbTu), colnames(cbRu))), data = dat3); saveRDS(m3, "out/m3_urban.rds")
  # cumulative RR at the 75th vs 25th percentile of built-up fraction: main + u * interaction coefficients
  rq3 <- function(prefix, prefix_u, cb, ref, at) {
    ix <- grep(paste0("^", prefix, "\\."), rownames(m3$summary.fixed)); iu <- grep(paste0("^", prefix_u, "\\."), rownames(m3$summary.fixed))
    V <- m3$misc$lincomb.derived.covariance.matrix
    out <- lapply(c(lo = q[[1]], hi = q[[2]]), function(uu) {
      cf <- m3$summary.fixed$mean[ix] + uu * m3$summary.fixed$mean[iu]
      Vu <- V[ix, ix] + uu^2 * V[iu, iu] + uu * (V[ix, iu] + V[iu, ix])
      crosspred(cb, coef = setNames(cf, rownames(m3$summary.fixed)[ix]), vcov = Vu, model.link = "log", cen = ref, at = at)
    }); out }
  r3T <- rq3("cbT", "cbTu", cb_t, ref_t, at_t); r3R <- rq3("cbR", "cbRu", cb_r, ref_r, at_r)
  saveRDS(list(T = r3T, R = r3R, q = q), "out/crosspred_rq3.rds")
  fwrite(data.table(model = c("primary", "urban interaction"), waic = c(m1$waic$waic, m3$waic$waic),
                    logscore = c(-mean(log(m1$cpo$cpo), na.rm = TRUE), -mean(log(m3$cpo$cpo), na.rm = TRUE))),
         "out/rq3_model_comparison.csv")
}
cat("Done. Outputs in out/\n")
