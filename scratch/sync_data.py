import sqlite3

db_path = r'd:\FIT-TPMS\FIT-TPMS\FIT-TPMS.db'

def run_sync():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Starting synchronization...")
    
    # 1. Get all approved registrations
    cursor.execute("""
        SELECT r.id as reg_id, r.student_id, r.lecturer_id, r.semester_id, r.course_type_id
        FROM registrations r
        WHERE r.status = 'approved'
    """)
    approved_regs = cursor.fetchall()
    print(f"Found {len(approved_regs)} approved registrations.")
    
    synced_count = 0
    already_synced = 0
    ambiguous_count = 0
    
    for reg in approved_regs:
        sid = reg['student_id']
        lid = reg['lecturer_id']
        sem_id = reg['semester_id']
        ct_id = reg['course_type_id']
        
        # Check if student is already in a class for this semester
        cursor.execute("""
            SELECT cs.class_id 
            FROM class_students cs
            JOIN classes c ON cs.class_id = c.id
            WHERE cs.student_id = ? AND c.semester_id = ?
        """, (sid, sem_id))
        existing = cursor.fetchone()
        
        if existing:
            already_synced += 1
            continue
            
        # Find exactly ONE class for this lecturer/semester/course_type
        cursor.execute("""
            SELECT c.id 
            FROM classes c
            JOIN courses co ON c.course_id = co.id
            WHERE c.lecturer_id = ? AND c.semester_id = ? AND co.course_type_id = ?
        """, (lid, sem_id, ct_id))
        potential_classes = cursor.fetchall()
        
        if len(potential_classes) == 1:
            class_id = potential_classes[0]['id']
            try:
                cursor.execute("""
                    INSERT INTO class_students (class_id, student_id, grade)
                    VALUES (?, ?, NULL)
                """, (class_id, sid))
                synced_count += 1
            except sqlite3.Error as e:
                print(f"Error syncing reg {reg['reg_id']}: {e}")
        elif len(potential_classes) > 1:
            print(f"Ambiguity for reg {reg['reg_id']}: {len(potential_classes)} classes found.")
            ambiguous_count += 1
        else:
            print(f"No class found for reg {reg['reg_id']} (Lec: {lid}, Sem: {sem_id}, Type: {ct_id})")
            
    conn.commit()
    conn.close()
    
    print("\n--- Sync Results ---")
    print(f"Already synced: {already_synced}")
    print(f"Newly synced entries: {synced_count}")
    print(f"Ambiguous cases (skipped): {ambiguous_count}")
    print("Done.")

if __name__ == "__main__":
    run_sync()
