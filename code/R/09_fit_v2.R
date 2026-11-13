# Primary and sensitivity models (glmmTMB): Poisson with distributed lag non-linear cross-bases for temperature and rainfall,
# ONI lags 0-6, country harmonics with province-specific random harmonic deviations, country-by-year effect, province effect
# (BYM2 covariance when P3_BYM2=<phi> is set, otherwise unstructured), province AR(1) over all calendar months, log population offset.
# Usage: Rscript code/R/09_fit_v2.R <label> [key=value ...]
#   keys: subset=ALL|ISO,ISO  drop_years=2015,2016  holdout=1 (2021-22 given zero weight)  noclimate=1  noONI=1  anomaly=1
#         urban=1 [urbanraw=1]  urbtert=1  offset=0  harm=3  rainlog=1  lag=9  lagdf=4  cknots=1  ctrymonth=1  bym2=<phi>
suppressPackageStartupMessages({library(data.table); library(dlnm); library(glmmTMB)})
M <- readRDS("out/p3_model_data.rds"); list2env(M, environment())
a <- commandArgs(TRUE); LABEL <- a[1]; kv <- setNames(sub(".*=", "", a[-1]), sub("=.*", "", a[-1]))
opt <- function(k, d = "") if (k %in% names(kv)) kv[[k]] else d
SUBSET <- opt("subset", "ALL"); DROP <- as.integer(strsplit(opt("drop_years", ""), ",")[[1]])
HOLD <- opt("holdout") == "1"; NOCLIM <- opt("noclimate") == "1"; NOONI <- opt("noONI") == "1"
ANOM <- opt("anomaly") == "1"; HARM <- as.integer(opt("harm", "2")); RLOG <- opt("rainlog") == "1"
NOTR <- opt("notrend") == "1"; CM <- opt("ctrymonth") == "1"; CK <- opt("cknots") == "1"; LAGX <- as.integer(opt("lag", "6")); LDF <- as.integer(opt("lagdf", "3"))
 URB <- opt("urban") == "1"; OFF <- opt("offset", if (isTRUE(HAS_POP)) "1" else "0") == "1"

cbT <- cb_t; cbR <- cb_r; rt0 <- ref_t; rr0 <- ref_r; ktu <- kt; kru <- kr
sel0 <- (SUBSET == "ALL" | D$iso3 %in% strsplit(SUBSET, ",")[[1]]) & !(D$year %in% DROP)
if (RLOG || CK || LAGX != 6 || LDF != 3) {     # rebuild cross-bases from the full 2009–22 series
  R0 <- fread("data/P3_dengue_admin1_month_climate.csv")[shapeID %in% unique(D$shapeID) & year %between% c(2009, 2022)]
  setorder(R0, shapeID, year, month); LAG <- LAGX; arglag <- list(fun = "ns", df = LDF, intercept = TRUE)
  lm0 <- function(x, g) sapply(0:LAG, function(l) ave(x, g, FUN = function(v) shift(v, l)))
  i0 <- which(R0$year >= 2010); key0 <- match(paste(D$shapeID, D$year, D$month), paste(R0$shapeID[i0], R0$year[i0], R0$month[i0]))
  rv <- if (RLOG) log1p(R0$power_precip_mm) else R0$power_precip_mm
  TM <- lm0(R0$power_tmean_c, R0$shapeID)[i0, ][key0, ]; RM <- lm0(rv, R0$shapeID)[i0, ][key0, ]
  base_t <- TM[sel0, 1]; base_r <- RM[sel0, 1]
  if (CK) { ktu <- quantile(base_t, c(.1, .5, .9), na.rm = TRUE); kru <- quantile(base_r, c(.1, .5, .9), na.rm = TRUE)
            rt0 <- median(base_t, na.rm = TRUE); rr0 <- median(base_r, na.rm = TRUE) }
  else if (RLOG) { kru <- quantile(base_r, c(.1, .5, .9), na.rm = TRUE); rr0 <- median(base_r, na.rm = TRUE) }
  bt <- range(TM[sel0, ], na.rm = TRUE); br <- range(RM[sel0, ], na.rm = TRUE)
  cbT <- crossbasis(TM, lag = LAG, argvar = list(fun = "ns", knots = ktu, Boundary.knots = bt), arglag = arglag)
  cbR <- crossbasis(RM, lag = LAG, argvar = list(fun = "ns", knots = kru, Boundary.knots = br), arglag = arglag)
  colnames(cbT) <- paste0("cbT.", colnames(cbT)); colnames(cbR) <- paste0("cbR.", colnames(cbR))
}
if (ANOM) {                                   # cross-bases on anomalies from province calendar-month climatology (2010–20)
  R <- fread("data/P3_dengue_admin1_month_climate.csv")[shapeID %in% unique(D$shapeID) & year %between% c(2009, 2022)]
  setorder(R, shapeID, year, month)
  R[, `:=`(ta = power_tmean_c - mean(power_tmean_c[year %between% c(2010, 2020)]),
           ra = power_precip_mm - mean(power_precip_mm[year %between% c(2010, 2020)])), by = .(shapeID, month)]
  lagm <- function(x, g) sapply(0:LAG, function(l) ave(x, g, FUN = function(v) shift(v, l)))
  i <- which(R$year >= 2010); key <- match(paste(D$shapeID, D$year, D$month), paste(R$shapeID[i], R$year[i], R$month[i]))
  TA <- lagm(R$ta, R$shapeID)[i, ][key, ]; RA <- lagm(R$ra, R$shapeID)[i, ][key, ]
  cbT <- crossbasis(TA, lag = LAG, argvar = list(fun = "ns", knots = quantile(TA[, 1], c(.1, .5, .9), na.rm = TRUE)), arglag = arglag)
  cbR <- crossbasis(RA, lag = LAG, argvar = list(fun = "ns", knots = quantile(RA[, 1], c(.1, .5, .9), na.rm = TRUE)), arglag = arglag)
}
X <- data.frame(y = D$dengue_cases, ctry = factor(D$iso3), cy = factor(D$cy_id), prov = factor(D$shapeID),
                tf = factor(D$t, levels = sort(unique(D$t))), year_c = D$year_c, year = D$year,
                s1 = sin(2 * pi * D$month / 12), c1 = cos(2 * pi * D$month / 12),
                s2 = sin(4 * pi * D$month / 12), c2 = cos(4 * pi * D$month / 12))
