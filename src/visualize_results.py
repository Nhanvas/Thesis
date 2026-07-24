import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. EMBEDDED CSV DATA (LOCKED v12 RESULTS)
# ==========================================
csv_data = """subject,pen_mult,beta,n_cps,n_seizures,tp,fn,det_rate,fcp_h,mean_lat_s,n_inter_h,auroc
chb03,0.3,0.6704,1224,7,7,0,1.0,29.09,-1.1,37.88,0.9579
chb03,0.5,1.1174,898,7,7,0,1.0,21.99,-1.1,37.88,0.9579
chb03,1.0,2.2348,514,7,7,0,1.0,12.8,-4.0,37.88,0.9579
chb03,2.0,4.4696,281,7,7,0,1.0,7.05,-12.6,37.88,0.9579
chb03,5.0,11.174,101,7,7,0,1.0,2.48,-21.1,37.88,0.9579
chb03,10.0,22.348,62,7,7,0,1.0,1.45,-21.1,37.88,0.9579
chb06,0.3,0.2951,2495,10,6,4,0.6,34.7,10.0,66.68,0.4401
chb06,0.5,0.4919,1830,10,4,6,0.4,26.78,7.0,66.68,0.4401
chb06,1.0,0.9838,1136,10,3,7,0.3,16.9,8.0,66.68,0.4401
chb06,2.0,1.9676,581,10,2,8,0.2,8.64,6.0,66.68,0.4401
chb06,5.0,4.9189,162,10,0,10,0.0,2.43,,66.68,0.4401
chb06,10.0,9.8378,62,10,0,10,0.0,0.93,,66.68,0.4401
chb13,0.3,0.8591,1017,12,11,1,0.9167,28.26,-1.8,32.84,0.8163
chb13,0.5,1.4319,763,12,10,2,0.8333,21.8,-4.4,32.84,0.8163
chb13,1.0,2.8638,460,12,9,3,0.75,13.55,-7.6,32.84,0.8163
chb13,2.0,5.7277,247,12,8,4,0.6667,7.28,-11.0,32.84,0.8163
chb13,5.0,14.3191,80,12,7,5,0.5833,2.22,-11.4,32.84,0.8163
chb13,10.0,28.6383,24,12,3,9,0.25,0.64,-13.3,32.84,0.8163
chb14,0.3,0.2298,1028,8,5,3,0.625,36.35,-1.6,25.95,0.7301
chb14,0.5,0.3831,770,8,4,4,0.5,28.71,-8.0,25.95,0.7301
chb14,1.0,0.7661,493,8,4,4,0.5,18.65,-8.0,25.95,0.7301
chb14,2.0,1.5323,260,8,3,5,0.375,9.91,-13.3,25.95,0.7301
chb14,5.0,3.8306,73,8,1,7,0.125,2.78,-16.0,25.95,0.7301
chb14,10.0,7.6613,35,8,1,7,0.125,1.31,-16.0,25.95,0.7301
chb15,0.3,0.5011,1463,20,19,1,0.95,32.84,-0.8,39.44,0.8192
chb15,0.5,0.8351,1114,20,18,2,0.9,25.84,-4.0,39.44,0.8192
chb15,1.0,1.6702,693,20,15,5,0.75,16.38,-1.1,39.44,0.8192
chb15,2.0,3.3404,367,20,17,3,0.85,8.52,-2.8,39.44,0.8192
chb15,5.0,8.351,130,20,15,5,0.75,2.89,-5.3,39.44,0.8192
chb15,10.0,16.702,87,20,15,5,0.75,1.83,-2.9,39.44,0.8192
chb16,0.3,0.8224,694,10,8,2,0.8,32.95,-9.5,18.97,0.9095
chb16,0.5,1.3707,523,10,6,4,0.6,26.25,-12.7,18.97,0.9095
chb16,1.0,2.7414,346,10,5,5,0.5,17.71,-15.2,18.97,0.9095
chb16,2.0,5.4828,179,10,6,4,0.6,9.12,-16.0,18.97,0.9095
chb16,5.0,13.707,55,10,1,9,0.1,2.85,-24.0,18.97,0.9095
chb16,10.0,27.414,31,10,0,10,0.0,1.63,,18.97,0.9095
chb17,0.3,3.3605,1271,3,2,1,0.6667,21.84,0.0,20.92,0.7729
chb17,0.5,5.6008,1217,3,2,1,0.6667,19.83,10.0,20.92,0.7729
chb17,1.0,11.2016,1052,3,2,1,0.6667,21.08,10.0,20.92,0.7729
chb17,2.0,22.4032,937,3,2,1,0.6667,21.12,10.0,20.92,0.7729
chb17,5.0,56.008,735,3,1,2,0.3333,22.51,16.0,20.92,0.7729
chb17,10.0,112.016,602,3,0,3,0.0,21.74,,20.92,0.7729
chb18,0.3,0.4326,1185,6,6,0,1.0,30.02,-4.7,35.54,0.9194
chb18,0.5,0.721,901,6,6,0,1.0,23.66,-4.7,35.54,0.9194
chb18,1.0,1.4421,577,6,5,1,0.8333,15.67,0.0,35.54,0.9194
chb18,2.0,2.8842,315,6,5,1,0.8333,8.58,0.0,35.54,0.9194
chb18,5.0,7.2105,111,6,5,1,0.8333,2.98,-4.0,35.54,0.9194
chb18,10.0,14.421,62,6,5,1,0.8333,1.6,-4.0,35.54,0.9194"""

