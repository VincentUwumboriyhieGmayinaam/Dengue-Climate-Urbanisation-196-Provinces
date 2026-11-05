# Paper 3 – GHSL province summaries. RUN THIS ON YOUR PC (R or RStudio). Takes about 10–20 minutes.
# Reads the six GHSL zips in your Downloads folder without unzipping them, sums built-up surface and population
# within each of the 232 provinces, and writes one small CSV next to this script:
#   ...\Paper3_Dengue_Climate\Earth_Engine\P3_ghsl_province_epoch.csv
# How to run: open RStudio, File > Open File > this script, then click "Source" (or press Ctrl+Shift+S).

if (!requireNamespace("terra", quietly = TRUE)) install.packages("terra", repos = "https://cloud.r-project.org")
library(terra)
terraOptions(progress = 0, memfrac = 0.6)

dl  <- file.path(Sys.getenv("USERPROFILE"), "Downloads")
dir <- file.path(Sys.getenv("USERPROFILE"), "OneDrive - University of Health and Allied Sciences", "Desktop", "My Manuscripts",
                 "NTD_Four_Papers_Data", "Paper3_Dengue_Climate", "Earth_Engine")
shpzip <- file.path(dir, "P3_provinces_ADM1_shapefile.zip")
stopifnot(file.exists(shpzip))
tmp <- file.path(tempdir(), "p3shp"); dir.create(tmp, showWarnings = FALSE); unzip(shpzip, exdir = tmp)
V <- vect(file.path(tmp, "P3_provinces_ADM1.shp"))
V <- project(V, "ESRI:54009")
cat("Provinces:", nrow(V), "\n")

out <- list()
for (kind in c("BUILT_S", "POP")) for (ep in c(2010, 2015, 2020)) {
  nm <- sprintf("GHS_%s_E%d_GLOBE_R2023A_54009_1000_V1_0", kind, ep)
  z <- file.path(dl, paste0(nm, ".zip")); stopifnot(file.exists(z))
  r <- rast(paste0("/vsizip/", normalizePath(z, winslash = "/"), "/", nm, ".tif"))
  vals <- numeric(nrow(V)); cells <- integer(nrow(V))
  for (iso in unique(V$iso3)) {                       # crop to each country to keep memory low
    i <- which(V$iso3 == iso); rc <- crop(r, ext(V[i]) + 2000)
    rc[rc < 0] <- NA
    e <- extract(rc, V[i], fun = sum, na.rm = TRUE, ID = FALSE)
    n <- extract(!is.na(rc), V[i], fun = sum, na.rm = TRUE, ID = FALSE)
    vals[i] <- e[[1]]; cells[i] <- n[[1]]
  }
  out[[paste(kind, ep)]] <- data.frame(iso3 = V$iso3, shapeID = V$shapeID, epoch = ep, kind = kind, value = vals, cells = cells)
  cat("done", kind, ep, "\n"); flush.console()
}
R <- do.call(rbind, out)
B <- R[R$kind == "BUILT_S", ]; P <- R[R$kind == "POP", ]
W <- merge(B[, c("iso3", "shapeID", "epoch", "value", "cells")], P[, c("shapeID", "epoch", "value")], by = c("shapeID", "epoch"))
names(W) <- c("shapeID", "epoch", "iso3", "built_m2", "land_km2", "pop")
W$built_fraction <- W$built_m2 / (W$land_km2 * 1e6)
f <- file.path(dir, "P3_ghsl_province_epoch.csv"); write.csv(W, f, row.names = FALSE)
cat("\nSaved:", f, "\n"); print(aggregate(cbind(pop_millions = pop / 1e6) ~ iso3 + epoch, W, sum))
