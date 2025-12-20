import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from datetime import datetime

def update_dim_pitcher_archetypes(engine: Engine):
    """
    Groups pitchers into 8 archetypes and updates the database.
    Now includes an 'updated_at' column to track the last run date.
    """
    
    # 1. Pull unique pitcher stats
    # query = """
    # SELECT 
    #     pitcher,
    #     AVG(release_speed) as avg_velo, 
    #     AVG(release_spin_rate) as avg_spin, -- The spin rate of a pitch measured in revolutions per minute (rpm) at the moment of release
    #     AVG(pfx_x) as avg_horiz_mvmt, -- Horizontal movement in feet from the catcher's perspective
    #     AVG(pfx_z) as avg_vert_mvmt -- Vertical movement from the catcher's perpsective.
    # FROM fact_statcast_pitches
    # WHERE release_speed IS NOT NULL 
    #     AND release_spin_rate IS NOT NULL
    #     AND pfx_x IS NOT NULL 
    #     AND pfx_z IS NOT NULL
    # GROUP BY pitcher
    # HAVING COUNT(*) > 100 
    # """
    
    query = """
    WITH pitcher_names AS (
    SELECT 
        key_mlbam, 
        CONCAT(first_name_chadwick, ' ', last_name_chadwick) as full_name 
    FROM dim_player
    )
    SELECT 
        p.pitcher,
        pn.full_name,
        AVG(p.release_speed) as avg_velo, 
        AVG(p.release_spin_rate) as avg_spin, -- The spin rate of a pitch measured in revolutions per minute (rpm) at the moment of release
        AVG(p.pfx_x) as avg_horiz_mvmt, -- Horizontal movement in feet from the catcher's perspective
        AVG(p.pfx_z) as avg_vert_mvmt -- Vertical movement from the catcher's perpsective.
    FROM fact_statcast_pitches p
    JOIN pitcher_names pn ON p.pitcher = pn.key_mlbam
    GROUP BY p.pitcher, pn.full_name
    HAVING COUNT(*) > 100
    """
    
    pitcher_stats = pd.read_sql(query, engine)

    # 2. Scale the data
    scaler = StandardScaler()
    features = ['avg_velo', 'avg_spin', 'avg_horiz_mvmt', 'avg_vert_mvmt']
    scaled_data = scaler.fit_transform(pitcher_stats[features])

    # 3. Create 8 Archetypes
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    pitcher_stats['archetype_id'] = kmeans.fit_predict(scaled_data)

    # 4. Map IDs and Add Timestamp
    archetype_map = {
        0: "Power Flamethrower",
        1: "Sinker / Tail Specialist",
        2: "Breaking Ball Specialist",
        3: "Standard Control Righty",
        4: "Position Player / Eephus",
        5: "Deceptive Angle Specialist",
        6: "Low-Spin / Heavy Sinker",
        7: "Power Slider / Sweeper"
    }
    pitcher_stats['archetype_name'] = pitcher_stats['archetype_id'].map(archetype_map)
    
    # Add the current timestamp to every row
    pitcher_stats['calculation_date'] = datetime.now()

    # 5. Database Update (Truncate and Append)
    with engine.connect() as conn:
        try:
            conn.execute(text("TRUNCATE TABLE dim_pitcher_archetypes;"))
            conn.commit()
            print("Refreshing existing dim_pitcher_archetypes table...")
        except Exception:
            print("Table 'dim_pitcher_archetypes' not found. Creating it for the first time...")
            conn.rollback()

    # Upload data including the new column
    pitcher_stats[['pitcher', 'full_name', 'archetype_id', 'archetype_name', 'calculation_date']].to_sql(
        'dim_pitcher_archetypes', 
        engine, 
        if_exists='append', 
        index=False
    )

    # 6. Ensure the Primary Key is set
    pk_check = """
    SELECT count(*) 
    FROM information_schema.table_constraints 
    WHERE table_name='dim_pitcher_archetypes' AND constraint_type='PRIMARY KEY';
    """
    with engine.connect() as conn:
        has_pk = conn.execute(text(pk_check)).scalar()
        if has_pk == 0:
            conn.execute(text("ALTER TABLE dim_pitcher_archetypes ADD PRIMARY KEY (pitcher);"))
            conn.commit()
            print("✅ Primary Key (pitcher) established.")

    print(f"✅ Successfully categorized {len(pitcher_stats)} pitchers.")