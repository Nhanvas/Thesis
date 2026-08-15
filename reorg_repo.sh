#!/usr/bin/env bash
# reorg_repo.sh — don repo sau khi lock baseline v3.1. Chay tu REPO ROOT.
#   cd F:/Study/Thesis/Code && bash reorg_repo.sh
# KHONG tu commit. Chay xong -> xem `git status` -> tu commit.
# Nguyen tac: archive-not-delete cho provenance; chi DELETE scratch. Giu flat-import cua src/.

cd "$(git rev-parse --show-toplevel)" || { echo "not a git repo"; exit 1; }
echo "repo root = $(pwd)"

PRE="results/history_superseded/pre_rebuild_detection"
R1="results/history_superseded/2026-08-14_rebuild_round1"
mkdir -p "$PRE" "$R1" archive src

mv_if () {  # mv_if <src> <dest_dir>
  if [ -e "$1" ]; then mv "$1" "$2"/ && echo "  moved  $1 -> $2/"; else echo "  skip   $1 (khong co)"; fi
}

echo ""
echo "== 1) ARCHIVE ket qua PRE-REBUILD (nguon so 0.750/0.829 da dua co) =="
for d in results/cpd results/phaseB results/phaseB_newweight results/phaseA_appendix \
         results/figures results/logs results/attribution_v3; do
  mv_if "$d" "$PRE"
done

echo ""
echo "== 2) ARCHIVE artifact round-1 era =="
mv_if "results/attrib_w403525" "$R1"

echo ""
echo "== 3) ARCHIVE code bi bac (Decision #24 FP-filter) =="
mv_if "src/fp_reduction_prior" "archive"

echo ""
echo "== 4) ARCHIVE orphan checkpoint (khac hash canonical joint GAE) =="
if [ -e "results/best_model.pt" ]; then
  mkdir -p archive/scaffolding
  mv "results/best_model.pt" "archive/scaffolding/orphan_best_model_20260509.pt" \
    && echo "  moved  results/best_model.pt -> archive/scaffolding/orphan_best_model_20260509.pt"
fi

echo ""
echo "== 5) GOM .py lac o ROOT vao src/ (FLAT — khong tao subdir, giu import) =="
for f in attribution_detail.py compare_labels_pernode.py validate_dominant_hitk_FINAL.py \
         label_eeg_pilot.py dump_components.py; do
  mv_if "$f" "src"
done

echo ""
echo "== 6) DELETE scratch (khong phai provenance cua so nao) =="
for f in scan_out.txt; do
  if [ -e "$f" ]; then rm -f "$f" && echo "  deleted $f"; fi
done

echo ""
echo "== 7) GIU NGUYEN (historical/canonical — khong dung) =="
echo "  KEEP  results/retrain_v3p1/         (BASELINE-OF-RECORD)"
echo "  KEEP  results/attribution_v5/       (attribution hien hanh)"
echo "  KEEP  results/locked/               (1 file, thesis_repro_lock doc -> giu de repro so retired)"
echo "  KEEP  results/attribution/, results/history_topology/  (verify rieng neu can)"
echo "  KEEP  data/models_retrain/, data/models/, data/processed/, data/splits/"

echo ""
echo "== 8) stage cho git (git tu nhan dien rename/delete) =="
git add -A
echo ""
echo "DONE. Kiem tra:"
echo "  git status            # chi nen thay moved/deleted cua file da track"
echo "  git status | grep -i retrain_v3p1   # PHAI rong (baseline khong bi dung toi)"
echo ""
echo "Neu OK:"
echo "  git commit -m \"Reorg: archive pre-rebuild + round-1 artifacts; group loose scripts into src/; drop scratch\""
echo "  git push origin main"
