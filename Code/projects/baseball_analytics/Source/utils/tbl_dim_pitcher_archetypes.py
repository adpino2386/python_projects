import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy.engine import Engine
from sqlalchemy import text
from datetime import date, timedelta
from datetime import datetime

def create_dim_pitcher_archetypes(engine: Engine):
    try:
        print("💾 Creating dim_pitcher_archetype...")
        def run_scouting_model(df):
            """
            Synthesizes pitching identity (GMM) with performance outcomes (Whiff/Barrel),
            Perceived Power (Extension), and Vertical Separation.
            """
            
            # 1. Identity Features (Physical & Tactical only)
            identity_features = [
                'ffour_usage', 'sinker_usage', 'bb_usage', 'offspeed_usage',
                'ffour_vaa_pct', 'sinker_vaa_pct', 'bb_vaa_pct', 'offspeed_vaa_pct',
                'velo_gap_pct', 'command_pct', 'paint_pct'
            ]
            
            # 2. Effectiveness Scores
            df['lethality_score'] = (
                (df['whiff_pct'] * 0.75) + 
                (df['suppression_pct'] * 0.20) + 
                (df['velo_pct'] * 0.05)
            ).round(1)

            # 3. Clustering (Archetype Definition)
            scaler = StandardScaler()
            scaled_identity = scaler.fit_transform(df[identity_features].fillna(0))
            
            gmm = GaussianMixture(n_components=7, random_state=42)
            df['style_cluster'] = gmm.fit_predict(scaled_identity)

            # 4. Outlier Detection (Unicorns)
            iso = IsolationForest(contamination=0.04, random_state=42)
            df['is_unicorn'] = iso.fit_predict(scaled_identity)
            
            # def calculate_pitcher_grade(row):
            #     # 1. Lethality (Results)
            #     # We give more weight to Suppression for Starters to reward Skubal's profile
            #     lethality = (row['whiff_pct'] * 0.5 + row['suppression_pct'] * 0.4 + row['movement_gap_pct'] * 0.1)
                
            #     # 2. Physicality (Tools)
            #     physicality = (row['perceived_velo_pct'] * 0.45 + row['ffour_vaa_pct'] * 0.45 + row['extension_pct'] * 0.1)
                
            #     # 3. Execution (Stability)
            #     #execution = (row['command_pct'] * 0.45 + row['paint_pct'] * 0.45 + row['neutrality_pct'] * 0.1)
                
            #     # Execution: Now includes Tunneling (0-100 percentile)
            #     # Give Tunneling 20% of the Execution weight
            #     execution = (row['command_pct'] * 0.35 + 
            #                  row['paint_pct'] * 0.35 + 
            #                  row['tunnel_pct'] * 0.20 + 
            #                  row['neutrality_pct'] * 0.10)
                
            #     # 4. Weighted GPA Score
            #     base_gpa = (lethality * 0.50) + (physicality * 0.30) + (execution * 0.20)
                
            #     # 5. THE STARTER CURVE (The "Skubal Adjustment")
            #     # If they are a starter, we boost their GPA by 5 points to account for the difficulty of volume
            #     if row['is_starter'] == 1:
            #         base_gpa += 5
                
            #     # 2. THE "SAMPLE SIZE" PENALTY (NEW)
            #     # If a pitcher has fewer than 5 appearances, they cannot get an A+ 
            #     # because the data isn't "stable" yet.
            #     if row['total_appearances'] < 5:
            #         base_gpa -= 10
                
            #     # 6. Final Mapping (More generous thresholds for A+)
            #     if base_gpa >= 85: return 'A+'
            #     elif base_gpa >= 75: return 'A'
            #     elif base_gpa >= 63: return 'B'  # Slightly wider B range
            #     elif base_gpa >= 50: return 'C'
            #     elif base_gpa >= 35: return 'D'
            #     else: return 'F'
            
            def calculate_pitcher_grade(row):
                # 1. STUFF+ (Physicality)
                # This is the "Weapon" - 60% of the overall grade
                stuff_plus = row['stuff_plus_pct']
                
                # 2. LOCATION+ (Surgicality)
                # This is the "Aim" - 40% of the overall grade
                location_plus = row['location_plus_pct']
                
                # 3. PITCHING+ (The Master Score)
                # Note: We weigh Stuff higher because it's harder to find/teach
                base_score = (stuff_plus * 0.60) + (location_plus * 0.40)
                
                # 4. VOLUME/STARTER ADJUSTMENTS
                if row['is_starter'] == 1:
                    base_score += 5  # The "Skubal Boost"
                
                if row['total_appearances'] < 5:
                    base_score -= 10 # The "Sample Size Penalty"

                # 5. FINAL LETTER GRADE
                if base_score >= 85: 
                    grade = 'A+'
                elif base_score >= 75: 
                    grade = 'A'
                elif base_score >= 60: 
                    grade = 'B'
                elif base_score >= 45: 
                    grade = 'C'
                else: 
                    grade = 'F'
                    
                return grade, stuff_plus, location_plus

            #df['overall_grade'] = df.apply(calculate_pitcher_grade, axis=1)
            df[['overall_grade', 'stuff_plus_final', 'location_plus_final']] = df.apply(
                lambda x: pd.Series(calculate_pitcher_grade(x)), axis=1
            )

            # def generate_scouting_report(row):
            #     tags = []
            #     summary = f"[{row['overall_grade']} GRADE] "
                
            #     # 1. Framework Identity
            #     s_plus = row['stuff_plus_pct']
            #     l_plus = row['location_plus_pct']
                
            #     # THE "STUFF" LABELS
            #     if s_plus >= 90:
            #         tags.append("💣 PURE FILTH")
            #     elif s_plus <= 20:
            #         tags.append("📉 LACKS BITE")

            #     # THE "LOCATION" LABELS
            #     if l_plus >= 90:
            #         tags.append("🎯 SURGEON")
            #     elif l_plus <= 20:
            #         tags.append("🏹 WILD THING")

            #     # 2. COMBINATION SCOUTING (The "Pitching+" Profiles)
            #     if s_plus >= 85 and l_plus >= 85:
            #         tags.append("👑 DOMINANT FORCE")
            #         summary += "A rare combination of elite physical tools and surgical precision. "
                
            #     elif s_plus >= 85 and l_plus <= 40:
            #         tags.append("💎 RAW DIAMOND")
            #         summary += "Elite stuff that is currently unrefined; a primary candidate for a pitching lab overhaul. "
                    
            #     elif l_plus >= 85 and s_plus <= 40:
            #         tags.append("🎓 THE PROFESSOR")
            #         summary += "Succeeds through elite sequencing and location despite below-average raw velocity. "

            #     # 3. KEEPING YOUR FAVORITES
            #     if row['tunnel_pct'] >= 90: tags.append("🧬 TUNNELER")
            #     if row['is_unicorn'] == -1: tags.append("🦄 UNICORN")
                
            #     return " | ".join(list(set(tags))), summary.strip()

            def generate_scouting_report(row):
                tags = []
                # Start the summary with the Grade and Handedness
                summary_header = f"[{row['overall_grade']} GRADE] ({row['hand']})"
                
                # 1. CORE IDENTITY TAGS (Physicality)
                s_plus = row['stuff_plus_pct']
                l_plus = row['location_plus_pct']
                
                if s_plus >= 90: tags.append("PURE FILTH")
                elif s_plus <= 20: tags.append("LACKS BITE")

                if l_plus >= 90: tags.append("SURGEON")
                elif l_plus <= 20: tags.append("WILD THING")

                # 2. MATCHUP TACTICS (New Logic)
                # We use the columns we just built in SQL
                profile = row['attack_profile']
                role = row['matchup_role']
                platoon = row['platoon_identity']
                
                # Build the Narrative Summary
                analysis = f"Identified as a {role}. "
                
                if "NORTH-SOUTH" in profile:
                    analysis += "Wins vertically with high-carry fastballs; elite matchup against low-ball hitters. "
                elif "EAST-WEST" in profile:
                    analysis += "Heavy horizontal movement profile; ideal for inducing double plays. "
                
                if platoon == "MATCHUP PROOF":
                    tags.append("PLATOON NEUTRAL")
                    analysis += "Maintains effectiveness regardless of batter handedness. "
                elif platoon == "PLATOON SENSITIVE":
                    tags.append("SPLIT RISK")
                    analysis += "Performance drops significantly against opposite-handed hitters. "

                # 3. SPECIAL TRAITS
                if row['tunnel_pct'] >= 90: tags.append("TUNNELER")
                if row['is_unicorn'] == -1: tags.append("UNICORN")
                if row['breakout_potential'] != 'OPTIMIZED':
                    tags.append("BREAKOUT")
                    analysis += f"Tactical Alert: {row['breakout_potential']}. "

                # Create the final string
                tag_str = " | ".join(list(set(tags)))
                final_summary = f"{summary_header} {tag_str} — {analysis.strip()}"
                
                return tag_str, final_summary

            # Apply to your DataFrame
            results = df.apply(generate_scouting_report, axis=1)
            df['archetype_tags'], df['scouting_summary'] = zip(*results)

            # Apply and split into two columns
            results = df.apply(generate_scouting_report, axis=1)
            df['archetype_tags'], df['scouting_summary'] = zip(*results)
            
            # # Apply Logic
            # results = df.apply(generate_scouting_report, axis=1)
            # df['archetype_tags'], df['scouting_summary'] = zip(*results)
            
            return df


        def update_dim_pitcher_archetypes(engine):
            """
            SQL to extract the necessary metrics for the Python model.
            """
            query = text("""
            WITH attack_zone_stats AS (
            SELECT 
                p.*,
                -- Define Command/Paint Zones
                CASE 
                    WHEN ABS(p.plate_x) <= 0.67 AND p.plate_z BETWEEN (p.sz_bot + 0.33) AND (p.sz_top - 0.33) THEN 'heart'
                    WHEN ABS(p.plate_x) <= 1.1 AND p.plate_z BETWEEN (p.sz_bot - 0.33) AND (p.sz_top + 0.33) THEN 'shadow'
                    WHEN ABS(p.plate_x) <= 1.5 AND p.plate_z BETWEEN (p.sz_bot - 0.75) AND (p.sz_top + 0.75) THEN 'chase'
                    ELSE 'waste'
                END as attack_zone,
                CASE WHEN p.description IN ('swinging_strike', 'swinging_strike_blocked', 'missed_bunt') THEN 1 ELSE 0 END as is_whiff,
                CASE WHEN p.description IN ('swinging_strike', 'swinging_strike_blocked', 'missed_bunt', 'foul', 'foul_tip', 'hit_into_play') THEN 1 ELSE 0 END as is_swing
            FROM fact_statcast_pitches p
            ),
            vaa_base_calc AS (
                SELECT 
                    az.*,
                    CASE WHEN az.pitch_type IN ('FA', 'FF', 'FC') THEN 
                        -ATAN((az.vz0 + (az.az * ((-az.vy0 - SQRT(az.vy0^2 - (2 * az.ay * (50 - (17/12))))) / az.ay))) / 
                        (-SQRT(az.vy0^2 - (2 * az.ay * (50 - (17/12)))))) * (180/3.14159) 
                    END as individual_ff_vaa
                FROM attack_zone_stats az
            ),
            aggregated_stats AS (
                SELECT 
                    p.pitcher,
                    p.p_throws,
                    COUNT(*) as total_pitches,        
                    AVG(p.release_extension) as avg_extension,
                    COALESCE(ROUND(AVG(CASE WHEN p.pitch_type IN ('FA', 'FF', 'FT', 'FC', 'SI') THEN p.release_speed + ((p.release_extension - 6.2) * 2) END)::numeric, 1), 0) as perceived_fb_velo,
                    (AVG(CASE WHEN p.pitch_type IN ('FA', 'FF') THEN p.pfx_z * 12 END) - 
                    AVG(CASE WHEN p.pitch_type IN ('CH', 'FS', 'SI') THEN p.pfx_z * 12 END)) as v_break_gap_raw,
                    
                    ROUND(100.0 * SUM(p.is_whiff) / NULLIF(SUM(p.is_swing), 0), 2) as whiff_rate_raw,
                    ROUND(100.0 * SUM(CASE WHEN p.launch_speed_angle = 6 THEN 1 ELSE 0 END) / 
                        NULLIF(SUM(CASE WHEN p.type = 'X' THEN 1 ELSE 0 END), 0), 2) as barrel_rate_raw,        
                    
                    ROUND(100.0 * SUM(CASE WHEN p.attack_zone = 'shadow' THEN 1 ELSE 0 END) / COUNT(*), 1) as paint_raw,
                    ROUND(100.0 * SUM(CASE WHEN p.attack_zone IN ('shadow', 'chase') THEN 1 ELSE 0 END) / COUNT(*), 1) as command_raw,        
                    
                    AVG(CASE WHEN p.stand = 'L' THEN p.estimated_woba_using_speedangle END) as xwoba_vs_lhb,
                    AVG(CASE WHEN p.stand = 'R' THEN p.estimated_woba_using_speedangle END) as xwoba_vs_rhb,           
                    
                    COALESCE(ROUND(AVG(CASE WHEN p.pitch_type IN ('FA', 'FF', 'FT', 'FC', 'SI') THEN p.release_speed END)::numeric, 1), 0) as fb_velo,
                    COALESCE(ROUND(AVG(CASE WHEN p.pitch_type IN ('CH', 'FS', 'FO', 'SC', 'ST', 'SL', 'KC', 'GY', 'SV', 'CS', 'KN', 'EP') THEN p.release_speed END)::numeric, 1), 0) as offspeed_velo,                                                                                                                                                                    
                    
                    ROUND(100.0 * SUM(CASE WHEN p.pitch_type IN ('FA', 'FF', 'FC') THEN 1 ELSE 0 END) / COUNT(*), 1) as ffour_usage,
                    ROUND(100.0 * SUM(CASE WHEN p.pitch_type IN ('SI', 'FT') THEN 1 ELSE 0 END) / COUNT(*), 1) as sinker_usage,
                    ROUND(100.0 * SUM(CASE WHEN p.pitch_type IN ('CU', 'SL', 'KC', 'ST', 'SV', 'CS', 'KN') THEN 1 ELSE 0 END) / COUNT(*), 1) as bb_usage,
                    ROUND(100.0 * SUM(CASE WHEN p.pitch_type IN ('CH', 'FS', 'FO', 'SC', 'ST', 'SL', 'KC', 'GY', 'SV', 'CS', 'KN', 'EP') THEN 1 ELSE 0 END) / COUNT(*), 1) as offspeed_usage,        
                    
                    COALESCE(ROUND(AVG(CASE WHEN p.pitch_type IN ('FA', 'FF', 'FT', 'FC', 'SI') THEN p.release_speed END)::numeric - 
                                AVG(CASE WHEN p.pitch_type IN ('CH', 'FS', 'FO', 'SC', 'ST', 'SL', 'KC', 'GY', 'SV', 'CS', 'KN', 'EP') THEN p.release_speed END)::numeric, 1), 0) as velo_gap,        
                    COALESCE(ROUND(AVG(p.individual_ff_vaa)::numeric, 2), 0) as ffour_vaa,
                    COALESCE(ROUND(AVG(CASE WHEN p.pitch_type IN ('SI', 'FT') THEN -ATAN((p.vz0 + (p.az * ((-p.vy0 - SQRT(p.vy0^2 - (2 * p.ay * (50 - (17/12))))) / p.ay))) / (-SQRT(p.vy0^2 - (2 * p.ay * (50 - (17/12)))))) * (180/3.14159) END)::numeric, 2), 0) as sinker_vaa,
                    COALESCE(ROUND(AVG(CASE WHEN p.pitch_type IN ('CU', 'SL', 'KC', 'ST', 'SV', 'CS', 'KN') THEN -ATAN((p.vz0 + (p.az * ((-p.vy0 - SQRT(p.vy0^2 - (2 * p.ay * (50 - (17/12))))) / p.ay))) / (-SQRT(p.vy0^2 - (2 * p.ay * (50 - (17/12)))))) * (180/3.14159) END)::numeric, 2), 0) as bb_vaa,
                    COALESCE(ROUND(AVG(CASE WHEN p.pitch_type IN ('CH', 'FS', 'FO', 'SC', 'EP') THEN -ATAN((p.vz0 + (p.az * ((-p.vy0 - SQRT(p.vy0^2 - (2 * p.ay * (50 - (17/12))))) / p.ay))) / (-SQRT(p.vy0^2 - (2 * p.ay * (50 - (17/12)))))) * (180/3.14159) END)::numeric, 2), 0) as offspeed_vaa,

                    COUNT(DISTINCT game_pk) as total_appearances,
                    (COUNT(*) / COUNT(DISTINCT game_pk)) as avg_pitches_per_app,
                    CASE WHEN (COUNT(*) / COUNT(DISTINCT game_pk)) >= 40 AND COUNT(DISTINCT game_pk) >= 3 THEN 1 ELSE 0 END as is_starter,
                    
                    STDDEV(p.release_pos_x) as release_x_std,
                    STDDEV(p.release_pos_z) as release_z_std,
                    (STDDEV(p.release_pos_x) + STDDEV(p.release_pos_z)) as tunnel_raw,
                    AVG(p.individual_ff_vaa - ((-0.68 * p.plate_z) - 3.8)) as vaa_above_expected_raw,       
                    -- RAW STUFF+ (Process)
                    ( (AVG(p.release_speed) * 0.4) + (AVG(p.release_extension) * 0.2) + (AVG(ABS(p.pfx_x)) * 12 * 0.2) + (AVG(p.pfx_z) * 12 * 0.2) ) as stuff_raw,
                    -- RAW LOCATION+ (Process)
                    ( (SUM(CASE WHEN p.attack_zone = 'shadow' THEN 1 ELSE 0 END)::float / COUNT(*)) * 0.6 + (SUM(CASE WHEN p.attack_zone = 'heart' THEN 0 ELSE 1 END)::float / COUNT(*)) * 0.4 ) as location_raw

                FROM vaa_base_calc p
                GROUP BY p.pitcher, p.p_throws
                HAVING COUNT(*) > 100 AND AVG(p.release_speed) > 84
            ),
            ranked_stats AS (
                SELECT 
                    ast.*,
                    ROUND((PERCENT_RANK() OVER (ORDER BY fb_velo))::numeric, 2) * 100 as velo_pct,
                    COALESCE(ROUND((PERCENT_RANK() OVER (PARTITION BY (offspeed_usage > 0) ORDER BY offspeed_velo))::numeric, 2) * 100, 0) as offspeed_velo_pct,
                    COALESCE(ROUND((PERCENT_RANK() OVER (PARTITION BY (offspeed_usage > 0) ORDER BY velo_gap))::numeric, 2) * 100, 0) as velo_gap_pct,                   
                    ROUND((PERCENT_RANK() OVER (ORDER BY whiff_rate_raw))::numeric, 2) * 100 as whiff_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY barrel_rate_raw DESC))::numeric, 2) * 100 as suppression_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY command_raw))::numeric, 2) * 100 as command_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY paint_raw))::numeric, 2) * 100 as paint_pct,            
                    ROUND((PERCENT_RANK() OVER (ORDER BY perceived_fb_velo))::numeric, 2) * 100 as perceived_velo_pct,
                    COALESCE(ROUND((PERCENT_RANK() OVER (PARTITION BY (offspeed_usage > 0 OR sinker_usage > 0) ORDER BY v_break_gap_raw))::numeric, 2) * 100, 0) as movement_gap_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY avg_extension))::numeric, 2) * 100 as extension_pct,           
                    COALESCE(ROUND((PERCENT_RANK() OVER (PARTITION BY (ffour_usage > 0) ORDER BY ffour_vaa))::numeric, 2) * 100, 0) as ffour_vaa_pct,
                    COALESCE(ROUND((PERCENT_RANK() OVER (PARTITION BY (sinker_usage > 0) ORDER BY sinker_vaa DESC))::numeric, 2) * 100, 0) as sinker_vaa_pct,
                    COALESCE(ROUND((PERCENT_RANK() OVER (PARTITION BY (bb_usage > 0) ORDER BY bb_vaa DESC))::numeric, 2) * 100, 0) as bb_vaa_pct,
                    COALESCE(ROUND((PERCENT_RANK() OVER (PARTITION BY (offspeed_usage > 0) ORDER BY offspeed_vaa DESC))::numeric, 2) * 100, 0) as offspeed_vaa_pct,
                    ROUND((100 - (ABS(COALESCE(xwoba_vs_lhb, 0.320) - COALESCE(xwoba_vs_rhb, 0.320)) * 100))::numeric, 2) as neutrality_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY tunnel_raw DESC))::numeric, 2) * 100 as tunnel_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY vaa_above_expected_raw))::numeric, 2) * 100 as vaa_plus_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY stuff_raw))::numeric, 2) * 100 as stuff_plus_pct,
                    ROUND((PERCENT_RANK() OVER (ORDER BY location_raw))::numeric, 2) * 100 as location_plus_pct
                FROM aggregated_stats ast
            )
            SELECT 
                CONCAT(pn.first_name_chadwick, ' ', pn.last_name_chadwick) as full_name,
                rs.p_throws as hand,
                rs.*,
                -- MATCHUP COLUMN 1: ATTACK PROFILE (Rise vs Run)
                CASE 
                    WHEN vaa_plus_pct > 75 THEN 'NORTH-SOUTH (High Rise)'
                    WHEN sinker_usage > 25 THEN 'EAST-WEST (Sinker/Run)'
                    WHEN movement_gap_pct > 75 THEN 'DECEPTIVE (High Break)'
                    ELSE 'BALANCED'
                END as attack_profile,
                -- MATCHUP COLUMN 2: ROLE IDENTITY
                CASE 
                    WHEN rs.whiff_pct > 75 AND rs.location_plus_pct > 75 THEN 'DOMINANT ACE'
                    WHEN rs.whiff_pct > 75 AND rs.location_plus_pct < 40 THEN 'POWER ARMS (High Risk)'
                    WHEN rs.location_plus_pct > 75 AND rs.whiff_pct < 45 THEN 'PITCH TO CONTACT SURGEON'
                    ELSE 'ROTATION STABILIZER'
                END as matchup_role,
                -- MATCHUP COLUMN 3: PLATOON RESISTANCE
                CASE 
                    WHEN rs.neutrality_pct > 75 THEN 'MATCHUP PROOF'
                    WHEN rs.neutrality_pct < 35 THEN 'PLATOON SENSITIVE'
                    ELSE 'STANDARD SPLITS'
                END as platoon_identity,
                ROUND((perceived_velo_pct * 0.25 + ffour_vaa_pct * 0.25 + whiff_pct * 0.5), 0) as ffour_quality_score,
                ROUND((movement_gap_pct * 0.25 + offspeed_vaa_pct * 0.25 + whiff_pct * 0.5), 0) as offspeed_quality_score,   
                CASE 
                    WHEN (ffour_vaa_pct > 80 AND ffour_usage < 20) THEN 'UNDERUSED ELITE FASTBALL'
                    WHEN (bb_vaa_pct > 80 AND bb_usage < 15) THEN 'UNDERUSED ELITE BREAKING'
                    WHEN (offspeed_vaa_pct > 80 AND offspeed_usage < 15) THEN 'UNDERUSED ELITE OFFSPD'
                    ELSE 'OPTIMIZED'
                END as breakout_potential
            FROM ranked_stats rs
            JOIN dim_player pn ON rs.pitcher = pn.key_mlbam
            ORDER BY stuff_plus_pct DESC;
            """)
            df = pd.read_sql(query, engine)
            
            return run_scouting_model(df)

        # Execute function
        pitcher_archetype_df = update_dim_pitcher_archetypes(engine)
        
        # Add the calculation_date
        pitcher_archetype_df['calculation_date'] = datetime.now()
        
        # Load to SQL
        pitcher_archetype_df.to_sql(
        'dim_pitcher_archetypes', 
        engine, 
        if_exists='replace',
        index=False, 
        chunksize=5000
        )
            
        print(f"   ✅ Successfully added {len(pitcher_archetype_df)} new rows of data.")

    except Exception as e:
        print(f"   ❌ ETL Failed during extraction or loading: {e}")
    