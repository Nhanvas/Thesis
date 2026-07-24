import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ==============================================================================
# 1. PARAMETERS & CONTINUOUS TIMELINE SETUP
# ==============================================================================
np.random.seed(42)
duration_min = 10  # 10 minutes overview
time_min = np.linspace(0, duration_min, 1200) # Clean trend resolution

channels = ['FP1-F7', 'F7-T7', 'FP2-F8', 'F8-T8']
n_channels = len(channels)

# ==============================================================================
# 2. GENERATE COMPRESSED qEEG AMPLITUDE ENVELOPE (Macro Trend - Clean Lines)
# ==============================================================================
eeg_envelope = np.zeros((n_channels, len(time_min)))

# Event indices (minutes)
sz1_start, sz1_end = 2.0, 3.5      # Seizure 1 (True Positive)
art_start, art_end = 5.5, 6.0      # Muscle Artifact (False Positive)
sz2_start, sz2_end = 8.0, 8.7      # Seizure 2 (Brief/Conditional TP/FN)

for ch in range(n_channels):
    # Base background amplitude (normal awake EEG is low voltage: 15-25 uV)
    base = 18.0 + np.random.normal(0, 1.5, len(time_min))
    
    # Seizure 1: High-voltage burst (150 - 180 uV)
    idx_sz1 = (time_min >= sz1_start) & (time_min <= sz1_end)
    base[idx_sz1] = 160.0 + np.random.normal(0, 8.0, np.sum(idx_sz1))
    base[(time_min >= sz1_start-0.1) & (time_min < sz1_start)] = np.linspace(18, 160, np.sum((time_min >= sz1_start-0.1) & (time_min < sz1_start)))
    base[(time_min > sz1_end) & (time_min <= sz1_end+0.1)] = np.linspace(160, 18, np.sum((time_min > sz1_end) & (time_min <= sz1_end+0.1)))

    # Artifact: Very high, unstable amplitude (220 - 260 uV)
    idx_art = (time_min >= art_start) & (time_min <= art_end)
    base[idx_art] = 240.0 + np.random.normal(0, 15.0, np.sum(idx_art))
    base[(time_min >= art_start-0.08) & (time_min < art_start)] = np.linspace(18, 240, np.sum((time_min >= art_start-0.08) & (time_min < art_start)))
    base[(time_min > art_end) & (time_min <= art_end+0.08)] = np.linspace(240, 18, np.sum((time_min > art_end) & (time_min <= art_end+0.08)))

    # Seizure 2: Moderate-voltage burst (80 - 100 uV)
    idx_sz2 = (time_min >= sz2_start) & (time_min <= sz2_end)
    base[idx_sz2] = 90.0 + np.random.normal(0, 5.0, np.sum(idx_sz2))
    base[(time_min >= sz2_start-0.1) & (time_min < sz2_start)] = np.linspace(18, 90, np.sum((time_min >= sz2_start-0.1) & (time_min < sz2_start)))
    base[(time_min > sz2_end) & (time_min <= sz2_end+0.1)] = np.linspace(90, 18, np.sum((time_min > sz2_end) & (time_min <= sz2_end+0.1)))

    eeg_envelope[ch] = base

# ==============================================================================
# 3. GENERATE MICRO RAW EEG ZOOM-IN AT SEIZURE 1 ONSET (15 Seconds @ 128 Hz)
# ==============================================================================
fs_zoom = 128
zoom_duration_sec = 15
t_zoom = np.linspace(-7.5, 7.5, zoom_duration_sec * fs_zoom)
onset_idx = len(t_zoom) // 2

raw_eeg = np.zeros((n_channels, len(t_zoom)))
for ch in range(n_channels):
    alpha = 15.0 * np.sin(2 * np.pi * 10 * t_zoom[:onset_idx])
    beta = 6.0 * np.sin(2 * np.pi * 20 * t_zoom[:onset_idx])
    noise_pre = np.random.normal(0, 4.0, onset_idx)
    raw_eeg[ch, :onset_idx] = alpha + beta + noise_pre
    
    delta = 110.0 * np.sin(2 * np.pi * 3.0 * t_zoom[onset_idx:])
    spike_harmonics = 45.0 * np.abs(np.sin(2 * np.pi * 6.0 * t_zoom[onset_idx:]))
    noise_post = np.random.normal(0, 8.0, len(t_zoom) - onset_idx)
    raw_eeg[ch, onset_idx:] = delta + spike_harmonics + noise_post

