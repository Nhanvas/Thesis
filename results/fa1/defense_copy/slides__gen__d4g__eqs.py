"""Equation images for the D4g appendix (matplotlib mathtext). Equations transcribed from the report (Eq. 1-12)."""
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["mathtext.fontset"] = "stix"
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
EQ = {
 "car":   r"$\tilde{x}_c(t)=x_c(t)-\frac{1}{18}\sum_{k=1}^{18}x_k(t)$",
 "wpli":  r"$\mathrm{wPLI}_{xy}=\frac{\left|\,E\left[\mathrm{Im}(C_{xy})\right]\right|}{E\left[\,\left|\mathrm{Im}(C_{xy})\right|\,\right]}$",
 "aec":   r"$\mathrm{AEC}_{xy}=\left|\,\mathrm{corr}\left(|H(x)|,\,|H(y)|\right)\right|$",
 "adj":   r"$A=0.5\,A_{\mathrm{wPLI}}+0.5\,A_{\mathrm{AEC}}$",
 "bp":    r"$x_{c,b}=\log\left(\frac{1}{|F_b|}\sum_{f\in F_b}\hat{P}_c(f)+\varepsilon\right)$",
 "row":   r"$x_{c,j}=A_{cj}\,/\,\max_{k,l}A_{kl},\quad j=1..18$",
 "ll":    r"$\mathrm{LL}_c=\log\left(\frac{1}{T-1}\sum_{t}|x_c(t)-x_c(t-1)|\right)$",
 "kurt":  r"$\kappa'_c=\mathrm{sign}(\kappa_c)\,\log(1+|\kappa_c|)$",
 "gcn":   r"$Z=\tilde{A}\,\mathrm{ReLU}(\tilde{A}XW_1)W_2,\qquad \tilde{A}=\tilde{D}^{-1/2}(A+I)\tilde{D}^{-1/2}$",
 "loss":  r"$L=\mathrm{MSE}(A,\hat{A})+\lambda\,\mathrm{MSE}(X_t,\hat{X}_t),\qquad \hat{A}=\mathrm{clamp}(ZZ^{\top},0,1),\ \lambda=0.1$",
 "maha":  r"$D_c(t)=\left(z_c(t)-\mu_c\right)^{\top}\Sigma_c^{-1}\left(z_c(t)-\mu_c\right)$",
 "rz":    r"$r_c(t)=\frac{D_c(t)-\mathrm{median}_t\,D_c}{\mathrm{MAD}_t\,D_c}$",
 "drift": r"$\tilde{S}_m(t)=S_m(t)-\mathrm{median}\{S_m(u):|u-t|\leq 225,\ u\ \mathrm{in\ the\ file\ of}\ t\}$",
 "ens":   r"$E(t)=\frac{1}{4}\sum_{m=1}^{4}P_m(t)$",
 "budget":r"$p_i=\min\left(\max(q_i,\,0.005),\,0.02\right),\qquad q_i=\frac{1}{N_i}\sum_t\mathbf{1}\left[\bar{r}_i(t)>k\right]$",
 "cpd":   r"$(\hat{\tau}_1,\hat{\tau}_2)=\arg\min_{\tau_1<\tau_2}\sum_{j=1}^{3}\left[\sum_{t\in s_j}k(x_t,x_t)-\frac{1}{|s_j|}\sum_{t,u\in s_j}k(x_t,x_u)\right]$",
 "sens":  r"$\mathrm{Sensitivity}=\frac{TP}{TP+FN}$",
 "prec":  r"$\mathrm{Precision}=\frac{TP}{TP+FP}$",
 "f1":    r"$F_1=\frac{2\,TP}{2\,TP+FP+FN}$",
 "fpday": r"$\mathrm{FP/day}=\frac{FP}{T_{\mathrm{non\text{-}seizure}}}\times 24$",
}
for k, tex in EQ.items():
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=30, color="#1E2430")
    fig.savefig(f"{OUT}/eq_{k}.png", dpi=200, bbox_inches="tight", pad_inches=0.06, transparent=False, facecolor="white")
    plt.close(fig)
print("ok", len(EQ))
