#!/usr/bin/env bash
# verify_local_complete.sh — chac chan MOI artifact Kaggle-generated da ve local. Chay tu repo root.
cd "$(git rev-parse --show-toplevel)" || exit 1
ok=1
chk () { if [ -e "$1" ]; then echo "  OK   $1"; else echo "  MISS $1  <-- THIEU"; ok=0; fi; }
cnt () { n=$(ls $1 2>/dev/null | wc -l); if [ "$n" -ge "$2" ]; then echo "  OK   $1  ($n file, can >= $2)";
         else echo "  MISS $1  ($n < $2)  <-- THIEU"; ok=0; fi; }

echo "== CHECKPOINTS (mat la ph?i train lai — dung uu tien so 1) =="
chk data/models_retrain/gae_joint_seed42.pt
for s in 42 1 2 3 4; do chk data/models_retrain/lstm_temporal_seed${s}.pt; done

echo "== ENSEMBLE ARRAYS (build_ens tren Kaggle -> local) =="
cnt "results/retrain_v3p1/ens/ens_seed42_*.npy" 16       # 8 subj x 2 split
cnt "results/retrain_v3p1/ens/ens_seed*_chb03_ictal.npy" 5   # 5 seed
cnt "results/retrain_v3p1/val_ens/*.npy" 6                # 3 val x 2 split
cnt "results/retrain_v3p1/ens_dec19/*.npy" 16

echo "== KET QUA CHOT =="
for f in final_eval_seed42.csv final_eval_seed99.csv fp_budget_locked.csv fp_budget_val_verdict.json; do
  chk results/retrain_v3p1/$f; done

echo "== CODE CHUOI INFERENCE (cho web demo chay AI) =="
for f in src/retrain/train_lstm_temporal_v3.py src/retrain/gae_joint.py src/retrain/lstm_temporal.py \
         src/retrain/build_ens.py src/retrain/score_ens.py src/retrain/fp_budget_operating_point.py \
         src/retrain/retrain_io.py src/ensemble_recipe.py src/cpd_pipeline_v14.py src/szcore_eval.py; do
  chk $f; done
for f in src/dataprep/preprocessing.py src/dataprep/graph_construction.py \
         src/dataprep/feature_extraction.py src/dataprep/compute_gamma_aec.py; do chk $f; done

echo ""
echo "== GRAPHS/FEATURES (input _topk20 — CAN cho reproduce baseline; demo tren EDF moi thi KHONG can) =="
cnt "data/processed/**/*_topk20.npy" 1 2>/dev/null || echo "  (kiem tay: graphs co the nam Kaggle dataset, gitignored 32.9GB)"

echo ""
if [ "$ok" = "1" ]; then echo "==> DU HET artifact quan trong tren local."; else
  echo "==> CO FILE THIEU (xem MISS o tren) — keo ve tu Kaggle TRUOC KHI xoa session."; fi
