# Reset script for Decentralized Campus Resource Booking System
# Clears test bookings from cse.db, it.db, entc.db and removes duplicate resources.
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\reset_demo_data.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESETTING DEMO DATA (PINE DB BASELINE & DEDUPLICATION) " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$dbPaths = @(
    "backend/department_nodes/cse_node/database/cse.db",
    "backend/department_nodes/it_node/database/it.db",
    "backend/department_nodes/etc_node/database/entc.db"
)

foreach ($dbPath in $dbPaths) {
    if (Test-Path $dbPath) {
        Write-Host "Processing $dbPath ..." -ForegroundColor Yellow
        python -c "
import sqlite3
conn = sqlite3.connect('$dbPath')
cursor = conn.cursor()

# 1. Clear all test bookings
cursor.execute('DELETE FROM bookings;')
cursor.execute(\"DELETE FROM sqlite_sequence WHERE name='bookings';\")

# 2. Deduplicate resources (keep min id per name and department)
cursor.execute('''
    DELETE FROM resources
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM resources
        GROUP BY name, department
    );
''')

conn.commit()
cursor.execute('SELECT COUNT(*) FROM bookings;')
b_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM resources;')
r_count = cursor.fetchone()[0]
conn.close()
print(f'   -> Bookings: {b_count} rows | Unique Resources: {r_count} rows')
"
    } else {
        Write-Host "Database $dbPath not found, skipping." -ForegroundColor Gray
    }
}

Write-Host "`nDemo database reset completed successfully! Initial bookings = 0 across all department nodes." -ForegroundColor Green
