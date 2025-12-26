import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy.engine import Engine
from sqlalchemy import text
from datetime import date, timedelta
from datetime import datetime
import joblib
import os

from dotenv import load_dotenv

def create_dim_pitcher_archetypes(engine: Engine):
    try:
        print("💾 Creating dim_pitcher_archetype...")
        def run_scouting_model(df):
            """
            Synthesizes pitching identity (GMM) with performance outcomes (Whiff/Barrel),
            Perceived Power (Extension), and Vertical Separation.
            """
            # 1. Identity Features
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

            # 1. Load the "Frozen" Models
            # scaler = joblib.load('pitcher_scaler_v1.pkl')
            # gmm    = joblib.load('pitcher_model_v1.pkl')
            
            # # This gets the path to the 'utils' folder
            # CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

            # # This moves UP one level to 'Source', then DOWN into 'input'
            # # It creates an absolute path that works regardless of where you run main.py from
            # SCALER_PATH = os.path.join(CURRENT_DIR, '..', 'input', 'pitcher_scaler_v1.pkl')
            # MODEL_PATH = os.path.join(CURRENT_DIR, '..', 'input', 'pitcher_model_v1.pkl')

            # # Now load using these constructed paths
            # scaler = joblib.load(SCALER_PATH)
            # gmm    = joblib.load(MODEL_PATH)
            
            # 1. Load the .env file 
            # Since .env is in the same folder as this script, we can just load it
            load_dotenv()

            # 2. Get the path from the environment variable
            # If it's not found, we provide a 'fallback' default
            input_folder = os.getenv('INPUT_DIR', '../input')

            # 3. Construct the full paths to your files
            # We use abspath to make sure Python doesn't get confused by the current working directory
            base_path = os.path.dirname(os.path.abspath(__file__))
            scaler_path = os.path.abspath(os.path.join(base_path, input_folder, 'pitcher_scaler_v1.pkl'))
            model_path = os.path.abspath(os.path.join(base_path, input_folder, 'pitcher_model_v1.pkl'))

            # 4. Load the files
            scaler = joblib.load(scaler_path)
            gmm    = joblib.load(model_path)
            
            # 3. Clustering (Archetype Definition)
            #scaler = StandardScaler()
            # Filling NaNs with 0 to ensure the scaler doesn't fail
            # scaled_identity = scaler.fit_transform(df[identity_features].fillna(0))
            
            # 2. Use the frozen scaler (DO NOT use fit_transform)
            # We use .transform() so we measure new data by OLD standards
            scaled_identity = scaler.transform(df[identity_features].fillna(0))
                
            # gmm = GaussianMixture(n_components=7, random_state=42)
            # df['style_cluster'] = gmm.fit_predict(scaled_identity)
            
            # 3. Use the frozen GMM (DO NOT use fit_predict)
            # This ensures Cluster 2 ALWAYS = "Heavy Sinker Specialist"
            df['style_cluster'] = gmm.predict(scaled_identity)

            
            # # Save the scaler and model for future use
            # joblib.dump(scaler, 'pitcher_scaler_v1.pkl')
            # joblib.dump(gmm, 'pitcher_model_v1.pkl')
            # print(" Models saved to your project folder!")

            # 4. Define the Tactical Labels (Mapped from your Profile Results)
            cluster_map = {
                    0: "Diverse Technician",
                    1: "High-Octane Power Arm",
                    2: "Elite Contact Manager",
                    3: "Corner Specialist",
                    4: "Vertical Specialist",
                    5: "Versatile Tactician",
                    6: "Vertical Power Lead"
                }
            df['pitcher_archetype_label'] = df['style_cluster'].map(cluster_map)

            # 5. Outlier Detection
            iso = IsolationForest(contamination=0.04, random_state=42)
            df['is_unicorn'] = iso.fit_predict(scaled_identity)
            
            # def profile_pitcher_clusters(df):
            #     """Temporary function to profile the clusters.

            #     Args:
            #         df (_type_): _description_

            #     Returns:
            #         _type_: _description_
            #     """
            #     # Defining the tactical metrics I want to see              
            #     profile_metrics = [
            #     'style_cluster', 
            #     # DNA
            #     'ffour_usage', 'sinker_usage', 'ffour_vaa_pct', 'velo_gap_pct', 'paint_pct',
            #     # RESULTS
            #     'fb_velo', 'whiff_pct', 'suppression_pct']
                
            #     # Calculate the mean for each cluster
            #     profile = df[profile_metrics].groupby('style_cluster').mean().round(2)
                
            #     # Sort by whiff_pct to see the "Dominance Hierarchy"
            #     #return profile.sort_values(by='whiff_pct', ascending=False)
            #     return df[profile_metrics].groupby('style_cluster').mean().round(2)
            
            # # Usage:
            # pitcher_profile_table = profile_pitcher_clusters(df)
            # print(pitcher_profile_table)
            
            # 6. Grading Logic
            def calculate_pitcher_grade(row):
                stuff_plus = row['stuff_plus_pct']
                location_plus = row['location_plus_pct']
                
                base_score = (stuff_plus * 0.60) + (location_plus * 0.40)
                
                if row.get('is_starter') == 1: base_score += 5 
                if row.get('total_appearances', 0) < 5: base_score -= 10 

                if base_score >= 85: grade = 'A+'
                elif base_score >= 75: grade = 'A'
                elif base_score >= 60: grade = 'B'
                elif base_score >= 45: grade = 'C'
                else: grade = 'F'
                    
                return grade, stuff_plus, location_plus

            df[['overall_grade', 'stuff_plus_final', 'location_plus_final']] = df.apply(
                lambda x: pd.Series(calculate_pitcher_grade(x)), axis=1
            )

            # 7. Scouting Report Generation
            def generate_scouting_report(row):
                tags = []
                # Header includes Archetype Label
                summary_header = f"[{row['overall_grade']} {row['pitcher_archetype_label']}] ({row['hand']})"
                
                # Tags
                if row['stuff_plus_pct'] >= 90: tags.append("💣 PURE FILTH")
                if row['location_plus_pct'] >= 90: tags.append("🎯 SURGEON")
                if row['is_unicorn'] == -1: tags.append("🦄 UNICORN")
                
                # Platoon Logic
                platoon = row['platoon_identity']
                if platoon == "MATCHUP PROOF": tags.append("🛡️ PLATOON NEUTRAL")
                elif platoon == "PLATOON SENSITIVE": tags.append("⚠️ SPLIT RISK")

                # Narrative Body
                analysis = f"Tactically identified as a {row['matchup_role']}. "
                if "NORTH-SOUTH" in row['attack_profile']:
                    analysis += "Dominates vertically; elite matchup vs low-ball hitters. "
                elif "EAST-WEST" in row['attack_profile']:
                    analysis += "East-West specialist; ideal for inducing ground balls. "

                tag_str = " | ".join(list(set(tags)))
                return tag_str, f"{summary_header} — TAGS: {tag_str} — SUMMARY: {analysis.strip()}"

            df['archetype_tags'], df['scouting_summary'] = zip(*df.apply(generate_scouting_report, axis=1))
            
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
                    -- UPDATED NEUTRALITY CALCULATION
                    ROUND(
                        (1 - PERCENT_RANK() OVER (
                            ORDER BY ABS(COALESCE(xwoba_vs_lhb, 0.320) - COALESCE(xwoba_vs_rhb, 0.320))
                        ))::numeric, 2
                    ) * 100 as neutrality_pct,
                    
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
                -- MATCHUP COLUMN 1: ATTACK PROFILE (UPDATED LOGIC)
                CASE 
                    WHEN vaa_plus_pct > 70 AND ffour_usage > 40 THEN 'NORTH-SOUTH (High Rise)'
                    WHEN sinker_usage > 25 AND movement_gap_pct > 60 THEN 'EAST-WEST (Heavy Run)'
                    WHEN bb_usage > 35 AND movement_gap_pct > 75 THEN 'LATERAL (Sweeper/Slide)'
                    WHEN tunnel_pct > 75 AND movement_gap_pct > 60 THEN 'DECEPTIVE (Tunneling)'
                    WHEN (vaa_plus_pct BETWEEN 40 AND 60) AND (movement_gap_pct BETWEEN 40 AND 60) THEN 'NEUTRAL/VERSATILE'
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
                    WHEN rs.total_pitches < 800 THEN 'INSUFFICIENT DATA'
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
    