# ==========================================
# 2. DATA PROCESSING & AGGREGATIONS
# ==========================================
df = pd.read_csv(io.StringIO(csv_data))

# Group by pen_mult to calculate global aggregated metrics
global_summary = df.groupby('pen_mult').agg(
    total_tp=('tp', 'sum'),
    total_seizures=('n_seizures', 'sum'),
    avg_fcp=('fcp_h', 'mean')
).reset_index()

global_summary['det_rate'] = (global_summary['total_tp'] / global_summary['total_seizures']) * 100

# Extract subject performance at pen_mult = 0.5 (recommended configuration)
sub_05 = df[df['pen_mult'] == 0.5].copy()
sub_05['det_rate_pct'] = sub_05['det_rate'] * 100
sub_05 = sub_05.sort_values(by='det_rate_pct', ascending=True)

# ==========================================
# 3. PLOTTING DESIGN (1 Row, 2 Columns)
# ==========================================
plt.style.use('seaborn-v0_8-whitegrid')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))

# ------------------------------------------
# PANEL A: Global Pareto Trade-off Curve
# ------------------------------------------
ax1.plot(global_summary['avg_fcp'], global_summary['det_rate'], 
         marker='o', markersize=8, color='#1f77b4', linestyle='-', linewidth=2.5, label='Pareto Frontier')

# Highlight specific operating points
for idx, row in global_summary.iterrows():
    pen = row['pen_mult']
    fcp = row['avg_fcp']
    dr = row['det_rate']
    
    # Custom label styling
    if pen == 0.5:
        # Bold and red highlighting for the recommended point
        ax1.plot(fcp, dr, marker='o', markersize=12, color='#d62728', markeredgecolor='black', zorder=5)
        ax1.text(fcp + 1.0, dr - 1.0, f"pen=0.5 (Balanced)\nDR: {dr:.1f}%, FCP/h: {fcp:.2f}", 
                 fontsize=10, fontweight='bold', color='#d62728', bbox=dict(facecolor='white', alpha=0.8, edgecolor='#d62728'))
    elif pen == 0.3:
        ax1.text(fcp + 1.0, dr + 1.0, f"pen=0.3 (High-Sens)\nDR: {dr:.1f}%", fontsize=9, color='#2ca02c')
    elif pen in [1.0, 2.0, 5.0, 10.0]:
        ax1.text(fcp - 1.0, dr - 3.0, f"pen={pen:.1f}", fontsize=9, color='#555555', ha='right')

ax1.set_title("A. Global Operating Trade-off Curve (76 Seizures)", fontsize=13, fontweight='bold', pad=15)
ax1.set_xlabel("Average False Change Points per Hour (FCP/h)", fontsize=11, labelpad=8)
ax1.set_ylabel("Event-level Detection Rate / Sensitivity (%)", fontsize=11, labelpad=8)
ax1.set_xlim(0, 35)
ax1.set_ylim(30, 95)
ax1.grid(True, linestyle='--', alpha=0.6)

# ------------------------------------------
# PANEL B: Subject-wise Performance (at pen=0.5)
# ------------------------------------------
bars = ax2.barh(sub_05['subject'], sub_05['det_rate_pct'], color='#2ca02c', edgecolor='#1e7b1e', height=0.6, alpha=0.85)

# Highlight chb06 (the challenging inverted subject) in a different color
for i, bar in enumerate(bars):
    subj = sub_05.iloc[i]['subject']
    fcp = sub_05.iloc[i]['fcp_h']
    dr = sub_05.iloc[i]['det_rate_pct']
    
    if subj == 'chb06':
        bar.set_color('#ff7f0e')  # Orange for chb06
        bar.set_edgecolor('#d66500')
        ax2.text(dr + 1.5, i - 0.1, f"DR: {dr:.0f}% (FCP/h: {fcp:.1f}) [Inverted Connectivity]", 
                 fontsize=9.5, fontweight='bold', color='#d66500')
    elif subj == 'chb17':
        bar.set_color('#bcbd22')  # Olive for chb17
        bar.set_edgecolor('#8c8d11')
        ax2.text(dr + 1.5, i - 0.1, f"DR: {dr:.0f}% (FCP/h: {fcp:.1f}) [Multi-session Drift]", 
                 fontsize=9.5, color='#8c8d11')
    else:
        ax2.text(dr + 1.5, i - 0.1, f"DR: {dr:.0f}% (FCP/h: {fcp:.1f})", fontsize=9.5, color='#333333')

ax2.set_title("B. Subject-wise Seizure Detection Rate at pen=0.5", fontsize=13, fontweight='bold', pad=15)
ax2.set_xlabel("Event-level Detection Rate (%)", fontsize=11, labelpad=8)
ax2.set_ylabel("Test Subject ID", fontsize=11, labelpad=8)
ax2.set_xlim(0, 125) # Padding for text labels
ax2.grid(True, axis='x', linestyle='--', alpha=0.6)

# Final Polish & Save
plt.suptitle("Unsupervised Seizure Localization Performance via GAE + PELT CPD", fontsize=15, fontweight='bold', y=0.98)
plt.tight_layout()

# Show the plot window locally
plt.show()