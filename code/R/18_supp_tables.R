# Supplementary exports: BYM2 province effect, variance components of the primary model, lag-specific RRs, phi profile.
suppressPackageStartupMessages({library(data.table); library(glmmTMB)})
r <- readRDS("out/v2_primary.rds"); m <- r$m
re <- ranef(m)$cond$one; fwrite(data.table(shapeID = sub("^prov", "", colnames(re)), effect = as.numeric(re[1, ])), "out/bym2_province_effect.csv")
vc <- VarCorr(m)$cond
comp <- rbindlist(lapply(names(vc), function(n) { v <- vc[[n]]; sd <- attr(v, "stddev")
  data.table(term = n, component = names(sd), sd = as.numeric(sd), corr = if (!is.null(attr(v, "correlation")) && ncol(v) > 1) attr(v, "correlation")[1, 2] else NA_real_) }))
comp <- comp[!grepl("^tf", component) | component == component[grepl("^tf", component)][1]]   # AR(1): one row
comp <- comp[!(term == "one" & component != component[term == "one"][1])]                   # BYM2: one row (common scale)
fwrite(comp, "out/primary_variance_components.csv"); print(comp)
L <- fread("out/curves_lag_v2_primary.csv")[lag %in% 0:6]; A <- fread("out/curves_lag_v2_anomaly.csv")[lag %in% 0:6]
fwrite(rbind(L, A), "out/lag_specific_RR.csv")
ph <- rbindlist(lapply(c("0.2", "0.5", "0.75", "0.9", "0.99"), function(p) { f <- sprintf("out/v2_bym2_%s.rds", p); if (!file.exists(f)) return(NULL)
  x <- readRDS(f); data.table(phi = as.numeric(p), AIC = AIC(x$m),
    T90 = x$cpT$allRRfit[as.character(28.5)], T90lo = x$cpT$allRRlow[as.character(28.5)], T90hi = x$cpT$allRRhigh[as.character(28.5)]) }))
iid <- readRDS("out/v2_iid.rds"); ph <- rbind(data.table(phi = 0, AIC = AIC(iid$m), T90 = iid$cpT$allRRfit["28.5"], T90lo = iid$cpT$allRRlow["28.5"], T90hi = iid$cpT$allRRhigh["28.5"]), ph)
fwrite(ph, "out/bym2_phi_profile.csv"); print(ph)
