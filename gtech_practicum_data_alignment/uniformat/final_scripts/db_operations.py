import sqlite3
import pandas as pd
import os

def setup_database(db_name="uniformat.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create uniformat_codes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uniformat_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            level1_code TEXT,
            level1_name TEXT,
            level2_code TEXT,
            level2_name TEXT,
            level3_code TEXT,
            level3_name TEXT,
            level4_code TEXT,
            level4_name TEXT,
            description TEXT,
            notes TEXT
        );
    """)

    # Create uniformat_inclusions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uniformat_inclusions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uniformat_code_id INTEGER,
            inclusion_text TEXT,
            FOREIGN KEY (uniformat_code_id) REFERENCES uniformat_codes(id)
        );
    """)

    # Create uniformat_exclusions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uniformat_exclusions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uniformat_code_id INTEGER,
            exclusion_text TEXT,
            FOREIGN KEY (uniformat_code_id) REFERENCES uniformat_codes(id)
        );
    """)

    conn.commit()
    conn.close()
    print(f"Database '{db_name}' and tables created successfully.")


def insert_excel_data_clearing_first(df, db_name="uniformat.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM uniformat_codes;")

    for index, row in df.iterrows():
        cursor.execute("""
            INSERT INTO uniformat_codes (type, level1_code, level1_name, level2_code, level2_name,
                                      level3_code, level3_name, level4_code, level4_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (row['Type'], row['Level 1 Code'], row['Level 1 Name'], row['Level 2 Code'], row['Level 2 Name'],
              row['Level 3 Code'], row['Level 3 Name'], row['Level 4 Code'], row['Level 4 Name']))
    conn.commit()
    conn.close()
    print("Excel data inserted into 'uniformat_codes' table.")


def incorporate_initial_gemini_data_into_db_no_desc(gemini_data, db_name):
    """
    Incorporate extracted inclusions and exclusions into the database.
    Does NOT update the 'description' field in uniformat_codes.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    print("\n--- Incorporating initial Gemini output (inclusions/exclusions only) into database ---")
    for element in gemini_data:
        level3_code_gemini = element.get('level3_code')
        inclusions = element.get('inclusions', [])
        exclusions = element.get('exclusions', [])

        if not level3_code_gemini:
            print(f"Skipping entry due to missing level3_code from Gemini: {element}")
            continue

        # Clean the code from Gemini just in case (strip whitespace)
        level3_code_gemini_cleaned = level3_code_gemini.strip()

        # Find the ID of the corresponding Level 3 element in uniformat_codes
        cursor.execute("""
            SELECT id FROM uniformat_codes
            WHERE level3_code = ?
            LIMIT 1;
        """, (level3_code_gemini_cleaned,))
        uniformat_code_id_result = cursor.fetchone()

        if uniformat_code_id_result:
            uniformat_code_id = uniformat_code_id_result[0]
            # Clear existing inclusions/exclusions for this ID to prevent duplicates on rerun
            cursor.execute("DELETE FROM uniformat_inclusions WHERE uniformat_code_id = ?", (uniformat_code_id,))
            cursor.execute("DELETE FROM uniformat_exclusions WHERE uniformat_code_id = ?", (uniformat_code_id,))

            # Insert inclusions
            for inc_item in inclusions:
                cursor.execute("INSERT INTO uniformat_inclusions (uniformat_code_id, inclusion_text) VALUES (?, ?)",
                               (uniformat_code_id, inc_item.strip()))

            # Insert exclusions
            for exc_item in exclusions:
                cursor.execute("INSERT INTO uniformat_exclusions (uniformat_code_id, exclusion_text) VALUES (?, ?)",
                               (uniformat_code_id, exc_item.strip()))
        else:
            print(f"Warning: No matching ID found in 'uniformat_codes' for Level 3 code '{level3_code_gemini_cleaned}' (from Gemini, len={len(level3_code_gemini_cleaned)}).")
            cursor.execute("SELECT level3_code, LENGTH(level3_code) FROM uniformat_codes WHERE level3_code LIKE ? LIMIT 5;", (f'%{level3_code_gemini_cleaned.replace(" ", "%")}%',))
            fuzzy_matches = cursor.fetchall()
            if fuzzy_matches:
                print(f"   Possible matches in DB (code, length): {fuzzy_matches}. Mismatch is likely due to subtle differences.")
            else:
                print(f"   '{level3_code_gemini_cleaned}' does not appear to exist in DB at all.")
            print("   Skipping enrichment for this element.")

    conn.commit()
    conn.close()
    print("\nInitial Gemini output (inclusions/exclusions) successfully incorporated into database.")


def get_level3_data_for_enhancement(db_name):
    """Retrieves all Level 3 data needed for enhancement from DB."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT level3_code, level3_name, description FROM uniformat_codes WHERE level3_code IS NOT NULL;")
    all_level3_elements_data = []

    for row in cursor.fetchall():
        code = str(row[0]).strip()
        name = row[1]
        current_description = row[2]

        cursor.execute("SELECT id FROM uniformat_codes WHERE level3_code = ? LIMIT 1", (code,))
        uniformat_code_id_result = cursor.fetchone()
        uniformat_code_id = uniformat_code_id_result[0] if uniformat_code_id_result else None

        inclusions = []
        exclusions = []
        if uniformat_code_id:
            cursor.execute("SELECT inclusion_text FROM uniformat_inclusions WHERE uniformat_code_id = ?", (uniformat_code_id,))
            inclusions = [row_inc[0] for row_inc in cursor.fetchall()]
            cursor.execute("SELECT exclusion_text FROM uniformat_exclusions WHERE uniformat_code_id = ?", (uniformat_code_id,))
            exclusions = [row_exc[0] for row_exc in cursor.fetchall()]

        all_level3_elements_data.append({
            'level3_code': code,
            'level3_name': name,
            'current_description': current_description,
            'inclusions': inclusions,
            'exclusions': exclusions
        })

    conn.close()
    return all_level3_elements_data


def update_description_in_db(level3_code, new_description, db_name):
    """Updates the 'description' field in uniformat_codes with the new enhanced description."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    try:
        # --- DEBUG: Verify Description Value Before Update ---
        print(f"--- DEBUG: Updating {level3_code} with new description (first 100 chars):")
        print(new_description[:100])
        print("----------------------------------------------------\n")

        cursor.execute("UPDATE uniformat_codes SET description = ? WHERE level3_code = ?",
                       (new_description, level3_code))
        conn.commit()
        print(f"Enhanced description successfully updated for {level3_code}.")
    except Exception as e:
        print(f"Error updating description for {level3_code}: {e}")
    finally:
        conn.close()