for (h in 1:HARM) { X[[paste0("s", h)]] <- sin(2 * pi * h * D$month / 12); X[[paste0("c", h)]] <- cos(2 * pi * h * D$month / 12) }
HS <- paste(paste0(c("s", "c"), rep(1:HARM, each = 2)), collapse = " + ")
X$cbT <- cbT; X$cbR <- cbR; X$ONI <- Om
if (OFF) X$logpop <- log(D$population)
URBRAW <- opt("urbanraw") == "1"; URBT <- opt("urbtert") == "1"
if (URB) { bfx <- if (URBRAW) D$built_fraction else log(D$built_fraction); X$u <- as.numeric(scale(bfx)); X$cbTu <- cbT * X$u; X$cbRu <- cbR * X$u }
if (URBT) { pb <- D[, .(b = mean(built_fraction)), by = .(iso3, shapeID)][, tt := as.integer(cut(rank(b, ties.method = "first"), 3, labels = FALSE)), by = iso3]
  tt <- pb$tt[match(D$shapeID, pb$shapeID)]; X$t2 <- as.numeric(tt == 2); X$t3 <- as.numeric(tt == 3)
  X$cbTt2 <- cbT * X$t2; X$cbTt3 <- cbT * X$t3; X$cbRt2 <- cbR * X$t2; X$cbRt3 <- cbR * X$t3 }
keep <- (SUBSET == "ALL" | D$iso3 %in% strsplit(SUBSET, ",")[[1]]) & !(D$year %in% DROP)
X <- X[keep, ]; X$ctry <- droplevels(X$ctry); X$prov <- droplevels(X$prov); X$cy <- droplevels(X$cy)  # tf levels kept intact
yobs <- X$y; X$w <- if (HOLD) as.numeric(X$year < 2021) else 1
nn <- !is.na(X$y); idx <- which(keep)[nn]; keep <- seq_along(keep) %in% idx; X <- X[nn, ]; yobs <- X$y
multi <- nlevels(X$ctry) > 1
fx <- c(if (!NOCLIM) c("cbT", "cbR"), if (!NOONI) "ONI", if (URB) c("u", "cbTu", "cbRu"), if (URBT) c("t2", "t3", "cbTt2", "cbTt3", "cbRt2", "cbRt3"),
        if (multi) paste0("ctry * (", HS, ")") else HS)