# ==============================================================================
# 4. PLOTTING THE COMBINED DIAGRAM WITH FIXED LAYOUT
# ==============================================================================
plt.style.use('seaborn-v0_8-whitegrid')
fig, (ax_macro, ax_micro) = plt.subplots(2, 1, figsize=(15, 11))

# Adjust vertical spacing globally to avoid title overlaps
plt.subplots_adjust(hspace=0.42, top=0.90, bottom=0.08)

# ------------------------------------------------------------------------------
# PANEL A: 10-Minute Quantitative EEG (qEEG) Amplitude Trend
# ------------------------------------------------------------------------------
offset_macro = 280.0 # Vertical channel spacing
for i in range(n_channels):
    # Plotting thin clean envelopes
    ax_macro.plot(time_min, eeg_envelope[i] - (i * offset_macro), color='#1e3a8a', linewidth=1.2)

# Set Y-Ticks as Channel Labels directly on the axis (Removes overlaps!)
ax_macro.set_yticks([-(i * offset_macro) for i in range(n_channels)])
ax_macro.set_yticklabels(channels, fontsize=10, fontweight='bold', color='#1e293b')

# Shading: Ground Truth (Red)
ax_macro.axvspan(sz1_start, sz1_end, color='#ef4444', alpha=0.15, label='Clinical Ground Truth (Manual Annotation)')
ax_macro.axvspan(sz2_start, sz2_end, color='#ef4444', alpha=0.15)

# Shading: Predictions (Yellow Hatched)
pred_intervals = [(sz1_start - 0.08, sz1_end + 0.05), (art_start, art_end), (sz2_start - 0.05, sz2_end + 0.02)]
for start, end in pred_intervals:
    ax_macro.axvspan(start, end, color='#f59e0b', alpha=0.10, edgecolor='#f59e0b', linewidth=1.5, linestyle='--', hatch='//', label='Algorithm Localization (pen=0.3)')

# Robust Text Positioning - Placed inside the "Annotation Lane" (y = 230 to 400)
# Arrow pointers connect text boxes to target events below
ax_macro.annotate("TRUE POSITIVE (TP)\nSeizure correctly localized\n(Latency: -4.8s)", 
                  xy=((sz1_start+sz1_end)/2, 180), xytext=((sz1_start+sz1_end)/2, 330),
                  arrowprops=dict(facecolor='#15803d', shrink=0.08, width=1, headwidth=6, headlength=6),
                  fontsize=9, fontweight='bold', ha='center', va='center',
                  bbox=dict(boxstyle="round,pad=0.4", fc='#f0fff4', ec='#166534', lw=1.2))

ax_macro.annotate("FALSE POSITIVE (FP)\nArtifact triggered at pen=0.3\n(Filtered out at pen=1.0)", 
                  xy=((art_start+art_end)/2, 230), xytext=((art_start+art_end)/2, 340),
                  arrowprops=dict(facecolor='#b91c1c', shrink=0.08, width=1, headwidth=6, headlength=6),
                  fontsize=9, fontweight='bold', ha='center', va='center',
                  bbox=dict(boxstyle="round,pad=0.4", fc='#fff5f5', ec='#991b1b', lw=1.2))

ax_macro.annotate("CONDITIONAL ZONE\nTP at pen=0.3\nFN (Missed) at pen=1.0", 
                  xy=((sz2_start+sz2_end)/2, 100), xytext=((sz2_start+sz2_end)/2, 330),
                  arrowprops=dict(facecolor='#374151', shrink=0.08, width=1, headwidth=6, headlength=6),
                  fontsize=9, fontweight='bold', ha='center', va='center',
                  bbox=dict(boxstyle="round,pad=0.4", fc='#f3f4f6', ec='#1f2937', lw=1.2))

