import pandas as pd
import numpy as np
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from datetime import datetime

def run_stability_audit(new_stats_df, engine):
    """
    Compares descriptive labels (names) to ignore random ID switching.
    """
    try:
        # Check if table exists first
        with engine.connect() as conn:
            result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'dim_pitcher_archetypes')"))
            exists = result.scalar()
        
        if not exists:
            print("ℹ️ First run detected: Archetype table created.")
            return

        old_df = pd.read_sql("SELECT pitcher, archetype_name AS old_label FROM dim_pitcher_archetypes", engine)
        comparison = new_stats_df.merge(old_df, on='pitcher', how='inner')
        
        comparison['new_label'] = comparison['archetype_name'].str.strip()
        comparison['old_label'] = comparison['old_label'].str.strip()
        
        changes = comparison[comparison['new_label'] != comparison['old_label']].copy()
        
        if not changes.empty:
            print(f"📈 Real evolution detected for {len(changes)} pitchers.")
            audit_log = changes[['pitcher', 'full_name', 'old_label', 'new_label']].copy()
            audit_log.columns = ['pitcher_id', 'full_name', 'old_archetype', 'new_archetype']
            audit_log['change_date'] = datetime.now()
            audit_log.to_sql('audit_pitcher_archetype_changes', engine, if_exists='append', index=False)
        else:
            print("✅ Data stable: No pitchers changed their identity.")
    except Exception as e:
        print(f"ℹ️ Audit skipped: {e}")

def update_dim_pitcher_archetypes(engine):
    # 1. Pull data
    query = """
    WITH pitcher_names AS (
        SELECT key_mlbam, CONCAT(first_name_chadwick, ' ', last_name_chadwick) as full_name 
        FROM dim_player
    )
    SELECT 
        p.pitcher, pn.full_name,
        AVG(CASE WHEN p.pitch_type IN ('FF', 'SI', 'FC') THEN p.release_speed END) as fb_velo,
        AVG(p.release_speed) as overall_avg_velo,
        AVG(p.release_spin_rate) as avg_spin,
        AVG(p.pfx_x) as avg_horiz_mvmt_ft,
        AVG(p.pfx_z) as avg_vert_mvmt_ft
    FROM fact_statcast_pitches p
    JOIN pitcher_names pn ON p.pitcher = pn.key_mlbam
    GROUP BY p.pitcher, pn.full_name HAVING COUNT(*) > 100
    """
    all_pitchers = pd.read_sql(query, engine)

    # 2. Conversions
    all_pitchers['avg_horiz_mvmt'] = (all_pitchers['avg_horiz_mvmt_ft'] * 12).round(2)
    all_pitchers['avg_vert_mvmt'] = (all_pitchers['avg_vert_mvmt_ft'] * 12).round(2)
    all_pitchers['avg_velo'] = all_pitchers['fb_velo'].fillna(all_pitchers['overall_avg_velo']).round(1)

    # 3. Handle Specialists (Knuckleballers, etc.)
    specialists = all_pitchers[all_pitchers['fb_velo'].isna()].copy()
    normal_pitchers = all_pitchers[all_pitchers['fb_velo'].notna()].copy()

    if not specialists.empty:
        specialists['archetype_name'] = specialists['overall_avg_velo'].apply(
            lambda x: "Position Player / Eephus" if x < 78 else "Knuckleball / Junkball Specialist"
        )
        specialists['archetype_id'] = 99

    # 4. Cluster Normal Pitchers
    features = ['fb_velo', 'avg_spin', 'avg_horiz_mvmt', 'avg_vert_mvmt']
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(normal_pitchers[features])
    
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    normal_pitchers['archetype_id'] = kmeans.fit_predict(scaled_data)

    profiles = normal_pitchers.groupby('archetype_id')[features].mean()
    special_ids = {
        profiles['fb_velo'].idxmax(): "Power Flamethrower",
        profiles['fb_velo'].idxmin(): "Soft-Tossing Crafty Veteran",
        profiles['avg_spin'].idxmax(): "Breaking Ball Specialist",
        profiles['avg_horiz_mvmt'].abs().idxmax(): "Sinker / Tail Specialist",
        profiles['avg_vert_mvmt'].idxmax(): "Deceptive Angle Specialist"
    }

    remaining = [i for i in range(8) if i not in special_ids]
    tiers = ["High-Intensity Power Pitcher", "Elite Command Specialist", "Tactical Movement Artist"]
    sorted_rem = profiles.loc[remaining].sort_values('fb_velo', ascending=False).index
    
    dynamic_map = special_ids.copy()
    for i, cluster_id in enumerate(sorted_rem):
        if i < len(tiers):
            dynamic_map[cluster_id] = tiers[i]
        else:
            dynamic_map[cluster_id] = f"Finesse Specialist (Group {cluster_id})"

    normal_pitchers['archetype_name'] = normal_pitchers['archetype_id'].map(dynamic_map)

    # 5. Combine and Percentiles
    final_stats = pd.concat([normal_pitchers, specialists])
    final_stats['velo_percentile'] = (final_stats['avg_velo'].rank(pct=True) * 100).round(0)
    final_stats['spin_percentile'] = (final_stats['avg_spin'].rank(pct=True) * 100).round(0)
    final_stats['mvmt_percentile'] = ((final_stats['avg_horiz_mvmt'].abs() + final_stats['avg_vert_mvmt'].abs()).rank(pct=True) * 100).round(0)
    # Add the current timestamp to every row
    final_stats['calculation_date'] = datetime.now()

    # 6. Audit & Update
    run_stability_audit(final_stats, engine)

    with engine.connect() as conn:
        # Create table if it doesn't exist so TRUNCATE doesn't fail
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_pitcher_archetypes (
                pitcher INT PRIMARY KEY,
                full_name TEXT,
                archetype_id INT,
                archetype_name TEXT,                
                avg_velo FLOAT,
                avg_spin FLOAT,
                avg_horiz_mvmt FLOAT,
                avg_vert_mvmt FLOAT,
                velo_percentile FLOAT,
                spin_percentile FLOAT,
                mvmt_percentile FLOAT,
                calculation_date TIMESTAMP
            )
        """))
        conn.execute(text("TRUNCATE TABLE dim_pitcher_archetypes;"))
        conn.commit()

    db_cols = [
        'pitcher', 'full_name', 'archetype_id', 'archetype_name', 'avg_velo', 'avg_spin', 
        'avg_horiz_mvmt', 'avg_vert_mvmt', 'velo_percentile', 'spin_percentile', 'mvmt_percentile',
        'calculation_date'
    ]
    final_stats[db_cols].to_sql('dim_pitcher_archetypes', engine, if_exists='append', index=False)
    
    print(f"🚀 Success: {len(final_stats)} pitchers updated with scouting percentiles.")
    
# avg_horiz_mvmt: For a Righty, a negative number (e.g., -12.0) means the ball "runs" 12 inches away from a left-handed hitter.

# velo_percentile: If Skubal is at 99, it means he throws harder than 99% of all other pitchers in your dataset.

# mvmt_percentile: This is a "total movement" score, showing who has the nastiest, most "wiggly" pitches in the league.