BYM <- opt("bym2", Sys.getenv("P3_BYM2", ""))
if (BYM != "") { phi <- as.numeric(BYM); Qg <- readRDS("out/bym2_Qginv_scaled.rds")[levels(X$prov), levels(X$prov)]
  SIG <- (1 - phi) * diag(nrow(Qg)) + phi * Qg; dimnames(SIG) <- dimnames(Qg); X$one <- factor(1) }
re <- c("(1 | cy)", if (BYM != "") "propto(0 + prov | one, SIG)" else "(1 | prov)", paste0("diag(0 + ", HS, " | prov)"), if (!OFF && !NOTR) "(0 + year_c | prov)", "ar1(tf + 0 | prov)", if (CM) "(1 | ctry:tf)")
form <- as.formula(paste("y ~", paste(c(fx, re, if (OFF) "offset(logpop)"), collapse = " + ")))
t0 <- Sys.time()
m <- glmmTMB(form, family = poisson, data = X, weights = w,
             control = glmmTMBControl(parallel = 2, optCtrl = list(iter.max = 3000, eval.max = 3000)))
cat(LABEL, "fitted in", round(difftime(Sys.time(), t0, units = "mins"), 1), "min; n =", sum(X$w > 0),
    "; converged:", m$fit$convergence == 0, "; pdHess:", m$sdr$pdHess, "; AIC:", round(AIC(m)), "\n")
out <- list(m = m, keep = keep, opt = kv, aic = AIC(m))
if (!NOCLIM) {
  b <- fixef(m)$cond; V <- vcov(m)$cond
  pk <- function(p) { i <- grep(paste0("^", p, "(cb|v)"), names(b)); list(coef = b[i], vcov = V[i, i]) }
  rt <- if (ANOM) 0 else round(rt0, 1); rr <- if (ANOM) 0 else (if (RLOG) round(rr0, 2) else round(rr0)); kt <- ktu; kr <- kru
  tt <- D$power_tmean_c[sel0]; rrv <- D$power_precip_mm[sel0]; if (RLOG) rrv <- log1p(rrv)
  at_t <- if (ANOM) round(seq(-3, 3, .1), 1) else sort(unique(round(c(seq(quantile(tt, .01), quantile(tt, .99), by = .1), kt, rt), 1)))
  at_r <- if (ANOM) round(seq(-200, 300, 2)) else if (RLOG) sort(unique(round(c(seq(0, quantile(rrv, .99), by = .02), kr, rr), 2))) else sort(unique(round(c(seq(0, quantile(rrv, .99), by = 2), kr, rr))))
  A1 <- pk("cbT"); A2 <- pk("cbR")
  out$cpT <- crosspred(cbT, coef = A1$coef, vcov = A1$vcov, model.link = "log", cen = rt, at = at_t, bylag = .2, cumul = TRUE)
  out$cpR <- crosspred(cbR, coef = A2$coef, vcov = A2$vcov, model.link = "log", cen = rr, at = at_r, bylag = .2, cumul = TRUE)
  s <- function(cp, x) sprintf("%.2f (%.2f–%.2f)", cp$allRRfit[as.character(x)], cp$allRRlow[as.character(x)], cp$allRRhigh[as.character(x)])
  rk <- function(x) if (RLOG) round(x, 2) else round(x)
  out$ref <- c(t = rt, r = rr); out$knots <- list(t = kt, r = kr)
  if (!ANOM) cat("Temperature P10", round(kt[1], 1), ":", s(out$cpT, round(kt[1], 1)), "  P90", round(kt[3], 1), ":", s(out$cpT, round(kt[3], 1)),
                 "\nRainfall    P10", rk(kr[1]), ":", s(out$cpR, rk(kr[1])), "  P90", rk(kr[3]), ":", s(out$cpR, rk(kr[3])), "\n")
  else cat("Anomaly +1°C:", s(out$cpT, 1), " +2°C:", s(out$cpT, 2), " −1°C:", s(out$cpT, -1), "  rain −50 mm:", s(out$cpR, -50), " +100 mm:", s(out$cpR, 100), "\n")
}
if (HOLD) { mu <- fitted(m)
  out$hold <- data.table(prov = X$prov, year = X$year, tf = X$tf, y = yobs, mu = mu)[year >= 2021] }
saveRDS(out, sprintf("out/v2_%s.rds", LABEL))