ax_macro.set_title("A. COMPRESSED QUANTITATIVE EEG (qEEG) AMPLITUDE TREND (10-Minute Continuous Overview)", 
                   fontsize=11.5, fontweight='bold', color='#0f172a', pad=12)
ax_macro.set_ylabel("Stacked Channels (Envelope Amplitude)", fontsize=10.5)
ax_macro.set_xlim(0, 10)
# Height margin extended up to +480 to secure a clean text-only "Annotation Lane"
ax_macro.set_ylim(-(n_channels * offset_macro) + 200.0, 480.0)
ax_macro.grid(True, linestyle=':', color='#cbd5e1', alpha=0.7)

# Legend placed outside/above the signal plot to guarantee zero overlap
handles, labels = ax_macro.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax_macro.legend(by_label.values(), by_label.keys(), loc='upper right', bbox_to_anchor=(1.0, 1.21),
                frameon=True, facecolor='white', edgecolor='#cbd5e1', framealpha=0.95, fontsize=9)

# ------------------------------------------------------------------------------
# PANEL B: Zoom-in Raw Multi-Channel Waveforms (15-Second Window)
# ------------------------------------------------------------------------------
offset_micro = 300.0 # Vertical raw spacing
for i in range(n_channels):
    ax_micro.plot(t_zoom, raw_eeg[i] - (i * offset_micro), color='#1e293b', linewidth=1.0)

# Set Y-Ticks as Channel Labels for raw waveforms
ax_micro.set_yticks([-(i * offset_micro) for i in range(n_channels)])
ax_micro.set_yticklabels(channels, fontsize=10, fontweight='bold', color='#1e293b')

# Annotation vertical lines
ax_micro.axvline(x=0, color='black', linestyle=':', linewidth=2, label='Clinical Onset Annotation (Ground Truth)')
ax_micro.axvline(x=-0.5, color='#dc2626', linestyle='--', linewidth=1.8, label='PELT Algorithm Detected Onset (-4.0s Early Warning)')

# Context boxes placed inside upper "Annotation Lane" (y = 200 to 350)
ax_micro.text(-3.8, 250, "INTERICTAL BACKGROUND\nLow-voltage Alpha/Beta awake rhythm", 
              fontsize=9, color='#334155', fontweight='bold', ha='center', va='center',
              bbox=dict(boxstyle="square,pad=0.4", fc='#f8fafc', ec='#94a3b8', lw=1.0))

ax_micro.text(3.8, 250, "ICTAL DISCHARGE ONSET\nHigh-voltage synchronous Spike-Wave discharges", 
              fontsize=9, color='#991b1b', fontweight='bold', ha='center', va='center',
              bbox=dict(boxstyle="square,pad=0.4", fc='#fef2f2', ec='#fca5a5', lw=1.0))

ax_micro.set_title("B. MICRO-ZOOM WINDOW: HIGH-RESOLUTION RAW EEG TRANSITION (15-Second Window at Seizure 1 Onset)", 
                   fontsize=11.5, fontweight='bold', color='#0f172a', pad=12)
ax_micro.set_ylabel("Stacked Raw Signals (µV)", fontsize=10.5)
ax_micro.set_xlabel("Time relative to clinical onset (seconds)", fontsize=10.5)
ax_micro.set_xlim(-7.5, 7.5)
# Extended upper limit (+380.0) to secure a clean text-only lane
ax_micro.set_ylim(-(n_channels * offset_micro) + 180.0, 380.0)
ax_micro.grid(True, linestyle=':', color='#cbd5e1', alpha=0.7)

# Legend placed elegantly inside the bottom window, avoiding wave overlaps
ax_micro.legend(loc='lower left', frameon=True, facecolor='white', edgecolor='#cbd5e1', framealpha=0.95, fontsize=9)

# Master Super-Title
plt.suptitle("UNSUPERVISED TEMPORAL SEIZURE LOCALIZATION VISUALIZATION (GAE + PELT)", 
             fontsize=13.5, fontweight='bold', color='#0f172a', y=0.97)

# Show clean, finalized plot
plt.show()