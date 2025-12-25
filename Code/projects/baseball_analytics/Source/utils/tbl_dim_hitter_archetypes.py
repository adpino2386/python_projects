import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy.engine import Engine
from sqlalchemy import text
from datetime import date, timedelta
from datetime import datetime

def create_dim_hitter_archetypes(engine: Engine):
    try:
        print("💾 Creating dim_hitter_archetype...")
        def run_hitter_scouting_model(df):
            """
            Stabilized Hitter Model: Uses Bayesian-weighted metrics to define 
            archetypes and calculate grades.
            """
            
            # 1. Identity Features (The DNA)
            # We use 'stabilized_ev' and 'neutrality_raw' to ensure cluster stability
            identity_features = [
                'chase_pct_raw', 'zone_swing_raw', 'first_pitch_swing_raw',
                'avg_la', 'pull_pct_raw', 'two_strike_contact_raw',
                'woba_vs_hard', 'woba_vs_break', 'woba_vs_offspeed',
                'neutrality_raw', 'stabilized_ev'
            ]
            
            # 2. Effectiveness Scores (Grade Components)
            # Power is now grounded in stabilized EV
            df['power_score'] = (
                (df['ev_pct'] * 0.50) + 
                (df['barrel_pct'] * 0.50)
            ).round(1)
            
            # Eye combines discipline with 'Battle' (2-strike) ability
            df['discipline_score'] = (
                (df['discipline_pct'] * 0.60) + 
                (df['battle_pct'] * 0.40)
            ).round(1)

            # 3. Clustering (Archetype Definition)
            scaler = StandardScaler()
            # Filling NaNs with league average proxies for safety
            scaled_data = scaler.fit_transform(df[identity_features].fillna(df[identity_features].median()))
            
            # 7 Clusters allows for enough nuance (Sluggers, Pests, Specialists, etc.)
            gmm = GaussianMixture(n_components=7, random_state=42, n_init=10)
            df['hitter_cluster'] = gmm.fit_predict(scaled_data)

            # 4. Outlier Detection (Unicorns)
            iso = IsolationForest(contamination=0.03, random_state=42)
            df['is_hitter_unicorn'] = iso.fit_predict(scaled_data)
            
            # 5. Overall Grade Calculation
            def calculate_scouting_grade(row, mode='hitter'):
                """
                Applies the 20-80 Scouting Scale (Standardized).
                A+ = 80 Grade (Generational)
                A  = 70 Grade (Elite All-Star)
                B  = 60 Grade (Plus)
                C  = 50 Grade (Average)
                """
                # 1. Get the combined Z-score from SQL
                z_score = row.get('combined_scouting_z', 0)
                
                # 2. Determine sample size based on player type
                if mode == 'hitter':
                    sample = row.get('total_pitches_faced', 0)
                else:
                    sample = row.get('total_pitches_thrown', 0)
                    
                # 3. Apply Reliability Penalty (Prevents small-sample "fluke" A's)
                if sample < 500:
                    z_score -= 1.0  # Moves a lucky 'A' down to a 'B' or 'C'
                elif sample < 1000:
                    z_score -= 0.4  # Slight penalty for unproven consistency
                    
                # 4. Universal Grade Thresholds
                if z_score >= 2.4:
                    return 'A+'
                elif z_score >= 1.5:
                    return 'A'
                elif z_score >= 0.6:
                    return 'B'
                elif z_score >= -0.5:
                    return 'C'
                else:
                    return 'D/F'

            # Usage:
            df['overall_grade'] = df.apply(lambda x: calculate_scouting_grade(x, mode='hitter'), axis=1)


            # 6. Scouting Report Generation
            def generate_hitter_report(row):
                tags = []
                
                # Logic for tags
                if row['power_score'] >= 90: tags.append("🔥 ELITE POWER")
                if row['discipline_score'] >= 90: tags.append("🎯 DISCIPLINE MASTER")
                if row['two_strike_identity'] == 'ELITE SPOILER': tags.append("🦟 PEST")
                if row['neutrality_pct'] > 85: tags.append("🛡️ MATCHUP PROOF")
                if row['is_hitter_unicorn'] == -1: tags.append("🦄 UNICORN")

                # Vertical Profile Analysis
                v_desc = f"Attacks the {row['vertical_profile']}."
                
                # Build Summary
                conf_prefix = "PROVISIONAL: " if "PROVISIONAL" in row['data_confidence'] else ""
                header = f"[{row['overall_grade']}] {conf_prefix}{row['full_name']} ({row['hand']})"
                
                tag_str = " | ".join(tags)
                body = f"{v_desc} Handles {row['swing_plane']} path. "
                
                # Platoon Insight
                if row['neutrality_pct'] < 30:
                    body += f"Extreme platoon splits detected; high risk against {row['hand']}HP. "
                else:
                    body += "Balanced splits make them difficult to platoon against. "

                return tag_str, f"{header}\nTAGS: {tag_str}\nSUMMARY: {body}"

            df['hitter_tags'], df['hitter_summary'] = zip(*df.apply(generate_hitter_report, axis=1))
            
            return df

        def update_dim_hitter_archetypes(engine):
            """
            SQL to extract the necessary metrics for the Python model.
            """
            query = text("""
            WITH constants AS (
                SELECT 
                    0.312 as lg_woba,    -- Actual 2024-25 league average
                    88.4  as lg_ev,      -- Current league avg exit velocity
                    0.045 as woba_sd,    -- Fixed Standard Deviation for wOBA
                    3.8   as ev_sd,      -- Fixed Standard Deviation for Exit Velocity
                    0.040 as barrel_sd,  -- Fixed Standard Deviation for Barrel Rate
                    500   as m_woba,     -- Reliability threshold for wOBA
                    150   as m_ev        -- Reliability threshold for EV
            ),
            attack_zone_stats AS (
                SELECT 
                    p.*,
                    CASE WHEN p.strikes = 2 THEN 1 ELSE 0 END as is_two_strike,
                    CASE WHEN p.inning >= 7 AND ABS(p.bat_score - p.fld_score) <= 2 THEN 1 ELSE 0 END as is_clutch,
                    CASE WHEN p.zone > 9 AND p.description IN ('swinging_strike', 'foul', 'hit_into_play', 'swinging_strike_blocked') THEN 1 ELSE 0 END as is_chase,
                    CASE WHEN p.zone <= 9 AND p.description IN ('swinging_strike', 'foul', 'hit_into_play', 'swinging_strike_blocked') THEN 1 ELSE 0 END as is_zone_swing,
                    CASE 
                        WHEN (p.stand = 'R' AND p.hc_x < 125) OR (p.stand = 'L' AND p.hc_x > 125) THEN 1 
                        ELSE 0 
                    END as is_pull
                FROM fact_statcast_pitches p
            ),
            hitter_base_stats AS (
                SELECT 
                    p.batter,
                    p.stand AS bat_side,
                    COUNT(*) AS total_pitches_faced,
                    COUNT(CASE WHEN p.type = 'X' THEN 1 END) as balls_in_play,
                    -- Bayesian Stabilized Metrics
                    ((SUM(p.woba_value) + (MAX(c.m_woba) * MAX(c.lg_woba))) / (COUNT(*) + MAX(c.m_woba))) as stabilized_woba,
                    ((SUM(p.launch_speed) + (MAX(c.m_ev) * MAX(c.lg_ev))) / (NULLIF(COUNT(CASE WHEN p.type = 'X' THEN 1 END), 0) + MAX(c.m_ev))) as stabilized_ev,
                    -- Raw Stats for Clustering & Context
                    AVG(CASE WHEN p.pitch_type IN ('FF', 'FA', 'FT', 'SI', 'FC') THEN p.woba_value END) AS woba_vs_hard,
                    AVG(CASE WHEN p.pitch_type IN ('SL', 'ST', 'CU', 'KC', 'SV', 'CS', 'GY', 'KN') THEN p.woba_value END) AS woba_vs_break,
                    AVG(CASE WHEN p.pitch_type IN ('CH', 'FS', 'FO', 'SC', 'EP') THEN p.woba_value END) AS woba_vs_offspeed,            
                    ROUND(SUM(p.is_chase)::numeric / NULLIF(SUM(CASE WHEN p.zone > 9 THEN 1 ELSE 0 END), 0) * 100, 1) as chase_pct_raw,
                    ROUND(SUM(p.is_zone_swing)::numeric / NULLIF(SUM(CASE WHEN p.zone <= 9 THEN 1 ELSE 0 END), 0) * 100, 1) as zone_swing_raw,
                    ROUND(SUM(CASE WHEN p.balls = 0 AND p.strikes = 0 AND p.description IN ('swinging_strike', 'foul', 'hit_into_play') THEN 1 ELSE 0 END)::numeric / 
                        NULLIF(SUM(CASE WHEN p.balls = 0 AND p.strikes = 0 THEN 1 ELSE 0 END), 0) * 100, 1) as first_pitch_swing_raw,
                    ROUND(SUM(CASE WHEN p.description IN ('swinging_strike', 'swinging_strike_blocked') THEN 1 ELSE 0 END)::numeric / 
                        NULLIF(SUM(CASE WHEN p.description IN ('swinging_strike', 'foul', 'hit_into_play') THEN 1 ELSE 0 END), 0) * 100, 1) as whiff_pct_hitter,      
                    AVG(p.launch_speed) AS avg_ev,
                    AVG(p.launch_angle) AS avg_la,
                    SUM(CASE WHEN p.launch_speed_angle = 6 THEN 1 ELSE 0 END)::float / NULLIF(SUM(CASE WHEN p.type = 'X' THEN 1 ELSE 0 END), 0) AS barrel_rate_raw,
                    AVG(CASE WHEN p.plate_z > (p.sz_top + p.sz_bot)/2 THEN p.woba_value END) as woba_high_raw,
                    AVG(CASE WHEN p.plate_z <= (p.sz_top + p.sz_bot)/2 THEN p.woba_value END) as woba_low_raw,      
                    ROUND(SUM(CASE WHEN p.is_two_strike = 1 AND p.description IN ('foul', 'hit_into_play') THEN 1 ELSE 0 END)::numeric / 
                        NULLIF(SUM(CASE WHEN p.is_two_strike = 1 AND p.description IN ('swinging_strike', 'foul', 'hit_into_play') THEN 1 ELSE 0 END), 0) * 100, 1) as two_strike_contact_raw,       
                    AVG(CASE WHEN p.is_clutch = 1 THEN p.woba_value END) as clutch_woba_raw,
                    100 - (ABS(COALESCE(AVG(CASE WHEN p.p_throws = 'L' THEN p.woba_value END), 0.320) - 
                            COALESCE(AVG(CASE WHEN p.p_throws = 'R' THEN p.woba_value END), 0.320)) * 100) as neutrality_raw,
                    ROUND(SUM(p.is_pull)::numeric / NULLIF(SUM(CASE WHEN p.type = 'X' THEN 1 ELSE 0 END), 0) * 100, 1) as pull_pct_raw
                FROM attack_zone_stats p, constants c
                GROUP BY p.batter, p.stand
                HAVING COUNT(*) > 150
            ),
            hitter_ranked AS (
                SELECT 
                    hb.*,
                    -- UNIVERSAL Z-SCORE CALCULATION
                    (hb.stabilized_ev - 88.5) / 3.5 as ev_z,
                    (hb.stabilized_woba - 0.320) / 0.045 as woba_z,
                    (hb.barrel_rate_raw - 0.075) / 0.040 as barrel_z,       
                    -- Percentiles (kept for existing columns)
                    ROUND((PERCENT_RANK() OVER (ORDER BY avg_ev))::numeric, 2) * 100 AS ev_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY barrel_rate_raw))::numeric, 2) * 100 AS barrel_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY stabilized_woba))::numeric, 2) * 100 AS woba_reliability_pct,
                    ROUND((1 - PERCENT_RANK() OVER (ORDER BY chase_pct_raw))::numeric, 2) * 100 AS discipline_pct,     
                    ROUND((PERCENT_RANK() OVER (ORDER BY first_pitch_swing_raw))::numeric, 2) * 100 AS aggression_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY woba_high_raw))::numeric, 2) * 100 AS high_ball_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY woba_low_raw))::numeric, 2) * 100 AS low_ball_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY pull_pct_raw))::numeric, 2) * 100 AS pull_pct,      
                    ROUND((PERCENT_RANK() OVER (ORDER BY two_strike_contact_raw))::numeric, 2) * 100 AS battle_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY clutch_woba_raw))::numeric, 2) * 100 AS clutch_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY neutrality_raw))::numeric, 2) * 100 as neutrality_pct,       
                    ROUND((PERCENT_RANK() OVER (ORDER BY woba_vs_hard))::numeric, 2) * 100 as woba_hard_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY woba_vs_break))::numeric, 2) * 100 as woba_break_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY woba_vs_offspeed))::numeric, 2) * 100 as woba_offspeed_pct
                FROM hitter_base_stats hb
            )
            SELECT 
                CONCAT(pn.first_name_chadwick, ' ', pn.last_name_chadwick) AS full_name,
                hr.bat_side as hand,
                hr.*,
                -- UNIVERSAL ANCHOR: Matches Pitcher Model Scale
                ((hr.woba_z * 0.5) + (hr.barrel_z * 0.3) + (hr.ev_z * 0.2)) as combined_scouting_z,
                CASE 
                    WHEN total_pitches_faced > 1500 THEN 'VERIFIED ELITE SAMPLE'
                    WHEN total_pitches_faced > 600 THEN 'STABILIZED'
                    ELSE 'PROVISIONAL (Small Sample)'
                END as data_confidence,
                CASE 
                    WHEN avg_la > 18 THEN 'UPPERCUT (Flyball)'
                    WHEN avg_la < 8 THEN 'DOWNWARD (Groundball)'
                    ELSE 'LEVEL (Line Drive)'
                END AS swing_plane,
                CASE 
                    WHEN battle_pct > 80 THEN 'ELITE SPOILER'
                    WHEN battle_pct < 25 THEN 'FREE SWINGER'
                    ELSE 'STANDARD'
                END AS two_strike_identity,
                CASE
                    WHEN high_ball_pct > 75 AND low_ball_pct < 40 THEN 'HIGH-BALL HUNTER'
                    WHEN low_ball_pct > 75 AND high_ball_pct < 40 THEN 'LOW-BALL GOLFER'
                    ELSE 'ALL-ZONE THREAT'
                END AS vertical_profile
            FROM hitter_ranked hr
            JOIN dim_player pn ON hr.batter = pn.key_mlbam
            ORDER BY combined_scouting_z DESC;
            """)
            df = pd.read_sql(query, engine)
            
            return run_hitter_scouting_model(df)

        # Execute function
        hitter_archetypes = update_dim_hitter_archetypes(engine)

        # Add the calculation_date
        hitter_archetypes['calculation_date'] = datetime.now()

        # Load to SQL
        hitter_archetypes.to_sql(
        'dim_hitter_archetypes', 
        engine, 
        if_exists='replace',
        index=False, 
        chunksize=5000
        )
        
        print(f"   ✅ Successfully added {len(hitter_archetypes)} new rows of data.")

    except Exception as e:
        print(f"   ❌ ETL Failed during extraction or loading: {e}")